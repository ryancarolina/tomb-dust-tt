# Human Playtest Plan: APP-067-code-owned-roll-stats-table

**backlog_ticket:** APP-067
**Commit:** `pending` (Stage 7 commit not yet on branch; use working tree with APP-067 impl)
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter / LLM API configured (full creation narration)
- [ ] Fresh session: type `new game` at prompt (empty roster)
- [ ] Optional second terminal: tail `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] Know the bug this fixes: pre-APP-067, GM could narrate STR **Final 7** when `roll_attributes` returned `final_attributes.STR: 6` (see ticket evidence in `session-2026-05-20.jsonl`)

## How to cross-check (all table TCs)

After picking a race, find the latest JSONL line with `"type": "tool_call"` and `"name": "roll_attributes"`. Use `data.result` as ground truth:

| Narration column | JSON path |
|------------------|-----------|
| Life event intro | `result.life_event.name` |
| Base | `result.base_rolls[attr]` |
| Genetic | `result.genetic_factors[attr].mod` |
| Life Evt | `result.life_event.mods[attr]` (0 if missing) |
| Racial | `result.racial_adjustments[attr]` (0 if missing) |
| **Final** | `result.final_attributes[attr]` — **authoritative** (may differ from column sum if clamped) |
| LUC Final | `result.final_attributes.LUC` |
| HP | `10 + result.final_attributes.STA * 5` |

Narration appears in the GM panel and in `gm_narration` JSONL lines for the same turn.

---

## Test cases

### TC-1: Attribute table matches engine payload (maps to AC #1, spec R1)

**Goal:** Code-owned table cells mirror `roll_attributes` tool output — no LLM-invented STR (or any attr) math.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch app (`python main.py`) | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM asks for delver name | [ ] |
| 3 | Enter a name (e.g. `Bumpy`) and submit | GM shows race table | [ ] |
| 4 | Pick a race (e.g. `human`) and submit | Single GM response includes attribute breakdown table | [ ] |
| 5 | Open JSONL; locate `roll_attributes` for this turn | `result.ok` is true; payload has `base_rolls`, `genetic_factors`, `life_event`, `racial_adjustments`, `final_attributes` | [ ] |
| 6 | Compare **every STR–SPI row** in narration to payload | Base, Genetic, Life Evt, Racial, and **Final** match JSON paths above for each attribute | [ ] |
| 7 | Spot-check **Final** vs column sum | If columns don't sum to Final (clamp case), narration still shows engine **Final** — not a recomputed sum | [ ] |

**Failure signals:** Final column off by one (classic bug: STR 6 in tool, 7 in table); wrong racial or genetic column; missing life event name line; table absent and LLM prose substitutes stat math.

---

### TC-2: LUC row and HP line (maps to AC #3, spec R1/R2)

**Goal:** LUC row uses dashes for breakdown columns; HP formula matches STA from table.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From TC-1 race-pick response | Table includes `\| LUC \| — \| — \| — \| — \| {n} \|` where `{n}` = `final_attributes.LUC` in tool log | [ ] |
| 2 | Read HP line below attribute table | Line matches `**HP:** {hp} (10 + STA {sta} × 5)` where `sta` = **Final** STA in table and `hp` = `10 + sta × 5` | [ ] |
| 3 | Cross-check HP to JSONL | Narrated `{hp}` equals `10 + result.final_attributes.STA * 5` | [ ] |

**Failure signals:** LUC shows Base/Genetic breakdown; HP uses wrong STA or wrong arithmetic; HP missing entirely.

---

### TC-3: Class table once + CLASS footer (maps to AC #2, spec R2/R3)

**Goal:** Roll turn presents stats + class tables in one narration; chain does not duplicate class table.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | After race pick (same response as TC-1/2) | Narration contains stats table **then** class table (`\| Class \| Requirement \| …`) in **one** GM message | [ ] |
| 2 | Count class prompt header | Exactly **one** occurrence of `Pick **one tier-1 class**` in that response | [ ] |
| 3 | Check status footer | Footer shows `Awaiting: CLASS_INPUT` (or UI creation badge at CLASS step) | [ ] |
| 4 | Scroll narration — no duplicate class block | No second full class table appended after a pause/second bubble on the same turn | [ ] |
| 5 | Confirm no stale roll path artifact | Response does **not** include `**Final attributes:**` one-liner above a second class table (that path is direct-CLASS only) | [ ] |

**Failure signals:** Two class tables in one turn; class table missing; footer still `STATS_REVIEW` or race prompt; duplicate `Pick **one tier-1 class**` lines.

---

### TC-4: Thin flavor only — no LLM stat table (maps to AC #2, spec R2)

**Goal:** GM flavor text may vary; attribute numbers come only from code formatter.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Read prose above the attribute table on roll turn | Brief flavor/color text only — no inline stat breakdown invented by LLM | [ ] |
| 2 | Compare table header | Exact header row: `\| Attr \| Base \| Genetic \| Life Evt \| Racial \| Final \|` | [ ] |
| 3 | Optional: run a second new game with different race | Table still matches that turn's `roll_attributes` payload (not memorized from TC-1) | [ ] |

**Failure signals:** LLM narrates a different table shape; numbers in prose disagree with table; missing markdown table entirely.

---

### TC-5: Resume at CLASS — no duplicate stats block (spec human hint, R3 regression)

**Goal:** Direct CLASS path re-shows class table without repeating full stats table.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Complete TC-1 through class-pick turn; **do not** pick a class yet | At CLASS step with stats already shown | [ ] |
| 2 | Save/exit app (`save` if available) or note session; relaunch and **Continue** (or reload save) | Creation resumes at CLASS | [ ] |
| 3 | Inspect GM narration on resume | Class table may reappear (`**Final attributes:**` one-liner + class table is OK) | [ ] |
| 4 | Confirm no duplicate stats table | Full `\| Attr \| Base \| Genetic \| …` block does **not** appear twice in resume flow | [ ] |

**Failure signals:** Second full attribute breakdown on resume; two class tables on resume turn.

---

## AC mapping (ticket)

| Ticket acceptance criterion | Covered by |
|-----------------------------|------------|
| Attribute table in `creation.py` from `roll_attributes` payload only | TC-1, TC-4 |
| `_auto_roll_stats()` thin flavor + code tables — no `_narrate_only` stat math | TC-1, TC-3, TC-4 |
| Narrated HP matches `10 + STA×5` from engine attrs | TC-2 |
| Test asserts table cells match `roll_result` (automated) | Covered by pytest; human confirms live parity in TC-1–2 |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- APP-068/069 may change NAME→RACE presentation; this plan stops at ROLL_STATS→CLASS.
- If TC-1 fails only on **Final** when clamp applies, file follow-up — display must use `final_attributes`, not column sum (domain spec § clamp vs Final).
- pytest gate: `cd app && python -m pytest tests/test_creation_flow.py -q` (should pass before playtest).
