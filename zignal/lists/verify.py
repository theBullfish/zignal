"""Continuous surface-consistency probe.

Closes L1.09's named-but-unfixed gap ("one-time close-verification
proves nothing about ongoing consistency"). Reads lists.json
(canonical), compares against:
  - the zignal drawer (most-recent wing=lists room=status entry)
  - the Z13 UNFINISHED_LISTS.md (over SSH if invoked from Temple)

Returns a dict with per-surface status; writes
/mnt/work/zignal/state/lists_verify.json with the result; emits a
divergence row into lists.json's next emit cycle if drift is found.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

CANONICAL = Path("/mnt/work/zignal/state/lists.json")
VERIFY_OUT = Path("/mnt/work/zignal/state/lists_verify.json")
Z13_MEMORY_PATH = "/home/z13/.claude/projects/-home-z13/memory/UNFINISHED_LISTS.md"
Z13_TARGET = "z13@100.106.69.123"
ZIGNAL_HTTP = "http://127.0.0.1:8540"
ZIGNAL_WING = "lists"


def _read_canonical() -> dict[str, Any] | None:
    if not CANONICAL.exists():
        return None
    try:
        return json.loads(CANONICAL.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _read_z13_markdown() -> tuple[str | None, str]:
    """Pull the markdown over SSH. Returns (text, status)."""
    try:
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             Z13_TARGET, f"cat {Z13_MEMORY_PATH}"],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode == 0:
            return proc.stdout, "ok"
        return None, f"ssh_failed:{proc.returncode}"
    except subprocess.TimeoutExpired:
        return None, "ssh_timeout"


def _read_drawer_latest() -> tuple[str | None, str]:
    """Fetch the latest wing=lists drawer content via /palace/search_raw,
    which returns full (untruncated) content. Selects the hit with the
    most-recent embedded generated_at timestamp."""
    body = json.dumps({
        "query": "Unfinished BIBLE Lists",
        "limit": 20,
        "wing": ZIGNAL_WING,
    }).encode()
    req = urllib.request.Request(
        f"{ZIGNAL_HTTP}/palace/search_raw",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if not (200 <= resp.status < 300):
                return None, f"http_{resp.status}"
            data = json.loads(resp.read().decode())
    except TimeoutError:
        return None, "timeout"
    except Exception as e:
        return None, f"error:{type(e).__name__}"
    hits = data.get("hits") or []
    if not hits:
        return None, "no_results"
    # Pick the hit with the most-recent embedded generated_at.
    gen_re = re.compile(r"Generated[:*\s]*([0-9T:.\-]+Z)")
    def gen_of(h: dict) -> str:
        c = h.get("content") or ""
        m = gen_re.search(c)
        return m.group(1) if m else ""
    hits_sorted = sorted(hits, key=gen_of, reverse=True)
    return hits_sorted[0].get("content") or "", "ok"


_ID_RE = re.compile(r"L\d+(?:\.\d+)?[a-z]?")
_MANIFEST_RE = re.compile(r"<!--\s*LISTS_MANIFEST_IDS:\s*([^>]+?)-->")


def _ids_in_text(text: str) -> set[str]:
    return set(_ID_RE.findall(text))


def _manifest_ids(text: str) -> set[str] | None:
    """Returns the explicit manifest id set if present, else None.
    Surfaces that render the manifest comment are reporting their
    *complete* id set; surfaces without it are subject to a more
    lenient subset check."""
    m = _MANIFEST_RE.search(text)
    if not m:
        return None
    return set(_ID_RE.findall(m.group(1)))


def verify() -> dict[str, Any]:
    canonical = _read_canonical()
    result: dict[str, Any] = {
        "canonical_present": canonical is not None,
        "canonical_count": canonical.get("count") if canonical else None,
        "canonical_generated_at": canonical.get("generated_at") if canonical else None,
        "surfaces": {},
        "divergence": [],
        "ok": True,
    }
    if not canonical:
        result["ok"] = False
        result["divergence"].append("canonical lists.json missing")
        VERIFY_OUT.parent.mkdir(parents=True, exist_ok=True)
        VERIFY_OUT.write_text(json.dumps(result, indent=2))
        return result

    canon_ids = {it.get("item_id") for it in canonical.get("items", [])}

    # Z13 markdown surface
    md, md_status = _read_z13_markdown()
    _compare_surface(result, "z13_markdown", md, md_status, canon_ids)

    # zignal drawer
    dr, dr_status = _read_drawer_latest()
    _compare_surface(result, "zignal_drawer", dr, dr_status, canon_ids)

    VERIFY_OUT.parent.mkdir(parents=True, exist_ok=True)
    VERIFY_OUT.write_text(json.dumps(result, indent=2))
    return result


def _compare_surface(result: dict, name: str, text: str | None,
                     status: str, canon_ids: set[str]) -> None:
    """Compare one surface against canonical.

    Contract:
      - If the surface emits a LISTS_MANIFEST_IDS comment, it is
        reporting its COMPLETE id set: drift = symmetric diff.
      - If no manifest comment, the surface is allowed to render a
        subset (e.g. top-10) — drift is only flagged when the
        surface contains an id that canonical does NOT have, OR
        when the surface is empty and canonical is not.
      - If the surface is unreachable, that itself is divergence."""
    if status != "ok":
        result["divergence"].append({"surface": name,
                                     "reason": f"unreachable: {status}"})
        result["ok"] = False
        result["surfaces"][name] = {"status": status, "ids_found": []}
        return
    if not text:
        text = ""
    manifest = _manifest_ids(text)
    if manifest is not None:
        # Strict comparison.
        only_canon = canon_ids - manifest
        only_surface = manifest - canon_ids
        ids_found = manifest
        if only_canon or only_surface:
            result["divergence"].append({
                "surface": name,
                "mode": "manifest_strict",
                "only_in_canonical": sorted(only_canon),
                "only_in_surface": sorted(only_surface),
            })
            result["ok"] = False
    else:
        # Lenient: subset check.
        raw_ids = _ids_in_text(text)
        # Items that LOOK like L#.## but aren't in canonical and
        # aren't part of file paths — flag those as extras.
        extras = raw_ids - canon_ids
        # Filter extras to plausible item ids only; drop noise like
        # the L37 in /mnt/.../fusion-v2/L37/something/ etc. by
        # requiring at least one dot.
        extras = {x for x in extras if "." in x}
        ids_found = raw_ids & canon_ids
        if extras:
            result["divergence"].append({
                "surface": name,
                "mode": "subset_lenient",
                "only_in_surface": sorted(extras),
            })
            result["ok"] = False
        if not ids_found and canon_ids:
            result["divergence"].append({
                "surface": name,
                "mode": "subset_lenient",
                "reason": "surface contains zero canonical ids",
            })
            result["ok"] = False
    result["surfaces"][name] = {"status": status,
                                "ids_found": sorted(ids_found)}


if __name__ == "__main__":
    import sys
    r = verify()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["ok"] else 1)
