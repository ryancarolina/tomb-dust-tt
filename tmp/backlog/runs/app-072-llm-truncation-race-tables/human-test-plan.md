# Human Playtest Plan: APP-072-llm-truncation-race-tables

**backlog_ticket:** APP-072  
**Status:** done (verify fix in PyGame)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter API key in `app/.env` (live model may hit `finish_reason: length` on RACE flavor)
- [ ] Fresh session: `new game`
- [ ] Scroll narration panel fully — duplicate tables often appear as stacked blocks
- [ ] Optional: tail `app/logs/session-YYYY-MM-DD.jsonl` for `llm_response` with `finish_reason: length` on RACE turn

## Acceptance criteria map

| Ticket AC | Test case(s) |
|-----------|----------------|
| RACE body is **only** `format_races_table()` | TC-1, TC-2 |
| Flavor ≤2 sentences, **no** markdown tables in flavor | TC-1 |
| Strip `\| Race \|` from flavor; no duplicate tables in one `gm_narration` | TC-1, TC-3 |
| Invalid race re-prompt still single table | TC-2 |

## Test cases

### TC-1: NAME → RACE — single race table (AC — Caddy / duplicate repro)

**Goal:** One turn at RACE shows exactly **one** code race table; clerk flavor above is short prose without a second `\| Race \|` block.

**Session repro:** Caddy @ 16:44:41 — truncated LLM race table **plus** full `format_races_table()` in same narration.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Launch `python main.py` | Window opens | [ ] |
| 2 | `new game` → submit delver name `Dumpy` (or `Caddy`) | Same turn or next: race step active | [ ] |
| 3 | Count race table headers in narration | Exactly **one** block starting with `\| Race \| Adjustments \|` (Description column may still appear per APP-059) | [ ] |
| 4 | Read text **above** the table | 1–2 sentences of clerk flavor — **no** markdown table rows (`\| Human \|`, cut-off rows, etc.) | [ ] |
| 5 | Confirm intro line | `Pick **one race**` present once | [ ] |
| 6 | Footer | `Awaiting: RACE_INPUT` | [ ] |
| 7 | (Optional) JSONL on RACE turn | If `finish_reason: length`, player narration still has only one `\| Race \| Adjustments \|` header | [ ] |

**Failure signals:** Two stacked race tables; truncated table ending mid-row (e.g. cut-off Human row) followed by a full table; ~10k-char LLM-only table with **no** code `Pick **one race**` intro (opposite historical failure).

### TC-2: Invalid race pick — re-prompt still one table (AC)

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | At RACE, submit invalid token e.g. `dragon` or `xyz` | Error message; race table re-shown | [ ] |
| 2 | Count `\| Race \| Adjustments \|` in that turn’s narration | Still exactly **1** | [ ] |
| 3 | Submit valid race e.g. `human` | Advances to roll/class; no extra race table on class turn | [ ] |

**Failure signals:** Duplicate headers on error turn; valid pick shows second race table chained incorrectly.

### TC-3: Contrast with APP-069 Undead path (no duplicate on roll turn)

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | `new game` → `Rick` → `undead` | Roll/class turn shows roll table — **not** a second race table in flavor or body | [ ] |

**Failure signals:** Race table reappears on roll stats turn (flavor regen bug).

### TC-4: Full desk smoke (no race-table bleed)

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | After valid race, complete `human` → `apprentice` through skills | Later steps show skills/schools tables — no stray `\| Race \| Adjustments \|` | [ ] |

## Automated cross-check (optional before sign-off)

```bash
python -m pytest app/tests/test_creation_tables.py -q
python -m pytest app/tests/test_creation_flow.py -q
```

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Related manual plans

- APP-069: flavor/race commit alignment — [../app-069-creation-narration-match-fsm/human-test-plan.md](../app-069-creation-narration-match-fsm/human-test-plan.md)
- APP-070: premature completion copy — [../app-070-block-premature-pre-delve/human-test-plan.md](../app-070-block-premature-pre-delve/human-test-plan.md)
- Shared QA reflection: [../app-069-creation-narration-match-fsm/reflection-qa-playtest.md](../app-069-creation-narration-match-fsm/reflection-qa-playtest.md)
