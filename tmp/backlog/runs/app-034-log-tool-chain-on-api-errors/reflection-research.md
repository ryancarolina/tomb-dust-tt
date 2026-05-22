# Reflection: Research — APP-034 tool-chain logging

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md, reflection-research.md, status.md checklist update

## Completed

- Read ticket APP-034, domain spec § APP-031/032 observability deferrals + APP-080 `tool_arg_coerced`, `app-logging-qa-spec.md` JSONL table, APP-031/032 research briefs.
- Verified post-APP-032 `_chat_completion` try/retry wrapper (L1208–1236) — still zero logging on exception paths.
- Mapped all six `_chat_completion` call sites and divergent caller logging (combat API + narrate pass silent).
- Contrasted `log_llm_request` / `log_llm_response` / `log_tool_call` / `log_error` — established why depth≥1 400s lack reconstructable chain today.
- Recommended single intercept in `_chat_completion` + `logger.py` helpers (`redact`, serialize tool chain, optional consolidated JSONL types).
- Documented deferred events from APP-031/032/080 for PM consolidation decision.
- Set `registry_gap: false` with app-master-spec + domain spec citations.

## Self-critique

- Did not replay gitignored `session-2026-05-20.jsonl` — Holt/Google string taken from prior research and domain spec.
- Did not mock live OpenRouter failures; payload shape inferred from SDK + existing `test_transcript_400_retry.py` patterns.
- “Redact keys” interpreted as API secrets — PM should confirm PII/player-text policy for `remember_fact` args in error dumps.
- Depth/context (`exploration` vs `creation` vs `combat`) not available inside `_chat_completion` without signature change — flagged as open design.

## Did I miss anything?

- [x] Ticket scope / Expected files — `orchestrator.py` + `logger.py` only; noted test-file precedent
- [x] Domain spec / registry_gap / AGENTS.md
- [x] APP-031/032 pairing — repair vs observe; retry paths traced
- [x] Code paths — `_chat_completion`, three tool loops, logger helpers
- [x] Redaction gap — no existing helper in repo
- [ ] Live 400 payload corpus — defer to post-impl logs / human playtest

## Handoff

**Ready for:** PM spec — define JSONL event schema (`api_error` minimum), redaction rules, payload caps, whether to absorb `transcript_400_retry` / `transcript_sanitized` / `tool_arg_coerced`, combat silent-path fix, optional `_chat_completion(..., depth=, loop=)` context param, `app-logging-qa-spec.md` event table sync, test module in Expected files

**Escalate human if:** Error logs grow too large for daily JSONL rotation — may need config flag or sample rate
