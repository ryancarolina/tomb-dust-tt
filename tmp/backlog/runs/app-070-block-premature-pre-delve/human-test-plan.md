# Human Playtest Plan: APP-070-block-premature-pre-delve

**backlog_ticket:** APP-070  
**Status:** done (verify fix in PyGame)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter API key in `app/.env` for live LLM flavor (sanitizer must handle bad completion copy)
- [ ] Fresh session: `new game` (empty roster)
- [ ] Tail `app/logs/session-YYYY-MM-DD.jsonl` in a second terminal (recommended)
- [ ] Stats panel / phase badge visible to confirm roster still empty mid-creation

## Acceptance criteria map

| Ticket AC | Test case(s) |
|-----------|----------------|
| No `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” until `_auto_finalize()` + non-empty roster | TC-1, TC-2, TC-4 |
| `_check_creation_drift` flags `premature_exploration_phase` when empty roster + false exploration copy | TC-1 (optional JSONL) |
| Skills-turn regression: bad LLM completion prose must not change step or show false completion in UI | TC-1 |

## Test cases

### TC-1: Dumpy / skills — no premature completion (AC — primary repro)

**Goal:** After skills input (and early “yes” if tried), narration must **not** claim registration or `PRE_DELVE` while roster is still empty.

**Session repro:** Dumpy @ 14:09–14:10 — skills chosen → “registered Delver”, `PRE_DELVE`, `RECEPTION_CHOICE`; no `character_create`; `roster_len` 0.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Launch `python main.py` | Window opens | [ ] |
| 2 | `new game` → name `Dumpy` → `human` → `apprentice` | On skills step: skills table + `Awaiting: SKILLS_INPUT` | [ ] |
| 3 | Submit skills: `Lore, Spellcasting, Arcana` (or historical `medicine, spellcasting, endurance`) | Advances to **spell schools** — schools table shown | [ ] |
| 4 | Read narration immediately after skills commit | **No** “registered Delver”, “You are now a registered”, `Phase: PRE_DELVE`, or `Awaiting: RECEPTION_CHOICE` | [ ] |
| 5 | Check stats panel / roster | Still **no** delver on roster; creation still active | [ ] |
| 6 | (Optional) JSONL after step 3–4 | If bad copy ever appears, `creation_drift` with `premature_exploration_phase` and `roster_len: 0` | [ ] |

**Failure signals:** Equipment confirm or reception copy right after skills; exploration/delve phase badge with empty roster; player told they may travel before equipment `yes`.

### TC-2: False `yes` at spell schools (AC — guard + no reception)

**Goal:** Premature affirmative must not skip to reception or finalize.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Reach `SPELL_SCHOOLS` (after TC-1 step 3) | Schools table visible | [ ] |
| 2 | Type `yes` and submit | Error or re-prompt; schools table **re-shown**; step still spell schools | [ ] |
| 3 | Narration after false `yes` | Still **no** registered Delver / `PRE_DELVE` / `RECEPTION_CHOICE` | [ ] |

**Failure signals:** Jump to world intro or reception; roster populated without equipment confirm.

### TC-3: Mid-FSM `Phase: preparation` only after finalize (AC — C2 guard)

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Complete schools → spells → equipment through `yes` | Character on roster; reception / world intro | [ ] |
| 2 | Final narration | `Awaiting: RECEPTION_CHOICE` and `Phase: preparation` **allowed** here | [ ] |
| 3 | Compare to TC-1 step 4 | Same footer strings must **not** have appeared before step 1 of this TC | [ ] |

**Failure signals:** `Phase: preparation` during SKILLS/SPELL_SCHOOLS/SPELLS/EQUIPMENT_GOLD with empty roster.

### TC-4: APP-069 overlap spot-check (skills body, not completion)

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | On skills step before commit | Body is skills table only — not equipment kit | [ ] |
| 2 | After skills commit | Body is schools table — not “registered Delver” block | [ ] |

## Automated cross-check (optional before sign-off)

```bash
python -m pytest app/tests/test_creation_flow.py -q -k "premature_completion or skills_turn"
```

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Related manual plans

- APP-069: FSM/body alignment — [../app-069-creation-narration-match-fsm/human-test-plan.md](../app-069-creation-narration-match-fsm/human-test-plan.md)
- APP-072: race table dedup — [../app-072-llm-truncation-race-tables/human-test-plan.md](../app-072-llm-truncation-race-tables/human-test-plan.md)
- Shared QA reflection: [../app-069-creation-narration-match-fsm/reflection-qa-playtest.md](../app-069-creation-narration-match-fsm/reflection-qa-playtest.md)
