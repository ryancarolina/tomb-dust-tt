# Reflection: Research — APP-031 transcript sanitize

**Agent:** Research
**Round:** 1
**Deliverables:** research-brief.md

## Completed

- Read AGENTS.md, ticket APP-031, domain spec § Problem/open work, APP-032 pairing ticket.
- Traced all six `chat_completion` call sites in `orchestrator.py` and three tool loops (`_llm_loop`, `_creation_llm_loop`, `_combat_llm_loop_inner`).
- Confirmed `openrouter.py` has no transcript sanitize despite domain spec file map.
- Mapped APP-028 TOOL FAILED system injection ordering as latent strict-provider risk.
- Cross-referenced APP-080 Holt session research for corrupted multi-invoke tool args.
- Set `registry_gap: false` with app-master-spec + orchestrator spec ownership.
- Documented APP-031 (prevent) vs APP-032 (retry) boundary and test suggestions.

## Self-critique

- **Session JSONL not re-read locally** — `app/logs/` empty in workspace; relied on APP-080 research-brief for 2026-05-20 Holt trace. A direct grep for `400` / `malformed` in logs would strengthen evidence if logs exist on dev machine.
- **System-before-tool ordering** is hypothesized from OpenAI invariants + code read; not reproduced against live Google 400 in this environment.
- **Invalid `tool_calls` structure** from merged XML is inferred from ticket grooming + error string; exact malformed payload shape not captured in repo fixtures yet.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator.py only; noted openrouter spec drift
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths not traced — narrate-only paths marked low risk
- [x] Tests or AC not mapped — suggested cases + mock pattern refs
- [ ] APP-034 logging interaction — mentioned briefly; not deep-traced
- [ ] Whether `build_messages` history could ever include dict roles beyond user/assistant — typed as `list[dict[str, str]]`; assumed safe

## Handoff

**Ready for:** PM spec draft (§ Transcript sanitize requirements, wire points, APP-032 split, test plan)
**Escalate human if:** Product wants sanitize in `openrouter.py` instead of orchestrator — requires ticket Expected files update before Dev impl
