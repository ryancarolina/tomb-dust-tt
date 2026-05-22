# Reflection: Research — APP-041 strip-status-tags-before-tts

**Agent:** Research  
**Round:** 1  
**Deliverables:** research-brief.md

## Completed

- Read AGENTS.md, ticket APP-041, domain spec `app-tts-narration-spec.md`, dev-team research template.
- Traced narration → TTS path: `orchestrator.process_turn` → `ui/app.py` `_process_turn` → `parse_scene` → `_speak_narration` → `speak_scene` → `synthesize_to_file`.
- Traced creation compose path: `_compose_creation_narration` + `strip_llm_status_tags` (upstream only).
- Read `play/tomb_gm/services/tts/scene.py` strip pipeline and `queue.py` line selection.
- Ran local `parse_scene` leak matrix with representative status-tag fixtures.
- Documented registry_gap false with master-spec citation.

## Self-critique

- Did not run full PyGame manual listen test — relied on programmatic `parse_scene` output; audible edge cases (e.g. partial bracket mid-sentence with nested pipes) not exhaustively probed.
- Assumed `lines_from_payload` does not re-sanitize — verified in `queue.py` but did not trace malformed dict payloads from future callers.
- APP-073 implementation state not re-read line-by-line; brief treats it as compose-only based on grep + prior run brief.

## Did I miss anything?

- [x] Ticket scope / Expected files — flagged path mismatch (`app/gm/tts` vs `play/tomb_gm/services/tts/`)
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths not traced — CLI speak path noted; not primary AC
- [x] Tests or AC not mapped — gap in `test_tts_scene.py` documented
- [ ] Session log replay — no gitignored log opened for audio bug repro

## Handoff

**Ready for:** PM spec draft (define strip rules, Expected files, test plan; coordinate APP-077/073 boundaries)  
**Escalate human if:** product wants status footers stripped from **display** panel too — out of ticket AC today
