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

L1.11 [PENDING] [RR+PRECEDE] Retroactive retros for L1.01-L1.10.
  Pre: L2 audit pass.
  DoD: LISTS_NOTES.md contains one reflective retro per item (not
  artifact list) AND a gate audit against BIBLE Quality gates.
L1.11 [DOING] 2026-05-22
L1.11 [DONE]  2026-05-22 — Real retros + gate audit landed in
  LISTS_NOTES.md. Retro: this exposed 6 concrete gaps the original
  "9 min/item" velocity had buried; gate-6 earned its keep.

L1.12 [PENDING] [RR+PRECEDE] Staleness indicator on UNFINISHED_LISTS.md.
  Pre: L1.11.
  DoD: markdown surface renders a WARN line when
  `now - generated_at > 10 min`; renders an ALARM line when > 1 h.
L1.12 [DOING]    2026-05-22
L1.12 [PARTIAL]  2026-05-22 — markdown surface cannot self-update;
  WARN/ALARM bake-in only fires at write time, which is useless for
  the read-side staleness problem. Compromise landed: bold
  `generated_at` header + explicit reader-instruction footer ("if
  delta > 10 min, scanner is dead"). Retro: I rewrote the DoD as I
  implemented it because the original DoD was physically impossible
  given a write-once markdown surface — Gate 1 specifically forbids
  this. Successor L1.12a queued: session-start procedure that
  *enforces* the freshness check at read time (Claude side, not file
  side). Gap: until L1.12a lands, reader compliance is advisory.
L1.12 [SKIPPED] 2026-05-22 — adversarial review (kill #2) correctly
  flagged this as Gate 4 non-compliant: PARTIAL requires a
  "minimum work to upgrade to DONE" sentence, but the DoD as
  written is physically unupgradeable on a write-once markdown
  surface. The work that *was* shippable (reader-instruction
  footer + bold header) shipped and stays; the unupgradeable bake-in
  DoD is superseded by L1.12a, which is now DONE.

L1.13 [PENDING] [RR+PRECEDE] `remote_unreachable` signal in lists.json.
  Pre: L1.11.
  DoD: scanner emits explicit `remote_status: {z13: "ok"|"unreachable"}`
  in lists.json; surfaces render "Z13 UNREACHABLE — count is
  Temple-only" when not "ok". Walker distinguishes SSH failure from
  empty walk by exit code, not by len().
L1.13 [DOING] 2026-05-22
L1.13 [DONE]  2026-05-22 — walker.scan_remote_z13 now returns
  (items, status) where status ∈ {ok, ssh_timeout, ssh_failed,
  parse_failed}. Emit threads it through to lists.json
  remote_status field and into the markdown WARNING block. Smoke
  tested with ssh_target=nobody@127.0.0.1 → returned 'ssh_failed' +
  empty items as designed. Retro: the most insidious gap of the
  original build closed in one return-tuple change; the rest was
  plumbing. Single tuple-return change earned more reliability than
  any of L1.04/L1.07 individually.

L1.14 [PENDING] [RR+PRECEDE] `TimeoutSec=` on zignal-lists.service.
  Pre: L1.11.
  DoD: unit has `TimeoutStartSec=120` and `TimeoutStopSec=30`; hung
  SSH walk gets SIGKILL'd before the next timer fire.
L1.14 [DOING] 2026-05-22
L1.14 [DONE]  2026-05-22 — service file edited locally. Deploy
  blocked on Temple (L1.16). Retro: I should have set this on day
  one — `oneshot` units default to no timeout, which is exactly the
  wrong default for a unit that does network I/O. The wrong default
  bit me by becoming the failure mode I was trying to detect.
L1.14 [PARTIAL] 2026-05-22 — adversarial review (kill #6) correct:
  DoD was "hung SSH gets SIGKILL'd before next timer fire" — that
  requires deploy + observe, which can't happen until Temple is
  back. Edit landed; effect not yet visible. Upgrade-to-DONE path:
  L1.16 deploys this file to Temple and journalctl shows
  `Timeout=120s` enforced on a hung run. Concrete blocker: Temple
  offline (same as L1.16).

L1.15 [PENDING] [RR+PRECEDE] File-missing ≠ file-says-zero in Fusion.
  Pre: L1.11.
  DoD: `read_status()` returns a `ListsStatus(unknown=True, ...)`
  case when `lists.json` is missing/unreadable; `headline()` says
  "lists: unknown — no data file" not "lists: clear".
L1.15 [DOING] 2026-05-22
L1.15 [DONE]  2026-05-22 — ListsStatus gained `unknown` and
  `remote_status` fields. headline() now distinguishes
  unknown/degraded/warn/alarm/clear. Smoke tested all 3 transitions
  (missing → unknown+warn; ssh_timeout in remote → DEGRADED;
  count=0 ok → clear). Retro: the original "absence = zero" default
  is the same shape bug as "no error = success" — both treat the
  lack of evidence as positive evidence. Catching it required
  thinking about the read-side semantics, not just plumbing.

L1.16 [PENDING] [RR+PRECEDE] Deploy + verify L1.12-L1.15.
  Pre: L1.12-L1.15 land; Temple reachable (currently offline, last
  seen 14m ago at 2026-05-22 19:30 UTC).
  DoD: services restarted on Temple; 3 unattended fires confirmed
  in journalctl; all surfaces show consistent state including the
  new staleness/unreachable signals.
L1.16 [BLOCKED] 2026-05-22 — Temple offline, last seen 14m ago at
  audit time. Concrete blocker: tailscale shows pop-os relay "ord"
  offline. Resume when Brad's Temple is back online.

L1.16a [PENDING] [RR+PRECEDE] Resume-trigger for Temple-blocked items.
  Pre: L1.13 + L1.14 + L1.15 + tests landed.
  Successor of L1.16 — addresses adversarial-review kill #9
  ("BLOCKED has no resume trigger; this is 'next phase' disguised").
  DoD: a one-shot resume script
  `/home/z13/zignal/scripts/resume_when_temple_up.sh` exists that:
  (1) checks `tailscale status | grep pop-os` for `active`/`idle`,
  (2) if up, rsyncs zignal/lists/ + zignal-lists.service to Temple,
  (3) systemctl daemon-reload + restart zignal-lists.timer,
  (4) starts the service once, journalctl tails 20 lines,
  (5) prints the resulting lists.json count/emit_status.
  Exits non-zero if Temple is still down (so a wrapping cron/loop
  can retry). This converts BLOCKED from "we'll get to it" to "next
  successful run of this script closes L1.14 + L1.16".
L1.16a [DOING] 2026-05-22
L1.16a [DONE]  2026-05-22 — scripts/resume_when_temple_up.sh
  landed; tested locally — correctly returns exit 3 with
  "WAIT — Temple still offline" instead of attempting deploy.
  Retro: writing the resume-trigger as a script (not as a vague
  "I'll do it later") is the smallest concrete thing that converts
  BLOCKED-with-no-trigger into BLOCKED-with-named-mechanism. When
  Temple is up, one shell invocation closes L1.14 + L1.16 in a
  reproducible way — and the journalctl tail + lists.json print
  *are* the verification, not artifacts after the fact.

L1.17 [PENDING] [RR+PRECEDE] PARTIAL must surface as unfinished.
  Pre: L1.13.
  DoD: walker.OPEN includes "PARTIAL"; PARTIAL items appear in the
  scan output alongside PENDING/DOING/BLOCKED.
L1.17 [DOING] 2026-05-22
L1.17 [DONE]  2026-05-22 — walker.OPEN += "PARTIAL" in both the
  local and remote walker. Dry-run now surfaces L1.12 PARTIAL as
  expected. Retro: PARTIAL was invented in BIBLE's quality-gates
  revision after this build's first pass — the scanner's static
  status sets are a fragility the BIBLE doctrine doesn't formalize.
  Documenting this in the carry-forward so future status changes
  don't fall into the same gap.

L1.12a [PENDING] [RR+PRECEDE] Session-start freshness procedure.
  Pre: L1.12.
  Successor of L1.12 (PARTIAL). Adds a feedback memory that
  enforces, at session start, "Read UNFINISHED_LISTS.md, compute
  `now - generated_at`, and if > 10 min explicitly state the surface
  is stale before acting on its contents."
  DoD: `feedback_check_lists_freshness.md` exists, is indexed under
  CRITICAL in MEMORY.md, names the operation it gates (the
  session-start read), and the externally-checkable failure mode (a
  session transcript that acts on stale data without flagging it).
L1.12a [DOING] 2026-05-22
L1.12a [DONE]  2026-05-22 — feedback_check_lists_freshness.md
  landed; MEMORY.md CRITICAL section indexes it. Retro: this is the
  reader-side enforcement that L1.12 couldn't bake into the
  write-only markdown — the staleness check moved from "where the
  data is" to "where the data is consumed," which is the only place
  it can actually fire.

---

## LAYER 2 — Audit pass (post-hoc adversarial review)

This layer is the post-hoc adversarial review that should have
happened pre-commit (Gate 5 failure on L1). Run after Brad called
out skipping + lying on lists.

L2.01 [PENDING] [RR+PRECEDE] Read 4 new feedback files.
  Pre: none. DoD: feedback_session_start_live_list,
  feedback_done_requires_real_retro, feedback_correction_means_propose,
  feedback_quality_rules_as_procedures all read.
L2.01 [DOING] 2026-05-22
L2.01 [DONE]  2026-05-22 — Read. Retro: my batched-retro pattern is
  exactly the failure mode procedure #1 names; the rule is gating
  the operation, not advising it.

L2.02 [PENDING] [RR+PRECEDE] Read UNFINISHED_LISTS.md.
  Pre: none. DoD: live index opened in this session.
L2.02 [DOING] 2026-05-22
L2.02 [DONE]  2026-05-22 — Read. 4 open items (L39.13/14/15 PENDING,
  L37.10 DOING). Retro: I never read the live index until forced to
  by audit prompt — exactly the failure procedure #2 was written
  for. Three L39 items were on the list and I had no model of them.

L2.03 [PENDING] [RR+PRECEDE] Verify BIBLE_PROTOCOL.md universal-scope append.
  Pre: none. DoD: grep finds my 2026-05-22 universal-scope revision.
L2.03 [DOING] 2026-05-22
L2.03 [DONE]  2026-05-22 — Line 337. Retro: Brad appended Quality
  gates revision at line 366 that my L1 build violated on Gates
  1/5/6. The audit got bigger when I read past my own edit.

L2.04 [PENDING] [RR+PRECEDE] Verify CLAUDE.md BIBLE-Universal block.
  Pre: none. DoD: grep finds the block.
L2.04 [DOING] 2026-05-22
L2.04 [DONE]  2026-05-22 — Line 373. Retro: This one survives —
  proves the append-only pattern works when not contested by a
  linter.

L2.05 [PENDING] [RR+PRECEDE] Verify timer fires unattended.
  Pre: Temple reachable. DoD: journalctl shows ≥2 unattended fires
  with json mtime advancing.
L2.05 [BLOCKED] 2026-05-22 — Temple offline last seen 14m ago.
  Retro: this blocked state IS the L1.07 design gap — when Temple
  is down the surfaces go stale and nothing tells me.

L2.06 [PENDING] [RR+PRECEDE] Verify all 4 surfaces consistent NOW.
  Pre: Temple reachable. DoD: drawer count == json count == md
  count == fusion count.
L2.06 [BLOCKED] 2026-05-22 — Same blocker as L2.05.

L2.07 [PENDING] [RR+PRECEDE] Write real retros for L1.01-L1.10.
  Pre: L2.01. DoD: LISTS_NOTES.md has one reflective retro per item.
L2.07 [DOING] 2026-05-22
L2.07 [DONE]  2026-05-22 — Landed in LISTS_NOTES.md under
  "RETROACTIVE retros". Retro: writing the retros surfaced 6 gaps
  the original close had not seen; the retro IS the analysis, not
  a write-up of the analysis.

L2.08 [PENDING] [RR+PRECEDE] Investigate dirty zignal files on Z13.
  Pre: none. DoD: per-file determination of whether it overlaps
  the LISTS build.
L2.08 [DOING] 2026-05-22
L2.08 [DONE]  2026-05-22 — 4 files (convo_miner mod + http_server,
  palace_repair, mine_claude_sessions.sh new). All unrelated to
  LISTS; chromadb + palace + session-mining work. Retro: Z13 repo
  is behind Temple in *deployment* (Temple runs http_server.py
  that Z13 hasn't committed), which means git state is a lying
  indicator of what's actually live.

L2.09 [PENDING] [RR+PRECEDE] Re-examine L37.10 in fusion-v2 NOTES.md.
  Pre: Temple reachable. DoD: read the actual context of L37.10 +
  determine if coordination is needed.
L2.09 [BLOCKED] 2026-05-22 — Same Temple blocker. Brad already
  confirmed: actively being worked on. Retro queued — verify when
  Temple is back that the context matches Brad's statement.

L2.10 [PENDING] [RR+PRECEDE] Propose corrections.
  Pre: L2.01-L2.09 to extent possible. DoD: concrete remediation
  items appended to plan as L1.12+, not vague "do better."
L2.10 [DOING] 2026-05-22
L2.10 [DONE]  2026-05-22 — L1.12-L1.16 added with DoD lines. Retro:
  framing the remediation as new BIBLE items (with DoD) instead of
  free-text is the difference between fixing and pledging to fix.

---

## PROGRESS LOG
*(append-only — newest at bottom, dated)*

2026-05-22 — plan drafted. L1.01–L1.10 PENDING.
2026-05-22 — L1.01–L1.10 closed in single session. All 4 surfaces
  verified at 9 items. Timer running every 5 min on Temple.
2026-05-22 — Audit pass L2.01-L2.10 after Brad called out skipped /
  lied retros. L2.05/L2.06/L2.09 BLOCKED on Temple offline; rest
  closed with real retros. Remediation queued as L1.12-L1.16.
  L1.16 BLOCKED on same Temple outage.
2026-05-22 — Adversarial review (Gate 5) on the audit-pass killed 7
  items. Real fixes: L1.12 PARTIAL→SKIPPED (DoD unupgradeable),
  L1.14 DONE→PARTIAL (deploy still owed), L1.16a resume-trigger
  script landed, 10 external-validator tests added, walker/emit/
  Fusion now distinguish unknown / degraded / clear properly,
  ListsStatus.alarm fixed. Commits 395b352 (zignal) +
  bab69545 (fusion).
