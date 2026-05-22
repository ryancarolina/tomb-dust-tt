# Reflection: Research — APP-032 400 retry

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md, reflection-research.md, status.md checklist update

## Completed

- Read AGENTS.md, ticket APP-032, domain spec § Transcript sanitize + Problem, dev-team templates.
- Verified APP-031 landed: `_chat_completion` + `sanitize_transcript_messages` + `_safe_prefix_fallback` at all six wire sites; `test_transcript_sanitize.py` (12 tests) green path documented.
- Traced OpenRouter pass-through (`openrouter.py` L41) and exception propagation — no handling until caller `except Exception`.
- Mapped all six `_chat_completion` call sites and their divergent fallback prose / logging behavior.
- Confirmed OpenAI SDK 2.37.0 exposes `BadRequestError` / `APIStatusError` for 400 classification.
- Documented intended APP-032 intercept in `_chat_completion`, reuse of `_safe_prefix_fallback`, and open design questions (caller list mutation, retry budget, detection heuristic).
- Set `registry_gap: false` with app-master-spec + domain spec citations.

## Self-critique

- Did not replay gitignored `session-2026-05-20.jsonl` — relied on APP-031 research and domain spec for the Google error string verbatim.
- Did not mock a live OpenRouter 400 in this run; SDK exception shape inferred from installed package, not from a captured session stack trace.
- “Caller messages not updated on retry” is architectural inference — PM should decide whether in-place truncate is required for multi-depth loops or per-call retry is sufficient.

## Did I miss anything?

- [x] Ticket scope / Expected files — noted test-file gap vs APP-031 precedent
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced — `_chat_completion`, openrouter, three tool loops, six fallbacks
- [x] Tests / AC mapped — suggested matrix; no test file in ticket yet
- [ ] Live provider 400 payload samples — unavailable in repo; defer to APP-034 / human TC-6

## Handoff

**Ready for:** PM spec draft — § APP-032 reactive retry requirements on `_chat_completion`, 400 detection rules, retry budget semantics, optional caller-list repair, domain spec checklist/changelog stub, test file in Expected files if following APP-031 pattern

**Escalate human if:** Post-APP-031 live play still shows malformed-transcript 400 at high rate — may indicate sanitizer bug (fix APP-031) rather than needing only APP-032 safety net
