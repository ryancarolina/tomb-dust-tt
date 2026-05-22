# Drift Check: APP-025-registry-hub-loop-test

**backlog_ticket:** APP-025  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) § Registry hub loop integration test (APP-025) | no | Checklist `[x]`, changelog **APP-025 done** (2026-05-22), file map row added; matches `test_registry_hub_loop.py` |
| Run [`spec.md`](./spec.md) R1–R5 | no | T1–T5 map to S0→S3 loop, events audit, exit vs extract contract |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Exploration domain row unchanged; test-only ticket — no registry gap |

## Code ↔ domain spec (APP-025 scope)

| Requirement | Code | Match |
|-------------|------|-------|
| Bootstrap `32-C` / `preparation` via salt-road session | `_ensure_salt_road_session` L15–19; `_assert_preparation_at_breley` L28–31 | yes |
| S1: `enter_dungeon(site_address="32-C-UG-1")` → dungeon/delve | T1 L102–107; T4 L166–170 | yes |
| Friendly `undercrypt` → `32-C-UG-1` | T2 L131–139 | yes |
| S2: `exit_dungeon()` → surface, phase stays delve, site cleared | T1 L109–114; T4 L172–177; `_bootstrap_delve_on_surface` L85–90 | yes |
| S3: `set_phase("extract")` → extract on surface | T1 L116–121; T5 L186–190 | yes |
| Ingress `events` `phase.set`: preparation→ingress→delve | T3 L152–156; `_phase_set_transitions` L56–69 with `after_id` scope | yes |
| Bridge-direct only — no `site_enter`, `world_travel`, orchestrator, LLM | Module grep: none present | yes |
| Isolated workspace via `conftest.py` `bridge` fixture | T1 uses `bridge`; T2–T4 use `bridge_with_session` | yes |

## Domain spec test matrix ↔ tests

| Case | Spec table | Test | Result |
|------|------------|------|--------|
| Full hub loop | Bootstrap → S3 | `test_registry_hub_loop_preparation_through_extract` (T1) | ✓ |
| Friendly site name | `enter_dungeon("undercrypt")` | `test_enter_dungeon_resolves_undercrypt_from_breley` (T2) | ✓ |
| Phase audit | `events` preparation→ingress→delve | `test_enter_dungeon_logs_ingress_phase_transitions` (T3) | ✓ |
| Exit vs extract | `exit_dungeon` keeps delve; extract separate | `test_exit_dungeon_keeps_delve_phase` (T4), `test_set_phase_extract_from_delve` (T5) | ✓ |

## Ticket AC ↔ verification

| Ticket AC | Result |
|-----------|--------|
| Bridge-direct loop: `32-C` / `preparation` → `enter_dungeon` → `exit_dungeon` → `set_phase("extract")` | ✓ T1 |
| After entry: `mode=dungeon`, `phase=delve` | ✓ T1, T2, T4 |
| After exit: `mode=surface`, `phase=delve` | ✓ T1, T4 |
| After `set_phase("extract")`: `phase=extract` | ✓ T1, T5 |
| `events` `phase.set` preparation→ingress→delve on `enter_dungeon` | ✓ T3 |
| Domain spec § synced + changelog on close | ✓ updated this pass |

## Tests run

```bash
cd app && python -m pytest tests/test_registry_hub_loop.py -v
```

**Result:** 5 passed in 0.70s

| Test | Case | Result |
|------|------|--------|
| `test_registry_hub_loop_preparation_through_extract` | T1 — full S0→S3 | ✓ |
| `test_enter_dungeon_resolves_undercrypt_from_breley` | T2 — friendly slug | ✓ |
| `test_enter_dungeon_logs_ingress_phase_transitions` | T3 — events audit | ✓ |
| `test_exit_dungeon_keeps_delve_phase` | T4 — exit ≠ extract | ✓ |
| `test_set_phase_extract_from_delve` | T5 — extract step | ✓ |

## Non-blocking notes (not drift)

| Item | Note |
|------|------|
| Full `app/tests` gate | Plan lists `python -m pytest app/tests -q`; not re-run in drift pass — focused module green |
| Optional R3 sub-test | `set_phase("extract")` while `mode=dungeon` deferred per plan; post-exit path covered |
| Production code | No `app/gm` or `play/tomb_gm` edits — test-only ticket as expected |
| `tmp/backlog/README.md` | Status index may lag until `release APP-025 --done` |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [x] Domain spec checklist + changelog — APP-025 done row added
- [x] Domain spec file map — `app/tests/test_registry_hub_loop.py` row added
- [x] Open work list — APP-025 removed
- [ ] `python tmp/backlog/claim_ticket.py release APP-025 --done` — **orchestrator** (QA drift: not run)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec § APP-025 matched implementation before drift; ticket AC, checklist tick, changelog, and file map were the lagging artifacts.
- Bridge behavior traced in impl QA (`bridge.enter_dungeon` → `advance_phase_for_dungeon_entry`; `exit_dungeon` → `exit_site`) — no prod fixes required.
- Human playtest deferred to Stage 7 `human-test-plan.md` (bridge-only ticket).
