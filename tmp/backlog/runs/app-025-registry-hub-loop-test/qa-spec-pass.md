# QA PASS: spec — round 1

**Task:** app-025-registry-hub-loop-test  
**backlog_ticket:** APP-025  
**ticket_path:** [tmp/backlog/app-025-registry-hub-loop-integration-test.md](../../app-025-registry-hub-loop-integration-test.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-exploration-delve-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (identical pair)
- [x] Acceptance criteria testable and mapped (R1–R5, T1–T5, domain § APP-025)
- [x] Code traces match repo (live probe + source read)
- [x] AGENTS.md / canon compliance (test-only; bridge-direct; no mechanics drift)
- [x] Tests/commands listed (`test_registry_hub_loop.py`, regression pair, full `app/tests`)
- [x] registry_gap false — exploration-delve spec owns § Registry hub loop integration test
- [x] Every ticket AC row covered in run spec + domain spec

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; `in_progress`; domain spec field correct |
| registry_gap | **PASS** | false — PM echoed research; no new domain spec needed |
| AC testability | **PASS** | Loop, state asserts, events audit, spec sync on close |
| Code traces | **PASS** | Bridge path, FSM, `exit_site` phase retention confirmed |
| Expected files ⊆ plan scope | **PASS** | Ticket ↔ spec ↔ domain Tests block aligned |
| Domain spec sync (draft) | **PASS** | § APP-025 + changelog PM draft; checklist open item correct pre-impl |

## Acceptance criteria mapping

| Ticket AC | spec.md | Domain spec | Testable | QA |
|-----------|---------|-------------|----------|-----|
| Bridge-direct loop: `32-C` / `preparation` → `enter_dungeon` → `exit_dungeon` → `set_phase("extract")` | R1 S0–S3; T1 | § Canonical loop table | pytest T1 | **PASS** |
| After entry: `mode=dungeon`, `phase=delve`; after exit: `mode=surface`, `phase=delve`; after `set_phase`: `phase=extract` | R1 assert table; T1/T4/T5 | Same table rows | inline + split tests | **PASS** |
| `events` `phase.set` rows: `preparation→ingress→delve` during `enter_dungeon` | R2; T3 | § Ingress observability | SQL + JSON payload | **PASS** (see note 1) |
| Domain spec § APP-025 synced; changelog on close | R5; AC mapping | § + changelog PM draft | drift on close | **PASS** |

## Code evidence (pre-implementation baseline)

| Claim | Evidence |
|-------|----------|
| Bootstrap at `32-C` / `preparation` / `surface` | Live probe; `play/tomb_gm/domain/session.py` `DEFAULT_HUB_ADDRESS`, `DEFAULT_PHASE` |
| `enter_dungeon` → `enter_site` + `advance_phase_for_dungeon_entry` | `app/gm/bridge.py` 652–690 |
| Phase FSM logs `phase.set` with `{from, to}` | `play/tomb_gm/services/extraction.py` 41–62, 65–79 |
| `exit_dungeon` → surface mode; phase unchanged | `exploration.py` 477–494 (no phase UPDATE); live probe `phase=delve` after exit |
| `set_phase("extract")` legal from `delve` | `PHASE_TRANSITIONS` `delve→extract`; live probe |
| `undercrypt` resolves to `32-C-UG-1` from Breley | Live probe `resolved_from=undercrypt`, `site_id=32-C-UG-1` |
| Salt-road bootstrap pattern exists | `app/tests/test_combat_monster_validation.py` `_ensure_salt_road_session` |
| `bridge.ctx.conn` used in app tests | `app/tests/test_setup_new_game_lifecycle.py` 49+ |
| Events stored as `payload_json` | `play/tomb_gm/cli/cmd_core.py` 293–303 |

## Adversarial notes (non-blocking)

1. **Events query shape (T3)** — Run spec R2 requires `events` audit via `bridge.ctx.conn` but does not pin session id source, SQL, or `json.loads(payload_json)`. No existing `app/tests/` helper cites `phase.set` rows (engine: `play/tomb_gm/tests/test_simulation.py`). Dev plan should add a small `_phase_set_transitions(conn, session_id)` helper or inline query using `bridge.status()["active"]["session_id"]` and filter rows **before** S2/S3 so later `extract` transitions do not pollute T3.
2. **Domain spec file map** — § File map omits `app/tests/test_registry_hub_loop.py`; Tests § and checklist reference it. Minor doc gap; add on ticket close or in Dev plan.
3. **Run spec AC mapping table** — § Acceptance criteria mapping has two summary rows; full AC coverage lives in R1–R5 / T1–T5. Acceptable; Dev plan should restate per-AC checklist.
4. **R3 optional sub-test** — `set_phase("extract")` while `mode=dungeon` succeeds (live probe: phase `extract`, mode still `dungeon`). Optional per spec; canonical loop remains exit-then-extract. Do not let optional sub-test replace ticket AC order in T1.
5. **Human playtest vs bridge bootstrap** — Stage 7 hints assume creation → hub; automated test correctly skips creation (Non-goals). Human-test-plan should not require creation for automated AC sign-off.

## Summary

Ticket, run `spec.md`, and domain spec § **Registry hub loop integration test (APP-025)** are aligned on scope, bridge-direct path, exit vs extract contract, events ingress audit, and Expected files. Live probe confirms the full S0→S3 loop and friendly `undercrypt` resolution without roster. Spec is implementation-ready for Dev plan (stage 3). Dev plan should nail T3 events helper SQL and session id sourcing.

## Re-review focus

_None — proceed to Dev plan + QA plan gates. If Dev plan omits T3 events query contract, QA plan round 1 should FAIL plan stage._
