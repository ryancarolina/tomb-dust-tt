# QA PASS: implementation — round 1

**Task:** app-031-transcript-sanitize-orphan-tool-messages  
**backlog_ticket:** APP-031  
**ticket_path:** [tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md](../../app-031-transcript-sanitize-orphan-tool-messages.md)  
**Round:** 1  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) § Transcript sanitize (APP-031)

## Verdict

**PASS** — `sanitize_transcript_messages`, `_safe_prefix_fallback`, and `Orchestrator._chat_completion` match ticket AC, run `spec.md` R1–R6, and plan test matrix T1–T10. All targeted and full-app pytest green.

## Automated tests

```text
python -m pytest app/tests/test_transcript_sanitize.py -v
12 passed in 0.49s

python -m pytest app/tests/ -q
132 passed in 12.14s
```

| Module | Tests | Result |
|--------|-------|--------|
| `test_transcript_sanitize.py` | 12 (T1–T10 + 3 T10 param cases) | ✓ |
| Full `app/tests/` | 132 (regression) | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Sanitize transcript: no orphan tool messages without preceding tool_calls | `sanitize_transcript_messages` L244–309; pass 2 drops orphan `tool` rows (L266–268) and unmatched ids (L287–290) | ✓ |
| Wire before every `chat_completion` | Single `_chat_completion` L1174–1192; six call sites at L1198, L1822, L1842, L2185, L2266, L2339; no other `chat_completion(` in orchestrator | ✓ |
| Expected file `app/gm/orchestrator.py` | Helpers + wrapper added | ✓ |
| Expected file `app/tests/test_transcript_sanitize.py` | New module with T1–T10 | ✓ |

## Run spec R1–R6 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Non-mutating `sanitize_transcript_messages`; safe-prefix fallback | Shallow copies throughout; `_safe_prefix_fallback` L226–241; empty-walk guard L307–308; T9 + T10 | ✓ |
| **R2** | Validity rules, orphan drop, round-trip | `_is_valid_tool_call` L189–206; `_normalize_assistant_message` L209–223; T1–T5, T7 | ✓ |
| **R3** | APP-028 reorder system-after-tools | Pass 2 partitions `tools` / `deferred` L284–296; T6, T8 | ✓ |
| **R4** | All six wire points via wrapper | Traced: `_call_narration_llm`, `_narrate_only`, `_creation_llm_loop`, `_combat_llm_loop_inner`, combat narrate pass, `_llm_loop` | ✓ |
| **R5** | Optional `transcript_sanitized` JSONL | Not implemented — deferred to APP-034 per spec/plan | deferred |
| **R6** | No 400 retry; helper public for APP-032 | Module-level `sanitize_transcript_messages` + `_safe_prefix_fallback`; no truncate/retry logic | ✓ |

## Plan test matrix → pytest

| Test ID | Name | Result |
|---------|------|--------|
| T1 | `test_orphan_tool_no_preceding_assistant` | ✓ |
| T2 | `test_assistant_empty_tool_calls_followed_by_tool` | ✓ |
| T3 | `test_invalid_tool_call_missing_id` | ✓ |
| T4 | `test_valid_two_tool_chain` | ✓ |
| T5 | `test_unmatched_tool_call_id` | ✓ |
| T6 | `test_system_between_assistant_and_tool` | ✓ |
| T7 | `test_holt_session_shape` | ✓ |
| T8 | `test_wrapper_called_in_llm_loop` | ✓ |
| T9 | `test_sanitize_does_not_mutate_caller_list` | ✓ |
| T10 | `test_tail_invalid_returns_safe_prefix` (3 cases) | ✓ |

## Independent code traces

| Flow | Path | Result |
|------|------|--------|
| Holt regression (depth ≥1 resubmit) | Invalid/empty `tool_calls` stripped → orphan tools dropped → safe-prefix keeps system+user | T7, T3 |
| APP-028 combat/exploration failure | `_llm_loop` appends system then tool; second `_chat_completion` receives tool→system order | T8 |
| Valid two-tool chain unchanged | Order and ids preserved; output copies ≠ input refs | T4 |
| Empty assistant shell | `content: None` + invalid calls → message dropped; fallback when entire walk empties | T3, T10 |
| Monkeypatch compatibility | T8 patches `gm.orchestrator.chat_completion`; wrapper still delegates to symbol | ✓ |

## Adversarial notes (non-blocking)

1. **R5 observability** — No `transcript_sanitized` JSONL event; explicitly deferred to APP-034.
2. **Ticket close pending** — Domain spec checklist/changelog already draft “done”; ticket still `in_progress` until `release APP-031 --done`.
3. **Human playtest** — Not run this round (Stage 7: multi-tool turn + tool failure recovery without Google 400).
4. **`_creation_llm_loop` integration** — Skipped per plan (zero callers); unit coverage sufficient.
5. **Assistant empty-shell edge** — T3 expects `[]` when input is only invalid assistant+tool (no system/user for fallback); matches spec algorithm.

## Handoff

**Ready for:** Stage 6 drift check + `release APP-031 --done` (ticket AC checkbox, Closed date, confirm domain spec changelog).  
**Pairing:** APP-032 should import `sanitize_transcript_messages` / `_safe_prefix_fallback` after truncate — no duplicate repair logic needed.
