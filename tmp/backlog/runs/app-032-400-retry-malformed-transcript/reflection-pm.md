# Reflection: PM — APP-032 400 retry

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-llm-orchestrator-spec.md` (§ Reactive 400 retry), `tmp/backlog/app-032-400-retry-on-malformed-transcript.md` (Expected files), `reflection-pm.md`

## Completed

- Drafted run-local [spec.md](./spec.md) with problem, goals, five requirements (R1–R5), seven-case test matrix, APP-031 pairing, and orchestrator-only wire scope.
- Added normative domain spec § **Reactive 400 retry (APP-032)** — narrow 400 detection, retry pipeline in `_chat_completion`, once-per-call budget, non-mutating contract, tests, APP-031 pairing table update.
- Updated ticket **Expected files** with `app/tests/test_transcript_400_retry.py` (APP-031 precedent).
- Added checklist item (open) and changelog entry in domain spec; appended APP-032 test command to § Tests.

## Decisions

- **Retry budget:** once per `_chat_completion` invocation — not once-per-turn. Multi-depth loops may each retry independently; research open question resolved per user directive.
- **Detection:** narrow — `BadRequestError` / 400 + transcript-related substrings only; unrelated 400s propagate without retry.
- **Truncate:** `_safe_prefix_fallback(caller messages)` → `sanitize_transcript_messages` — reuse APP-031 primitives; truncate from original caller array, not first-pass `clean`.
- **Caller mutation:** out of v1 — retry uses internal copies; loops keep appending to original list (consistent with APP-031 non-mutating contract).
- **Test file:** new `test_transcript_400_retry.py` rather than extending sanitize module — keeps APP-031/032 test ownership clear.

## Self-critique

- Detection substrings are Google-biased — novel provider wordings may miss until APP-034 logs inform expansion; documented as risk in research, acceptable for v1 safety net.
- `_llm_loop` integration test may need careful mock of underlying `chat_completion` vs `_chat_completion` — Dev plan should pick one monkeypatch layer.
- Optional `transcript_400_retry` JSONL deferred to APP-034 — QA may want at least mock assertion that retry path was taken without event wiring.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator.py + test module added
- [x] Domain spec / registry_gap — registry_gap false; § APP-032 added as sibling to APP-031
- [x] Code paths not traced — research brief covered; R2 pins `_chat_completion` intercept
- [x] Tests or AC mapped — seven pytest rows in run + domain spec
- [x] APP-031 pairing — R3 + shared primitives explicit
- [ ] Caller in-place repair — explicitly deferred; escalate if live play shows repeated 400 at depth 2+ after successful depth-1 retry

## Handoff

**Ready for:** QA spec review (round 1)  
**Escalate human if:** QA rejects narrow detection as too brittle, or requires in-place caller `messages` repair for multi-depth loops
