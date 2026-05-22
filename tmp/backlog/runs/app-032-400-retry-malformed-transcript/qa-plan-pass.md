# QA PASS: plan

**Task:** app-032-400-retry-malformed-transcript  
**backlog_ticket:** APP-032  
**ticket_path:** [tmp/backlog/app-032-400-retry-on-malformed-transcript.md](../../app-032-400-retry-on-malformed-transcript.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`; domain § Reactive 400 retry APP-032)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-llm-orchestrator-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (impl: `orchestrator.py`, `test_transcript_400_retry.py`; domain spec changelog on close is process-only)
- [x] Acceptance criteria testable — ticket AC + spec R1–R5 mapped in helper design, retry pipeline, site inheritance table, test matrix R1–R7, and AC mapping table
- [x] Code traces match repo — `_safe_prefix_fallback` L226, `sanitize_transcript_messages` L244, sanitize-only `_chat_completion` L1174–1192; six `_chat_completion(` call sites at L1198, L1822, L1842, L2185, L2266, L2339; `_llm_loop` GM-falters fallback at L2343–2347; no existing `is_malformed_transcript_400` / retry
- [x] AGENTS.md / canon compliance — orchestrator-only scope; `openrouter.py` explicitly out of scope; TurnTruth N/A (API transcript layer)
- [x] Tests/commands listed — seven pytest rows + `test_transcript_sanitize.py` regression + full `tests/`
- [x] Spec R1–R5 coverage in plan (narrow detection, once-per-call retry, APP-031 pairing, caller unchanged, R5 defer to APP-034)
- [x] `qa-spec-pass.md` adversarial notes carried into plan (caller list not repaired v1 limit; third-marker edge; detection brittleness; R5 optional)
- [x] Monkeypatch target — `gm.orchestrator.chat_completion` module symbol (matches APP-031 `test_wrapper_called_in_llm_loop` pattern)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` — `is_malformed_transcript_400` + `_chat_completion` retry wrapper | Yes |
| `app/tests/test_transcript_400_retry.py` (new) | Yes |
| `tmp/app-llm-orchestrator-spec.md` — checklist + changelog on close | Process (Spec sync on close); not impl gate |

**Out of scope (explicit):** `openrouter.py`; caller loop edits; in-place caller `messages` repair; non-400 retries; `transcript_400_retry` JSONL (APP-034) — aligned with spec non-goals.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 `is_malformed_transcript_400` narrow detection | § `is_malformed_transcript_400` design; marker tuple; never-raises contract | R1a/R1b parametrize (`test_is_malformed_transcript_400_cases`) |
| R2 truncate → sanitize → retry once in `_chat_completion` | § Wire pattern; § `_chat_completion` retry loop; truncate from **caller original** | R2, R4; pinned Holt-shaped fixture + expected 2nd-attempt payload |
| R3 APP-031 pairing (shared primitives, no fork) | Summary pairing; task 1–2 adjacency to sanitize helpers | R2 asserts `_safe_prefix_fallback` + `sanitize_transcript_messages` chain |
| R4 six sites unchanged; exhausted retry → existing fallbacks | § Site inheritance table; § Code-path traces | No caller edits; R7 `_llm_loop` integration (no GM falters) |
| R5 observability optional | § Open questions Q2 — defer APP-034 | Not blocking |
| Ticket AC: malformed transcript 400 → truncate + retry once | Full retry pipeline + primary regression narrative | R2 + R7 |
| Ticket AC: land tests | § Test matrix; task 3–4 | `test_transcript_400_retry.py` in Expected files |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-032 `in_progress`, P1 |
| Plan ⊆ Expected files | **PASS** | No unauthorized impl paths |
| Spec R1–R5 in plan | **PASS** | Algorithm + budget + non-mutating contract sufficient for impl |
| Code traces | **PASS** | Line refs spot-checked against live `orchestrator.py` |
| Test plan vs run `spec.md` / domain § Tests | **PASS** | All seven named cases + APP-031 regression commands |
| APP-031 boundary | **PASS** | First attempt still proactive sanitize; truncate uses caller original not `clean` |
| TurnTruth / narration gate conflict | **PASS** | API transcript layer only |

## Notes (non-blocking — implementation QA)

1. **`APIStatusError` positive fixture** — Plan R1 type gate supports `APIStatusError` with `status_code == 400`; parametrize rows focus on `BadRequestError`. Impl should add at least one `APIStatusError` positive row so R1 type branch is exercised.
2. **Wire pseudocode vs live delegate** — Plan `cc_kwargs` sketch passes `client=` keyword; live code uses positional `self.client` first — equivalent; impl should preserve existing positional call shape.
3. **`assert_transcript_invariants` import** — Plan open Q1 prefers sibling import; verify `cd app && pytest` import path during impl (duplicate one-liner only if cycle fails).
4. **R7 call-count** — Three `chat_completion` invocations (depth-0 tool, depth-1 fail, depth-1 retry) matches `_llm_loop` recurse at L2443 after APP-028 TOOL FAILED append; dev reflection flag acknowledged.
5. **Caller list not repaired** — Documented v1 limit (depth N+1 may re-400 with independent per-call retry); do not mutate caller list without PM ticket.

## Summary

`plan.md` is **implementation-ready**: single intercept in `_chat_completion`, narrow 400 detection, once-per-call retry budget, APP-031 primitive reuse on caller-original truncate, six inherited wire points, and a concrete seven-test matrix including `_llm_loop` depth ≥1 integration. Impl scope stays within ticket Expected files. Proceed to workstreams + implementation (Stage 4).

## Re-review focus

_None — proceed to implementation._
