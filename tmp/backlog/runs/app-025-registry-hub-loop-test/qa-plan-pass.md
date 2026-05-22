# QA PASS: plan — round 1

**Task:** app-025-registry-hub-loop-test  
**backlog_ticket:** APP-025  
**ticket_path:** [tmp/backlog/app-025-registry-hub-loop-integration-test.md](../../app-025-registry-hub-loop-integration-test.md)  
**Round:** 1  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) § Registry hub loop integration test (APP-025)  
**domain_spec_creation:** not_needed (`registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## qa-spec-pass re-review focus — resolution

| qa-spec note | Severity | Status | Evidence in `plan.md` |
|--------------|----------|--------|------------------------|
| T3 events query shape (session id, SQL, `json.loads`, scope filter) | major (plan gate) | **Fixed** | §4 `_max_event_id`, `_phase_set_transitions`, `_active_session_id`; contract table (conn, session id, payload keys, `ORDER BY id ASC`, `id > after_id`); canonical T3 body §4.3 |
| Domain spec file map omits new module | minor | **Deferred correctly** | §8 close-time file map row; not impl scope |
| Per-AC checklist restatement | minor | **Fixed** | §7 Acceptance criteria checklist; § Requirements → implementation map |
| R3 optional sub-test bounded | minor | **Fixed** | §6 optional non-blocking; must not alter T1 order; out of scope in Approach |
| Human playtest vs bridge bootstrap | minor | **N/A at plan gate** | Approach + Non-goals in spec; Stage 7 separate |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-exploration-delve-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (impl: `app/tests/test_registry_hub_loop.py`; close: domain spec)
- [x] Acceptance criteria testable — ticket AC + spec R1–R5 mapped in §7, § Requirements → implementation map, T1–T5 matrix
- [x] Code traces match repo (independent spot-check below)
- [x] AGENTS.md / canon compliance (test-only; bridge-direct; no `build/` drift; isolated workspace)
- [x] Tests/commands listed (new module, phase FSM regressions, full `app/tests` gate)
- [x] Spec R1–R5 coverage in plan (loop, undercrypt, events audit, exit vs extract, fixtures policy, no prod change unless bug)
- [x] Anti-patterns guardrails (Flow E) — no `site_enter`, illegal `set_phase(delve)`, `world_travel` to layered address
- [x] qa-spec-pass adversarial note 1 (T3 contract) addressed — primary round-1 gate criterion

## Independent code traces (round 1)

| Claim | Repo evidence | Result |
|-------|---------------|--------|
| `bridge` fixture + isolated workspace | `app/tests/conftest.py:25–35` | **Match** |
| Salt-road bootstrap pattern | `app/tests/test_combat_monster_validation.py:13–17` | **Match** (plan copy verbatim) |
| `enter_dungeon` → resolve + `enter_site` + `advance_phase_for_dungeon_entry` | `app/gm/bridge.py:652–690` | **Match** |
| `exit_dungeon` → `exit_site` | `app/gm/bridge.py:697–700` | **Match** |
| `set_phase` + `phase.set` log `{from, to}` | `play/tomb_gm/services/extraction.py:41–62`, `65–79` | **Match** |
| `bridge.ctx.conn` + dict row access | `app/gm/bridge.py:20` `row_factory = sqlite3.Row`; `test_setup_new_game_lifecycle.py:49+` | **Match** |
| Session id `"current"` in app tests | `test_setup_new_game_lifecycle.py:83` | **Match** |
| Events `payload_json` column | `play/tomb_gm/tests/test_simulation.py:56–59` | **Match** |
| `PHASE_TRANSITIONS` `delve→extract` | `extraction.py:12–17` | **Match** |

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/tests/test_registry_hub_loop.py` (new) | Yes |
| `tmp/app-exploration-delve-spec.md` (checklist, changelog, file map) | Yes (close-time only) |

**Explicitly not touched (no scope creep):** `app/gm/bridge.py`, `play/tomb_gm/services/*`, orchestrator, `conftest.py` shared helper extraction, APP-051 golden path.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 bridge-direct S0–S3 loop | Flow A; §6 T1 | `test_registry_hub_loop_preparation_through_extract` |
| R1 friendly `undercrypt` | Flow B; §6 T2 | `test_enter_dungeon_resolves_undercrypt_from_breley` |
| R2 ingress `events` audit | Flow C; §4 helpers | `test_enter_dungeon_logs_ingress_phase_transitions` |
| R3 exit ≠ extract | Flow D; §5 `_bootstrap_delve_on_surface` | T1, T4, T5 |
| R4 module + fixtures policy | §1–2; Approach table | docstring; `conftest` `bridge`; no LLM imports |
| R5 test-only unless bug | Approach; § Files | green pytest; prod fix only if red |
| Ticket AC: full loop | §7 row 1 | **T1** |
| Ticket AC: mode/phase asserts | §7 rows 2–4 | **T1**, **T2**, **T4**, **T5** |
| Ticket AC: `phase.set` rows | §7 row 5 | **T3** + §4 |
| Ticket AC: domain spec sync | §8 | `release --done` |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-025 `in_progress`, P1 feature |
| Plan ⊆ Expected files | **PASS** | Single new test module at impl |
| Spec R1–R5 in plan | **PASS** | Flows A–E + matrix |
| Code traces | **PASS** | Bridge path, FSM, events shape verified |
| T3 events contract | **PASS** | qa-spec-pass round-1 gate criterion met |
| Test plan vs qa-spec-pass | **PASS** | T1–T5 + regression trio + full suite |
| Failure isolation | **PASS** | T1 full loop; T2–T5 separate functions |
| Close-time spec sync | **PASS** | §8 checklist, changelog, file map |

## Notes (non-blocking — implementation QA)

1. **`_assert_ingress_phase_audit` stub (§4.3):** Wrapper uses `after_id=0` without snapshot — incomplete. Impl should follow canonical inline T3 body only; omit wrapper if unused (Dev reflection agrees).
2. **T2 `resolved_from`:** Optional assert is correct — bridge sets when slug ≠ canonical (`bridge.py:688–689`). Impl may use strict `== "undercrypt"` after one live confirm.
3. **Duplicate `bridge_with_session` fixture:** Local module copy mirrors `test_combat_monster_validation.py` — acceptable per plan; no `conftest` extraction until APP-051.
4. **Bootstrap `phase.set` noise:** `_max_event_id` before `enter_dungeon` excludes post-bootstrap events — adequate; if bootstrap ever logs phase transitions, T3 still scoped correctly.
5. **`impl-check APP-025`:** Plan open question — impl must run before editing `app/tests/`.
6. **Optional R3 sub-test (`set_phase("extract")` while `mode=dungeon`):** Correctly deferred; do not merge into T1 ordering.

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
