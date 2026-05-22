# LISTS Surface — zignal cross-system unfinished-item warning
*Version 1 — 2026-05-22 — Brad + Claude*

Source of truth for the build. BIBLE-protocol: append-only, numbered,
no renumbering, retros per item in `LISTS_NOTES.md`.

---

## BIBLE BUILD PROTOCOL

Read `/home/z13/.claude/BIBLE_PROTOCOL.md` before touching this plan.
Universal scope (2026-05-22): every task = numbered list. No exceptions.

## STATUS LEGEND

```
[PENDING]   not started
[DOING]     in flight (one per layer)
[DONE]      complete + retro written
[BLOCKED]   started, cannot finish, blocker documented
[SKIPPED]   intentionally not done, reason documented
```

## CORE DOCTRINE (non-negotiable for THIS build)

1. **One source of truth** — scanner emits canonical JSON; zignal
   drawer, Fusion bridge, and `UNFINISHED_LISTS.md` all render from
   the same JSON. No surface computes anything on its own.
2. **Nothing on Z13 except source/doctrine** — scanner runs on Temple;
   plan/source files OK on Z13.
3. **Append-only everything** — this plan, NOTES.md, the scanner's
   output JSON history.
4. **Flash means visible** — if there is one unfinished item anywhere,
   all three surfaces must show it. No silent rows.

## ITEM PROTOCOL

- Status appendix under each item with timestamp.
- Retro line (one sentence minimum) for every `[DONE]`.
- Commits reference `L#.##`.

---

## LAYER 1 — LISTS surface

L1.01 [PENDING] [RR+PRECEDE] zignal surface shape = drawer "lists".
  Pre: none. Decision: option (a) — new drawer via signal_add_drawer.
  Cheapest, visible from signal_list_rooms/drawers polls.
L1.01 [DOING] 2026-05-22
L1.01 [DONE]  2026-05-22 — Brad "go" lock. Surface = zignal drawer "lists".

L1.02 [PENDING] [RR+PRECEDE] Scanner spec: what counts as a list.
  Pre: L1.01.
  Match BIBLE markers across the system:
    - any `[PENDING]` or `[DOING]` line in BUILD_PLAN.md / NOTES.md
      and *_BUILD_PLAN.md / *_NOTES.md variants
    - any L#.## item without `[DONE]`/`[SKIPPED]` appendix
  Scan roots:
    - Temple: /mnt/work/**, /home/watchdog/** (source repos)
    - Z13: /home/z13/** (via SSH from Temple)
    - Fusion: /home/z13/fusion + Temple fusion install
  Excludes: archives (HuntDeckApp, hunt-deck per memory), .git, node_modules.
L1.02 [DOING] 2026-05-22
L1.02 [DONE]  2026-05-22 — spec frozen as written. Scanner targets BIBLE-format
  L#.## items; status appendix lines determine open/closed.

L1.03 [PENDING] [RR+PRECEDE] Scanner service implementation.
  Pre: L1.02 spec frozen.
  Path: /mnt/work/zignal/zignal/lists/ (Temple).
  - walker.py — glob roots, parse L#.## items + status appendix lines
  - schema.py — UnfinishedItem(source_path, item_id, status, age_days,
    line, first_seen, last_seen)
  - emit.py — write canonical JSON to /mnt/work/zignal/state/lists.json
L1.03 [DOING] 2026-05-22
L1.03 [DONE]  2026-05-22 — schema/walker/emit/cli landed; remote walker
  runs over SSH from Temple→Z13; dry-run found 9 open items.

L1.04 [PENDING] [RR+PRECEDE] Wire scanner → zignal "lists" drawer.
  Pre: L1.03 emits JSON.
  Drawer rows = one per unfinished item; header = count + age of oldest.
L1.04 [DOING] 2026-05-22
L1.04 [DONE]  2026-05-22 — emit.write_zignal_drawer POSTs to
  zignal-http :8540 /palace/file as wing="lists" room="status".

L1.05 [PENDING] [RR+PRECEDE] Flashing warning rule.
  Pre: L1.04 wired.
  - Drawer state = warn when count > 0; alarm when oldest > 7 days.
  - Surface in Fusion via /home/z13/fusion/fusion/zignal_io adapter.
  - Both surfaces read from lists.json, never recompute.
L1.05 [DOING] 2026-05-22
L1.05 [DONE]  2026-05-22 — fusion/zignal_io/lists.py ListsStatus
  exposes warn/alarm/headline reading lists.json. Fusion never recomputes.

L1.06 [PENDING] [RR+PRECEDE] Cadence: zignal-lists.service systemd timer.
  Pre: L1.04 wired. Default 5 min; tune after first observation.
L1.06 [DOING] 2026-05-22
L1.06 [DONE]  2026-05-22 — zignal-lists.{service,timer} installed on
  Temple, User=watchdog, OnUnitActiveSec=5min. enable --now confirmed.

L1.07 [PENDING] [RR+PRECEDE] Claude-visible surface.
  Pre: L1.03 emits JSON.
  Scanner also writes
  /home/z13/.claude/projects/-home-z13/memory/UNFINISHED_LISTS.md
  (over SSH pull, or pushed from Temple via existing watchdog→z13 path).
  Format: count + top 10 oldest items + source paths.
L1.07 [DOING] 2026-05-22
L1.07 [DONE]  2026-05-22 — Temple→Z13 SSH pubkey installed;
  emit.write_z13_memory pushes markdown over SSH every run.

L1.08 [PENDING] [RR+PRECEDE] MEMORY.md pointer to UNFINISHED_LISTS.md.
  Pre: L1.07 writes the file.
  One CRITICAL-section line so I see it on every session start.
L1.08 [DOING] 2026-05-22
L1.08 [DONE]  2026-05-22 — MEMORY.md CRITICAL section now leads with
  UNFINISHED_LISTS.md pointer.

L1.09 [PENDING] [RR+PRECEDE] One source of truth verification.
  Pre: L1.04 + L1.05 + L1.07 all done.
  Diff drawer / Fusion bridge / UNFINISHED_LISTS.md against lists.json.
  Confirm all three render identical row counts + IDs.
L1.09 [DOING] 2026-05-22
L1.09 [DONE]  2026-05-22 — all 4 surfaces (json+md+drawer+fusion) show
  identical 9-item set with matching L#.## IDs.

L1.10 [PENDING] [RR+PRECEDE] Commit + retro batch.
  Pre: L1.01–L1.09 closed.
  Commit message references the full L1.01–L1.10 range.
L1.10 [DOING] 2026-05-22
L1.10 [DONE]  2026-05-22 — zignal commit references L1.01-L1.10;
  fusion commit references L1.05. Both repos clean.

---

## PROGRESS LOG
*(append-only — newest at bottom, dated)*

2026-05-22 — plan drafted. L1.01–L1.10 PENDING.
2026-05-22 — L1.01–L1.10 closed in single session. All 4 surfaces
  verified at 9 items. Timer running every 5 min on Temple.
