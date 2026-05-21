# QA PASS: plan — round 1

**Task:** APP-017-reconcile-empty-roster
**backlog_ticket:** APP-017
**ticket_path:** [tmp/backlog/app-017-reconcile-empty-roster-on-load.md](../../app-017-reconcile-empty-roster-on-load.md)
**Round:** 1
**domain_spec_creation:** not_needed (qa-spec-pass round 2 confirmed)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-session-persistence-spec.md`
- [x] Ticket domain spec matches spec/plan (run `spec.md`, domain § Reconcile empty roster on load)
- [x] Acceptance criteria testable (R1–R5, ticket AC, T-017a–f / T-017c2, pytest commands)
- [x] Code traces match repo (independent re-trace below)
- [x] AGENTS.md / canon compliance (session persistence only; no `build/` edits)
- [x] Tests/commands listed with hygiene (`_session_state_path` + `SAVE_PATH` monkeypatch)
- [x] Plan files ⊆ ticket Expected files (`orchestrator.py` + new test module only)
- [x] registry_gap not applicable at plan stage (spec QA confirmed `false`)

## Independent code trace (adversarial)

| Claim | Repo evidence | Verdict |
|-------|---------------|---------|
| Root bug: sync uses `characters` not `roster` | `app/gm/orchestrator.py:186` — `not status.get("characters")` | Confirmed |
| No `engine_status` read on load today | `app/ui/app.py:449-451` — `import_creation_state` + `_sync_creation_from_status` only; no snapshot read | Confirmed |
| Symptom: empty chips when inactive + `CHARACTER_CREATION` | `app/ui/suggestions.py:95-96` — returns `[]` when `not creation_active` | Confirmed |
| APP-016 producer unchanged | `app/ui/app.py:393-426` `_save_session`; `test_engine_status_on_save.py` T4a | Confirmed |
| Resume NAME clobber (R4 violation) | `app/gm/orchestrator.py:572-576` — `CreationState(active=True, step="NAME")` | Confirmed — plan removes |
| Disk path helper exists | `app/gm/orchestrator.py:313-314` `_session_state_path()` | Confirmed — plan colocates helpers |
| `_restore_history` hardcoded path | `app/gm/orchestrator.py:126` — not `_session_state_path()` | Confirmed — plan correctly out of scope |
| Engine `ROSTER_SETUP` derivation | `play/tomb_gm/cli/cmd_core.py:178-182` — empty roster + chars → `ROSTER_SETUP` | Confirmed — T-017f guard valid |
| `_creation_drift_scope` already uses `roster` | `app/gm/orchestrator.py:215-218` | Confirmed — plan aligns drift/reconcile |
| Legacy T4c baseline fixture | `app/tests/test_engine_status_on_save.py:86-127` | Confirmed — T-017d copies pattern |
| Session-state patch prior art | `app/tests/test_creation_block_on_new_game.py:11-12` | Confirmed |
| T-017e chip strings | `app/ui/suggestions.py:17`; `test_ui_suggestions.py:28-35` | Confirmed |
| `get_player_suggestions` on orchestrator | `app/gm/orchestrator.py:116-121` wraps `build_player_suggestions` | Confirmed |

## AC mapping (plan → ticket → spec/domain)

| Ticket / spec AC | Plan coverage | Test |
|------------------|---------------|------|
| Empty roster + inactive + mid-creation → force active | `_force_creation_active_if_reconcile_needed` + sync prelude | T-017a, T-017b |
| Live `SETUP` + saved `CHARACTER_CREATION` | `_effective_awaiting_for_reconcile` SETUP fallback | T-017b |
| Post-finalize non-empty live roster unchanged | Early return + sync C2 | T-017c |
| Stale saved roster; live empty wins | Live roster only for empty check | T-017c2 |
| Legacy / missing `engine_status` | `_read_saved_engine_status` → `None`; no force on SETUP-only | T-017d |
| `ROSTER_SETUP` orphan rows no-op | Explicit guard before effective awaiting | T-017f |
| Suggestion chips after reconcile | Sync before suggestions path | T-017e |
| APP-018 boundary (active only; no NAME clobber) | Prelude `getattr` hook; remove L575-576; force helper sets `active` only | T-017b, R4 |
| Orchestrator-only disk read (R5) | `_session_state_path()` in helpers; no `ui/app.py` edit | All disk tests |
| Reconcile without successful resume | Reconcile in `_sync_creation_from_status` called from `_load_session` (A3) before resume | T-017a/b via sync; Flow A |

## Scope gate

| Path | In ticket Expected? | In plan | Role |
|------|---------------------|---------|------|
| `app/gm/orchestrator.py` | Yes | Yes | **Edit** — helpers, sync prelude, resume trim |
| `app/tests/test_reconcile_empty_roster_on_load.py` | Yes | Yes | **Add** — T-017a–f, T-017c2 |
| `tmp/app-session-persistence-spec.md` | Close only | Out of scope (WS close) | Changelog on ticket release |
| `app/ui/app.py` | No | Out of scope | Reconcile via orchestrator sync — correct |

## Cross-checks (qa-spec-pass r2 → plan)

- [x] Merge order 018 → 017 in `_sync_creation_from_status` prelude (`getattr` hook + force helper before body)
- [x] R3 `roster` not `characters` in sync C3 + `ROSTER_SETUP` guard in force helper
- [x] R2 live roster wins over stale saved (T-017c2); awaiting fallback when live `SETUP`
- [x] Plan traces match run `spec.md` R1–R5 and domain § APP-017 tests table
- [x] Batch note: APP-018 hook no-op until 018 lands; no duplicate force-active in 018 scope

## Notes (non-blocking)

1. **UI `_load_session` import before sync** — `app/ui/app.py:449` still calls `import_creation_state` before `_sync_creation_from_status`. APP-017 bug path is `creation_state: null` (import no-op); prelude hook covers 018→017 inside sync. Full orchestrator-owned merge lands with APP-018; coordinate to avoid double-restore when both touch disk.
2. **Fixture reuse** — `save_path` / `headless_app` live in `test_engine_status_on_save.py`; new module must duplicate fixtures or import helpers (pytest does not auto-share). Pattern matches other app tests.
3. **T-017c finalize** — Full `INPUTS` loop needs `roll_attributes` monkeypatch (per `test_engine_status_on_save.py` T4b / dev-plan reflection); plan references but does not spell patch — impl should copy T4b setup.
4. **T-017b step assert** — Default `CreationState.step == "NAME"`; sync body `WORLD_INTRO → NAME` only fires when step is `WORLD_INTRO`. Assert holds for fresh orchestrator; document if test seeds `WORLD_INTRO`.
5. **Idempotency** — Design is idempotent; no explicit “call sync twice” test — optional impl hardening.
6. **Pytest not run** — Plan gate only; impl QA must execute plan § Commands.
7. **`_is_mid_creation_resume_failure`** — Does not read `engine_status`; plan open Q4 — acceptable; reconcile at A3 covers post-`_load_session` path before resume failure narration.

## Summary

Plan is implementation-ready: minimal orchestrator diff (three helpers + sync prelude + `characters`→`roster` + resume trim), dedicated test module within ticket Expected files, and full AC/test mapping aligned with qa-spec-pass round 2 and domain § APP-017. No blockers.

## Re-review focus

_None — proceed to workstreams / implementation._
