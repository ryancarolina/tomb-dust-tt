# Human Playtest Plan: APP-080-normalize-tool-args

**backlog_ticket:** APP-080  
**Commit:** pending (Stage 7 — use latest commit with APP-080 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-080 normalizes LLM tool args before `GameBridge` dispatch so corrupted scalars (especially `remember_fact.importance` with XML/markup bleed) no longer raise `TypeError` and silently drop quest memory. Unit tests cover the Holt fixture (`test_tool_args.py`); **manual play validates end-to-end quest persistence** when the GM calls `remember_fact` and the player later asks for objectives via `memory_recall`. Pre-fix failure (session 2026-05-20): `remember_fact` `{ok: false}` → only generic `enter_dungeon` auto-fact remained.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (do not Continue from a mid-creation or mid-delve save)
- [ ] Optional log watch: second terminal tail `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] Know the bug this fixes:
  - **`remember_fact` fails** when `importance` arrives as a corrupted string (e.g. `"4</importance>…<invoke name=\"enter_dungeon\">…"`) → `{ok: false, error: "'<' not supported…"}` in JSONL.
  - **Quest fact never stored**; LLM retries `enter_dungeon` only → memory holds `"Player entered dungeon at room …"` but **not** Holt/signet quest text.
  - **`memory_recall`** for quest giver/objective returns empty or only dungeon-entry noise.

## How to inspect session JSONL (all TCs)

Search today's log for `"type": "tool_call"` entries.

| Tool | Pass when |
|------|-----------|
| `remember_fact` | At least one line with `"name": "remember_fact"` and `"result": {"ok": true, …}` (or `"ok": true` in result object) |
| `remember_fact` args (logged post-normalize) | `"importance"` is a **JSON number** (e.g. `4`), not a string containing `</invoke>` or `<invoke` |
| `memory_recall` | `"name": "memory_recall"` with `"ok": true` and `facts` array non-empty when player asked about the quest |
| `fortune_spend` (optional) | If present: `"ok": true` — **no** log `error` containing `unexpected keyword argument 'amount'` |
| `enter_dungeon` | `"ok": true` when entering undercrypt; does **not** replace quest fact in recall |

**Example pass fragment (shape only):**

```json
{"type": "tool_call", "data": {"name": "remember_fact", "args": {"fact": "Marshal Holt tasked … signet ring …", "importance": 4, "entities": ["Marshal Holt", …]}, "result": {"ok": true, "memory_id": 1}}}
```

**Pre-fix failure fragment (regression watch):**

```json
{"type": "tool_call", "data": {"name": "remember_fact", "args": {"importance": "4</importance>…"}, "result": {"ok": false, "error": "'<' not supported between instances of 'str' and 'int'"}}}
```

---

## Test cases

### TC-1: Automated regression gate (required before manual play)

**Goal:** Confirm APP-080 unit + full app suite green before live LLM play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_tool_args.py -q` | Exit code **0**; 15 passed | [ ] |
| 2 | From repo root: `python -m pytest app/tests/ -q` | Exit code **0**; full app suite green | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Creation → Registry reception (setup for exploration)

**Goal:** Reach `Phase: preparation` at Breley (`32-C`) with a non-empty roster — same gate as APP-057.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM prompts for delver name | [ ] |
| 3 | Type `Dumpy` and submit | Race table appears | [ ] |
| 4 | Type `human` and submit | Stats + class tables | [ ] |
| 5 | Type `apprentice` and submit | Skills table | [ ] |
| 6 | Type `Lore, Spellcasting, Arcana` and submit | Spell schools table | [ ] |
| 7 | Type `pyromancy, ether` and submit | Tier-1 spells table | [ ] |
| 8 | Type `ember-touch, static-lash` and submit | Equipment summary | [ ] |
| 9 | Type `yes` and submit | Footer includes **`Phase: preparation`** and **`Awaiting: RECEPTION_CHOICE`**; location **32-C** (Breley) | [ ] |
| 10 | Left stats panel | Shows **Dumpy** (non-empty roster) | [ ] |

**Failure signals:** Stuck in creation; empty roster; crash. **Stop** — exploration/memory TCs need a finished delver.

---

### TC-3: Holt quest hook — `remember_fact` persists (primary — maps to ticket AC)

**Goal:** After accepting Marshal Holt's signet quest, campaign memory stores quest text (not lost to arg normalization failure).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-2 at reception, type e.g. `I seek Marshal Garrick Holt about licensed delving` and submit | GM narrates Registry/Breley context; may direct you toward Holt | [ ] |
| 2 | Type e.g. `I go to Marshal Holt's office and listen to his offer` and submit | Holt offers the **brother's signet ring** quest from **32-C-UG-1** / Breley undercrypt (hollow knights) | [ ] |
| 3 | Type e.g. `I accept the quest to retrieve the signet ring` and submit | GM confirms contract/quest; narration references Holt + ring + undercrypt | [ ] |
| 4 | JSONL check (same session, after step 3) | At least one `"name": "remember_fact"` with **`"ok": true`** | [ ] |
| 5 | Inspect that `remember_fact` log line `args.fact` | Contains quest substance: **Holt** (or Garrick) + **signet ring** (or brother's ring) + **undercrypt** (or **32-C-UG-1**) | [ ] |
| 6 | Inspect `args.importance` on that line | Integer **1–5** (often **4** or **5** for quest); **not** a string with `</invoke>` / `<invoke` | [ ] |

**Failure signals:** No `remember_fact` call after quest accept (retry step 3 with clearer accept); `remember_fact` `ok: false` with TypeError/comparison errors; quest narrated but no memory tool call; only generic travel facts in later recall.

**Note:** Markup-bleed corruption cannot be forced reliably in manual play — Holt fixture in TC-1 is authoritative for that path. If corruption appears naturally in logs, steps 5–6 are the regression detector.

---

### TC-4: Enter undercrypt — `enter_dungeon` without wiping quest memory

**Goal:** Dungeon entry succeeds via tool; quest fact remains distinct from auto `enter_dungeon` room fact.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Type e.g. `enter breley undercrypt` or `enter dungeon at 32-C-UG-1` and submit | GM calls **`enter_dungeon`** (not fiction-only entry); narration reflects threshold crossing | [ ] |
| 2 | Read footer / stats | Phase moves toward **delve** (or in-dungeon); location shows undercrypt / **UG** layer — not still surface-only fiction | [ ] |
| 3 | JSONL check | `"name": "enter_dungeon"` with **`"ok": true`**; `site_address` or resolved address present in args | [ ] |
| 4 | JSONL: prior `remember_fact` from TC-3 | Still present with **`ok: true`** — not overwritten by failed remember | [ ] |

**Failure signals:** Interior narration while still `Phase: preparation` at surface with no successful `enter_dungeon`; `enter_dungeon` `ok: false` only; APP-024 refusal line about threshold with no tool success.

---

### TC-5: `memory_recall` returns quest fact (primary — maps to run spec Stage 7)

**Goal:** Player question triggers recall; GM answer uses stored Holt quest, not only dungeon-entry boilerplate.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Still in session after TC-3 (before or after TC-4), type e.g. `What was my quest from Marshal Holt?` or `What does Holt want me to do?` and submit | GM answers with **signet ring** / **brother** / **undercrypt** objective | [ ] |
| 2 | JSONL check for this turn | `"name": "memory_recall"` with **`"ok": true`** | [ ] |
| 3 | Inspect `memory_recall` result `facts` (if logged) or GM prose | Top facts mention **Holt quest** — **not** only `"Player entered dungeon at room …"` | [ ] |
| 4 | Negative check | GM does **not** invent a new quest unrelated to Holt if recall returned facts | [ ] |

**Failure signals:** GM guesses quest with no `memory_recall` tool; recall `ok: true` but empty `facts`; answer only describes last room entry; player told "no record" after TC-3 showed `remember_fact` ok.

---

### TC-6: Session log regression sweep (maps to ticket logging AC / optional APP-034)

**Goal:** No silent tool-arg type failures on memory tools in this session.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Open `app/logs/session-YYYY-MM-DD.jsonl` for this playthrough | File exists and contains `player_input` + `tool_call` events | [ ] |
| 2 | Search `remember_fact` | **Zero** results with `ok: false` and errors mentioning `'<' not supported` or `TypeError` | [ ] |
| 3 | Search `memory_recall` | If any calls exist, **no** `unexpected keyword` / `top` vs `top_k` TypeError in `result.error` | [ ] |
| 4 | Search `fortune_spend` | If any calls exist, **no** `unexpected keyword argument 'amount'` | [ ] |

**Failure signals:** Any memory-tool `ok: false` from Python type errors after APP-080; corrupted `importance` strings still logged without coercion to int (post-fix should log clean ints).

---

### TC-7: Fortune spend — arg whitelist (secondary — maps to R3)

**Goal:** If player spends Fortune, `fortune_spend` succeeds with `character_id` only (spurious `amount` dropped).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Confirm stats panel shows Fortune **≥ 1** (e.g. `1/2`) | Pool available — else **skip** TC-7 | [ ] |
| 2 | Type e.g. `Dumpy spends Fortune for advantage on my next roll` and submit | GM spends 1 Fortune; narration acknowledges advantage | [ ] |
| 3 | JSONL check | `"name": "fortune_spend"` with **`"ok": true`**; args contain **`character_id`** only (no required `amount`) | [ ] |

**Failure signals:** `fortune_spend` `ok: false` with `amount` keyword error; Fortune pool unchanged after successful narration.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | `remember_fact` no longer loses quest facts to `importance` type errors | TC-3, TC-5, TC-6 | [ ] |
| Ticket | Coerced args reach bridge; memory persists | TC-3 step 4–6, TC-5 | [ ] |
| R2 | `memory_recall` works after quest stored | TC-5 | [ ] |
| R3 | `fortune_spend` not broken by stray `amount` | TC-7 (or skip + note) | [ ] |
| R4 | `enter_dungeon` succeeds in exploration loop | TC-4 | [ ] |
| Impl QA | Automated tests green | TC-1 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Markup bleed:** Repro is unit-tested (`HOLT_REMEMBER_FACT_ARGS` in `test_tool_args.py`); manual play proves **happy-path** persistence only unless logs show natural corruption (TC-3 step 6).
- **APP-034:** `tool_arg_coerced` telemetry not in v1 — do not fail playtest if absent.
- **APP-025:** Full Registry hub → extract loop automation is separate; this plan stops at quest + ingress + recall.
- **Creation dependency:** TC-2 mirrors [APP-057 human-test-plan](../app-057-test-creation-flow/human-test-plan.md); run that first if reception is unstable.
- **Minimum bar for release sign-off:** TC-1 + TC-3 + TC-5 pass; TC-4 and TC-6 strongly recommended.
