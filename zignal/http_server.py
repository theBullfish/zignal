"""Zignal HTTP service — palace + KG + wake stack over the network.

One palace, one server, one source of truth. Wraps MemoryStack +
KnowledgeGraph + searcher + file_event into a FastAPI service so any
machine on the Tailscale fabric (Z13, Blue, Dread, future) can read
and write the same Zignal palace without filesystem mounts or
divergent local copies.

Run on Temple:
  python3 -m zignal.http_server --host 0.0.0.0 --port 8540

Health:
  curl http://temple:8540/health

Auth:
  None — Tailscale ACL is the boundary. Do not bind to a public iface.

The dialectic plugin's zignot backend speaks this protocol; nothing
else here depends on it. Keep endpoints additive — existing endpoints
must remain wire-compatible.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("zignal_http")


import chromadb  # type: ignore
from fastapi import Body, FastAPI  # type: ignore
from pydantic import BaseModel, Field  # type: ignore


def _patch_chromadb_persistent_data():
    """Coerce legacy dict-shaped HNSW pickles into PersistentData objects.

    Some palaces were written by chromadb 0.5/0.6 versions that left the
    HNSW segment metadata file (`index_metadata.pickle`) as a raw dict
    with ``dimensionality=None``. Newer chromadb's HNSW segment reader
    does ``self._persist_data.dimensionality`` and explodes. We wrap
    ``load_from_file`` so dicts are upgraded to a real ``PersistentData``
    instance with the dimensionality back-filled from the embedding
    function we know is in use (ONNXMiniLM_L6_V2 → 384).
    """
    try:
        from chromadb.segment.impl.vector import local_persistent_hnsw as _hnsw
    except Exception as exc:
        logger.debug("chromadb hnsw not importable: %s", exc)
        return
    PD = getattr(_hnsw, "PersistentData", None)
    if PD is None:
        return
    original = PD.load_from_file

    def _patched(filename: str):
        import pickle as _pickle
        with open(filename, "rb") as f:
            obj = _pickle.load(f)
        if not isinstance(obj, dict):
            return obj
        dim = obj.get("dimensionality")
        if dim is None:
            dim = int(os.environ.get("ZIGNAL_HNSW_DIM", "384"))
        wrapped = PD(
            dimensionality=dim,
            total_elements_added=int(obj.get("total_elements_added") or 0),
            id_to_label=obj.get("id_to_label") or {},
            label_to_id=obj.get("label_to_id") or {},
            id_to_seq_id=obj.get("id_to_seq_id") or {},
        )
        try:
            wrapped.max_seq_id = int(obj.get("max_seq_id") or 0)
        except Exception:
            wrapped.max_seq_id = 0
        return wrapped

    _hnsw.PersistentData.load_from_file = staticmethod(_patched)
    logger.info("chromadb HNSW load_from_file patched (legacy dict → PersistentData)")


_patch_chromadb_persistent_data()

from zignal.config import SignalConfig
from zignal.knowledge_graph import KnowledgeGraph
from zignal.layers import MemoryStack
from zignal.searcher import search_memories as search_fn


# ── Request models (module-scope so Pydantic resolves forward refs) ──

class FileEventIn(BaseModel):
    wing: str
    room: str = "general"
    content: str
    source: str = ""
    added_by: str = "remote"
    dedup_threshold: float = 0.9


class SearchIn(BaseModel):
    query: str
    wing: Optional[str] = None
    room: Optional[str] = None
    n_results: int = 5


class WakeIn(BaseModel):
    wing: Optional[str] = None


class RecallIn(BaseModel):
    wing: Optional[str] = None
    room: Optional[str] = None
    n_results: int = 10


class TripleIn(BaseModel):
    subject: str
    predicate: str
    object: str
    source: str = "remote"
    confidence: float = 1.0
    subject_type: Optional[str] = None
    object_type: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class EntityQueryIn(BaseModel):
    name: str
    as_of: Optional[str] = None
    direction: str = "outgoing"


class RelationshipQueryIn(BaseModel):
    predicate: str
    as_of: Optional[str] = None


class TimelineIn(BaseModel):
    entity_name: Optional[str] = None


class InvalidateIn(BaseModel):
    subject: str
    predicate: str
    object: str
    ended: Optional[str] = None
    reason: Optional[str] = None


def _lazy_imports():
    """Kept for backwards compatibility — imports are now module-scope."""
    return


def build_app(palace_path: Optional[str] = None,
              kg_path: Optional[str] = None,
              collection_name: Optional[str] = None,
              identity_path: Optional[str] = None):
    """Build the FastAPI app bound to the given paths.

    Paths default to SignalConfig's resolution chain (env > config file >
    package defaults) so a fresh Temple install needs no flags.
    """
    _lazy_imports()

    cfg = SignalConfig()
    palace_path = palace_path or cfg.palace_path
    collection_name = collection_name or cfg.collection_name

    app = FastAPI(title="zignal-http", version="0.1.0")
    state: Dict[str, Any] = {
        "palace_path": palace_path,
        "kg_path": kg_path,
        "collection_name": collection_name,
        "identity_path": identity_path,
        "kg": None,
        "stack": None,
        "started_at": time.time(),
    }

    def _kg():
        if state["kg"] is None:
            state["kg"] = KnowledgeGraph(db_path=state["kg_path"])
        return state["kg"]

    def _stack():
        if state["stack"] is None:
            state["stack"] = MemoryStack(
                palace_path=state["palace_path"],
                identity_path=state["identity_path"],
            )
        return state["stack"]

    def _palace_collection():
        client = chromadb.PersistentClient(path=state["palace_path"])
        return client.get_or_create_collection(state["collection_name"])

    # ── Health & status ───────────────────────────────────────────────

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "zignal-http", "version": "0.1.0",
                "palace": state["palace_path"], "collection": state["collection_name"]}

    @app.get("/status")
    def status():
        try:
            col = _palace_collection()
            drawers = col.count()
        except Exception as exc:
            drawers = -1
            logger.warning("status: palace probe failed: %s", exc)
        try:
            kg_stats = _kg().stats()
        except Exception as exc:
            kg_stats = {"error": str(exc)}
        return {
            "drawers": drawers,
            "palace_path": state["palace_path"],
            "collection_name": state["collection_name"],
            "kg_stats": kg_stats,
            "uptime_s": int(time.time() - state["started_at"]),
        }

    # ── Palace operations ────────────────────────────────────────────

    @app.post("/palace/file")
    def palace_file(body: FileEventIn = Body(...)):
        col = _palace_collection()
        content = (body.content or "").strip()
        if not content:
            return {"filed": False, "reason": "empty"}
        try:
            results = col.query(
                query_texts=[content], n_results=1, include=["distances"],
            )
            if results.get("distances") and results["distances"][0]:
                sim = 1.0 - results["distances"][0][0]
                if sim >= body.dedup_threshold:
                    return {"filed": False, "reason": "duplicate", "similarity": sim}
        except Exception:
            pass

        now = datetime.now()
        drawer_id = (
            f"http_{body.wing}_{body.room}_"
            f"{hashlib.md5((content[:100] + now.isoformat()).encode()).hexdigest()[:16]}"
        )
        col.add(
            ids=[drawer_id],
            documents=[content],
            metadatas=[{
                "wing": body.wing,
                "room": body.room,
                "source_file": body.source,
                "added_by": body.added_by,
                "filed_at": now.isoformat(),
            }],
        )
        return {"filed": True, "drawer_id": drawer_id, "wing": body.wing, "room": body.room}

    @app.post("/palace/search")
    def palace_search(body: SearchIn = Body(...)):
        try:
            block = _stack().search(
                body.query, wing=body.wing, room=body.room, n_results=body.n_results,
            )
        except Exception as exc:
            logger.warning("search failed: %s", exc)
            return {"text": "", "error": str(exc)}
        return {"text": block, "query": body.query, "wing": body.wing, "room": body.room}

    @app.post("/palace/search_raw")
    def palace_search_raw(body: SearchIn = Body(...)):
        try:
            res = search_fn(
                body.query,
                palace_path=state["palace_path"],
                wing=body.wing,
                room=body.room,
                n_results=body.n_results,
            )
        except Exception as exc:
            logger.warning("search_raw failed: %s", exc)
            return {"hits": [], "error": str(exc)}
        if not isinstance(res, dict):
            return {"hits": [], "error": "search returned non-dict"}
        if res.get("error"):
            return {"hits": [], "error": res["error"]}
        # zignal.searcher.search_memories returns:
        #   {"query": ..., "filters": ..., "results": [{"text","wing","room",...,"similarity"}, ...]}
        hits = []
        for item in res.get("results") or []:
            sim = item.get("similarity")
            distance = None
            if isinstance(sim, (int, float)):
                distance = 1.0 - float(sim)
            md = {
                "wing": item.get("wing"),
                "room": item.get("room"),
                "source_file": item.get("source_file"),
                "added_by": item.get("added_by"),
                "filed_at": item.get("filed_at"),
            }
            hits.append({
                "content": item.get("text") or item.get("content") or "",
                "metadata": {k: v for k, v in md.items() if v is not None},
                "distance": distance,
            })
        return {"hits": hits}

    @app.post("/palace/recall")
    def palace_recall(body: RecallIn = Body(...)):
        try:
            block = _stack().recall(
                wing=body.wing, room=body.room, n_results=body.n_results,
            )
        except Exception as exc:
            logger.warning("recall failed: %s", exc)
            return {"text": "", "error": str(exc)}
        return {"text": block}

    @app.get("/palace/wake")
    def palace_wake_get(wing: Optional[str] = None):
        try:
            block = _stack().wake_up(wing=wing)
        except Exception as exc:
            logger.warning("wake failed: %s", exc)
            return {"text": "", "error": str(exc)}
        return {"text": block, "wing": wing}

    @app.post("/palace/wake")
    def palace_wake_post(body: WakeIn = Body(...)):
        try:
            block = _stack().wake_up(wing=body.wing)
        except Exception as exc:
            logger.warning("wake failed: %s", exc)
            return {"text": "", "error": str(exc)}
        return {"text": block, "wing": body.wing}

    # ── KG operations ────────────────────────────────────────────────

    @app.post("/kg/triple")
    def kg_triple(body: TripleIn = Body(...)):
        kg = _kg()
        if body.subject_type:
            try:
                kg.add_entity(body.subject, entity_type=body.subject_type,
                              properties=body.properties or None)
            except Exception:
                pass
        if body.object_type:
            try:
                kg.add_entity(body.object, entity_type=body.object_type)
            except Exception:
                pass
        try:
            tid = kg.add_triple(
                subject=body.subject,
                predicate=body.predicate,
                obj=body.object,
                source=body.source,
                confidence=body.confidence,
            )
        except TypeError:
            tid = kg.add_triple(
                body.subject, body.predicate, body.object,
                source=body.source,
            )
        return {"triple_id": str(tid) if tid else "", "ok": True}

    @app.post("/kg/query/entity")
    def kg_query_entity(body: EntityQueryIn = Body(...)):
        kg = _kg()
        try:
            res = kg.query_entity(body.name, as_of=body.as_of, direction=body.direction)
        except Exception as exc:
            return {"results": [], "error": str(exc)}
        return {"results": res or []}

    @app.post("/kg/query/relationship")
    def kg_query_relationship(body: RelationshipQueryIn = Body(...)):
        kg = _kg()
        try:
            res = kg.query_relationship(body.predicate, as_of=body.as_of)
        except Exception as exc:
            return {"results": [], "error": str(exc)}
        return {"results": res or []}

    @app.post("/kg/timeline")
    def kg_timeline(body: TimelineIn = Body(...)):
        try:
            res = _kg().timeline(entity_name=body.entity_name)
        except Exception as exc:
            return {"timeline": [], "error": str(exc)}
        return {"timeline": res or []}

    @app.post("/kg/invalidate")
    def kg_invalidate(body: InvalidateIn = Body(...)):
        try:
            res = _kg().invalidate(
                body.subject, body.predicate, body.object,
                ended=body.ended, reason=body.reason or "",
            )
        except TypeError:
            res = _kg().invalidate(body.subject, body.predicate, body.object)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "result": str(res) if res else ""}

    @app.get("/kg/stats")
    def kg_stats():
        try:
            return {"stats": _kg().stats()}
        except Exception as exc:
            return {"stats": {}, "error": str(exc)}

    return app


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="zignal.http_server")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=int(os.environ.get("ZIGNAL_HTTP_PORT", 8540)))
    p.add_argument("--palace", default=os.environ.get("ZIGNAL_PALACE_PATH"))
    p.add_argument("--kg", default=os.environ.get("ZIGNAL_KG_PATH"))
    p.add_argument("--collection", default=os.environ.get("ZIGNAL_COLLECTION"))
    p.add_argument("--identity", default=os.environ.get("ZIGNAL_IDENTITY_PATH"))
    p.add_argument("--log-level", default="info")
    args = p.parse_args(argv)

    logging.basicConfig(level=args.log_level.upper(),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    import uvicorn  # type: ignore
    app = build_app(
        palace_path=args.palace, kg_path=args.kg,
        collection_name=args.collection, identity_path=args.identity,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    sys.exit(main())
