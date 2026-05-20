# Reflection: Dev — APP-015 workstreams

**Agent:** Dev (workstreams)  
**Round:** 1  
**Inputs:** `plan.md` (round 2), `spec.md`, `qa-plan-pass.md` (round 2), ticket APP-015  
**Deliverables:** `workstreams.md`, `reflection-dev-workstreams.md`

## Completed

- Read plan WS1–WS3 breakdown, Traces A–H, AC mapping table, and QA plan PASS (PLAN-001/002 resolved).
- Split into **WS1** (orchestrator helpers + C1–C2 prepend) and **WS2** (T-015a–d test module), matching plan task breakdown.
- Mapped plan WS3 (UI, bridge, spec changelog) to explicit out-of-scope / release-only — not a third impl stream.
- Documented APP-014 merge ordering (C1 → C2 → L1 → …), `engine_status` pop requirement, and Trace E caller inheritance in WS1 constraints.
- Copied test matrix, fixtures, and pytest gates from plan § WS2 and § Tests.

## Stream decision

| Option | Verdict |
|--------|---------|
| **Single stream** | Viable — two files, one ticket; APP-002/003 precedent |
| **WS1 + WS2 (chosen)** | WS1 is independently testable via import smoke; WS2 needs WS1 behavior for T-015a–d; allows orchestrator-only land if batch time-boxes tests |
| WS3 spec sync | Rejected — domain changelog + `release --done` on ticket close (APP-066/067 pattern) |

Did **not** add a stream for `app/ui/app.py` — plan and domain defer UI-only clear; orchestrator-first makes `_save_session` idempotent (Trace F/G).

## Alignment checks

| Source | Check |
|--------|-------|
| qa-plan-pass R2 | PLAN-001 fixed: C2 must `pop` `engine_status`; reflected in WS1 §3 and constraints |
| qa-plan-pass R2 | PLAN-002 fixed: T-015d in WS2 matrix and gates |
| Ticket Expected files | Vague “session persistence layer” — plan files ⊆ `orchestrator.py` + `app/tests/`; workstreams list concrete paths |
| APP-014 batch | Merge order documented; WS1 prepends before L1 whether or not APP-014 merged |
| APP-016 boundary | WS1 clears stale snapshot on new game; APP-016 write-on-save out of scope |
| Run spec.md C5 | Still indexes T-015a–c in pointer table; domain spec is authority for T-015d (qa-plan note — no blocker) |

## Self-critique

- WS1 has only import smoke until WS2 — acceptable; ticket AC needs T-015a–d for close.
- Did not re-verify live `orchestrator.py` line numbers beyond grep anchors (~L348 `setup_new_game`, ~L294 resume probe); plan traces accepted from qa-plan-pass.
- Ticket Expected files should be tightened to `app/gm/orchestrator.py` and `app/tests/test_creation_block_on_new_game.py` on release (currently generic).
- T-015c may be brittle on exact variant-B copy strings — impl should assert **absence** of stale SKILLS/name, not full prose lock, unless domain spec mandates exact footer.

## Did I miss anything?

- [x] Plan WS1–WS2 mapped; WS3 out-of-scope listed
- [x] Domain C1–C4 and T-015a–d mapped to streams
- [x] Traces A–H preserved (A–E risks in WS1; F–G planned; H in WS2 T-015c)
- [x] Test commands and hygiene (tmp path, no dev save) in WS2
- [x] Open questions (missing file no-op, no history strip, APP-014 merge) in WS1 constraints
- [x] No code implemented (workstreams-only stage)

## Handoff

**Ready for:** Orchestrator dispatches **WS1** (required), then **WS2**  
**Order:** WS1 → WS2 (sequential; T-015a–d fail until C1–C2 land)  
**Escalate human if:** Batch merge with APP-014 conflicts in `setup_new_game` body order, or product waives T-015c recovery assert
