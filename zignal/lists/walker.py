"""Walk filesystem for BIBLE plan files; parse unfinished L#.## items.

BIBLE format (from /home/z13/.claude/BIBLE_PROTOCOL.md):
- Items are numbered L#.## (e.g. L22.05, L1.01).
- Status appendix lines under an item carry [PENDING], [DOING], [DONE],
  [BLOCKED], [SKIPPED], [SUPERSEDED].
- An item is "unfinished" if its latest status is PENDING/DOING/BLOCKED.
"""
from __future__ import annotations
import os
import re
import json
import subprocess
import datetime as dt
from pathlib import Path
from typing import Iterable
from .schema import UnfinishedItem

# Match either:
#   "L22.05 [PENDING] ..."   (item declaration)
#   "L22.05 [DOING] 2026-05-22 14:10"  (status appendix)
ITEM_RE = re.compile(r"^\s*(L\d+(?:\.\d+)?[a-z]?)\s+\[([A-Z]+)\]")

OPEN = {"PENDING", "DOING", "BLOCKED", "PARTIAL"}
CLOSED = {"DONE", "SKIPPED", "SUPERSEDED"}

PLAN_GLOBS = ("BUILD_PLAN.md", "NOTES.md", "*_BUILD_PLAN.md", "*_NOTES.md")
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
                "HuntDeckApp", "hunt-deck", ".cache", "target", "dist"}


def _find_plan_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if any(_match(fn, pat) for pat in PLAN_GLOBS):
                out.append(Path(dirpath) / fn)
    return out


def _match(name: str, pattern: str) -> bool:
    if pattern.startswith("*"):
        return name.endswith(pattern[1:])
    return name == pattern


def _parse_file(path: Path, host: str, today: dt.date) -> list[UnfinishedItem]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()

    # First pass: collect every (id, status, line, date) appearance.
    appearances: dict[str, list[tuple[int, str, dt.date | None, str]]] = {}
    for i, ln in enumerate(lines, start=1):
        m = ITEM_RE.match(ln)
        if not m:
            continue
        item_id, status = m.group(1), m.group(2)
        date = _extract_date(ln)
        appearances.setdefault(item_id, []).append((i, status, date, ln.strip()))

    out: list[UnfinishedItem] = []
    for item_id, entries in appearances.items():
        # Latest status = last appearance.
        last_status = entries[-1][1]
        if last_status not in OPEN:
            continue
        # Find first OPEN appearance to compute age.
        first_open = next((e for e in entries if e[1] in OPEN), entries[0])
        first_line, _, first_date, excerpt = first_open
        age = (today - first_date).days if first_date else 0
        out.append(UnfinishedItem(
            host=host,
            source_path=str(path),
            item_id=item_id,
            status=last_status,
            line=first_line,
            excerpt=excerpt[:200],
            age_days=max(age, 0),
        ))
    return out


_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _extract_date(line: str) -> dt.date | None:
    m = _DATE_RE.search(line)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def scan_local(roots: Iterable[Path], host: str,
               today: dt.date | None = None) -> list[UnfinishedItem]:
    today = today or dt.date.today()
    items: list[UnfinishedItem] = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for plan in _find_plan_files(root):
            items.extend(_parse_file(plan, host, today))
    return items


REMOTE_WALKER = r'''
import os, re, json, sys, datetime as dt
ITEM_RE = re.compile(r"^\s*(L\d+(?:\.\d+)?[a-z]?)\s+\[([A-Z]+)\]")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
OPEN = {"PENDING","DOING","BLOCKED","PARTIAL"}
EXCLUDE = {".git","node_modules","__pycache__",".venv","venv",
           "HuntDeckApp","hunt-deck",".cache","target","dist"}
PATS = ("BUILD_PLAN.md","NOTES.md","_BUILD_PLAN.md","_NOTES.md")
today = dt.date.today()
def match(n):
    return n in ("BUILD_PLAN.md","NOTES.md") or n.endswith("_BUILD_PLAN.md") or n.endswith("_NOTES.md")
out = []
for root in sys.argv[1:]:
    if not os.path.isdir(root): continue
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in EXCLUDE]
        for f in fn:
            if not match(f): continue
            p = os.path.join(dp, f)
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            apps = {}
            for i, ln in enumerate(txt.splitlines(), 1):
                m = ITEM_RE.match(ln)
                if not m: continue
                iid, st = m.group(1), m.group(2)
                dm = DATE_RE.search(ln)
                d = None
                if dm:
                    try: d = dt.date(int(dm.group(1)),int(dm.group(2)),int(dm.group(3)))
                    except: pass
                apps.setdefault(iid, []).append((i, st, d, ln.strip()))
            for iid, es in apps.items():
                if es[-1][1] not in OPEN: continue
                fo = next((e for e in es if e[1] in OPEN), es[0])
                age = (today - fo[2]).days if fo[2] else 0
                out.append(dict(host="z13", source_path=p, item_id=iid,
                                status=es[-1][1], line=fo[0],
                                excerpt=fo[3][:200], age_days=max(age,0)))
print(json.dumps(out))
'''


def scan_remote_z13(roots: Iterable[str],
                    ssh_target: str = "z13@100.106.69.123"
                    ) -> tuple[list[UnfinishedItem], str]:
    """Returns (items, status). status: 'ok' | 'ssh_timeout' |
    'ssh_failed' | 'parse_failed'. Empty items + 'ok' means Z13 has
    no open items; empty items + non-'ok' means we could not see Z13.
    Surfaces must distinguish these two cases."""
    args = " ".join(f"'{r}'" for r in roots)
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
           ssh_target, f"python3 - {args}"]
    try:
        proc = subprocess.run(cmd, input=REMOTE_WALKER, capture_output=True,
                              text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return [], "ssh_timeout"
    if proc.returncode != 0:
        return [], "ssh_failed"
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [], "parse_failed"
    return [UnfinishedItem(**row) for row in data], "ok"
