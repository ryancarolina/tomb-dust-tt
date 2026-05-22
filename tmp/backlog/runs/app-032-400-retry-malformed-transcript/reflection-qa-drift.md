# Reflection: QA — APP-032 drift

**Agent:** QA (drift)  
**Round:** 1  
**Deliverables:** `drift-check.md`, domain spec sync, ticket AC + close, `reflection-qa-drift.md`

## Completed

- Compared `is_malformed_transcript_400`, `_chat_completion` retry wrapper, and APP-031 pairing in `orchestrator.py` against domain § Reactive 400 retry (APP-032), run `spec.md` R1–R5, and ticket AC.
- Ran `pytest tests/test_transcript_400_retry.py tests/test_transcript_sanitize.py -q` — **31 passed**.
- Synced `tmp/app-llm-orchestrator-spec.md` open-work line (removed APP-032; range now APP-033–APP-034).
- Marked ticket AC `[x]`, Status `done`, Closed 2026-05-22.

## Self-critique

- Did not re-run full `app/tests/` suite (qa-implementation-pass reported broader green).
- Did not replay Holt session JSONL or live Google 400 path in PyGame.
- Did not run `claim_ticket.py release APP-032 --done` — orchestrator handoff per run convention.
- Detection heuristic may miss novel provider wordings — acceptable v1 scope; negative fixtures cover unrelated 400s.

## Did I miss anything?

- [x] Ticket scope / Expected files (`orchestrator.py`, `test_transcript_400_retry.py`)
- [x] Domain spec behavior § + checklist + changelog
- [x] APP-031 pairing (sanitize + `_safe_prefix_fallback`; no duplicate repair logic)
- [x] Retry budget (once per `_chat_completion`; non-mutating caller contract)
- [x] Tests mapped to spec matrix R1–R7
- [ ] Human playtest — Stage 7
- [ ] `transcript_400_retry` JSONL — APP-034

## Handoff

**Ready for:** Orchestrator `release APP-032 --done`, Stage 7 commit + `human-test-plan.md`  
**Escalate human if:** Live provider returns malformed-transcript 400 on retry-safe prefix (double-400 exhaustion) or novel error strings bypass `is_malformed_transcript_400`.
