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


def _payload(items: list[UnfinishedItem],
             remote_status: dict[str, str] | None = None) -> dict:
    items_sorted = sorted(items, key=lambda x: (-x.age_days, x.source_path, x.item_id))
    return {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "count": len(items_sorted),
        "oldest_age_days": items_sorted[0].age_days if items_sorted else 0,
        "remote_status": remote_status or {},
        "items": [it.to_dict() for it in items_sorted],
    }


def write_json(items: list[UnfinishedItem],
               remote_status: dict[str, str] | None = None) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(_payload(items, remote_status), indent=2))
    return JSON_PATH


def _markdown(items: list[UnfinishedItem],
              remote_status: dict[str, str] | None = None) -> str:
    payload = _payload(items, remote_status)
    lines: list[str] = []
    lines.append("# Unfinished BIBLE Lists")
    lines.append("")
    lines.append(f"**Generated: {payload['generated_at']}**")
    lines.append("")
    lines.append("> Reader: compare `generated_at` against the current "
                 "date/time. If the delta is > 10 min, the scanner is "
                 "almost certainly dead (Temple offline or "
                 "zignal-lists.timer not firing). Surfaces lie when stale.")
    lines.append("")
    lines.append(f"{payload['count']} open items, "
                 f"oldest {payload['oldest_age_days']} days.")
    lines.append("")
    rs = payload.get("remote_status") or {}
    for host, status in rs.items():
        if status != "ok":
            lines.append(f"> **WARNING:** remote `{host}` was {status} "
                         f"during this scan — counts are partial.")
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


def write_z13_memory(items: list[UnfinishedItem],
                     remote_status: dict[str, str] | None = None
                     ) -> tuple[bool, str]:
    """Push UNFINISHED_LISTS.md to Z13 over SSH. Returns
    (ok, status_string). status_string is 'ok', 'ssh_timeout',
    or 'ssh_failed:<rc>:<stderr-head>'."""
    md = _markdown(items, remote_status)
    try:
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             Z13_TARGET, f"cat > {Z13_MEMORY}"],
            input=md, capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            return True, "ok"
        return False, f"ssh_failed:{proc.returncode}:{(proc.stderr or '')[:80]}"
    except subprocess.TimeoutExpired:
        return False, "ssh_timeout"


def write_zignal_drawer(items: list[UnfinishedItem],
                        remote_status: dict[str, str] | None = None
                        ) -> tuple[bool, str]:
    """File the latest summary into zignal wing=lists room=status.
    Returns (ok, status_string). status_string is 'ok',
    'http_<status>', 'timeout', or 'error:<exc-head>'."""
    body = json.dumps({
        "wing": ZIGNAL_WING,
        "room": ZIGNAL_ROOM,
        "content": _markdown(items, remote_status),
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
            if 200 <= resp.status < 300:
                return True, "ok"
            return False, f"http_{resp.status}"
    except TimeoutError:
        return False, "timeout"
    except Exception as e:
        return False, f"error:{type(e).__name__}:{str(e)[:60]}"


def emit_all(items: list[UnfinishedItem],
             remote_status: dict[str, str] | None = None) -> dict:
    json_path = write_json(items, remote_status)
    z13_ok, z13_status = write_z13_memory(items, remote_status)
    drawer_ok, drawer_status = write_zignal_drawer(items, remote_status)
    emit_status = {
        "z13_memory": z13_status,
        "zignal_drawer": drawer_status,
    }
    # Re-write JSON with emit_status now that we know it (best effort).
    try:
        payload = json.loads(json_path.read_text())
        payload["emit_status"] = emit_status
        json_path.write_text(json.dumps(payload, indent=2))
    except (OSError, json.JSONDecodeError):
        pass
    return {
        "json_path": str(json_path),
        "z13_memory_pushed": z13_ok,
        "zignal_drawer_filed": drawer_ok,
        "count": len(items),
        "remote_status": remote_status or {},
        "emit_status": emit_status,
    }
