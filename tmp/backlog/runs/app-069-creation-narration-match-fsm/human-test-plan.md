# Human Playtest Plan: APP-069-creation-narration-match-fsm

**backlog_ticket:** APP-069  
**Status:** done (verify fix in PyGame)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter API key in `app/.env` (live clerk flavor) **or** accept short stub flavor if mock path used elsewhere
- [ ] Fresh session: type `new game` (no resume from mid-creation unless TC-4)
- [ ] Optional second terminal: tail `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] UI: note **creation step badge** / stats panel phase if visible during desk flow

## Acceptance criteria map

| Ticket AC | Test case(s) |
|-----------|----------------|
| Gated steps: body only from code `format_*` / `_auto_present_*` — no free LLM tables/kits on SKILLS–EQUIPMENT_GOLD | TC-2, TC-3 |
| APP-057 golden path: step-appropriate table keywords each turn | TC-3 |
| No `Phase: PRE_DELVE` / “registered Delver” before WORLD_INTRO + roster (mid-FSM owned by APP-070) | TC-3 (spot-check); full gate → APP-070 plan |
| Rick / Undead: flavor must match committed `creation.race` | TC-1 |

## Test cases

### TC-1: Rick / Undead flavor matches committed race (AC — Phase 1 repro)

**Goal:** After committing **undead**, roll/class narration must not praise “Human lineage” (or other wrong-race flavor) while the code roll table and FSM show Undead.

**Session repro:** Rick @ 17:09 — `creation.race == "undead"` but flavor said Human.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch `python main.py` | Window opens; no traceback | [ ] |
| 2 | Type `new game` and submit | Clerk asks for delver name; footer `Awaiting: CHARACTER_CREATION` or name step | [ ] |
| 3 | Enter name `Rick` and submit | Race table appears (`Pick **one race**`); footer `Awaiting: RACE_INPUT` | [ ] |
| 4 | Enter `undead` (or `Undead`) and submit | Roll stats table (`Attr \| Base \| …`); chained class table; step advances toward CLASS | [ ] |
| 5 | Read narration on the roll/class turn | Short clerk flavor (≤2 sentences) references **Undead** or undead-appropriate tone — **not** “Human lineage”, “Human blood”, etc. | [ ] |
| 6 | Scan full narration body on that turn | Code-owned roll table present; **no** LLM-invented duplicate race table above it | [ ] |
| 7 | (Optional) JSONL: latest `creation_step` after race commit | `data.step` is `CLASS` (or `ROLL_STATS` if logged before chain); committed race is undead | [ ] |

**Failure signals:** “Human” (or another race) in flavor while you picked Undead; flavor contradicts racial adjustments shown in the roll table; stuck re-showing race table after valid `undead` input.

### TC-2: Wrong-step body blocked on apprentice caster path (AC — gated bodies)

**Goal:** Each desk step shows **only** the table for that step — no equipment kit on spell schools, no schools table on skills.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | `new game` → `Dumpy` → `human` → `apprentice` | Skills table: `Pick **3 skills**`, `\| Category \| Skill \|`, `Awaiting: SKILLS_INPUT` | [ ] |
| 2 | Submit `Lore, Spellcasting, Arcana` | Schools table: `\| School \| Tradition \|`, `Awaiting: SPELL_SCHOOLS_INPUT` — **not** equipment/`Registry kit` | [ ] |
| 3 | Submit `pyromancy, ether` | Spells table + `Pick **2 tier-1 spells**`, `Awaiting: SPELLS_INPUT` | [ ] |
| 4 | Submit `ember-touch, static-lash` | Equipment summary: `**Registry kit:**`, `**Starting gold:**`, `Reply **yes**`, `Awaiting: EQUIPMENT_GOLD_CONFIRMATION` | [ ] |
| 5 | On each of steps 1–4, confirm forbidden content absent | No `Pick **one race**` after NAME; no skill table on schools turn; no spell table on equipment turn | [ ] |

**Failure signals (historical APP-069):** At `SPELL_SCHOOLS`, prose lists wrong skills and shows equipment table; LLM quarterstaff/robe kit instead of code `format_equipment_summary`; skills input at `RACE` ignored with race table loop.

### TC-3: Golden path completion + keyword sanity (AC — APP-057 / Phase 2)

**Goal:** Full apprentice caster path completes with step-appropriate bodies and legitimate reception only at end.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Continue TC-2 through equipment: submit `yes` | `WORLD_INTRO` / reception copy; stats panel shows a character | [ ] |
| 2 | Final narration footer | `Awaiting: RECEPTION_CHOICE` and `Phase: preparation` **only after** roster populated | [ ] |
| 3 | Mid-creation spot-check (steps 1–4) | Narration does **not** contain `Phase: PRE_DELVE` or “registered Delver” (if seen, file under APP-070) | [ ] |
| 4 | (Optional) JSONL after finalize | `creation_finalize` or roster events; `roster_len` > 0 | [ ] |

**Failure signals:** Empty roster but reception copy; exploration phase badge before equipment confirm.

### TC-4: Wrong-step input does not advance FSM (regression, APP-011 adjacent)

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | At spell schools step, type `Yes` and submit | Error + schools table re-shown; still on spell schools | [ ] |
| 2 | At skills step, type `ready` and submit | Error + skills table re-shown | [ ] |

## Automated cross-check (optional before sign-off)

```bash
python -m pytest app/tests/test_creation_flow.py -q -k "roll_stats_flavor or full_creation"
```

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Related manual plans

- APP-070: premature PRE_DELVE / registered Delver — [../app-070-block-premature-pre-delve/human-test-plan.md](../app-070-block-premature-pre-delve/human-test-plan.md)
- APP-072: duplicate race tables — [../app-072-llm-truncation-race-tables/human-test-plan.md](../app-072-llm-truncation-race-tables/human-test-plan.md)
- Shared QA reflection: [reflection-qa-playtest.md](./reflection-qa-playtest.md)
