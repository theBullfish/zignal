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
#   "L22.05 [PENDING] ..."   (item declaration, ID first)
#   "L22.05 [DOING] 2026-05-22 14:10"  (status appendix)
#   "- [PENDING] L22.05 ..." (bulleted list, status first — fusion-v2 form)
# Capture order normalized to (id, status) regardless of input shape.
_ITEM_ID_FIRST = re.compile(
    r"^\s*(L\d+(?:\.\d+)*[a-z]?)\s+\[([A-Z]+)(?:\s[^\]]*)?\]"
)
_ITEM_STATUS_FIRST = re.compile(
    r"^\s*[-*]?\s*\[([A-Z]+)(?:\s[^\]]*)?\]\s+(L\d+(?:\.\d+)*[a-z]?)"
)


def _match_item(line: str) -> tuple[str, str] | None:
    m = _ITEM_ID_FIRST.match(line)
    if m:
        return m.group(1), m.group(2)
    m = _ITEM_STATUS_FIRST.match(line)
    if m:
        return m.group(2), m.group(1)
    return None

OPEN = {"PENDING", "DOING", "BLOCKED", "PARTIAL", "DEFER", "DEFERRED"}
CLOSED = {"DONE", "SKIPPED", "SUPERSEDED"}

PLAN_GLOBS = (
    "BUILD_PLAN.md", "NOTES.md", "PROGRESS.md", "BIBLE.md",
    "BUILD_PLAN_*.md", "NOTES_*.md", "PROGRESS_*.md", "BIBLE_*.md",
    "*_BUILD_PLAN.md", "*_NOTES.md", "*_PROGRESS.md", "*_BIBLE.md",
)
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
    """Glob match supporting prefix (`X_*.md`), suffix (`*_X.md`),
    and exact patterns. Case-insensitive — goya-corpus uses
    lowercase build_plan filenames."""
    import fnmatch
    return fnmatch.fnmatchcase(name.upper(), pattern.upper())


# Range form: "L45.01-L45.05 [DONE] ..." closes 5 items in one line.
_RANGE_RE = re.compile(
    r"^\s*[-*]?\s*"
    r"(L\d+(?:\.\d+)+)\s*[-–—]\s*(L\d+(?:\.\d+)+)\s+\[([A-Z]+)\]"
)


def _expand_range(start_id: str, end_id: str) -> list[str]:
    """Expand "L45.01-L45.05" -> 5 ids; "L39.16.02-L39.16.03" -> 2.
    Returns [] if the range can't be expanded safely (different
    prefixes, descending, or >50)."""
    try:
        s_parts = start_id[1:].split(".")
        e_parts = end_id[1:].split(".")
        if len(s_parts) != len(e_parts):
            return []
        # Only the last component may differ.
        if s_parts[:-1] != e_parts[:-1]:
            return []
        s_n, e_n = int(s_parts[-1]), int(e_parts[-1])
        if e_n < s_n or e_n - s_n > 50:
            return []
        prefix = ".".join(s_parts[:-1])
        width = max(len(s_parts[-1]), len(e_parts[-1]))
        return [f"L{prefix}.{str(n).zfill(width)}"
                for n in range(s_n, e_n + 1)]
    except (ValueError, IndexError):
        return []


def _parse_file(path: Path, host: str, today: dt.date) -> list[UnfinishedItem]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()

    # First pass: collect every (id, status, line, date) appearance.
    # Skip lines inside ```code fences``` — those are format examples,
    # not real plan items.
    appearances: dict[str, list[tuple[int, str, dt.date | None, str]]] = {}
    in_fence = False
    for i, ln in enumerate(lines, start=1):
        stripped = ln.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        date = _extract_date(ln)
        # Try range form first (closes multiple items in one line).
        rm = _RANGE_RE.match(ln)
        if rm:
            start_id, end_id, status = rm.group(1), rm.group(2), rm.group(3)
            for iid in _expand_range(start_id, end_id):
                appearances.setdefault(iid, []).append(
                    (i, status, date, ln.strip())
                )
            continue
        matched = _match_item(ln)
        if not matched:
            continue
        item_id, status = matched
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
ID_FIRST = re.compile(r"^\s*(L\d+(?:\.\d+)*[a-z]?)\s+\[([A-Z]+)(?:\s[^\]]*)?\]")
STATUS_FIRST = re.compile(r"^\s*[-*]?\s*\[([A-Z]+)(?:\s[^\]]*)?\]\s+(L\d+(?:\.\d+)*[a-z]?)")
RANGE = re.compile(r"^\s*[-*]?\s*(L\d+(?:\.\d+)+)\s*[-–—]\s*(L\d+(?:\.\d+)+)\s+\[([A-Z]+)(?:\s[^\]]*)?\]")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
OPEN = {"PENDING","DOING","BLOCKED","PARTIAL","DEFER","DEFERRED"}
EXCLUDE = {".git","node_modules","__pycache__",".venv","venv",
           "HuntDeckApp","hunt-deck",".cache","target","dist"}
today = dt.date.today()
import fnmatch as _fnmatch
GLOBS = ("BUILD_PLAN.md","NOTES.md","PROGRESS.md","BIBLE.md",
         "BUILD_PLAN_*.md","NOTES_*.md","PROGRESS_*.md","BIBLE_*.md",
         "*_BUILD_PLAN.md","*_NOTES.md","*_PROGRESS.md","*_BIBLE.md")
def match(n):
    nu = n.upper()
    return any(_fnmatch.fnmatchcase(nu, g.upper()) for g in GLOBS)
def parse_item(ln):
    m = ID_FIRST.match(ln)
    if m: return m.group(1), m.group(2)
    m = STATUS_FIRST.match(ln)
    if m: return m.group(2), m.group(1)
    return None
def expand_range(s, e):
    try:
        sp = s[1:].split("."); ep = e[1:].split(".")
        if len(sp) != len(ep) or sp[:-1] != ep[:-1]: return []
        si, ei = int(sp[-1]), int(ep[-1])
        if ei < si or ei - si > 50: return []
        w = max(len(sp[-1]), len(ep[-1]))
        pref = ".".join(sp[:-1])
        return ["L%s.%s" % (pref, str(n).zfill(w)) for n in range(si, ei+1)]
    except: return []
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
            in_fence = False
            for i, ln in enumerate(txt.splitlines(), 1):
                if ln.lstrip().startswith("```"):
                    in_fence = not in_fence; continue
                if in_fence: continue
                dm = DATE_RE.search(ln); d = None
                if dm:
                    try: d = dt.date(int(dm.group(1)),int(dm.group(2)),int(dm.group(3)))
                    except: pass
                rm = RANGE.match(ln)
                if rm:
                    for iid in expand_range(rm.group(1), rm.group(2)):
                        apps.setdefault(iid, []).append((i, rm.group(3), d, ln.strip()))
                    continue
                pi = parse_item(ln)
                if not pi: continue
                iid, st = pi
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
