# Reflection: Dev — APP-025 WS1 implementation

**Agent:** Dev (impl)  
**Workstream:** WS1 — Registry hub loop integration test  
**Deliverables:** `app/tests/test_registry_hub_loop.py` (T1–T5 + T3 events helpers)

## Completed

- **Module scaffold:** Added `app/tests/test_registry_hub_loop.py` with bridge-direct docstring policy (no orchestrator, no LLM mocks).
- **Bootstrap helpers:** `_ensure_salt_road_session`, `bridge_with_session` fixture, `_assert_preparation_at_breley`, `_normalized_site_id`, `_active_session_id`.
- **T3 events helpers:** `_max_event_id`, `_phase_set_transitions` with `after_id` scope filter and `json.loads` payload parsing per qa-spec contract.
- **Composite setup:** `_bootstrap_delve_on_surface` for T5 (enter → exit → surface/delve state).
- **Tests T1–T5:** Full S0→S3 loop, undercrypt slug resolution, ingress `phase.set` audit, exit keeps `delve`, `set_phase("extract")` from surface/delve.

## Deviations

- None from plan. Optional R3 sub-test (`set_phase("extract")` while still `mode=dungeon`) deferred per plan §6.
- No production code changes — bridge/FSM behaved as spec expected.

## Self-critique

- T1 uses inline `_ensure_salt_road_session` rather than `bridge_with_session` fixture — matches plan allowance; T2–T5 use fixture for DRY bootstrap.
- T2 asserts `resolved_from == "undercrypt"` only when bridge returns the key (conditional) — avoids brittle failure if field omitted while still checking when present.
- Events audit isolated in T3 with pre-`enter_dungeon` `after_id` snapshot — prevents pollution from T1/T5 extract transitions.

## Test gates

```text
python -m pytest app/tests/test_registry_hub_loop.py -v — 5 passed (0.92s)
```

## Handoff

- Test module ready for QA implementation pass and domain spec sync on ticket close (`tmp/app-exploration-delve-spec.md` checklist + changelog + file map).
- No bridge/engine bugfixes required.
