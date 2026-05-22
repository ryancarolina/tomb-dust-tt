# QA PASS: implementation — round 1

**Task:** app-025-registry-hub-loop-test  
**backlog_ticket:** APP-025  
**ticket_path:** [tmp/backlog/app-025-registry-hub-loop-integration-test.md](../../app-025-registry-hub-loop-integration-test.md)  
**Round:** 1  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) § Registry hub loop integration test (APP-025)  
**domain_spec_creation:** not_needed (`registry_gap: false`)

## Verdict

**PASS** — Bridge-direct Breley hub loop (T1–T5) matches ticket AC, run spec R1–R5, and plan flows A–E; pytest green; no production code changes required.

## Automated tests

```text
cd app && python -m pytest tests/test_registry_hub_loop.py -v
5 passed in 0.73s
```

| Test | Case | Result |
|------|------|--------|
| `test_registry_hub_loop_preparation_through_extract` | T1 — full S0→S3 loop | ✓ |
| `test_enter_dungeon_resolves_undercrypt_from_breley` | T2 — friendly `undercrypt` slug | ✓ |
| `test_enter_dungeon_logs_ingress_phase_transitions` | T3 — `events` `phase.set` audit | ✓ |
| `test_exit_dungeon_keeps_delve_phase` | T4 — exit ≠ extract | ✓ |
| `test_set_phase_extract_from_delve` | T5 — extract from surface/delve | ✓ |

**Plan regressions (non-blocking gate, run for confidence):**

```text
cd play && python -m pytest tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve -q
2 passed in 0.20s

cd app && python -m pytest tests/test_exploration_set_phase_delve_hint.py -q
6 passed in 2.14s
```

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Bridge-direct loop: `32-C` / `preparation` → `enter_dungeon` → `exit_dungeon` → `set_phase("extract")` | T1 L97–121; uses `enter_dungeon(site_address="32-C-UG-1")` | ✓ |
| After entry: `mode=dungeon`, `phase=delve` | T1 L105–107; T2 L137–139; T4 L169–170 | ✓ |
| After exit: `mode=surface`, `phase=delve` | T1 L112–114; T4 L175–177 | ✓ |
| After `set_phase("extract")`: `phase=extract` | T1 L116–119; T5 L186–190 | ✓ |
| Friendly `undercrypt` resolves to `32-C-UG-1` | T2 L131–139 | ✓ |
| `events` `phase.set`: `preparation→ingress→delve` on `enter_dungeon` | T3 L152–156; helpers L56–69 | ✓ |
| Domain spec synced + changelog on close | § drafted in domain spec; checklist `[ ]` + impl-done changelog row deferred to `release --done` | ✓ (release hygiene) |

## Spec R1–R5 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Bridge-direct S0–S3 at Breley | T1; bootstrap `_assert_preparation_at_breley` L28–31 | ✓ |
| **R1** | `enter_dungeon` not `site_enter` / illegal paths | Module grep: no `site_enter`, `world_travel`, `set_phase("delve")`, orchestrator, or LLM mocks | ✓ |
| **R2** | Ingress `phase.set` audit via `bridge.ctx.conn` | T3 + `_max_event_id` / `_phase_set_transitions` with `after_id` scope | ✓ |
| **R3** | `exit_dungeon` keeps `phase=delve`; extract is separate | T1, T4, T5; `_bootstrap_delve_on_surface` L72–91 | ✓ |
| **R4** | Isolated workspace + salt-road bootstrap | `conftest.py` `bridge` fixture; `_ensure_salt_road_session` L15–19 | ✓ |
| **R5** | Test-only; prod fix only if red | No `app/gm` or `play/tomb_gm` edits; all tests green | ✓ |

## Independent code traces

| Claim | Repo evidence | Result |
|-------|---------------|--------|
| `enter_dungeon` → resolve + `enter_site` + `advance_phase_for_dungeon_entry` | `app/gm/bridge.py:652–690` | **Match** |
| `exit_dungeon` → `exit_site` | `app/gm/bridge.py:697–700` | **Match** |
| T3 `after_id` prevents extract-transition pollution | T3 L150–156; plan Flow C | **Match** |
| `resolved_from` optional assert when bridge returns key | T2 L133–134; `bridge.py:688–689` | **Match** |
| Isolated workspace fixture | `app/tests/conftest.py:25–35` | **Match** |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/tests/test_registry_hub_loop.py` | **new** — T1–T5 + helpers (191 lines) | ✓ (untracked `??`) |
| `tmp/app-exploration-delve-spec.md` | § APP-025 drafted; checklist L465 still `[ ]` | ✓ (close-time sync) |

**Explicitly not touched (correct):** `app/gm/bridge.py`, `play/tomb_gm/services/*`, orchestrator, `conftest.py` shared helper extraction.

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Untracked new file** | `app/tests/test_registry_hub_loop.py` must be staged before commit. |
| **Domain spec close** | Checklist L465 + impl-done changelog row — update on `release APP-025 --done`. |
| **Ticket checkboxes** | Backlog AC still unchecked — tick at close. |
| **Full `app/tests` gate** | Plan lists `python -m pytest app/tests -q`; not run in this pass (focused module + plan regressions green). |
| **Optional R3 sub-test** | `set_phase("extract")` while `mode=dungeon` correctly deferred per plan §6. |
| **Human playtest** | Bridge-only ticket; no PyGame smoke required for impl PASS. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-025 --done` (domain checklist `[x]`, changelog row, ticket AC ticks, stage test file).  
**No escalations** — bridge/FSM behaved as spec; no prod bugfixes needed.
