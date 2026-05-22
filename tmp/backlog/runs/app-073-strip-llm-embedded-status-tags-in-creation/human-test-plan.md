# Human Playtest Plan: APP-073-strip-llm-embedded-status-tags-in-creation

**backlog_ticket:** APP-073  
**Commit:** pending (Stage 7 — use latest commit with APP-073 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-073 hardens flavor sanitizers so LLM prose cannot leak status tags or duplicate mechanical tables into creation narration. Automated pytest passed at impl QA (`test_creation_flavor_sanitize.py`); manual play confirms live LLM behavior — especially the **Undead roll** regression from `session-2026-05-20.jsonl` (Spluffy/Tuffy: LLM invented `### Your Attributes` with wrong STR/STA above the code table).

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (do not Continue from a mid-creation save)
- [ ] Optional log watch: second terminal tail `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] Know the bug this fixes:
  - **Duplicate stat tables:** LLM flavor embeds `### Your Attributes` or compact `| STR | AGI | … |` with **wrong numbers**, then code appends authoritative `| Attr | Base | … |` table.
  - **Duplicate Awaiting:** Inline wrong labels (`Awaiting: SKILL_INPUT`, `MAGIC_SCHOOLS_INPUT`, `EQUIPMENT_CONFIRMATION`) appear **above** the code footer; `parse_narration_status_line()` picks the first match → drift / stale chips.

## How to inspect narration (all TCs)

**Flavor region** = everything **before** the first code-owned table header `| Attr | Base |` (or, on non-roll steps, everything before the step's code table header, e.g. `| Category | Skill |`).

**Footer** = last line of composed narration from `format_creation_status()`.

| Check | Pass when |
|-------|-----------|
| Single stat table | Exactly **one** `\| Attr \| Base \|` header block in full narration |
| No LLM stat leak in flavor | Flavor region has **no** `### Your Attributes`, **no** `\| Attr \| Base \|`, **no** compact `\| STR \| AGI \| STA \|`, **no** `` `roll_attributes( `` fragment |
| Single Awaiting | Full narration contains exactly **one** `Awaiting:` line; it is the **footer** and matches `CREATION_STATUS_LABELS` for the current step |
| Wrong labels absent | Flavor region has **no** `SKILL_INPUT`, `MAGIC_SCHOOLS_INPUT`, `EQUIPMENT_CONFIRMATION`, bracket `[Location:…]`, or `[Phase:…]` blocks |

**Cross-check (Undead roll):** After race pick, find JSONL `tool_call` with `"name": "roll_attributes"`. **Final** column in narration must match `data.result.final_attributes` — not any numbers the LLM might have invented in flavor (pre-APP-073 bug).

---

## Test cases

### TC-1: Automated regression gate (recommended before manual play)

**Goal:** Confirm APP-073 unit + integration tests green before live LLM play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_creation_flavor_sanitize.py -q` | Exit code **0**; 4 passed | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_creation_tables.py app/tests/test_creation_flow.py -q` | Exit code **0**; no regressions | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Undead roll — single authoritative stat table (maps to ticket AC, spec S7)

**Goal:** Replay ticket evidence path — pick **undead** after name; narration shows **one** attribute breakdown from code, not LLM duplicate with wrong numbers.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM asks for delver name; creation active | [ ] |
| 3 | Enter name **`Spluffy`** (ticket repro name) and submit | Race table appears; footer `Awaiting: RACE_INPUT` | [ ] |
| 4 | Type **`undead`** and submit | Single GM response includes stats roll + class table chain | [ ] |
| 5 | Count `\| Attr \| Base \|` header blocks in full narration | Exactly **one** | [ ] |
| 6 | Scan **flavor region** (prose above first `\| Attr \| Base \|`) | **No** `### Your Attributes`; **no** second stat table; **no** compact `\| STR \| AGI \| STA \|` row; **no** `` `roll_attributes( `` fragment | [ ] |
| 7 | Thin clerk flavor allowed | 0–3 sentences of banter above table is OK — must not include stat numbers or markdown tables | [ ] |
| 8 | Open JSONL; locate `roll_attributes` for this turn | `data.result.final_attributes` present | [ ] |
| 9 | Compare **Final** column (STR–SPI + LUC) to JSON payload | Every Final cell matches `final_attributes` — LLM-invented values (e.g. STR 14 in flavor) must **not** appear anywhere in flavor region | [ ] |
| 10 | Same response includes class table | `\| Class \| Requirement \|` (or current formatter header) present **after** stats table | [ ] |
| 11 | Read footer | **`Awaiting: CLASS_INPUT`** (step advanced past ROLL_STATS) | [ ] |

**Failure signals:** Two attribute tables; `### Your Attributes` visible; flavor shows different STR/STA than code table Final column; missing stats or class table; crash on undead submit; footer still `RACE_INPUT` or `STATS_REVIEW`.

**Optional repeat:** Run TC-2 steps 1–11 again with name **`Tuffy`** and race **`undead`** — second ticket evidence path; same pass criteria.

---

### TC-3: Single Awaiting tag — no duplicate status in flavor (maps to ticket AC S1, spec S1)

**Goal:** Full narration has exactly one canonical `Awaiting:` from code footer; flavor never carries inline or bracket status tags.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From TC-2 undead roll response | Count `Awaiting:` in full narration | Exactly **one** |
| 2 | Confirm footer label | Matches current step — after roll turn: `Awaiting: CLASS_INPUT` | [ ] |
| 3 | Scan flavor region on roll turn | **No** `Awaiting:` substring; **no** `[Location:…]`; **no** `[Phase:…]` | [ ] |
| 4 | On name step (before TC-2 step 3 if re-running) | Footer `Awaiting: NAME_INPUT`; flavor region has no second status line | [ ] |
| 5 | On race step (after name, before undead) | Footer `Awaiting: RACE_INPUT`; flavor region has no bracket status block | [ ] |

**Failure signals:** Two or more `Awaiting:` lines; wrong label in flavor (`SKILL_INPUT`, `MAGIC_SCHOOLS_INPUT`, `EQUIPMENT_CONFIRMATION`); bracket `[Location: 32-C | Phase: desk | …]` in narration body.

---

### TC-4: Extended creation — gated steps stay clean (maps to ticket AC prompts / drift)

**Goal:** Steps after CLASS do not reintroduce wrong inline `Awaiting:` labels in flavor (historical Supa/Bumpy session bugs).

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Continuing from TC-2 at CLASS, pick a valid tier-1 class (e.g. `apprentice`) and submit | Skills table + note; footer **`Awaiting: SKILLS_INPUT`** (not `SKILL_INPUT`) | [ ] |
| 2 | Scan flavor region on skills response | **No** `Awaiting: SKILL_INPUT` or `SKILL_INPUT` anywhere above footer | [ ] |
| 3 | If caster path: enter three skills (e.g. `Lore, Spellcasting, Arcana`) and submit | Schools table; footer **`Awaiting: SPELL_SCHOOLS_INPUT`** (not `MAGIC_SCHOOLS_INPUT`) | [ ] |
| 4 | Scan flavor region on schools response | **No** `MAGIC_SCHOOLS_INPUT` or `MAGIC_SCHOOLS_*` in flavor region | [ ] |
| 5 | Optional: advance to equipment confirm step | Footer **`Awaiting: EQUIPMENT_GOLD_CONFIRMATION`** (not `EQUIPMENT_CONFIRMATION`) | [ ] |
| 6 | On each step above | Exactly **one** `Awaiting:` in full narration | [ ] |

**Failure signals:** Wrong awaiting token in flavor region; duplicate `Awaiting:` lines; UI suggestion chips show stale internal token (known APP-065 overlap — note but do not fail APP-073 if narration footer alone is correct).

**Scope note:** TC-4 is **smoke only** through SKILLS (and schools if convenient). Full Dumpy golden path (APP-057) not required for APP-073 sign-off.

---

### TC-5: Drift log — no `awaiting_mismatch` on clean play (maps to spec human hint)

**Goal:** When flavor sanitizer works, JSONL should not log drift from first-match wrong `Awaiting:` in flavor.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Complete TC-2 (minimum) or TC-2 + TC-4 | Session log written to `app/logs/session-<today>.jsonl` | [ ] |
| 2 | Search log for `"type": "creation_drift"` | **No** entries with `awaiting_mismatch` during the tested creation turns | [ ] |
| 3 | Optional: inspect `creation_step` snapshots | `awaiting` in snapshot aligns with footer label for each step taken | [ ] |

**Failure signals:** `creation_drift` with `awaiting_mismatch` and narrated label ≠ `CREATION_STATUS_LABELS[step]` while player followed prompts normally.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Strip bracket Location/Phase and any `Awaiting:` from flavor | TC-3, TC-4 | [ ] |
| Ticket | `_compose_creation_narration` — prose-only flavor; one code footer | TC-3 | [ ] |
| Ticket | ROLL_STATS → CLASS: **one** attribute breakdown; numbers match engine | TC-2 steps 5–9 | [ ] |
| Ticket | No duplicate stat table on Undead roll (session repro) | TC-2 steps 4–7 | [ ] |
| Spec S7 | `count("\| Attr \| Base \|") == 1` on roll turn | TC-2 step 5 | [ ] |
| Spec S1 | Single canonical `Awaiting:`; no wrong labels in flavor | TC-3, TC-4 | [ ] |
| Spec | No `awaiting_mismatch` drift on clean play | TC-5 | [ ] |
| Impl QA | Automated tests (if not run separately) | TC-1 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-065:** Suggestion chips may still show stale tokens if chip source is not yet hardened — APP-073 only guarantees **narration** is clean; note chip bugs separately.
- **APP-059:** Table column shapes (e.g. race Description column) unchanged by APP-073.
- **Human vs stub:** Integration test uses `BAD_STAT_FLAVOR` stub; live LLM may produce different leak shapes (`finish_reason: length`, compact stat row). TC-2 undead path is the authoritative manual repro.
- **Minimum sign-off:** TC-1 + TC-2 + TC-3 required; TC-4 and TC-5 strongly recommended before batch close with APP-065.
