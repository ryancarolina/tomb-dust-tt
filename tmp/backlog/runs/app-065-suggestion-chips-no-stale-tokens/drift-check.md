# Drift Check: app-065-suggestion-chips-no-stale-tokens

**backlog_ticket:** APP-065  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) | was yes (checklist open; changelog draft-only) | **Synced:** § Suggestion chips matches code; checklist `[x]`; changelog **APP-065 done** row |
| Run [`spec.md`](./spec.md) R1–R6 | no | Verified against `suggestions.py`, `orchestrator.py`, `app.py`, `test_ui_suggestions.py` |
| Ticket [`app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md`](../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md) | no | All AC checked; status `done`; Closed 2026-05-20 |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **Always refresh** — empty list clears stale chips (success + exception) | `_process_turn` `finally` → `_queue_turn_suggestions`; always `put(("suggestions", …))` | yes |
| **Code-owned source** — no narration scrape | `_extract_suggestions` absent from `app/`; turn path calls `get_player_suggestions()` only | yes |
| **Lookup order** — active `creation.step` → `awaiting` → `[]`; inactive creation ignores step | `build_player_suggestions` L80–101; `get_player_suggestions` L107–121 | yes |
| **Equipment chips** — `Yes, confirm` / `I need different gear` | `PLAYER_SUGGESTIONS_BY_CREATION_STEP["EQUIPMENT_GOLD"]` | yes |
| **Startup** — `load game` / `new game` when save exists | SETUP branch L87–90; init seed `app.py` L141–146 | yes |
| **Blocklist** — `UPPER_SNAKE_CASE`, suffixes, engine enums, `CREATION_STATUS_LABELS` | `is_blocked_chip_token` + `filter_player_suggestions` | yes |
| **Click submits display label** | `input_box.py` L92–94 unchanged (label == submit) | yes |
| **Post-finalize** — no equipment chips from stale step | inactive guard L95–96; integration test post-finalize | yes |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Empty suggestions clear stale chips every turn | ✓ `_queue_turn_suggestions` unconditional; `test_queue_turn_suggestions_empty_list_always_put` |
| Never show raw internal tokens | ✓ blocklist + maps; `test_blocked_internal_tokens`, `test_builder_never_returns_blocked` |
| Player-facing actions only (curated map) | ✓ `app/ui/suggestions.py`; no narration parse |
| Equipment confirm phrases; startup preserved | ✓ map + `test_equipment_gold_active_chips`, `test_setup_has_save` / `test_setup_no_save` |
| Click submits display label, not token | ✓ `input_box.py` unchanged |
| Domain spec documents source + blocklist | ✓ § Suggestion chips L38–88; checklist + changelog closed |

## Run spec R1–R6 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** | Always clear stale chips (`[]`, success + exception) | **PASS** |
| **R2** | Code-owned source; no narration; post-finalize ignores stale step | **PASS** |
| **R3** | Equipment player phrases; objection via non-confirm | **PASS** |
| **R4** | Blocklist defense in depth | **PASS** |
| **R5** | Click never sends internal token | **PASS** |
| **R6** | Domain spec sync on close | **PASS** |

## Tests run

```bash
cd app; python -m pytest tests/test_ui_suggestions.py tests/test_creation_flow.py tests/test_session_resume_failure.py -q
```

**Result:** 28 passed (2.45s)

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_ui_suggestions.py` | 17 (builder, blocklist, queue, exception, post-finalize) | ✓ |
| `app/tests/test_creation_flow.py` | narration `Awaiting:` regression | ✓ |
| `app/tests/test_session_resume_failure.py` | footer `Awaiting:` regression | ✓ |

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| `_extract_suggestions` removed | `rg "_extract_suggestions" app/` — zero | ✓ |
| Turn path uses orchestrator only | `_queue_turn_suggestions` → `get_player_suggestions()` | ✓ |
| `get_player_suggestions` does not read narration | `orchestrator.py` L107–121: creation + bridge status + has_save | ✓ |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec checklist + changelog — **APP-065 done**
- [x] Spec ↔ code — no drift on chip source, blocklist, or always-clear rule
- [ ] `python tmp/backlog/claim_ticket.py release APP-065 --done` — **orchestrator** (QA drift: not run per convention)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec § Suggestion chips was drafted at PM stage (r2); implementation matched before drift — only checklist/changelog/ticket close lagged.
- **Batch bleed:** `orchestrator.py` working tree may include APP-073/075 hunks; APP-065 `get_player_suggestions()` is isolated and correct.
- **Non-blocking:** No dedicated `COMBAT_TURN` blocklist unit assert (covered by `_BLOCKED_ENUMS`); human Bumpy repro deferred to Stage 7 `human-test-plan.md`.
- **`app-master-spec.md`:** No registry gap; priority table unchanged (UI behavior stays under `app-pygame-ui-spec.md`).
