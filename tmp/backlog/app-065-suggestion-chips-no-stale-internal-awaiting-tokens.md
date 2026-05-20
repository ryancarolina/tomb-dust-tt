# APP-065: Suggestion chips — no stale or internal awaiting tokens



| Field | Value |

|-------|-------|

| **ID** | APP-065 |

| **Type** | bug |

| **Priority** | P1 |

| **Status** | done |

| **Closed** | 2026-05-20 |

| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |

| **Created** | 2026-05-20 |



## Summary



Input **suggestion chips** are built by parsing the GM narration footer (`Awaiting: …`). That exposes **internal FSM labels** (e.g. `EQUIPMENT_CONFIRMATION`, `PLAYER_ACTIONS`, `NAME_INPUT`) as clickable actions. When a later narration line **omits** `Awaiting:`, chips are **not cleared** — stale tokens remain and get submitted as player input.



**Repro (Bumpy, session 2026-05-20):** GM ends creation with `Awaiting: EQUIPMENT_CONFIRMATION` → chip appears → player confirms with “I am ready” → post-finalize narration has no `Awaiting:` → chip stays → click sends `EQUIPMENT_CONFIRMATION` → GM rejects as invalid.



## Acceptance criteria



- [x] When `_extract_suggestions` returns empty, call `set_suggestions([])` so **stale chips are cleared** every turn.

- [x] Suggestion chips **never** show raw internal tokens: `*_INPUT`, `*_CONFIRMATION`, `PLAYER_ACTIONS`, `RECEPTION_CHOICE`, engine `awaiting` enums (`CHARACTER_CREATION`, `COMBAT_TURN`, `SETUP`, etc.), or other `UPPER_SNAKE_CASE` step labels parsed from narration.

- [x] Chips are **player-facing actions only** — sourced from a curated map and/or engine `suggest.prompts` / orchestrator, not blind parse of GM status footer.

- [x] Creation step examples: equipment confirm → `Yes, confirm` / `I need different gear` (not `EQUIPMENT_CONFIRMATION`); startup remains `load game` / `new game`.

- [x] Clicking a chip submits the **display label** (or mapped player text), never an internal token.

- [x] Domain spec documents chip source-of-truth and blocklist rules.



## Expected files



- `app/ui/app.py` — turn-loop suggestion refresh; remove narration scrape

- `app/ui/suggestions.py` — player chip maps, blocklist, `build_player_suggestions()`

- `app/ui/panels/input_box.py` — if chip display vs submit text diverges (unlikely v1)

- `app/gm/orchestrator.py` — `get_player_suggestions()`

- `app/tests/test_ui_suggestions.py` — unit tests for builder, blocklist, lookup order

- `tmp/app-pygame-ui-spec.md`



## Spec sync (required on close)



1. Mark **Status** → `done` in this ticket (add **Closed** date).

2. Update the domain spec checklist / changelog in [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md).

3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.



## Notes



- Root cause in `app/ui/app.py`: only updates suggestions when parse is non-empty; `_extract_suggestions` treats any `Awaiting:` value as chip text.

- Engine already builds human prompts in `play/tomb_gm/suggest.py` (`prompts` list) for LLM context — UI should reuse or mirror that, not scrape narration footers.

- **Related:** [APP-007](app-007-code-owned-creation-status-line.md) (canonical status line), [APP-036](app-036-creation-step-badge-in-ui.md) (creation step display from engine).



## Dependencies



| Ticket | Relationship |

|--------|--------------|

| APP-007 | related — align awaiting vocabulary |

| APP-036 | related — engine-owned creation UI state |



## Claim / release



```bash

python tmp/backlog/claim_ticket.py APP-065 --task suggestion-chips

python tmp/backlog/claim_ticket.py release APP-065 --done

```


