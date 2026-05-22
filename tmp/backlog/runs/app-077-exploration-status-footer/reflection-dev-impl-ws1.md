# Reflection: Dev — APP-077 WS1 implementation

**Agent:** Dev (impl)  
**Workstream:** WS1 — Helpers + compose pipeline + combat wire  
**Deliverables:** `creation.py`, `orchestrator.py`, `system_prompt.py`, `logger.py`, `test_exploration_status_footer.py`

## Completed

- **F1–F3:** Added `_primary_roster_entry` and `format_exploration_status` in `creation.py` — Location from `display_address`/`address`, roster slot pin, transit GP suffix, combat `Turn:` from `combat.turn_id` only (no `actor` fallback).
- **F4:** Extended `_LLM_STATUS_TAG_RE` with full exploration bracket alternation for idempotent re-compose (F8).
- **F5:** Added `strip_llm_meta_narration` for `---` + `**Campaign Memory Updated:**` trailing blocks.
- **F6–F8:** Expanded `_compose_exploration_narration` — APP-024 → drift log → strip tags → strip meta → append fresh `format_exploration_status(self.bridge.status())`; empty body still emits footer.
- **F9:** Added `_emit_exploration_narration` + `_is_code_only_combat_narration`; wired combat emit paths at `_combat_turn` L2302/L2334; death and prefix-only `[Mechanics failed — …]` paths skip compose.
- **F10:** Removed LLM status-line mandate from `system_prompt.py` HOW YOU WORK + Response Format.
- **F11:** Added `log_exploration_drift` + `_log_exploration_drift_if_needed` (telemetry only, pre-strip).
- **Tests:** New `test_exploration_status_footer.py` — 10 cases covering golden footers, strip helpers, compose/idempotency, combat wrong-GP integration.

## Deviations

- **Regression fix:** Updated `test_exploration_site_entry_gate.py::test_site_entry_gate_bypass_when_in_dungeon` — dungeon bypass now asserts prose + single code footer (APP-077 changes player-visible shape; strict `== ENTRY_PROSE` no longer valid).
- Chose `_emit_exploration_narration` wrapper over scattered inline compose at combat sites (plan allowed either; wrapper keeps F9 choke point clear).

## Self-critique

- Double-compose path (`_llm_loop` all_failed + `process_turn`) relies on F4 broad bracket strip — covered by `test_compose_idempotent_double_call`.
- Empty-roster footer uses `?/?`, `?/1`, `GP: 0` per qa-spec-pass SPEC-002; visible in dungeon bypass regression when test orchestrator has no roster.
- L2287 early combat-end return without `_emit_narration` left out of scope per plan NOTE-003.

## Test gates

```text
pytest tests/test_exploration_status_footer.py -q — 10 passed
pytest tests/test_exploration_site_entry_gate.py -q — 7 passed (after dungeon bypass assertion update)
pytest tests/test_exploration_set_phase_delve_hint.py -q — 6 passed
pytest tests/test_creation_flavor_sanitize.py -q -k status — 2 passed
```

## Handoff

- Domain spec changelog + ticket `release --done` remain for close-out (not in WS1 impl scope).
- APP-083 Phase 2 verify should run **before** compose when wired; current strip/footer is defense-in-depth until then.
