# Drift Check: APP-032-400-retry-malformed-transcript

**backlog_ticket:** APP-032  
**Verdict:** PASS (synced)

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) § Reactive 400 retry (APP-032) | was minor (open work still listed APP-032) | **Synced:** removed APP-032 from open-work line; checklist `[x]`, changelog, behavior § already matched code |
| Run [`spec.md`](./spec.md) R1–R5 | no | Verified against `orchestrator.py`, `test_transcript_400_retry.py` |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | No APP-032 row; priority table unchanged |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| `is_malformed_transcript_400` — narrow 400 + transcript substring heuristic; never raises | `orchestrator.py` L314–336; `_MALFORMED_TRANSCRIPT_MARKERS` L314–317 | yes |
| Exception types: `BadRequestError` / `APIStatusError` with `status_code == 400` | L323–326 | yes |
| Unrelated 400 → no retry | L322–323 re-raise path | yes |
| Proactive sanitize first (APP-031 pairing) | L1210 `sanitize_transcript_messages(messages)` | yes |
| Malformed 400 → `_safe_prefix_fallback(caller messages)` → sanitize → one retry | L1224–1228; truncate from **caller** `messages`, not `clean` | yes |
| Kwargs preserved on retry (`tools`, `tool_choice`, `max_tokens`, `temperature`) | L1211–1218 `cc_kwargs`; L1226–1228 merge | yes |
| Non-mutating caller contract | Retry uses internal copies; tests R6 | yes |
| Single intercept — six call sites inherit | `_chat_completion` only; no caller loop edits | yes |
| Exhausted retry re-raises to existing fallbacks | L1221–1223, L1226–1228; `test_malformed_400_twice_propagates`, R7 | yes |
| Optional `transcript_400_retry` JSONL | not implemented | deferred (APP-034; spec optional v1) |

## Spec test matrix → pytest

| Spec case | Test | Result |
|-----------|------|--------|
| Malformed-transcript 400 then success | `test_malformed_400_then_success` | ✓ |
| Unrelated 400 (invalid model) | `test_unrelated_400_no_retry` | ✓ |
| Malformed 400 twice | `test_malformed_400_twice_propagates` | ✓ |
| Non-400 (429, connection) | `test_non_400_no_retry` | ✓ |
| `is_malformed_transcript_400` parametrize | `test_is_malformed_transcript_400_cases` (12 cases) | ✓ |
| Caller list immutability | `test_caller_messages_unchanged_after_retry` | ✓ |
| `_llm_loop` depth ≥1 integration | `test_llm_loop_depth1_retry_integration` | ✓ |
| APP-031 regression | `test_transcript_sanitize.py` (12 tests) | ✓ |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| On malformed transcript 400, repair/truncate history and retry once | ✓ |

## Tests run

```bash
cd app; python -m pytest tests/test_transcript_400_retry.py tests/test_transcript_sanitize.py -q
```

**Result:** 31 passed (0.96s)

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [ ] `python tmp/backlog/claim_ticket.py release APP-032 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Pre-drift lag was documentation only: open-work line still referenced APP-032 while checklist/changelog marked done.
- R5 observability (`transcript_400_retry` JSONL) explicitly deferred to APP-034 — not AC drift.
- Caller `messages` not repaired in-place after retry — documented v1 limit in run spec; per-call retry budget at each loop depth.
- Human Google 400 / multi-tool recovery playtest deferred to Stage 7 (`human-test-plan.md`).
