# Human Playtest Plan: APP-032-400-retry-malformed-transcript

**backlog_ticket:** APP-032  
**Commit:** pending (Stage 7 — use latest commit with APP-032 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-032 adds a **reactive safety net** inside `Orchestrator._chat_completion`: when a strict provider still returns **400 Bad Request** on a malformed in-turn tool transcript (after APP-031 proactive sanitize), the orchestrator truncates to a safe prefix (`system` + last `user`), re-sanitizes, and retries **once**. Unit tests cover R1–R7 in `test_transcript_400_retry.py`; **manual play validates live multi-tool turns no longer die mid-chain** with `"The GM falters. (API error: …)"`. Pre-fix failure (session 2026-05-20): Holt quest accept + `enter_dungeon` chain hit Google malformed-transcript 400 at `_llm_loop` depth ≥1 and killed the turn.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-…`)
- [ ] Fresh session: type **`new game`** (or **Continue** only if you already have a delver at Breley reception — TC-2 can be skipped)
- [ ] Optional log watch: second terminal tail `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] Know what APP-032 fixes (pairs with APP-031):
  - **APP-031** proactively sanitizes every `_chat_completion` payload.
  - **APP-032** recovers when sanitize alone is insufficient — truncate → sanitize → **one** retry per API call.
  - **Player-visible failure without fix:** `"The GM falters. (API error: Tool-call assistant message produced no valid function calls but is followed by tool result messages)"` mid-turn.
  - **You cannot observe retry directly in PyGame** — pass = turn completes with normal GM prose; fail = API error fallback or hung turn.

## What to look for (all TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| Narration shows **`The GM falters. (API error:`** mid-turn | GM returns normal prose; turn completes |
| Multi-tool chain stops after first tool with no narration | Quest accept + dungeon entry (or equivalent) both resolve in session |
| JSONL `error` / `chat_completion` with malformed-transcript 400 wording | No such errors in this session |
| Player action gets no GM response after tool chain | Narration arrives within usual LLM latency |
| Tool failure turn shows API error instead of honest failure narration | GM narrates refusal/failure in character; session continues |

## How to inspect session JSONL (all TCs)

Search today's log for tool chains and API failures.

| Signal | Pass when |
|--------|-----------|
| Multi-tool chain | Two or more `"type": "tool_call"` lines with **different** `"name"` values within the **same** player turn (before next `player_input`) |
| `remember_fact` | `"ok": true` after quest accept (pairs with APP-080; memory persistence is separate) |
| `enter_dungeon` | `"ok": true` when entering undercrypt |
| Malformed-transcript 400 | **Zero** lines containing `Tool-call assistant message produced no valid function calls` or `no valid function calls but is followed by tool` |
| Player-visible fallback | **Zero** narration matching `The GM falters. (API error:` |
| Tool failure path | `"ok": false` on a tool may appear — **next** LLM response in same turn must still be narration, not API error |
| `transcript_400_retry` | May be **absent** (R5 deferred to APP-034) — **not** a failure |

**Pre-fix failure fragment (regression watch):**

```text
The GM falters. (API error: Tool-call assistant message produced no valid function calls but is followed by tool result messages)
```

---

## Acceptance criteria map

| Ticket AC / Spec | Test case(s) |
|------------------|--------------|
| On malformed transcript 400, repair/truncate history and retry once | TC-1 (pytest), TC-3, TC-6 |
| Multi-tool depth ≥1 turn completes without session-killing API fail (run spec Stage 7) | TC-3 |
| Tool failure mid-chain → narrate pass, not hard 400 (APP-028 + retry) | TC-4 |
| Combat tool failure → narrate pass without 400 (optional) | TC-5 |
| Residual 400 after APP-031 — turn recovers via truncate+retry | TC-3, TC-6 |
| Unrelated 400 / non-400 — no spurious retry (pytest only) | TC-1 |

---

## Test cases

### TC-1: Automated regression gate (required before manual play)

**Goal:** Confirm APP-032 retry matrix + APP-031 sanitize regression green before live LLM play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_transcript_400_retry.py -q` | Exit code **0**; 19 tests pass | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_transcript_sanitize.py -q` | Exit code **0**; 12 tests pass (APP-031 regression) | [ ] |
| 3 | Optional: `python -m pytest app/tests/ -q` | Exit code **0**; full app suite green | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug against APP-032.

---

### TC-2: Creation → Registry reception (setup for exploration)

**Goal:** Reach `Phase: preparation` at Breley (`32-C`) with a non-empty roster — required for exploration tool loops that trigger `_llm_loop` depth ≥1.

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

**Goal:** One or more exploration turns invoke **multiple tools** in a chain (`remember_fact` + `enter_dungeon` is the canonical Holt regression). Even if the provider would 400 on depth ≥1 resubmit, APP-032 truncate+retry lets the turn complete — **no** `"The GM falters. (API error: …)"`.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At reception, type e.g. `I seek Marshal Garrick Holt about licensed delving` and submit | GM narrates Registry/Breley context | [ ] |
| 2 | Type e.g. `I go to Marshal Holt's office and listen to his offer` and submit | Holt offers the **brother's signet ring** quest from **Breley undercrypt** / **32-C-UG-1** | [ ] |
| 3 | Type e.g. **`I accept Holt's quest to retrieve the signet ring and enter the Breley undercrypt now at 32-C-UG-1`** and submit | GM confirms quest **and** processes dungeon entry in one turn (may take longer — multi-tool depth) | [ ] |
| 4 | Read narration panel after step 3 completes | **No** `The GM falters. (API error:` text; prose covers quest and/or threshold crossing | [ ] |
| 5 | Footer / stats after step 3 | Phase moves toward **delve** or undercrypt location — not stuck at surface-only fiction | [ ] |
| 6 | JSONL: same turn as step 3 | At least **two** distinct tool names (e.g. `remember_fact` and `enter_dungeon`) before next `player_input` | [ ] |
| 7 | JSONL: `enter_dungeon` on that turn | **`"ok": true`** | [ ] |
| 8 | JSONL: same turn / session | **No** malformed-transcript 400 error strings; turn did not abort mid-chain | [ ] |

**Failure signals:** API error narration after quest accept; only first tool runs then silence; `enter_dungeon` never called; session appears hung.

**Note:** If step 3 splits across two player turns, still pass TC-3 if **each** turn with multiple tools completes without API error. Step 6 applies per multi-tool turn.

**Alternate one-turn prompt (if step 3 stalls):** accept quest on step 3a, then `enter breley undercrypt at 32-C-UG-1` on step 3b — both turns must avoid API errors.

---

### TC-4: Tool failure recovery — same turn still narrates (maps to run spec Stage 7)

**Goal:** A failed tool call inserts TOOL FAILED into the in-turn transcript; if the next `_chat_completion` would 400, APP-032 retries with safe prefix; GM still returns honest failure narration — not a hard API fail.

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

### TC-5: Combat tool failure → narrate pass (optional)

**Goal:** Illegal combat action fails tool; if narrate-pass `_chat_completion` would 400, retry recovers; player sees failure narration.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Enter undercrypt (TC-3) and explore until combat starts | Combat UI / footer shows combat phase | [ ] |
| 2 | On PC turn, type an **illegal** action e.g. **`I cast fireball at the ceiling`** or **`I attack with a weapon I don't have`** and submit | GM narrates failure or correction — **not** API error | [ ] |
| 3 | Read narration | **No** `The GM falters. (API error:` | [ ] |
| 4 | JSONL check | `"name": "combat_action"` with `"ok": false` possible; turn still completes with narration | [ ] |
| 5 | Submit one legal combat action (e.g. `I attack the nearest enemy with my weapon`) | Combat continues normally | [ ] |

**Skip:** Mark **skipped — no combat encountered** if undercrypt exploration does not trigger combat within ~10 minutes. TC-3 + TC-4 are the minimum bar.

---

### TC-6: Session log regression sweep (maps to ticket AC)

**Goal:** Entire play session free of malformed-transcript 400s and player-visible API fallbacks after APP-032.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Open `app/logs/session-YYYY-MM-DD.jsonl` for this playthrough | File exists; contains `player_input` and `tool_call` events | [ ] |
| 2 | Search `Tool-call assistant message produced no valid function calls` | **Zero** matches | [ ] |
| 3 | Search `The GM falters` or `chat_completion` + `400` | **Zero** matches tied to transcript/tool ordering | [ ] |
| 4 | Search `remember_fact` + `enter_dungeon` | If both present, they appear in exploration turns without intervening API errors | [ ] |
| 5 | Optional: search `transcript_400_retry` | May be absent (R5 deferred to APP-034) — **not** a failure | [ ] |

**Failure signals:** Any malformed-transcript 400 string; multiple API error fallbacks in one session — file bug: APP-032 retry did not recover or detection missed provider wording.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | On malformed transcript 400, truncate + retry once | TC-1, TC-3, TC-6 | [ ] |
| Ticket | Multi-tool exploration turn completes without session kill | TC-3 | [ ] |
| R4 | Caller fallbacks unchanged when retry exhausted (pytest) | TC-1 | [ ] |
| Run spec | Tool failure path still narrates same turn | TC-4 | [ ] |
| Run spec | Combat narrate pass after tool failure (if reachable) | TC-5 or skip | [ ] |
| Impl QA | Automated tests green | TC-1 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-031:** Proactive sanitize remains first line of defense; APP-032 is the safety net when sanitize alone 400s. Both should pass together — run [APP-031 human-test-plan](../app-031-transcript-sanitize-orphan-tool-messages/human-test-plan.md) only if bisecting which layer failed.
- **APP-034:** `transcript_400_retry` and `transcript_sanitized` JSONL telemetry deferred — do not fail TC-6 if absent.
- **APP-080:** `remember_fact` arg coercion is separate; TC-3 step 7 cares about **turn survival**, not memory persistence.
- **Cannot force** provider 400 in manual play — Holt-shaped malformed arrays are unit-tested in `test_transcript_400_retry.py` (`test_malformed_400_then_success`, `test_llm_loop_depth1_retry_integration`). Manual play is a **live regression gate** for the same player-visible symptom.
- **Minimum bar for release sign-off:** TC-1 + TC-3 + TC-4 + TC-6 pass.
- **Retry is invisible:** A passing TC-3 does not prove retry fired — it proves the turn survived. Double-400 exhaustion (retry failed) would still show `"The GM falters"` — that is a TC-3/TC-6 fail.
