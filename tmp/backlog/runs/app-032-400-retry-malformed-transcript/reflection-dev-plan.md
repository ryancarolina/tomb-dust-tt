# Reflection: Dev — APP-032 plan

**Agent:** Dev  
**Round:** 1  
**Deliverables:** `plan.md`, `reflection-dev-plan.md`

## Completed

- Read research-brief, spec.md, qa-spec-pass, ticket Expected files, domain spec § Reactive 400 retry (APP-032).
- Verified APP-031 landed: `_safe_prefix_fallback`, `sanitize_transcript_messages`, sanitize-only `_chat_completion` at L1174–1192; six call sites wired.
- Verified no existing `is_malformed_transcript_400` or retry logic in repo.
- Confirmed `BadRequestError` construction for tests via `httpx.Response(400, …)` on local OpenAI SDK 2.x.
- Wrote `plan.md` with `is_malformed_transcript_400` design, `_chat_completion` retry pipeline, site inheritance table, seven-test matrix (R1–R7), AC mapping.
- Scoped impl to ticket Expected files only; deferred R5 JSONL to APP-034.

## Self-critique

- **R7 call-count assumption:** Plan expects three `chat_completion` calls (depth-0 success, depth-1 fail, depth-1 retry). Impl must confirm `_llm_loop` does not short-circuit before depth-1 resubmit when first tool fails — APP-031 integration test already exercises fail-then-resubmit; retry adds one extra call on the depth-1 attempt only.
- **Third substring heuristic:** Spec requires `tool result messages` plus `tool_call(s)` in `str(exc)` — positive Google string already satisfies via substring 2; parametrize should still include isolated third-marker case per QA adversarial note #4.
- **Import from test module:** Plan prefers importing `assert_transcript_invariants` from `test_transcript_sanitize.py`; did not run pytest import path check — impl should verify conftest `sys.path` or inline a one-liner duplicate if needed.
- **Caller list not repaired:** Documented as v1 limit; successful retry may still leave malformed tail for depth+1 — acceptable per spec but impl should not “fix” by mutating caller list without ticket.

## Did I miss anything?

- [x] Ticket scope / Expected files — plan files ⊆ `orchestrator.py` + `test_transcript_400_retry.py`
- [x] Domain spec / registry_gap / AGENTS.md — registry_gap false; orchestrator-only; TurnTruth N/A
- [x] Code paths traced — `_chat_completion` intercept; `_llm_loop` GM falters fallback; six sites
- [x] Tests / AC mapped — R1–R7 matrix + APP-031 regression commands
- [x] APP-031 pairing — truncate uses `_safe_prefix_fallback` on caller original, not `clean`
- [ ] `httpx` as test dependency — transitive via `openai`; if missing in CI, use minimal mock `response` object with `status_code` + `request`

## Handoff

**Ready for:** QA plan gate (adversarial review of detection heuristics, retry budget, R7 integration call-count, caller immutability)

**Escalate human if:** QA plan requires mutating caller `messages` after retry — needs PM scope change / new ticket
