# Human Playtest Plan: APP-076-swap-default-llm-to-haiku-4-5

**backlog_ticket:** APP-076  
**Commit:** pending (Stage 7 — use latest commit with APP-076 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-076 is a **config-only** default model swap (`google/gemini-3.1-flash-lite` → `anthropic/claude-haiku-4.5`). Automated import smoke passed at impl QA; this plan verifies the new default is visible in UI, used on live LLM turns, and logged in session JSONL.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (do not Continue from a mid-creation save)
- [ ] Log path to inspect after play: `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] No local override of `llm.model` outside shipped `app/config.yaml`

## Test cases

### TC-1: UI shows Haiku 4.5 default (maps to R1 / ticket AC)

**Goal:** Confirm shipped config is loaded and displayed before any LLM turn.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Look at status area above the input box (right side) | Label reads **`Model: anthropic/claude-haiku-4.5`** | [ ] |
| 3 | Optional: open `app/config.yaml` and compare | UI label matches `llm.model` value exactly | [ ] |

**Failure signals:** Window crash on launch; label shows `google/gemini-3.1-flash-lite`, `anthropic/claude-sonnet-4`, or `unknown`; missing API key error before label check is OK — fix `.env` and relaunch.

### TC-2: New game + one creation step with tool (maps to R3 / ticket AC)

**Goal:** Live LLM turn succeeds on creation path using the new default model.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Type `new game` and submit | GM prompts for delver name; creation active | [ ] |
| 2 | Type a short name (e.g. `HaikuSmoke`) and submit | GM responds; narration advances (race table or next creation step) | [ ] |
| 3 | Watch terminal / narration for errors | **No** OpenRouter 400/404, "model not found", or hung spinner with traceback | [ ] |
| 4 | Optional JSONL peek (during play) | At least one `llm_request` event appears in today's session log | [ ] |

**Failure signals:** API error mentioning invalid model id; repeated empty GM response; traceback in terminal; creation stuck with no advancement after name submit.

**Tool-call note:** Name commit typically triggers creation advancement via code-first path; a subsequent step (e.g. race choice) may invoke desk tools. Either **name submit with GM response** or **one explicit creation choice** (e.g. `human` at race step) satisfies "one creation step with tool" if logs show `llm_request` — prefer advancing through name + one choice if unsure.

### TC-3: One exploration turn (maps to R3 / ticket AC)

**Goal:** Post-creation (or earliest available) GM turn uses Haiku without errors.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Continue from TC-2 — either finish minimal creation or use suggestion chips to advance until Hub/exploration | Player reaches a state where travel/exploration input is accepted (not blocked on creation-only steps) | [ ] |
| 2 | Submit one exploration-style input (e.g. `look around`, `go to registry`, or a suggestion chip for travel) | GM narrates a response; no crash | [ ] |
| 3 | Check terminal | No LLM/API error after exploration turn | [ ] |

**Failure signals:** Exploration blocked incorrectly during creation (may need more creation steps first — not a model failure); persistent 400 errors on any GM turn.

**Shortcut if creation is long:** After TC-2 proves LLM works on creation, advance only as far as needed for one non-creation GM reply; full character sheet not required for APP-076 sign-off.

### TC-4: Session JSONL model field (maps to R4 / ticket AC)

**Goal:** Structured logs record the configured model id on LLM requests.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Close app or leave running; open latest `app/logs/session-*.jsonl` | File exists for today's session | [ ] |
| 2 | Search for `"event": "llm_request"` or `"llm_request"` entries | At least one matching line | [ ] |
| 3 | Inspect `data.model` (or `"model"` field) on those lines | Value is **`anthropic/claude-haiku-4.5`** on every `llm_request` checked | [ ] |
| 4 | Optional PowerShell: `Select-String -Path "app/logs/session-*.jsonl" -Pattern '"model"'` | No lines show `google/gemini-3.1-flash-lite` for this session | [ ] |

**Example expected fragment:**

```json
{"event": "llm_request", "data": {"messages": 12, "model": "anthropic/claude-haiku-4.5", "depth": 0}, ...}
```

**Failure signals:** Missing `llm_request` events after TC-2/3 GM replies; `"model": "google/gemini-3.1-flash-lite"` or `"anthropic/claude-sonnet-4"` on requests when config says Haiku 4.5.

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | `config.yaml` Haiku 4.5 default | TC-1 (UI confirms loaded config) | [ ] |
| Ticket | Manual smoke: creation + exploration | TC-2, TC-3 | [ ] |
| Ticket | JSONL `model` field | TC-4 | [ ] |
| R3 | No LLM errors on live turns | TC-2 step 3, TC-3 step 3 | [ ] |
| R4 | `log_llm_request` model id | TC-4 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Out of scope:** Per-mode model routing, changing Orchestrator code fallback (`anthropic/claude-sonnet-4`), or tuning `max_tokens` / `temperature`.
- **If smoke fails:** Check OpenRouter dashboard for `anthropic/claude-haiku-4.5` availability; escalate to APP-031/032 if 400s on tool transcripts persist under Haiku.
- **Config-only:** No Python regression suite required beyond import smoke; failures here indicate runtime/API issues, not missing unit tests for this ticket.
