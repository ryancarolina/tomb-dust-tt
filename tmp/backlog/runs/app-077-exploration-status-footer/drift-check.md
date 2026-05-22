# Drift Check: app-077-exploration-status-footer

**backlog_ticket:** APP-077  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) § Code-owned status footer (APP-077) | was yes (checklist open; changelog draft-only) | **Synced:** § matches code; task checklist `[x]`; changelog **APP-077 done** row |
| [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) § APP-077 | was yes (open-work row; changelog draft-only) | **Synced:** compose pipeline matches code; open-work row removed; changelog **APP-077 done** row |
| Run [`spec.md`](./spec.md) F1–F11 | no | Verified against `creation.py`, `orchestrator.py`, `system_prompt.py`, `logger.py`, tests |
| Ticket [`app-077-code-owned-exploration-status-footer.md`](../../app-077-code-owned-exploration-status-footer.md) | no | All AC checked; status `done`; Closed 2026-05-22 |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| Footer fields from `bridge.status()` (Location, Phase, HP, Fortune, GP+transit, combat Turn, Awaiting) | `format_exploration_status` L705–730 in `creation.py` | yes |
| Roster pin = lowest `slot` | `_primary_roster_entry` L698–702 | yes |
| Compose order: APP-024 → drift log → strip tags → strip meta → footer | `_compose_exploration_narration` L662–675 | yes |
| Empty body still appends footer | L671–675; `test_compose_empty_body_still_footer` | yes |
| Strip LLM bracket tags (exploration tokens) | `_LLM_STATUS_TAG_RE` L115–119; `strip_llm_status_tags` | yes |
| Strip meta narration leaks | `strip_llm_meta_narration` L591–597 | yes |
| Exploration `process_turn` compose | L1244 | yes |
| `_llm_loop` `all_failed and content` compose | L2702 | yes |
| Combat success paths compose before emit | `_emit_exploration_narration` L731–734; L2374, L2406 | yes |
| Code-only combat failure/death skip footer | `_is_code_only_combat_narration` L718–729 | yes |
| Prompt: client appends status; no LLM bracket mandate | `system_prompt.py` L213, L273 | yes |
| Optional drift telemetry | `log_exploration_drift` in `logger.py`; `_log_exploration_drift_if_needed` L677–716 | yes (shipped) |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Exploration footer contract (code-owned from engine) | ✓ `format_exploration_status` + `_compose_exploration_narration`; domain spec § APP-077 |
| Combat footer contract (`Turn:` when combat active) | ✓ `format_exploration_status` combat branch; golden + `test_combat_turn_compose_wrong_gp` |
| `format_exploration_status` golden snapshot | ✓ `test_format_exploration_status_golden`, gp transit, empty roster |
| `_compose_exploration_narration` strip + single footer | ✓ `test_compose_exploration_single_footer`, idempotency test |
| Strip meta narration leaks | ✓ `strip_llm_meta_narration`; `test_strip_llm_meta_narration` |
| Empty body still append footer | ✓ `test_compose_empty_body_still_footer` |
| Wire `_llm_loop` + combat success paths | ✓ L2702 inner compose; combat `_emit_exploration_narration` |
| Update `system_prompt.py` | ✓ L213, L273 |
| Optional `log_exploration_drift` | ✓ shipped; no unit test (optional per ticket) |
| Integration: wrong GP in LLM bracket → engine GP in footer | ✓ compose + combat integration tests |

## Run spec F1–F11 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **F1–F3** | `format_exploration_status` field mapping | **PASS** |
| **F4** | Broad `_LLM_STATUS_TAG_RE` | **PASS** |
| **F5** | `strip_llm_meta_narration` | **PASS** |
| **F6–F8** | `_compose_exploration_narration` pipeline | **PASS** |
| **F9** | Combat/exploration emit wrapper + code-only skip | **PASS** |
| **F10** | `system_prompt.py` mandate removal | **PASS** |
| **F11** | `log_exploration_drift` telemetry | **PASS** (shipped, untested) |

## Tests run

```bash
cd app; python -m pytest tests/test_exploration_status_footer.py tests/test_exploration_site_entry_gate.py tests/test_exploration_set_phase_delve_hint.py -q
```

**Result:** 23 passed (4.40s)

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_exploration_status_footer.py` | 10 (golden, strip, compose, combat wire) | ✓ |
| `app/tests/test_exploration_site_entry_gate.py` | 7 (APP-024; in-dungeon bypass asserts single code footer) | ✓ |
| `app/tests/test_exploration_set_phase_delve_hint.py` | 6 (APP-022 regression) | ✓ |

## Out-of-scope file (documented)

| File | Change | Justification |
|------|--------|---------------|
| `app/tests/test_exploration_site_entry_gate.py` | `test_site_entry_gate_bypass_when_in_dungeon` — assert prose + single `[Location:` footer instead of exact equality | APP-077 changes player-visible shape; gate behavior unchanged. Added to ticket Expected files. |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec checklist + changelog — **APP-077 done** (exploration + orchestrator specs)
- [x] Spec ↔ code — no drift on footer contract, compose order, or prompt mandate
- [ ] `python tmp/backlog/claim_ticket.py release APP-077 --done` — **orchestrator** (QA drift: not run per convention)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec § APP-077 and orchestrator § APP-077 were drafted at PM stage; implementation matched before drift — only checklist/changelog/ticket close lagged.
- **Non-blocking:** No unit test for `log_exploration_drift` / `_log_exploration_drift_if_needed` (optional AC).
- **Non-blocking:** `_is_code_only_combat_narration` omits footer on prefix-only `[Mechanics failed — …]` returns — documented in qa-implementation-pass IMPL-NOTE-004; human playtest deferred to Stage 7.
- **APP-083:** Compose runs without verify gate on exploration/combat LLM paths — documented non-goal; strip+footer are defense-in-depth until Phase 2.
