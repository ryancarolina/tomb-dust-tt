# Drift Check: APP-028-combat-failure-narration

**backlog_ticket:** APP-028  
**Date:** 2026-05-21  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-combat-play-spec.md`](../../../app-combat-play-spec.md) | was yes (checklist `[ ]`, test Pass column empty, no close changelog) | **Synced:** checklist **APP-028** `[x]`; T1–T11 Pass ✓; changelog **APP-028 done** (2026-05-21) |
| Run [`spec.md`](./spec.md) R1–R8 | no | Verified against `orchestrator.py`, `test_combat_failure_narration.py` |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | No registry/priority change required for APP-028 |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** Beat-trigger `_handle_combat_trigger` → canonical failure string; `combat.active = False` | `orchestrator.py` L2000–2014 | yes |
| **R1** Store failure on `_beat_combat_start_failure` after `process_beat` | L2171–2173 | yes |
| **R1** `_llm_loop` short-circuit before `all_failed` content branch | L2113–2117 | yes |
| **R1** No `run_combat_monster_turns()` on failed start | L2018 only on success; T1 | yes |
| **R2** Exploration `all_failed` — prefix only for combat tools | `_COMBAT_TOOL_NAMES` L84–91; branch L2127–2132 | yes |
| **R2** Per-tool `TOOL FAILED ({fn}): …` on partial failure | L2100–2106 | yes |
| **R3** Combat inner `all_failed` strip (no appended model content) | `_combat_llm_loop_inner` L1934–1948; T8–T9 | yes |
| **R4** Combat inner partial failure — system injection before tool result | L1925–1932; T10 | yes |
| **R5** Five exploration combat tools in failure table | T3–T7 parametrized | yes |
| **R6** State truth — `status.combat` null after beat failure | T2 | yes |
| **R8** Logging on beat short-circuit / all-failed strip | L2116, L2120, L1945; T11 (beat path) | yes |
| **`pending_start` path** | L1785–1792 (pre-existing; matches spec shape) | yes |
| Wrong tool in combat loop | L1913–1914 | yes |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Enforce failure narration for all combat tools | ✓ — exploration tools (T3–T7), beat-trigger (T1–T2), combat inner + wrong tool (T8–T10) |

## Tests run

```bash
cd app; python -m pytest tests/test_combat_failure_narration.py -q
```

**Result:** 11 passed (1.14s)

| ID | Test | Result |
|----|------|--------|
| T1 | `test_handle_combat_trigger_returns_failure_string` | ✓ |
| T2 | `test_beat_trigger_e2e_llm_loop_short_circuits` | ✓ |
| T3–T7 | `test_llm_loop_all_failed_strips_content[*]` | ✓ |
| T8 | `test_combat_inner_all_failed_strips_content` | ✓ |
| T9 | `test_combat_inner_wrong_tool_failure` | ✓ |
| T10 | `test_combat_inner_partial_failure_injects_tool_failed` | ✓ |
| T11 | `test_all_failed_or_beat_failure_logs` (optional; beat path only) | ✓ |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-21
- [ ] `python tmp/backlog/claim_ticket.py release APP-028 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes (non-blocking)

- **T11 partial:** Asserts beat short-circuit `log_error` only; exploration `all_failed` strip log not asserted (spec marks T11 optional).
- **Log message copy:** Exploration strip path logs `"returning content"` even when combat branch returns prefix-only — cosmetic; player text correct.
- **`all_failed` without pre-tool content:** Falls through to depth retry; tests cover content-present path (primary failure mode from logs).
- **Human playtest:** Stage 7 — attack-outside-combat, unknown monster, beat-trigger ghoul fiction deferred to `human-test-plan.md`.
