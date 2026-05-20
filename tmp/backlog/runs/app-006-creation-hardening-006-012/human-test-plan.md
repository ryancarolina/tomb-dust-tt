# Human Playtest Plan: APP-006-creation-hardening-006-012

**backlog_ticket:** APP-006 … APP-012
**Commit:** pending
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter/API config loaded (or expect clerk fallback flavor text)
- [ ] Fresh session: type `new game`
- [ ] Log path: `app/logs/session-YYYY-MM-DD.jsonl`

## Test cases

### TC-1: Code-owned tables through apprentice caster (APP-006, APP-007)

**Goal:** Tables and status footer come from code, not LLM invention.

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | `new game` → name → race → class (apprentice path) | Skills table appears with ★ key skills | [ ] |
| 2 | Pick 3 valid skills incl. Spellcasting | Schools table appears (arcane schools) | [ ] |
| 3 | Pick 2 schools, 2 spells | Equipment shows kit + GP numbers | [ ] |
| 4 | Check narration footer | `Awaiting: …_INPUT` matches step; no duplicate LLM `[Location:…]` mid-creation | [ ] |

**Failure signals:** LLM-only skill list; wrong GP; `Phase: PRE_DELVE` before finalize

### TC-2: "Yes" at wrong step (APP-011)

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | At spell schools step, type `Yes` | Error + schools table re-shown; step unchanged | [ ] |
| 2 | At skills step, type `ready` | Error + skills table re-shown | [ ] |

### TC-3: Finalize roster gate (APP-009)

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Complete creation through equipment confirm | World intro; character on roster in stats panel | [ ] |
| 2 | JSONL | `creation_finalize` with non-empty roster | [ ] |

**Failure signals:** PRE_DELVE narration with empty roster; UI shows delver without engine character

### TC-4: No exploration during creation (APP-008)

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | During creation, try travel/delve phrases | Clerk keeps you on creation; no site travel | [ ] |
| 2 | JSONL mid-creation | No `world_travel` / `site_enter` tool calls | [ ] |

### TC-5: Resume mid-creation (APP-010)

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Stop mid-creation (e.g. at SKILLS) — close app | `app/session_state.json` has `creation_state.step` | [ ] |
| 2 | Relaunch → `continue` | Same step resumed (not reset to NAME) | [ ] |

### TC-6: Thin LLM flavor (APP-012)

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Observe creation turns | Short clerk flavor + code table body | [ ] |
| 2 | After finalize | Exploration tools work on next action | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | |
