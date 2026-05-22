# QA PASS: Implementation

**Task:** app-077-exploration-status-footer  
**backlog_ticket:** APP-077  
**ticket_path:** [tmp/backlog/app-077-code-owned-exploration-status-footer.md](../../app-077-code-owned-exploration-status-footer.md)  
**Round:** 1  
**Reviewer role:** QA (implementation review)

**Verdict:** PASS

## Tests run

| Command | Result |
|---------|--------|
| `cd app && python -m pytest tests/test_exploration_status_footer.py -q` | **10 passed** |
| `cd app && python -m pytest tests/test_exploration_site_entry_gate.py -q` | **7 passed** |
| `cd app && python -m pytest tests/test_exploration_set_phase_delve_hint.py -q` | **6 passed** |
| `cd app && python -m pytest tests/test_creation_flavor_sanitize.py -q -k status` | **2 passed** |

## Diff scope reviewed

### Ticket Expected files (all touched as required)

| File | Review |
|------|--------|
| `app/gm/creation.py` | **PASS** — `_LLM_STATUS_TAG_RE` broadened (F4); `strip_llm_meta_narration` (F5); `_primary_roster_entry` + `format_exploration_status` (F1–F3) at L115–730 |
| `app/gm/orchestrator.py` | **PASS** — `_compose_exploration_narration` compose order APP-024 → drift → strip → meta → footer (F6–F8); `_emit_exploration_narration` + `_is_code_only_combat_narration` (F9); combat emit at L2374/L2406; exploration `process_turn` L1244; `_llm_loop` inner compose L2702 |
| `app/gm/system_prompt.py` | **PASS** — F10: step 6 + Response Format mandate removed; client-appends-state instruction at L213, L273 |
| `app/gm/logger.py` | **PASS** — F11: `log_exploration_drift` at L57–59 |
| `app/tests/test_exploration_status_footer.py` | **PASS** — 10 cases cover golden footers, strip, compose, idempotency, combat wrong-GP integration |
| `tmp/app-exploration-delve-spec.md` | **PM draft present** — § Code-owned status footer (APP-077) L339+; implementation changelog + open-work checkbox update deferred to Stage 6 drift |
| `tmp/app-llm-orchestrator-spec.md` | **PM draft present** — § APP-077 L594+; close-out changelog deferred to Stage 6 |

### Out-of-scope file (justified)

| File | Note |
|------|------|
| `app/tests/test_exploration_site_entry_gate.py` | **Acceptable** — `test_site_entry_gate_bypass_when_in_dungeon` updated to assert prose + single code footer (APP-077 changes player-visible shape). Not in ticket Expected files; necessary APP-024 regression fix. Recommend adding path to ticket Expected files before commit for audit trail. |

## Acceptance criteria mapping

| Ticket AC | Status | Evidence |
|-----------|--------|----------|
| Exploration footer contract (code-owned from engine) | **PASS** | `format_exploration_status` + `_compose_exploration_narration`; domain spec § APP-077 |
| Combat footer contract (`Turn:` when combat active) | **PASS** | `format_exploration_status` L722–725; `test_format_exploration_status_golden` combat variant; `test_combat_turn_compose_wrong_gp` |
| `format_exploration_status` golden snapshot | **PASS** | `test_format_exploration_status_golden`, `test_format_exploration_status_gp_transit`, `test_format_exploration_status_empty_roster` |
| `_compose_exploration_narration` strip + single footer | **PASS** | `test_compose_exploration_single_footer`, `test_compose_idempotent_double_call` |
| Strip meta narration leaks | **PASS** | `strip_llm_meta_narration` L591–597; `test_strip_llm_meta_narration` |
| Empty body still append footer | **PASS** | `test_compose_empty_body_still_footer`; compose L671–675 |
| Wire `_llm_loop` + combat success paths | **PASS** | Inner compose L2702; `_emit_exploration_narration` at combat L2374/L2406 |
| Update `system_prompt.py` (no LLM status mandate) | **PASS** | L213, L273 — verified by read |
| Optional `log_exploration_drift` | **PASS** (shipped) | `logger.py` L57; `_log_exploration_drift_if_needed` L677–716 — no unit test (optional per plan) |
| Integration: wrong GP in LLM bracket → engine GP in footer | **PASS** | `test_compose_exploration_single_footer`, `test_combat_turn_compose_wrong_gp` |

## Requirements trace (plan F1–F11)

| ID | Impl locus | Test gate | Result |
|----|------------|-----------|--------|
| F1–F3 | `creation.py` `format_exploration_status` | golden + combat + empty roster | PASS |
| F4 | `_LLM_STATUS_TAG_RE` | `test_strip_llm_status_tags_exploration_bracket` + creation `-k status` | PASS |
| F5 | `strip_llm_meta_narration` | `test_strip_llm_meta_narration` | PASS |
| F6–F8 | `_compose_exploration_narration` | compose unit tests incl. idempotency | PASS |
| F9 | `_emit_exploration_narration`, death/prefix skip | `test_combat_turn_compose_wrong_gp` | PASS |
| F10 | `system_prompt.py` | manual grep | PASS |
| F11 | `log_exploration_drift` | no test (optional) | PASS (shipped) |

## Adversarial notes (non-blocking)

1. **IMPL-NOTE-001 — No drift-log unit test** — F11 telemetry implemented but untested; acceptable per plan (optional AC).
2. **IMPL-NOTE-002 — Spec close-out pending** — Domain specs have PM draft sections; ticket AC checkboxes, changelog dated implementation entry, and “Open work” row removal belong in Stage 6 drift — not an implementation defect.
3. **IMPL-NOTE-003 — L2287 early return** — Pre-existing combat-end path without `_emit_narration` remains out of scope (qa-spec-pass NOTE-003); not regressed by this change.
4. **IMPL-NOTE-004 — Prefix-only combat skip** — `_is_code_only_combat_narration` skips footer on `[Mechanics failed — …]` with no trailing prose; exploration `all_failed` path still composes (plan PLAN-004). Human playtest should confirm combat HUD suffices when footer omitted.

## TurnTruth gate (APP-083)

Compose runs on LLM prose paths without verify gate (documented non-goal). Strip + footer are defense-in-depth until APP-083 Phase 2 — consistent with spec F12 and `tomb-dust-turn-truth-verify.mdc`.

## Summary

Implementation matches approved plan and ticket AC. All plan regression commands green. Expected-file scope honored except one justified regression test update. **Ready for Stage 6 drift check + ticket release.**
