"""External validator for zignal.lists.

Covers Gate 3 (external validator in test loop) for L1.13/L1.15/L1.17:
- walker distinguishes empty-Z13 from unreachable-Z13 (status codes)
- emit JSON carries remote_status + emit_status
- Fusion ListsStatus distinguishes unknown / degraded / warn / clear
- walker.OPEN includes PARTIAL
- ListsStatus.alarm does NOT lie on unknown
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Z13 dev: zignal lives at /home/z13/zignal; fusion at /home/z13/fusion
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "/home/z13/fusion")

from zignal.lists.walker import (  # noqa: E402
    OPEN, scan_local, scan_remote_z13, _parse_file,
)
from zignal.lists.emit import _markdown, _payload  # noqa: E402
from zignal.lists.schema import UnfinishedItem  # noqa: E402
from fusion.zignal_io.lists import read_status, ListsStatus  # noqa: E402


# --- walker -----------------------------------------------------------

def test_open_set_includes_partial():
    assert "PARTIAL" in OPEN
    assert "PENDING" in OPEN
    assert "DOING" in OPEN
    assert "BLOCKED" in OPEN
    assert "DONE" not in OPEN
    assert "SKIPPED" not in OPEN


def test_parse_file_picks_up_partial(tmp_path: Path):
    plan = tmp_path / "BUILD_PLAN.md"
    plan.write_text(
        "L1.01 [PENDING] [RR+PRECEDE] item one\n"
        "L1.01 [DOING] 2026-05-22\n"
        "L1.01 [PARTIAL] 2026-05-22 — gap statement here\n"
        "L1.02 [PENDING] item two\n"
        "L1.02 [DONE] 2026-05-22 — closed\n"
    )
    import datetime as dt
    items = _parse_file(plan, host="z13", today=dt.date(2026, 5, 22))
    ids = {(i.item_id, i.status) for i in items}
    assert ("L1.01", "PARTIAL") in ids  # PARTIAL surfaces
    assert ("L1.02", "DONE") not in ids  # DONE does not


def test_remote_z13_unreachable_returns_status():
    # ssh to a target that won't auth in BatchMode within 5s
    items, status = scan_remote_z13(
        ["/nonexistent"], ssh_target="nobody@127.0.0.1"
    )
    assert items == []
    assert status in ("ssh_timeout", "ssh_failed", "parse_failed")
    assert status != "ok"


# --- emit / markdown --------------------------------------------------

def test_payload_carries_remote_status():
    p = _payload([], {"z13": "ssh_failed"})
    assert p["remote_status"] == {"z13": "ssh_failed"}
    assert p["count"] == 0


def test_markdown_renders_degraded_warning():
    md = _markdown([], {"z13": "ssh_timeout"})
    assert "WARNING" in md
    assert "ssh_timeout" in md
    # Reader-side staleness instruction must be present
    assert "generated_at" in md.lower() or "Generated:" in md


# --- Fusion read_status ----------------------------------------------

def test_read_status_missing_file_is_unknown(tmp_path: Path):
    s = read_status(tmp_path / "nope.json")
    assert s.unknown is True
    assert s.warn is True       # unknown raises warn
    assert s.alarm is False     # but NOT alarm — kill #11
    assert "unknown" in s.headline()


def test_read_status_clear_path(tmp_path: Path):
    p = tmp_path / "lists.json"
    p.write_text(json.dumps({
        "count": 0, "oldest_age_days": 0, "items": [],
        "generated_at": "2026-05-22T00:00:00Z",
        "remote_status": {"z13": "ok"},
        "emit_status": {"z13_memory": "ok", "zignal_drawer": "ok"},
    }))
    s = read_status(p)
    assert s.unknown is False
    assert s.warn is False
    assert s.alarm is False
    assert s.headline() == "lists: clear"


def test_read_status_degraded_on_remote_failure(tmp_path: Path):
    p = tmp_path / "lists.json"
    p.write_text(json.dumps({
        "count": 1, "oldest_age_days": 0,
        "items": [{"item_id": "L1.01"}],
        "generated_at": "2026-05-22T00:00:00Z",
        "remote_status": {"z13": "ssh_timeout"},
        "emit_status": {"z13_memory": "ok", "zignal_drawer": "ok"},
    }))
    s = read_status(p)
    assert s.warn is True
    assert "DEGRADED" in s.headline()


def test_read_status_degraded_on_emit_failure(tmp_path: Path):
    p = tmp_path / "lists.json"
    p.write_text(json.dumps({
        "count": 0, "oldest_age_days": 0, "items": [],
        "generated_at": "2026-05-22T00:00:00Z",
        "remote_status": {"z13": "ok"},
        "emit_status": {"z13_memory": "ssh_failed:255:Host unreachable",
                        "zignal_drawer": "ok"},
    }))
    s = read_status(p)
    assert s.warn is True
    assert "DEGRADED" in s.headline()


def test_read_status_alarm_on_old_items(tmp_path: Path):
    p = tmp_path / "lists.json"
    p.write_text(json.dumps({
        "count": 1, "oldest_age_days": 30,
        "items": [{"item_id": "L99.99"}],
        "generated_at": "2026-05-22T00:00:00Z",
        "remote_status": {"z13": "ok"},
        "emit_status": {"z13_memory": "ok", "zignal_drawer": "ok"},
    }))
    s = read_status(p)
    assert s.warn is True
    assert s.alarm is True
    assert "ALARM" in s.headline()


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
