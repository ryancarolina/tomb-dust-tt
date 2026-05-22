# Human Playtest Plan: APP-031-transcript-sanitize-orphan-tool-messages

**backlog_ticket:** APP-031  
**Commit:** pending (Stage 7 — use latest commit with APP-031 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-031 sanitizes in-turn LLM `messages` before every orchestrator `chat_completion` so orphan `tool` rows (and APP-028 `system` TOOL FAILED lines between assistant `tool_calls` and `tool` results) no longer trigger provider **400** errors on depth ≥1 resubmit. Unit tests cover T1–T10 in `test_transcript_sanitize.py`; **manual play validates live multi-tool exploration turns** complete without session-killing API failures. Pre-fix failure (session 2026-05-20): mid-turn `"The GM falters. (API error: …)"` after malformed `remember_fact` + `enter_dungeon` chain.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (or **Continue** only if you already have a delver at Breley reception — TC-2 can be skipped)
- [ ] Optional log watch: second terminal tail `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] Know the bug this fixes:
  - **Multi-tool turn** (e.g. `remember_fact` then `enter_dungeon` in one `_llm_loop` chain) resubmits a transcript where strict providers reject assistant + orphan `tool` ordering.
  - **Player sees** `"The GM falters. (API error: …)"` instead of narration — turn feels broken mid-chain.
  - **JSONL** may contain `log_error` / `chat_completion` with text like *Tool-call assistant message produced no valid function calls but is followed by tool result messages* (Google via OpenRouter).

## What to look for (all TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| Narration panel shows **`The GM falters. (API error:`** mid-turn | GM returns normal prose; turn completes |
| Player action gets no GM response after tool chain | Narration arrives within usual LLM latency |
| JSONL `chat_completion` / `error` with malformed-transcript / orphan-tool wording | No such errors in this session |
| Quest accepted but session dies before dungeon entry narration | Holt quest + undercrypt entry both narrated in same session |
| Tool failure turn shows API error instead of honest failure narration | GM narrates refusal/failure in character after bad tool call |

## How to inspect session JSONL (all TCs)

Search today's log for tool and error events.

| Signal | Pass when |
|--------|-----------|
| Multi-tool chain | Two or more `"type": "tool_call"` lines with **different** `"name"` values within the **same** player turn (before next `player_input`) |
| `remember_fact` | `"ok": true` after quest accept (pairs with APP-080; failure here is not APP-031 unless followed by 400) |
| `enter_dungeon` | `"ok": true` when entering undercrypt |
| `chat_completion` errors | **Zero** lines containing `Tool-call assistant message produced no valid function calls` or generic malformed-transcript 400 |
| Player-visible fallback | **Zero** narration lines matching `The GM falters. (API error:` |
| Tool failure path | `"name": "enter_dungeon"` or `"process_beat"` with `"ok": false` may appear — **next** LLM response in same turn must still be narration, not API error |

**Pre-fix failure fragment (regression watch):**

```text
The GM falters. (API error: Tool-call assistant message produced no valid function calls but is followed by tool result messages)
```

---

## Acceptance criteria map

| Ticket AC / Spec | Test case(s) |
|------------------|--------------|
| Sanitize transcript: no orphan tool messages without preceding `tool_calls` | TC-1, TC-3, TC-4, TC-6 |
| Multi-tool turn completes without 400 (run spec Stage 7) | TC-3 |
| Tool failure recovery — next model call in same turn returns narration (R3 APP-028 reorder) | TC-4 |
| Combat tool failure → narrate pass without 400 (R4 site 5) | TC-5 (optional) |
| No session-killing Google malformed-transcript errors | TC-6 |

---

## Test cases

### TC-1: Automated regression gate (required before manual play)

**Goal:** Confirm APP-031 unit + full app suite green before live LLM play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_transcript_sanitize.py -q` | Exit code **0**; 12 tests pass | [ ] |
| 2 | From repo root: `python -m pytest app/tests/ -q` | Exit code **0**; full app suite green | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Creation → Registry reception (setup for exploration)

**Goal:** Reach `Phase: preparation` at Breley (`32-C`) with a non-empty roster — required for exploration tool loops.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM prompts for delver name | [ ] |
| 3 | Type `Holt` and submit | Race table appears | [ ] |
| 4 | Type `human` and submit | Stats + class tables | [ ] |
| 5 | Type `apprentice` and submit | Skills table | [ ] |
| 6 | Type `Lore, Spellcasting, Arcana` and submit | Spell schools table | [ ] |
| 7 | Type `pyromancy, ether` and submit | Tier-1 spells table | [ ] |
| 8 | Type `ember-touch, static-lash` and submit | Equipment summary | [ ] |
| 9 | Type `yes` and submit | Footer includes **`Phase: preparation`** and **`Awaiting: RECEPTION_CHOICE`**; location **32-C** (Breley) | [ ] |
| 10 | Left stats panel | Shows **Holt** (non-empty roster) | [ ] |

**Failure signals:** Stuck in creation; empty roster; crash. **Stop** — TC-3+ need a finished delver.

**Skip:** If continuing from an existing save already at reception with a living character, mark TC-2 skipped and note character name.

---

### TC-3: Multi-tool exploration turn — Holt quest + undercrypt (primary — maps to ticket AC)

**Goal:** One or more exploration turns invoke **multiple tools** in a chain (`remember_fact` + `enter_dungeon` is the canonical Holt regression). Turn completes with narration — **no** API error mid-chain.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At reception, type e.g. `I seek Marshal Garrick Holt about licensed delving` and submit | GM narrates Registry/Breley context | [ ] |
| 2 | Type e.g. `I go to Marshal Holt's office and listen to his offer` and submit | Holt offers the **brother's signet ring** quest from **Breley undercrypt** / **32-C-UG-1** | [ ] |
| 3 | Type e.g. **`I accept Holt's quest to retrieve the signet ring and enter the Breley undercrypt now at 32-C-UG-1`** and submit | GM confirms quest **and** processes dungeon entry in one turn (may take longer — multi-tool depth) | [ ] |
| 4 | Read narration panel after step 3 completes | **No** `The GM falters. (API error:` text; prose covers quest and/or threshold crossing | [ ] |
| 5 | Footer / stats after step 3 | Phase moves toward **delve** or undercrypt location — not stuck at surface-only fiction | [ ] |
| 6 | JSONL: same turn as step 3 | At least **two** distinct tool names (e.g. `remember_fact` and `enter_dungeon`) before next `player_input` | [ ] |
| 7 | JSONL: `enter_dungeon` on that turn | **`"ok": true`** | [ ] |
| 8 | JSONL: same session | **No** `chat_completion` error with malformed-transcript / orphan-tool wording on that turn | [ ] |

**Failure signals:** API error narration after quest accept; only first tool runs then silence; `enter_dungeon` never called; session appears hung.

**Note:** If step 3 splits across two player turns (LLM narrates quest first, player enters on next line), still pass TC-3 if **each** turn with multiple tools completes without API error. Step 6 applies per turn that chains tools.

**Alternate one-turn prompt (if step 3 stalls):** accept quest on step 3a, then `enter breley undercrypt at 32-C-UG-1` on step 3b — both turns must avoid API errors.

---

### TC-4: Tool failure recovery — same turn still narrates (maps to R3 APP-028)

**Goal:** A failed tool call inserts TOOL FAILED into the in-turn transcript; sanitizer reorders before the next `chat_completion`; GM still returns honest failure narration — not a 400.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | From surface Breley (`32-C`) or reception, type e.g. **`enter dungeon at 99-Z-UG-1`** (invalid AV-GRID) and submit | GM responds with in-character refusal or error — **not** API error boilerplate | [ ] |
| 2 | Read narration | **No** `The GM falters. (API error:` | [ ] |
| 3 | JSONL check for this turn | `"name": "enter_dungeon"` with **`"ok": false`** is acceptable | [ ] |
| 4 | JSONL: after failed tool | Turn still emits GM narration / assistant content — no orphaned mid-turn 400 | [ ] |
| 5 | Type a valid follow-up e.g. `look around the registry` and submit | Normal exploration continues; session not broken | [ ] |

**Failure signals:** API error instead of narrated failure; app stuck with no response; subsequent turns all fail.

**Alternate failure trigger:** `travel to 99-Z` or `go to invalid grid 00-X` — same pass criteria.

---

### TC-5: Combat tool failure → narrate pass (optional — maps to R4 combat site 5)

**Goal:** Illegal combat action fails tool; combat narrate pass sanitizes assistant/system/tool ordering; player sees failure narration.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Enter undercrypt (TC-3) and explore until combat starts (e.g. provoke hollow knights — may take several turns) | Combat UI / footer shows combat phase | [ ] |
| 2 | On PC turn, type an **illegal** action e.g. **`I cast fireball at the ceiling`** (spell not in kit) or **`I attack with a weapon I don't have`** and submit | GM narrates failure or correction — **not** API error | [ ] |
| 3 | Read narration | **No** `The GM falters. (API error:` | [ ] |
| 4 | JSONL check | `"name": "combat_action"` with `"ok": false` possible; turn still completes with narration | [ ] |
| 5 | Submit one legal combat action (e.g. `I attack the nearest enemy with my weapon`) | Combat continues normally | [ ] |

**Skip:** Mark **skipped — no combat encountered** if undercrypt exploration does not trigger combat within ~10 minutes. TC-3 + TC-4 are the minimum bar.

---

### TC-6: Session log regression sweep (maps to ticket AC + spec observability)

**Goal:** Entire play session free of malformed-transcript 400s and player-visible API fallbacks.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Open `app/logs/session-YYYY-MM-DD.jsonl` for this playthrough | File exists; contains `player_input` and `tool_call` events | [ ] |
| 2 | Search `Tool-call assistant message produced no valid function calls` | **Zero** matches | [ ] |
| 3 | Search `The GM falters` or `chat_completion` + `400` | **Zero** matches tied to transcript/tool ordering | [ ] |
| 4 | Search `remember_fact` + `enter_dungeon` | If both present, they appear in exploration turns without intervening API errors | [ ] |
| 5 | Optional: search `transcript_sanitized` | May be absent (R5 deferred to APP-034) — **not** a failure | [ ] |

**Failure signals:** Any malformed-transcript 400 string; multiple API error fallbacks in one session.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | No orphan tool messages cause provider 400 on resubmit | TC-1, TC-3, TC-6 | [ ] |
| Ticket | Multi-tool exploration turn completes | TC-3 | [ ] |
| R3 | Tool failure path still narrates (APP-028 reorder) | TC-4 | [ ] |
| R4 | Combat narrate pass after tool failure (if reachable) | TC-5 or skip | [ ] |
| Impl QA | Automated tests green | TC-1 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-032:** Reactive 400 truncate/retry is **not** in APP-031 — if TC-6 still shows malformed-transcript 400, file against APP-032 (sanitize alone insufficient).
- **APP-080:** `remember_fact` arg coercion is separate; TC-3 step 7 cares about **turn survival**, not memory persistence (see [APP-080 human-test-plan](../app-080-normalize-tool-args/human-test-plan.md) for memory AC).
- **APP-034:** `transcript_sanitized` JSONL telemetry deferred — do not fail if absent.
- **Creation dependency:** TC-2 mirrors [APP-057](../app-057-test-creation-flow/human-test-plan.md) / APP-080 setup; skip if save already at reception.
- **Minimum bar for release sign-off:** TC-1 + TC-3 + TC-4 + TC-6 pass.
- **Cannot force** LLM markup bleed or structurally invalid `tool_calls` in manual play — Holt-shaped cases remain unit-tested in `test_transcript_sanitize.py` T7/T8.
