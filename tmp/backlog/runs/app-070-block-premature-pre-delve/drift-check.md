# Drift Check: APP-070-block-premature-pre-delve

**backlog_ticket:** APP-070  
**Date:** 2026-05-20  
**Verdict:** PASS (after spec remediation)

## Specs compared

| Spec | Drift at review? | Action |
|------|------------------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | **yes → fixed** | PM round claimed § APP-070 but section was absent on disk; QA drift added § **Block premature completion copy (APP-070)** + changelog **APP-070 done** row |
| Run [`spec.md`](./spec.md) / [`plan.md`](./plan.md) | no | C1–C5, D1–D2, T1 match `creation.py`, `orchestrator.py`, `test_creation_flow.py` |
| [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) | minor | `premature_completion_copy` reason shipped in code; logging spec table not updated (non-blocking; D2 optional telemetry) |

## Code ↔ domain spec (APP-070)

| Requirement | Code location | Match |
|-------------|---------------|-------|
| **C1** Sanitizer when `active` or `roster_len == 0` | `orchestrator.py` `_compose_creation_narration` L562–572; `creation.py` `sanitize_premature_completion_flavor` L581–596 | yes |
| **C2** Flavor only; body/footer untouched | Sanitizer runs on `cleaned` flavor before `parts.append`; `_auto_finalize` `footer=` path unchanged | yes |
| **C3** Blank on PRE_DELVE, RECEPTION_CHOICE, registered-delver phrases | `_PREMATURE_FLAVOR_MARKERS` L571–577 | yes |
| **C4** `Phase: preparation` in flavor when active and not `WORLD_INTRO` | `_PREMATURE_PREPARATION_PHASE_RE` L578, L594–595 | yes |
| **C5** Re-run `strip_llm_status_tags` after mutation | L569–570 | yes |
| **D1a** `pre_delve` / `pre-delve` when empty roster | `orchestrator.py` L234–235 | yes |
| **D1b** `RECEPTION_CHOICE` while `creation.active` | L236–237 | yes |
| **D1c** `preparation` while active and `step != WORLD_INTRO` | L238–243 | yes |
| **D2** `premature_completion_copy` | L218–219, `_PREMATURE_COMPLETION_COPY_RE` L71–74 | yes |
| **T1** `test_skills_turn_rejects_premature_completion_flavor` | `test_creation_flow.py` L127–162 | yes |

**Compose order note:** Domain spec documents actual pipeline (APP-072 race dedup → APP-069 flavor → APP-070 completion strip); matches implementation.

**APP-009 cross-link:** `_auto_finalize` roster gate not modified; golden path turn 8 still asserts `RECEPTION_CHOICE` + `Phase: preparation` with non-empty roster and `PRE_DELVE not in last`.

## Ticket AC ↔ code

| # | Acceptance criterion | Result |
|---|----------------------|--------|
| 1 | No `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” in player narration until finalize + non-empty roster | **PASS** |
| 2 | `_check_creation_drift` flags `premature_exploration_phase` for PRE_DELVE / preparation reception when `roster_len == 0` | **PASS** |
| 3 | Regression test: mock bad LLM at SKILLS; FSM/roster/UI unchanged | **PASS** |

## Tests run

```bash
cd app && python -m pytest tests/test_creation_flow.py -q
cd app && python -m pytest tests/test_creation_flow.py::test_skills_turn_rejects_premature_completion_flavor -q
```

**Result:** 5 passed (1.28s); T1 isolated 1 passed (0.62s)

## Prior QA impl round

Stage 5 reported **FAIL** (T1 missing). Dev r2 added `test_skills_turn_rejects_premature_completion_flavor`; drift round confirms suite green and spec section restored.

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in [`app-070-block-premature-pre-delve-narration.md`](../../app-070-block-premature-pre-delve-narration.md)
- [x] Domain spec § APP-070 + changelog **APP-070 done** (2026-05-20)
- [x] Ticket **Status** → `done` / **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-070 --done` — orchestrator (clears `tmp/.active-ticket.json`)

## Ancillary notes (non-blocking)

- `roster_len` passed into `sanitize_premature_completion_flavor` but unused inside helper (gate is caller-only).
- If compose strips all leak markers, drift may not fire on narrated phase/awaiting — acceptable per plan; T1 locks player-visible behavior.
- Human PyGame playtest (Dumpy repro) deferred to Stage 7 per run `spec.md`.
