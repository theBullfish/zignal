"""Z13-side pull of lists.json from Temple.

Closes L1.07's named gap: "push-not-pull means transient SSH failure
= stale memory file with no warning." This module runs on Z13,
pulls /mnt/work/zignal/state/lists.json over SSH, and re-renders
UNFINISHED_LISTS.md locally. If the pull fails, the markdown is
overwritten with a clear "STALE — pull failed at <time>" banner so
the staleness is visible at the consumption point.

Invocation:
    python3 -m zignal.lists.pull
or:
    bash scripts/pull_lists.sh   (wrapper)
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from .emit import _markdown
from .schema import UnfinishedItem

TEMPLE_TARGET = "watchdog@100.79.198.99"
TEMPLE_JSON_PATH = "/mnt/work/zignal/state/lists.json"
Z13_MEMORY = Path("/home/z13/.claude/projects/-home-z13/memory/UNFINISHED_LISTS.md")


def _pull_json() -> tuple[dict | None, str]:
    """Returns (payload, status). status: 'ok', 'ssh_timeout',
    'ssh_failed:<rc>', 'parse_failed'."""
    try:
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             TEMPLE_TARGET, f"cat {TEMPLE_JSON_PATH}"],
            capture_output=True, text=True, timeout=15,
        )
    except subprocess.TimeoutExpired:
        return None, "ssh_timeout"
    if proc.returncode != 0:
        return None, f"ssh_failed:{proc.returncode}"
    try:
        return json.loads(proc.stdout), "ok"
    except json.JSONDecodeError:
        return None, "parse_failed"


def _stale_markdown(reason: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (f"# Unfinished BIBLE Lists\n\n"
            f"**STALE — pull from Temple failed at {now} ({reason}).**\n\n"
            f"> The local UNFINISHED_LISTS.md could not be refreshed.\n"
            f"> The Temple scanner may be down, or this Z13 host cannot\n"
            f"> reach Temple over SSH. Do NOT treat the previous contents\n"
            f"> as current. Last known state is below for reference only.\n\n"
            f"---\n\n")


def pull() -> dict:
    payload, status = _pull_json()
    result: dict = {"status": status, "pulled_at_utc":
                    dt.datetime.now(dt.timezone.utc).isoformat()}
    if status != "ok" or payload is None:
        prior = Z13_MEMORY.read_text() if Z13_MEMORY.exists() else ""
        Z13_MEMORY.parent.mkdir(parents=True, exist_ok=True)
        Z13_MEMORY.write_text(_stale_markdown(status) + prior)
        result["wrote_stale_banner"] = True
        return result
    # Hydrate items so _markdown can render the same shape as
    # Temple's emit produces.
    items = [UnfinishedItem(**it) for it in payload.get("items", [])]
    md = _markdown(items, payload.get("remote_status") or {})
    # Inject the pull-side generated_at so the reader sees the actual
    # underlying generation time, not the pull time.
    Z13_MEMORY.parent.mkdir(parents=True, exist_ok=True)
    Z13_MEMORY.write_text(md)
    result["count"] = payload.get("count", 0)
    result["generated_at"] = payload.get("generated_at")
    return result


if __name__ == "__main__":
    import sys
    r = pull()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["status"] == "ok" else 1)
