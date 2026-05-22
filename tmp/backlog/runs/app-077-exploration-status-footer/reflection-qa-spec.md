# Reflection: QA spec — APP-077 round 1

**Agent:** QA (adversarial)  
**Round:** 1  
**Deliverables:** qa-spec-pass.md, reflection-qa-spec.md

## Completed

- Read ticket APP-077 AC, run `spec.md`, domain `tmp/app-exploration-delve-spec.md` § APP-077 + APP-024/089 coordination, orchestrator `tmp/app-llm-orchestrator-spec.md` § APP-077 + § Mechanical-truth narration gate (APP-083), `research-brief.md`, dev-team templates.
- Cross-walked every ticket AC to spec F1–F12 and domain § Footer contract / Compose order / Tests.
- Verified TurnTruth / APP-083 / APP-089 / APP-090 ordering across run spec, domain spec, orchestrator spec, and `tomb-dust-turn-truth-verify.mdc` — no compose-before-verify contradiction.
- Spot-checked live code (`_compose_exploration_narration` stub, `process_turn` double-compose, `_combat_turn` emit sites, `_LLM_STATUS_TAG_RE`, `cmd_core.py` combat payload, `system_prompt.py` mandate) — gaps match spec intent (pre-impl).
- Confirmed `registry_gap: false` and expected files ⊆ ticket.

## Verdict rationale

Default FAIL bar not met: no missing AC, no wrong domain owner, no untestable core behavior, TurnTruth ordering documented and consistent. Issued **PASS** with non-blocking notes (ticket AC signature drift, F3 actor fallback vs live status shape, empty roster edge, double-compose idempotency emphasis, stale research brief).

## Self-critique

- Did not run pytest (spec stage; no impl).
- Did not read full `system_prompt.py` combat sections — relied on research + F10 table.
- Did not enumerate every `_combat_turn` return path for compose coverage — F9 + spot-check only; flagged L2287 pre-existing emit skip as out-of-scope NOTE.
- Session log evidence (`session-2026-05-22.jsonl`) gitignored — unverified; human playtest hints adequate for Stage 7.

## Did I miss anything?

- [x] Ticket AC ↔ spec ↔ domain
- [x] registry_gap / expected files
- [x] Test contracts and commands
- [x] TurnTruth / APP-083 ordering
- [x] APP-024 compose order coordination
- [ ] Whether F4 bracket regex should also strip unbracketed `Location: … | Phase: …` lines — spec pins bracket shape; APP-041/TTS sibling handles speak path; acceptable
- [ ] Exact `strip_llm_meta_narration` regex fixtures — deferred to Dev plan (spec intent clear)

## Handoff

**Ready for:** Dev plan (`plan.md`) — pin idempotent compose helper, `format_exploration_status` empty-roster behavior, combat compose single choke before `_emit_narration` L2334/L2302, extend `_LLM_STATUS_TAG_RE` without creation footer regression, optional `log_exploration_drift` hook point.

**Escalate human if:** Dev discovers combat status lacks `turn_id` on common paths — revisit F3 fallback in domain spec.

**Orchestrator:** Mark Stage “QA spec PASS” in `status.md`; dispatch Dev plan round 1.
