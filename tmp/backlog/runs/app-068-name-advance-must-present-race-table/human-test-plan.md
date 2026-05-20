# Human Playtest Plan: APP-068-name-advance-must-present-race-table

**backlog_ticket:** APP-068  
**Commit:** `e9326f1` (verify after Stage 7 commit if different)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)  
**Spec:** [spec.md](./spec.md) · **Ticket:** [app-068-name-advance-must-present-race-table.md](../../app-068-name-advance-must-present-race-table.md)

## Prerequisites

- [ ] OpenRouter API key configured in app config (live LLM flavor on NAME→RACE is expected; offline/mock may skip `llm_request` but code table must still appear)
- [ ] Fresh session: start with **`new game`** (not Continue) so creation is at NAME
- [ ] Log path (optional but recommended): `app/logs/session-YYYY-MM-DD.jsonl` (today’s date)
- [ ] Narration panel visible; scroll if needed — race table is multi-line markdown

## AC / requirement map

| ID | Source | What human play proves |
|----|--------|-------------------------|
| **AC-1** | Ticket | After valid NAME, **same turn** shows code race table + footer (`_auto_present_race`) |
| **AC-2** | Ticket / R2 | At RACE with race unset, narration is **not** bare `"The clerk waits."` |
| **AC-3** | Ticket / R3 | Pytest covers integration; human confirms UI matches (table header + `Awaiting: RACE_INPUT`) |
| **R1** | spec.md | Intro `Pick **one race**`, header `\| Race \| Adjustments \| Description \|`, footer `Awaiting: RACE_INPUT` |
| **R2** | spec.md | No clerk-waits fallthrough when step is RACE |

---

## Test cases

### TC-1: Valid name → race table same turn (maps to AC-1, R1)

**Goal:** Successful NAME commit presents the full code race table and RACE footer on the **same** GM response — not on a later turn.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch: `cd app && python main.py` | Window opens; no traceback | [ ] |
| 2 | Type `new game` and submit | GM prompts for delver name (creation at NAME) | [ ] |
| 3 | Enter a valid name (≥2 chars), e.g. `Caddy`, and submit **once** | **Single** new narration block appears (do not submit again yet) | [ ] |
| 4 | Read that narration body | Contains intro **`Pick **one race**`** (or equivalent “pick one race” prompt from code table) | [ ] |
| 5 | Same narration block | Contains markdown table header **`| Race | Adjustments | Description |`** (pipe characters visible) | [ ] |
| 6 | Same narration block (footer / status strip) | Contains **`Awaiting: RACE_INPUT`** | [ ] |
| 7 | UI suggestion chips / input hint (if shown) | Prompts for race choice, not “enter name again” | [ ] |

**Expected (pass):** One turn after name submit → clerk flavor (optional) + full race markdown table + `Awaiting: RACE_INPUT`.

**Failure signals:**

- Only **`The clerk waits.`** (or similarly empty one-liner) with **no** race table on that turn
- Table or `Awaiting: RACE_INPUT` appears only after **second** submit of the same name
- `creation_advanced` logged NAME→RACE but UI shows no table (matches pre-fix session bug)
- Crash or hang after name submit

---

### TC-2: No bare clerk-waits at RACE (maps to AC-2, R2)

**Goal:** Regression guard for the exact failure mode from ticket evidence (`session-2026-05-20.jsonl`).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Complete TC-1 steps 1–3 with name `Dumpy` (or repeat TC-1 with another valid name) | Same-turn response received | [ ] |
| 2 | Compare full narration text to failure string | Narration stripped is **not** exactly `The clerk waits.` | [ ] |
| 3 | Confirm step context | Player can pick a race from the table without re-entering the name | [ ] |

**Expected (pass):** Narration is substantive (table + footer); clerk line alone never substitutes for RACE presentation.

**Failure signals:**

- Exact narration `The clerk waits.` after valid NAME
- Log shows `creation_advanced` `NAME`→`RACE` but `gm_narration` is only clerk-waits with no `| Race |` in payload
- Player must type the name again to see the race table

---

### TC-3: Invalid name, then valid name (maps to R1 edge)

**Goal:** NAME validation does not break same-turn race presentation on the **first** successful NAME commit.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | `new game` → submit name `A` (too short) | Rejection / re-prompt at NAME; **no** race table yet | [ ] |
| 2 | Submit valid name `Caddy` once | Same-turn race table per TC-1 (intro, header, `Awaiting: RACE_INPUT`) | [ ] |
| 3 | Narration check | Still **not** bare `The clerk waits.` | [ ] |

**Failure signals:** Valid name after invalid attempt shows clerk-waits only; table missing; stuck at NAME with no clear error.

---

### TC-4: Optional — session JSONL ordering (maps to spec § Test plan manual)

**Goal:** Log sequence matches fixed orchestrator path (NAME → `_auto_present_race` → flavor + table).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Run TC-1 in a fresh session | Note timestamp of name submit | [ ] |
| 2 | Open `app/logs/session-<today>.jsonl` | Find lines for that turn | [ ] |
| 3 | Order after player input | `creation_advanced` with `completed_step`/`advanced_to` indicating **NAME → RACE** | [ ] |
| 4 | Before `gm_narration` for that turn | Optional `llm_request` (thin flavor); **not required** for pass if table is present in UI | [ ] |
| 5 | `gm_narration` line for that turn | Text includes `\| Race \|` and `Awaiting: RACE_INPUT`; not clerk-waits only | [ ] |

**Failure signals:** `creation_advanced` NAME→RACE followed immediately by `gm_narration` = `The clerk waits.` with no `llm_request` and no table text in log.

---

### TC-5: Smoke — continue creation after race table (regression guard)

**Goal:** APP-068 fix does not block normal RACE → CLASS flow.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | After TC-1, pick a race from table (e.g. `human`) and submit | GM advances (stats/class path per build); no duplicate race-only table unless re-prompted | [ ] |
| 2 | No spurious loop | Game does not ask for `Caddy` / name again at RACE | [ ] |

**Failure signals:** Stuck re-asking for name at RACE; duplicate race tables every turn without a choice.

---

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- Duplicate race table on **recovery** re-prompt (name re-entered at RACE) is out of scope per spec non-goals; file follow-up if confusing in play.
- APP-066: engine `awaiting` vs footer `Awaiting: RACE_INPUT` label drift is separate; this plan only checks footer string in narration.
- APP-059: column/catalog layout of `format_races_table()` is not under APP-068 — only presence of header and RACE_INPUT footer.
- If TC-1 fails intermittently, capture `app/logs/session-*.jsonl` snippet and note whether failure is first launch vs resumed save.
