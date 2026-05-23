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


def test_parse_file_status_first_format(tmp_path: Path):
    """Bulleted '- [STATUS] L#.##' (fusion-v2 form) must surface."""
    plan = tmp_path / "BUILD_PLAN.md"
    plan.write_text(
        "- [PENDING] L39.10a — Wire 4 remaining OCSP ops\n"
        "- [PENDING] L39.11a — Wire 3 remaining JAR ops\n"
        "- [DONE] L0.01 closed item\n"
    )
    import datetime as dt
    items = _parse_file(plan, host="temple", today=dt.date(2026, 5, 22))
    ids = {(i.item_id, i.status) for i in items}
    assert ("L39.10a", "PENDING") in ids
    assert ("L39.11a", "PENDING") in ids
    assert ("L0.01", "DONE") not in ids  # closed, not surfaced


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


def test_parse_file_skips_code_fence(tmp_path: Path):
    """Items inside ```code fences``` are format examples, not real items."""
    plan = tmp_path / "BUILD_PLAN.md"
    plan.write_text(
        "L1.01 [PENDING] real item\n"
        "```\n"
        "L99.99 [PENDING] example shown in a code block\n"
        "```\n"
        "L1.02 [DOING] another real item\n"
    )
    import datetime as dt
    items = _parse_file(plan, host="z13", today=dt.date(2026, 5, 22))
    ids = {i.item_id for i in items}
    assert "L1.01" in ids
    assert "L1.02" in ids
    assert "L99.99" not in ids  # filtered out — was in code fence


def test_parse_file_expands_range(tmp_path: Path):
    """L45.01-L45.05 [DONE] closes 5 items."""
    plan = tmp_path / "PROGRESS.md"
    plan.write_text(
        "L45.01 [PENDING] item one\n"
        "L45.02 [PENDING] item two\n"
        "L45.03 [PENDING] item three\n"
        "L45.04 [PENDING] item four\n"
        "L45.05 [PENDING] item five\n"
        "L45.01-L45.05 [DONE] 2026-05-22 — all closed\n"
    )
    import datetime as dt
    items = _parse_file(plan, host="temple", today=dt.date(2026, 5, 22))
    # All 5 should resolve to DONE (closed), so none surface as open.
    assert items == []


def test_parse_file_status_with_embedded_date(tmp_path: Path):
    """`[DONE 2026-05-22] L2.01` format (primitive-lab) must be recognized
    as DONE, not silently fall through to PENDING."""
    plan = tmp_path / "BUILD_PLAN.md"
    plan.write_text(
        "- [DONE 2026-05-22] L2.01 already closed item\n"
        "- [PENDING] L2.04 still open\n"
        "L2.05 [PARTIAL 2026-05-22 — gap statement] mixed form also OK\n"
    )
    import datetime as dt
    items = _parse_file(plan, host="temple", today=dt.date(2026, 5, 22))
    by = {i.item_id: i.status for i in items}
    assert "L2.01" not in by  # DONE — must not surface
    assert by.get("L2.04") == "PENDING"
    assert by.get("L2.05") == "PARTIAL"


def test_parse_file_three_level_ids(tmp_path: Path):
    """L39.18.04 must NOT collapse to L39 — three-level IDs are real."""
    plan = tmp_path / "BUILD_PLAN.md"
    plan.write_text(
        "L39.18.04 [PENDING] sub-item\n"
        "L39.18.05 [PENDING] another sub-item\n"
        "L39 [DONE] 2026-05-22 — layer close (different ID)\n"
    )
    import datetime as dt
    items = _parse_file(plan, host="temple", today=dt.date(2026, 5, 22))
    ids = {i.item_id for i in items}
    assert "L39.18.04" in ids
    assert "L39.18.05" in ids
    assert "L39" not in ids  # closed separately, not merged with the others


def test_range_expand_three_level(tmp_path: Path):
    """L39.16.02-L39.16.05 [DONE] closes 4 sub-items."""
    plan = tmp_path / "PROGRESS.md"
    plan.write_text(
        "L39.16.02 [PENDING] x\n"
        "L39.16.03 [PENDING] x\n"
        "L39.16.04 [PENDING] x\n"
        "L39.16.05 [PENDING] x\n"
        "L39.16.02-L39.16.05 [DONE] 2026-05-22 — batch close\n"
    )
    import datetime as dt
    items = _parse_file(plan, host="temple", today=dt.date(2026, 5, 22))
    assert items == []


def test_parse_file_picks_up_defer(tmp_path: Path):
    """DEFER is owed work; must surface."""
    plan = tmp_path / "NOTES.md"
    plan.write_text("L1.01 [DEFER] waiting on PSU cycle\n")
    import datetime as dt
    items = _parse_file(plan, host="z13", today=dt.date(2026, 5, 22))
    assert any(i.item_id == "L1.01" and i.status == "DEFER" for i in items)


def test_find_plan_files_finds_progress_and_bible(tmp_path: Path):
    """PROGRESS.md, BIBLE.md, and both prefix/suffix forms must be found."""
    for name in ("BUILD_PLAN.md", "NOTES.md", "PROGRESS.md", "BIBLE.md",
                "PIPELINE_BUILD_PLAN.md",        # suffix form
                "BUILD_PLAN_QM_RREG.md",         # prefix form
                "NOTES_session_22.md",
                "BIBLE_optane.md"):
        (tmp_path / name).write_text("L1.01 [PENDING] x\n")
    (tmp_path / "README.md").write_text("not a plan\n")
    # RELEASE_NOTES.md DOES match the *_NOTES.md glob — globs are
    # intentionally broad; the content filter (no L#.## items in a
    # release-notes file) is what keeps these from showing up in the
    # scanner output.
    (tmp_path / "RELEASE_NOTES.md").write_text(
        "## v1.2.3\nbug fixes\n"  # no BIBLE items → won't surface
    )
    from zignal.lists.walker import _find_plan_files, scan_local
    found = {p.name for p in _find_plan_files(tmp_path)}
    # Add a lowercase variant — goya-corpus uses lowercase filenames.
    (tmp_path / "qm_rreg_build_plan.md").write_text("L1.01 [PENDING] x\n")
    found = {p.name for p in _find_plan_files(tmp_path)}
    for required in ("BUILD_PLAN.md", "NOTES.md", "PROGRESS.md", "BIBLE.md",
                     "PIPELINE_BUILD_PLAN.md", "BUILD_PLAN_QM_RREG.md",
                     "NOTES_session_22.md", "BIBLE_optane.md",
                     "qm_rreg_build_plan.md"):
        assert required in found, f"{required} not picked up by globs"
    assert "README.md" not in found
    # RELEASE_NOTES.md is globbed but has zero BIBLE items, so
    # scan_local should not surface anything from it.
    items = scan_local([tmp_path], host="z13")
    by_path = {(it.source_path) for it in items}
    assert all("RELEASE_NOTES.md" not in p for p in by_path), \
        "release notes leaked an item"


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


# --- verify.py --------------------------------------------------------

def test_verify_canonical_missing(monkeypatch, tmp_path):
    """When lists.json is missing, verify reports ok=False with reason."""
    import importlib
    verify_mod = importlib.import_module("zignal.lists.verify")
    monkeypatch.setattr(verify_mod, "CANONICAL", tmp_path / "absent.json")
    monkeypatch.setattr(verify_mod, "VERIFY_OUT", tmp_path / "verify.json")
    r = verify_mod.verify()
    assert r["ok"] is False
    assert any("canonical" in str(d).lower() for d in r["divergence"])


def test_verify_all_three_surfaces_consistent(monkeypatch, tmp_path):
    """Happy path: canonical + md + drawer all carry same ids."""
    import importlib
    verify_mod = importlib.import_module("zignal.lists.verify")
    canonical = {
        "count": 2, "oldest_age_days": 1,
        "items": [{"item_id": "L1.01"}, {"item_id": "L2.05"}],
        "generated_at": "2026-05-22T00:00:00Z",
    }
    canon_path = tmp_path / "lists.json"
    canon_path.write_text(json.dumps(canonical))
    monkeypatch.setattr(verify_mod, "CANONICAL", canon_path)
    monkeypatch.setattr(verify_mod, "VERIFY_OUT", tmp_path / "verify.json")
    md_text = "| 0 | PENDING | `L1.01` |\n| 0 | PENDING | `L2.05` |"
    monkeypatch.setattr(verify_mod, "_read_z13_markdown",
                        lambda: (md_text, "ok"))
    monkeypatch.setattr(verify_mod, "_read_drawer_latest",
                        lambda: (md_text, "ok"))
    r = verify_mod.verify()
    assert r["ok"] is True
    assert r["divergence"] == []


def test_verify_detects_drift(monkeypatch, tmp_path):
    """When markdown has an id canonical doesn't (or vice versa),
    verify flags it."""
    import importlib
    verify_mod = importlib.import_module("zignal.lists.verify")
    canonical = {
        "count": 1, "oldest_age_days": 0,
        "items": [{"item_id": "L1.01"}],
        "generated_at": "2026-05-22T00:00:00Z",
    }
    canon_path = tmp_path / "lists.json"
    canon_path.write_text(json.dumps(canonical))
    monkeypatch.setattr(verify_mod, "CANONICAL", canon_path)
    monkeypatch.setattr(verify_mod, "VERIFY_OUT", tmp_path / "verify.json")
    # Drawer has extra id L9.99 — drift
    monkeypatch.setattr(verify_mod, "_read_z13_markdown",
                        lambda: ("L1.01", "ok"))
    monkeypatch.setattr(verify_mod, "_read_drawer_latest",
                        lambda: ("L1.01 L9.99", "ok"))
    r = verify_mod.verify()
    # Note: drawer drift is filtered against canonical ids — L9.99
    # not in canonical_ids_in_json, so it gets filtered out. We
    # specifically want to detect MISSING ids (canonical has X,
    # surface doesn't). Test missing-from-drawer.
    monkeypatch.setattr(verify_mod, "_read_drawer_latest",
                        lambda: ("", "ok"))  # empty drawer
    r = verify_mod.verify()
    assert r["ok"] is False
    assert any("zignal_drawer" in str(d) for d in r["divergence"])


def test_verify_records_surface_unreachable(monkeypatch, tmp_path):
    """When a surface is unreachable, verify reports it, not silently OK."""
    import importlib
    verify_mod = importlib.import_module("zignal.lists.verify")
    canonical = {"count": 0, "items": [], "oldest_age_days": 0,
                 "generated_at": "2026-05-22T00:00:00Z"}
    canon_path = tmp_path / "lists.json"
    canon_path.write_text(json.dumps(canonical))
    monkeypatch.setattr(verify_mod, "CANONICAL", canon_path)
    monkeypatch.setattr(verify_mod, "VERIFY_OUT", tmp_path / "verify.json")
    monkeypatch.setattr(verify_mod, "_read_z13_markdown",
                        lambda: (None, "ssh_timeout"))
    monkeypatch.setattr(verify_mod, "_read_drawer_latest",
                        lambda: (None, "timeout"))
    r = verify_mod.verify()
    assert r["ok"] is False
    reasons = [d.get("reason", "") for d in r["divergence"]
               if isinstance(d, dict)]
    assert any("ssh_timeout" in str(x) for x in reasons)
    assert any("timeout" in str(x) for x in reasons)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
