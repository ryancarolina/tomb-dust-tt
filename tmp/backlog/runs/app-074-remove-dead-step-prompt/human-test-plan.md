# Human Playtest Plan: APP-074-remove-dead-step-prompt

**backlog_ticket:** APP-074  
**Commit:** pending (Stage 7 — use latest commit with APP-074 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-074 deletes dead `get_step_prompt()` only — **no behavior change** on the live code-first path. This plan is a **smoke gate through the RACE step** to confirm `_auto_present_race` / `format_races_table()` still drive narration after the removal. Automated pytest already passed at impl QA; manual play catches UI/LLM integration regressions pytest may miss.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (do not Continue from a mid-creation save)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for pytest TC-1

## Test cases

### TC-1: Automated regression gate (maps to R1 / R2 — optional but recommended)

**Goal:** Confirm creation suite still green after `get_step_prompt` deletion before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_creation_flow.py app/tests/test_creation_tables.py play/tomb_gm/tests/test_creation_gating.py -q` | Exit code **0**; all tests pass | [ ] |
| 2 | From repo root: `rg "get_step_prompt" app/` | Zero matches | [ ] |

**Failure signals:** Any pytest failure; grep hit under `app/` — stop manual play and file bug.

### TC-2: Smoke — new game through RACE table (maps to R2 / ticket AC)

**Goal:** After name commit, narration shows a **single code-owned race table** and `Awaiting: RACE_INPUT` — not legacy LLM table duplication or empty `"The clerk waits."` fallthrough.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM prompts for delver name; creation active (footer or status shows creation awaiting, e.g. name input) | [ ] |
| 3 | Type a short name (e.g. `Smoke`) and submit | Narration includes **one** markdown table with header `\| Race \| Adjustments \|` (Description column may still appear per APP-059 — not a failure) | [ ] |
| 4 | Read narration footer / status line | Contains **`Awaiting: RACE_INPUT`** | [ ] |
| 5 | Scan narration body | **Not** exactly `"The clerk waits."` alone with no race table (APP-068 regression) | [ ] |
| 6 | Count `\| Race \| Adjustments \|` header blocks in composed narration | Exactly **one** — table comes from code body, not a second LLM-emitted table (APP-072) | [ ] |
| 7 | Optional: thin clerk flavor | 0–2 sentences of banter **above** the table is OK; flavor must not replace or duplicate the code table | [ ] |

**Failure signals:** Crash on `new game` or name submit; no race table after name; missing `RACE_INPUT`; duplicate race tables; stuck on NAME; traceback in terminal.

### TC-3: RACE commit advances chain (maps to R2 — one step past smoke)

**Goal:** Picking a race still routes through `_execute_creation_choice` → `_chain_after_creation_choice` → `_auto_roll_stats` (live path untouched by dead prompt removal).

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Continuing from TC-2 at RACE step, type `human` and submit | Stats roll table appears (d20 rolls / attribute block) | [ ] |
| 2 | Read same response | Class table also present in narration (ROLL_STATS chain includes `format_classes_table`) | [ ] |
| 3 | Read footer | Awaiting advances past `RACE_INPUT` (e.g. class selection input — exact label may vary) | [ ] |
| 4 | Optional JSONL check | Log contains `creation_advanced` or step snapshot showing advance from `RACE` | [ ] |

**Failure signals:** Race not accepted after table was shown; infinite race re-prompt; stats/class tables missing; crash on race submit.

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Creation flow works after removal (smoke through race) | TC-2, TC-3 | [ ] |
| R2 | Code-first path: `_auto_present_*` / `format_*_table` present tables | TC-2 steps 3–6 | [ ] |
| R2 | No `"The clerk waits."` empty chain after NAME | TC-2 step 5 | [ ] |
| R1 | `get_step_prompt` absent from `app/` | TC-1 step 2 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Out of scope:** Full Dumpy golden path (APP-057) — run only if TC-2/3 fail and deeper bisect is needed.
- **APP-059:** Race table may still show a Description column; formatter change is separate.
- **Non-regression expectation:** If TC-2 and TC-3 pass, no further manual creation testing required for this chore.
- **system_prompt.py:** Still mentions legacy `set_creation_choice` desk tools — known non-goal per spec; not a failure here unless LLM starts tool-calling during RACE.
