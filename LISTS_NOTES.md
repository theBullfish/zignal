# LISTS Build — Retroactive Review Log
*Append-only. New retros at bottom. Earlier retros never touched.*

Doctrine: `/home/z13/.claude/BIBLE_PROTOCOL.md`
Plan: `./LISTS_BUILD_PLAN.md`

---

## 2026-05-22 — L1.01 retroactive review

### Artifacts
- LISTS_BUILD_PLAN.md drafted (zignal repo).
- LISTS_NOTES.md created (this file).

### Doctrine adherence
- Append-only: PASS — status appendix lines only.
- One source of truth: PENDING — not yet built; locked in plan.
- Nothing on Z13 except source: PASS — plan/source lives with zignal repo.

### Open items
1. Scanner not yet implemented (L1.03).

### Net result
Surface choice locked: zignal drawer "lists". No code yet.

---

## 2026-05-22 — L1.02 retroactive review

### Artifacts
- Spec frozen in L1.02 of the plan (no separate file).

### Doctrine adherence
- BIBLE marker spec covers `[PENDING]` / `[DOING]` and L#.## items
  without `[DONE]`/`[SKIPPED]`. Covers the format Brad just universalized.
- Scan roots include Temple + Z13 (SSH) + Fusion install. No exclusions
  that would hide real plans.

### Open items
1. SSH credential path for Temple → Z13 read (key vs sshpass) — resolve
   in L1.03 when implementing the walker.

### Net result
Scanner spec is concrete enough to implement.

---

## 2026-05-22 — L1.03–L1.10 batch retro

### Artifacts
- zignal/lists/{__init__,schema,walker,emit,cli}.py — 5 files, ~300 LOC
- zignal-lists.{service,timer} on Temple, User=watchdog, 5-min cadence
- /mnt/work/zignal/state/lists.json (canonical, 9 items at close)
- /home/z13/.claude/projects/-home-z13/memory/UNFINISHED_LISTS.md (pushed via SSH)
- MEMORY.md CRITICAL section line pointing at it
- fusion/zignal_io/lists.py — ListsStatus read-only consumer

### Doctrine adherence
- One source of truth: PASS — all 4 surfaces show identical 9-item set.
- Nothing on Z13 except source: PASS — scanner runs on Temple as
  watchdog; only push to Z13 is the markdown memory file (data, not service).
- Append-only: PASS — plan and notes only grew, no edits in place.
- Flash means visible: PASS — Fusion ListsStatus.warn=True when count>0.

### Open items (carried forward)
1. fusion-v2/NOTES.md L37.10 [DOING] is now visible — Brad may want to
   decide if it's a real DOING or a stale appendix that should be closed.
2. Scanner excludes HuntDeckApp/hunt-deck per memory; verify no legitimate
   Mirai/HuntDeckApp plans get hidden.
3. Drawer dedup_threshold=0.99 — successive identical scans will still
   file (content changes only when items change). Tune if palace bloats.

### Net result
Brad now sees a live unfinished-items panel in three places: zignal
drawer wing=lists, Fusion zignal_io.ListsStatus, and his own MEMORY.md
on every session start. Same JSON, no surface lies.


