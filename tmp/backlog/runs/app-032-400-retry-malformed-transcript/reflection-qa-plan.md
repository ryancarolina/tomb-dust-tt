# Reflection: QA — APP-032 plan (round 1)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `qa-plan-pass.md`, `reflection-qa-plan.md`

## Completed

- Read run `spec.md`, `plan.md`, `qa-spec-pass.md`, ticket Expected files, domain § Reactive 400 retry (APP-032).
- Spot-checked live `orchestrator.py`: APP-031 helpers landed; `_chat_completion` sanitize-only; six call sites; `_llm_loop` except → GM falters at L2343–2347.
- Verified plan impl scope ⊆ ticket Expected files (`orchestrator.py`, `test_transcript_400_retry.py`).
- Mapped spec R1–R5 and all seven pytest rows to plan sections; confirmed `qa-spec-pass` adversarial notes addressed in plan.
- Validated R7 integration sketch against `test_wrapper_called_in_llm_loop` and `_llm_loop` recurse after TOOL FAILED append.
- Issued **PASS** — no blockers requiring `qa-plan-report-1.md`.

## Self-critique

- **Line-number drift:** Plan cites `_llm_loop` fallback L2343–2347 (accurate today); did not re-enumerate all six `_chat_completion` call-site lines in the plan gate table — relied on grep spot-check instead.
- **R1 type coverage:** Flagged missing explicit `APIStatusError` positive parametrize row as non-blocking impl note; could have been a minor PLAN finding if spec QA treated it as mandatory in plan (spec lists type OR; plan design covers it).
- **Did not run** `impl-check` or attempt a dry-run patch — plan review is document vs repo trace only, per gate scope.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced (`_chat_completion` intercept; `_llm_loop` primary regression)
- [x] Tests / AC mapped (R1–R7 ↔ spec test plan)
- [x] APP-031 pairing (truncate source = caller original)
- [x] TurnTruth / narration gate — N/A confirmed
- [ ] Live `BadRequestError` construction in CI — plan cites local SDK 2.x verification; impl QA must confirm pytest env

## Handoff

**Ready for:** workstreams + implementation (Stage 4); QA impl gate after code lands

**Escalate human if:** impl widens scope to mutate caller `messages` after retry or adds retry on unrelated 400s — PM scope change required
