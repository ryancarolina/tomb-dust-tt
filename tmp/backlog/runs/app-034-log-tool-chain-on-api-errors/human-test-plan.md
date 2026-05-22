# Human Playtest Plan: APP-034-log-tool-chain-on-api-errors

**backlog_ticket:** APP-034  
**Commit:** pending (Stage 7 — use latest commit with APP-034 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-034 adds **structured JSONL `api_error` rows** on every `_chat_completion` failure (after APP-032 retry exhaustion or immediate non-retryable re-raise), with redacted `messages_summary` and `tool_chain`. Unit tests in `test_api_error_logging.py` (U1–U5, I1–I9) are the **primary** verification; manual play confirms the **live write path** to `app/logs/session-YYYY-MM-DD.jsonl` and redaction in a real session file.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] Valid OpenRouter API key in `app/.env` for TC-2 setup (TC-3 temporarily breaks the model, not the key)
- [ ] Ability to edit `app/config.yaml` and **revert** after TC-3 (backup copy recommended)
- [ ] Second terminal to tail or search today's log: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Know APP-034 vs APP-032:
  - **APP-032** retries malformed-transcript 400 once; **success** → no `api_error`.
  - **APP-034** logs `api_error` when the API call **still fails** after that retry (or on non-retryable errors).
  - **Healthy play** should produce **zero** `api_error` lines.

## Pass / fail signals (global)

| Good (pass) | Bad (fail — file bug) |
|-------------|------------------------|
| After induced API failure, JSONL has **exactly one** new `"type": "api_error"` for that failed call | No `api_error` row when player sees `The GM falters. (API error:` |
| `api_error` `data` includes required keys (see TC-2) | Missing `context`, `exc_type`, `error`, `model`, `attempt`, `messages_summary`, `tool_chain` |
| Log file contains **no** raw `sk-or-v1-` substrings | API key or Bearer token appears verbatim in JSONL |
| Normal play session has **no** `api_error` rows | `api_error` spam on every turn without real failures |
| Combat API failure still shows player `[Mechanics failed — API error:` **and** logs `context: combat_tools` or `combat_narrate` | Combat fails with mechanics prefix but **no** `api_error` in JSONL (pre-034 silent gap) |

## How to inspect session JSONL (all TCs)

Log path: `app/logs/session-<today>.jsonl` (one line = one JSON object).

**Find api_error rows (PowerShell from repo root):**

```powershell
Select-String -Path "app/logs/session-$(Get-Date -Format yyyy-MM-dd).jsonl" -Pattern '"type": "api_error"'
```

**Or** open the file and search for `"type": "api_error"`.

### Required `api_error` payload shape

Each row looks like:

```json
{"ts": "...", "type": "api_error", "data": { ... }}
```

| Field | Pass when |
|-------|-----------|
| `context` | One of: `llm_loop`, `creation_llm_loop`, `combat_tools`, `combat_narrate`, `narrate_flavor`, `narrate_only` |
| `exc_type` | Exception class name (e.g. `BadRequestError`) |
| `error` | Redacted error string (no raw API key) |
| `model` | Model id from config at failure time |
| `tools_present` | `true` or `false` |
| `attempt` | `1` (non-retryable or first failure) or `2` (malformed 400 exhausted retry) |
| `malformed_transcript_400` | `true` only for malformed-transcript 400 path |
| `original_len`, `sent_len` | Integers; on attempt 2 with retry, `sent_len` < `original_len` |
| `messages_summary` | Array of compact per-message rows (roles, previews capped) |
| `tool_chain` | Array (may be **empty** on failure before any assistant `tool_calls` in transcript) |
| `depth` | Present when call site passed depth (exploration/combat loops) |
| `retry_truncated` | `true` only on attempt 2 after APP-032 prefix retry |

**Optional (not required for pass):** `"type": "transcript_400_retry"` when malformed 400 retry runs and second attempt succeeds.

**Redaction sweep (required on any session with errors):**

```powershell
Select-String -Path "app/logs/session-$(Get-Date -Format yyyy-MM-dd).jsonl" -Pattern 'sk-or-v1-'
```

Pass when **zero** matches.

---

## Acceptance criteria map

| Ticket AC / Spec | Test case(s) |
|------------------|--------------|
| `_chat_completion` emits JSONL `api_error` on every API failure | TC-1 (pytest), TC-3 |
| Payload includes `messages_summary`, `tool_chain` | TC-2, TC-3 (optional TC-4) |
| `redact_secrets` — no raw API keys in JSONL | TC-1 (pytest), TC-5 |
| Combat API failures logged (`combat_tools` / `combat_narrate`) | TC-1 I6–I7 (pytest); TC-6 optional |
| Optional `transcript_400_retry` on malformed retry | TC-1 I3; not required in manual pass |
| No duplicate `log_error` for same API exception | TC-1 I8 (pytest) |

---

## Test cases

### TC-1: Automated regression gate (required before manual play)

**Goal:** Confirm APP-034 matrix + APP-032 regression green.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | `cd app` then `python -m pytest tests/test_api_error_logging.py -q` | Exit code **0**; **14 passed** | [ ] |
| 2 | `python -m pytest tests/test_transcript_400_retry.py -q` | Exit code **0**; **19 passed** (APP-032 regression) | [ ] |
| 3 | Optional: `python -m pytest tests/ -q` | Exit code **0**; full app suite green | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug against APP-034.

---

### TC-2: JSONL schema reference (maps to R3 — no app run)

**Goal:** Tester knows what to validate before inducing a failure.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Read **How to inspect session JSONL** above | Understand required `api_error` fields | [ ] |
| 2 | Note `tool_chain` may be `[]` on early-turn failures | Empty chain is **not** auto-fail for TC-3 | [ ] |
| 3 | Note non-empty `tool_chain` is proven by pytest `test_tool_chain_on_400_with_tools` (I9) | TC-4 optional for live multi-tool failure | [ ] |

---

### TC-3: Induced API failure → `api_error` in live JSONL (maps to ticket AC — **primary manual**)

**Goal:** Prove `log_api_error` writes to disk when OpenRouter rejects a request.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Copy `app/config.yaml` to `app/config.yaml.bak` | Backup saved | [ ] |
| 2 | In `app/config.yaml`, set `llm.model` to `invalid/nonexistent-model-APP034-test` | Invalid model configured | [ ] |
| 3 | Delete or rename today's log if you need a clean file: `app/logs/session-YYYY-MM-DD.jsonl` | Optional clean baseline | [ ] |
| 4 | `cd app && python main.py` | Window opens | [ ] |
| 5 | Type `new game`, submit; type any name (e.g. `LogTest`), submit | Creation starts; next LLM call may fail | [ ] |
| 6 | Wait for GM response or error narration | Player sees **`The GM falters. (API error:`** or creation error path — turn does not hang forever | [ ] |
| 7 | Quit app (Escape or close window) | Process ended | [ ] |
| 8 | Open `app/logs/session-YYYY-MM-DD.jsonl` | At least one line with `"type": "api_error"` **after** step 5 submit | [ ] |
| 9 | Inspect latest `api_error` `data` | `context` is `creation_llm_loop` or `llm_loop`; `attempt` is **1**; `malformed_transcript_400` is **false**; `model` is `invalid/nonexistent-model-APP034-test` | [ ] |
| 10 | Confirm `messages_summary` is a non-empty array | At least one summary row (e.g. `user`) | [ ] |
| 11 | Redaction sweep on log file | **Zero** `sk-or-v1-` matches | [ ] |
| 12 | Restore `app/config.yaml` from backup; delete `.bak` if desired | Valid model restored | [ ] |

**Failure signals:** No `api_error` despite visible API error fallback; crash without log write; raw API key in JSONL; app hangs with no response and no log line within ~60s.

**Cleanup:** Always restore config before further play.

---

### TC-4: Optional — non-empty `tool_chain` on live failure (maps to spec Stage 7 hint)

**Goal:** When failure happens on a transcript that already has assistant `tool_calls` + `tool` rows, JSONL captures chain order.

**Only run if TC-3 passed and you want extra confidence beyond pytest I9.**

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Restore valid `llm.model` in `app/config.yaml` | Normal model | [ ] |
| 2 | `python main.py`; complete **Dumpy** creation to Registry (`new game` → Holt path → `yes`) | `Awaiting: RECEPTION_CHOICE` at **32-C** | [ ] |
| 3 | Submit `I accept the Holt contract` (or equivalent); wait for GM + tools to finish | Turn completes; JSONL shows `tool_call` rows (e.g. `remember_fact`) | [ ] |
| 4 | **Before** next submit: set `llm.model` to `invalid/nonexistent-model-APP034-test` again | Invalid model | [ ] |
| 5 | Submit `enter the undercrypt` or `I head to the undercrypt` | API failure fallback visible | [ ] |
| 6 | Inspect latest `api_error` | `tool_chain` has **≥1** round with `assistant_tool_calls` and matching `tool_results`; `messages_summary` includes `tool` rows with `tool_call_id` | [ ] |
| 7 | Restore config | Valid model | [ ] |

**Failure signals:** `api_error` present but `tool_chain` empty when JSONL in same turn already shows prior `tool_call` + `tool` messages before the failed request — file bug.

---

### TC-5: Invalid API key redaction (maps to R1 — optional)

**Goal:** Auth-related errors do not leak `OPENROUTER_API_KEY` into JSONL.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Copy `app/.env` to `app/.env.bak` | Backup | [ ] |
| 2 | Set `OPENROUTER_API_KEY=sk-or-v1-invalid-test-key-APP034` in `.env` | Bad key | [ ] |
| 3 | Valid model in `config.yaml`; `python main.py`; `new game` + one submit | API/auth failure path | [ ] |
| 4 | Search log for `sk-or-v1-invalid-test-key-APP034` | **Zero** matches; `error` or nested fields use `[REDACTED]` if key echoed | [ ] |
| 5 | Restore `.env` from backup | Valid key restored | [ ] |

**Failure signals:** Full fake key string appears in JSONL.

---

### TC-6: Healthy session — no spurious `api_error` (maps to I3 negative path)

**Goal:** Normal play does not emit `api_error` when API succeeds (including APP-032 retry success).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Valid `config.yaml` and `.env` | Normal configuration | [ ] |
| 2 | `python main.py`; play one short turn at Registry (e.g. `look around` after finished creation) | GM narration returns; no persistent API error banner | [ ] |
| 3 | Search today's JSONL for `"type": "api_error"` | **Zero** rows **or** only rows from earlier TC-3/TC-5 in same file — no new rows from this step | [ ] |

**Failure signals:** New `api_error` on every turn during healthy API connectivity.

---

### TC-7: Combat API failure logging (pytest-only minimum; optional manual)

**Goal:** Confirm combat silent-gap fix — **pytest I6/I7 satisfies AC**; manual is optional.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | TC-1 step 1 already covers `test_combat_tools_failure_logged` and `test_combat_narrate_failure_logged` | Both pass | [ ] |
| 2 | *(Optional)* Induce invalid model during active combat and inspect JSONL | `api_error` with `context`: `combat_tools` or `combat_narrate`; player still sees `[Mechanics failed — API error:` | [ ] |

**Note:** Combat encounter setup is lengthy; **skip step 2** if TC-1 passes — not required for APP-034 sign-off.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | `_chat_completion` emits `api_error` on API failure | TC-1, TC-3 | [ ] |
| Ticket | Payload includes `messages_summary`, `tool_chain` | TC-2, TC-3 step 10; TC-4 optional | [ ] |
| Ticket | No raw API keys in JSONL | TC-3 step 11; TC-5 optional | [ ] |
| Ticket | Combat failures logged | TC-1 (I6–I7); TC-7 optional | [ ] |
| R6 | Optional `transcript_400_retry` | TC-1 I3 only — not manual gate | [ ] |

## Minimum bar

**TC-1 + TC-3** pass before considering APP-034 verified at the table. TC-4–TC-7 are optional depth.

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all required TC pass / issues: … |

## Notes for next ticket

- **APP-032 pairing:** Malformed-transcript recovery may emit `transcript_400_retry` without `api_error` — expected on success path.
- **Batch:** `orchestrator.py` may also contain APP-022/026 hunks; logging behavior is independent — verify `api_error` fields, not unrelated hints/gates.
- **Close-stage:** `tmp/app-logging-qa-spec.md` JSONL table cross-sync may still be pending at ticket close — not a playtest failure.
- **Do not** commit `config.yaml.bak`, `.env.bak`, or edited invalid model to the repo.
