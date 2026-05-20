# Reflection: QA — APP-014 drift check (Stage 6)

**backlog_ticket:** APP-014  
**date:** 2026-05-20  
**verdict:** PASS  
**report:** drift-check.md

## What I verified

- Re-read domain spec § **setup_new_game lifecycle (APP-014)** (L1–L7, callers, invariants, batch table vs APP-015/016).
- Traced `setup_new_game` in `app/gm/orchestrator.py` and all three callers (`process_turn` new game, `_handle_player_death`, `run_ended` resume).
- Confirmed bridge surface (`end_session`, `force_close_all_sessions`, `wipe_all_data`, `campaign_new`, `session_start`) unchanged in APP-014 scope.
- Re-ran mandated pytest: T-014a–c (3), app `-k` filter (9), engine `-k session` (5).
- Updated domain spec checklist + changelog and closed ticket AC / status in backlog file.

## Key finding

**No spec ↔ code drift** for APP-014. Prior wipe-first ordering that caused `active session already exists` / `campaign already has an open session` is fixed: L1/L1b precede L2; success path reaches NAME with a single open session; corpses survive wipe (T-014c). Domain spec § APP-014, tests T-014a–c, and implementation align.

## Contrast with round 1 impl QA

| Item | Impl QA R1 | Drift check |
|------|------------|-------------|
| L1–L7 mapping | PASS | Re-verified on disk — still PASS |
| Ticket AC / spec checklist | Deferred Stage 6 | All [x]; changelog **APP-014 done** |
| pytest | 3 + 9 + 5 | Same counts — green |
| APP-015 entry helpers | Noted batch bleed | Confirmed spec-documented (C1–C2 before L1); not APP-014 drift |

## Process notes

- Drift PASS sets ticket **Status** `done` and **Closed** date; orchestrator still runs `release APP-014 --done` for session file cleanup.
- Did not run manual PyGame partial-creation → **`new game`** — deferred Stage 7 per prior QA handoff; not a drift blocker given T-014a/b.
- APP-015/016 sections in the same domain spec file were read for batch boundaries only; APP-015 AC not evaluated in this drift round.

## Handoff

Orchestrator: `release APP-014 --done`, Stage 7 `human-test-plan.md` (manual new-game from partial creation), batch board update for APP-014-APP-015-APP-016.
