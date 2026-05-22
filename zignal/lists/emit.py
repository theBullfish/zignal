"""Emit canonical JSON + the three surfaces.

Surface 1: /mnt/work/zignal/state/lists.json (canonical)
Surface 2: zignal drawer "lists" (via signal_add_drawer / palace)
Surface 3: /home/z13/.claude/projects/-home-z13/memory/UNFINISHED_LISTS.md
Surface 4 (read-only consumer): Fusion via /home/z13/fusion/fusion/zignal_io
"""
from __future__ import annotations
import json
import subprocess
import urllib.request
import datetime as dt
from pathlib import Path
from typing import Iterable
from .schema import UnfinishedItem

STATE_DIR = Path("/mnt/work/zignal/state")
JSON_PATH = STATE_DIR / "lists.json"

Z13_MEMORY = Path("/home/z13/.claude/projects/-home-z13/memory/UNFINISHED_LISTS.md")
Z13_TARGET = "z13@100.106.69.123"

ZIGNAL_HTTP = "http://127.0.0.1:8540"
ZIGNAL_WING = "lists"
ZIGNAL_ROOM = "status"


def _payload(items: list[UnfinishedItem]) -> dict:
    items_sorted = sorted(items, key=lambda x: (-x.age_days, x.source_path, x.item_id))
    return {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "count": len(items_sorted),
        "oldest_age_days": items_sorted[0].age_days if items_sorted else 0,
        "items": [it.to_dict() for it in items_sorted],
    }


def write_json(items: list[UnfinishedItem]) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(_payload(items), indent=2))
    return JSON_PATH


def _markdown(items: list[UnfinishedItem]) -> str:
    payload = _payload(items)
    lines: list[str] = []
    lines.append("# Unfinished BIBLE Lists")
    lines.append("")
    lines.append(f"*Generated {payload['generated_at']} — "
                 f"{payload['count']} open items, "
                 f"oldest {payload['oldest_age_days']} days*")
    lines.append("")
    lines.append("Canonical JSON: `/mnt/work/zignal/state/lists.json` (Temple).")
    lines.append("Scanner: `zignal.lists` module. Doctrine: "
                 "`/home/z13/.claude/BIBLE_PROTOCOL.md`.")
    lines.append("")
    if not items:
        lines.append("**No open items.**")
        return "\n".join(lines) + "\n"
    lines.append("## Top 10 oldest")
    lines.append("")
    lines.append("| Age (d) | Status | ID | Source |")
    lines.append("|---------|--------|----|--------|")
    for it in payload["items"][:10]:
        src = f"`{it['host']}:{it['source_path']}:{it['line']}`"
        lines.append(f"| {it['age_days']} | {it['status']} | "
                     f"`{it['item_id']}` | {src} |")
    lines.append("")
    if payload["count"] > 10:
        lines.append(f"_(+{payload['count'] - 10} more in lists.json)_")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_z13_memory(items: list[UnfinishedItem]) -> bool:
    """Push UNFINISHED_LISTS.md to Z13 over SSH."""
    md = _markdown(items)
    try:
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             Z13_TARGET, f"cat > {Z13_MEMORY}"],
            input=md, capture_output=True, text=True, timeout=30,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def write_zignal_drawer(items: list[UnfinishedItem]) -> bool:
    """File the latest summary into zignal wing=lists room=status."""
    body = json.dumps({
        "wing": ZIGNAL_WING,
        "room": ZIGNAL_ROOM,
        "content": _markdown(items),
        "source": "zignal.lists.cli",
        "added_by": "zignal-lists.service",
        "dedup_threshold": 0.99,
    }).encode()
    req = urllib.request.Request(
        f"{ZIGNAL_HTTP}/palace/file",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def emit_all(items: list[UnfinishedItem]) -> dict:
    json_path = write_json(items)
    z13_ok = write_z13_memory(items)
    drawer_ok = write_zignal_drawer(items)
    return {
        "json_path": str(json_path),
        "z13_memory_pushed": z13_ok,
        "zignal_drawer_filed": drawer_ok,
        "count": len(items),
    }
