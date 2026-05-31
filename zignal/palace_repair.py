"""Palace repair — re-embed a chromadb palace whose HNSW pickle is broken.

Some palaces (Brad's Temple, ~8.5k drawers as of 2026-05-21) were written
by chromadb versions that left ``index_metadata.pickle`` with
``dimensionality=None`` and HNSW segment files that segfault current
chromadb when queried.

The documents and metadata are intact in ``chroma.sqlite3``. This module
walks the FTS5 + metadata tables, rebuilds the document set, and writes
to a *fresh* collection with the same configuration. The old collection
is left in place for safety; once the new one is verified, the operator
can swap names.

Run on Temple (where the palace lives):
  python3 -m zignal.palace_repair --palace ~/.signal/palace --suffix _v2

Then point clients at the new collection name.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


logger = logging.getLogger("palace_repair")


def _collect_documents(palace_path: Path) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Read (chromadb_id, document_text, metadata_dict) for every drawer.

    Documents live in the FTS5 contentless table; chromadb stores the
    canonical text per-row alongside the embedding. We pull from
    ``embedding_fulltext_search_content`` which has the text. Metadata is
    pivoted from ``embedding_metadata`` which uses an EAV layout.
    """
    db = palace_path / "chroma.sqlite3"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    # Map chromadb-internal numeric id → external embedding_id (the drawer UUID).
    id_map: Dict[int, str] = {}
    for r in conn.execute("SELECT id, embedding_id FROM embeddings"):
        id_map[r["id"]] = r["embedding_id"]

    # Pull documents — chromadb stores them in embedding_metadata under
    # the "chroma:document" key, and mirrors to the FTS5 content table.
    docs_by_internal: Dict[int, str] = {}
    for r in conn.execute(
        "SELECT id, string_value FROM embedding_metadata "
        "WHERE key='chroma:document' AND string_value IS NOT NULL"
    ):
        docs_by_internal[r["id"]] = r["string_value"]
    if not docs_by_internal:
        # Fallback to FTS5 content table (id column = internal id).
        try:
            for r in conn.execute("SELECT id, c0 FROM embedding_fulltext_search_content"):
                docs_by_internal[r["id"]] = r["c0"] or ""
        except sqlite3.OperationalError:
            pass

    # Pull metadata, pivoting EAV → dict per id.
    metadata_by_internal: Dict[int, Dict[str, Any]] = defaultdict(dict)
    for r in conn.execute(
        "SELECT id, key, string_value, int_value, float_value, bool_value "
        "FROM embedding_metadata"
    ):
        if r["key"] == "chroma:document":
            # chromadb sometimes stashes the doc here too.
            if r["string_value"]:
                docs_by_internal.setdefault(r["id"], r["string_value"])
            continue
        v = (
            r["string_value"] if r["string_value"] is not None else
            r["int_value"]    if r["int_value"]    is not None else
            r["float_value"]  if r["float_value"]  is not None else
            r["bool_value"]
        )
        if v is not None:
            metadata_by_internal[r["id"]][r["key"]] = v

    out: List[Tuple[str, str, Dict[str, Any]]] = []
    for internal_id, ext_id in id_map.items():
        text = docs_by_internal.get(internal_id, "")
        meta = metadata_by_internal.get(internal_id, {})
        if not text.strip():
            continue
        out.append((ext_id, text, meta))
    conn.close()
    return out


def repair(palace_path: Path, source_collection: str, target_collection: str,
           batch_size: int = 64, embedding_function=None) -> Dict[str, Any]:
    import chromadb
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    ef = embedding_function or ONNXMiniLM_L6_V2()
    client = chromadb.PersistentClient(path=str(palace_path))

    try:
        existing = client.get_collection(target_collection)
        existing_count = existing.count()
        if existing_count > 0:
            logger.warning("target collection %s already exists with %d rows; "
                           "delete it manually to re-repair", target_collection, existing_count)
            return {"status": "exists", "count": existing_count}
    except Exception:
        pass

    target = client.get_or_create_collection(
        target_collection, embedding_function=ef
    )

    docs = _collect_documents(palace_path)
    logger.info("repair: %d documents collected from %s", len(docs), palace_path)
    started = time.monotonic()
    written = 0

    for i in range(0, len(docs), batch_size):
        chunk = docs[i:i + batch_size]
        ids = [d[0] for d in chunk]
        texts = [d[1] for d in chunk]
        metas = [d[2] for d in chunk]
        try:
            target.add(ids=ids, documents=texts, metadatas=metas)
            written += len(chunk)
        except Exception as exc:
            logger.warning("batch %d-%d failed: %s; trying per-row", i, i + len(chunk), exc)
            for j, (eid, text, meta) in enumerate(chunk):
                try:
                    target.add(ids=[eid], documents=[text], metadatas=[meta])
                    written += 1
                except Exception as exc2:
                    logger.debug("row %s failed: %s", eid, exc2)
        if (i // batch_size) % 5 == 0:
            elapsed = time.monotonic() - started
            logger.info("repair progress: %d/%d (%.1fs)", written, len(docs), elapsed)

    elapsed = time.monotonic() - started
    final_count = target.count()
    logger.info("repair done: %d/%d written to %s in %.1fs",
                final_count, len(docs), target_collection, elapsed)
    return {
        "status": "ok",
        "source": source_collection,
        "target": target_collection,
        "expected": len(docs),
        "written": final_count,
        "elapsed_s": elapsed,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="zignal.palace_repair")
    p.add_argument("--palace", required=True, help="palace directory path")
    p.add_argument("--source", default="signal_drawers")
    p.add_argument("--target", default=None,
                   help="target collection name (default: <source>_v2)")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--log-level", default="info")
    args = p.parse_args(argv)

    logging.basicConfig(level=args.log_level.upper(),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    palace = Path(args.palace).expanduser()
    if not palace.is_dir():
        print(f"palace path not found: {palace}", file=sys.stderr)
        return 1
    target = args.target or f"{args.source}_v2"
    res = repair(palace, args.source, target, batch_size=args.batch_size)
    print(res)
    return 0 if res.get("status") == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
