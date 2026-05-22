# Reflection: PM — APP-077 spec

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-exploration-delve-spec.md` § Code-owned status footer (APP-077), `tmp/app-llm-orchestrator-spec.md` § APP-077 cross-link, `reflection-pm.md`

## Completed

- Drafted run-local `spec.md` from research-brief, ticket AC, and dev-team template — requirements F1–F12 mapped to acceptance criteria and nine test cases.
- Added durable § **Code-owned status footer (exploration & combat) (APP-077)** to exploration domain spec: footer field mapping (PM decision on GP + transit), combat `Turn:` segment, compose order with APP-024/022, wiring table, meta strip, idempotency, test matrix.
- Updated APP-024 coordination cross-link to point at new § and orchestrator spec.
- Added orchestrator spec § **Code-owned exploration/combat status footer (APP-077)** — helpers, compose pipeline, `system_prompt.py` before/after table, APP-083 ordering, related tickets.
- Updated domain + orchestrator changelogs, task checklist row, file map, and test commands.

## PM decisions (pinned for Dev)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| GP source | Lowest-slot roster `gold`; append `(+N transit)` when `party.gold_in_transit > 0` | Ticket cited wrong GP lie; transit is party-level but sheet gold is player-visible carry |
| Roster pin | Lowest `slot` entry | Matches ticket notes and `_auto_finalize` single-PC assumption |
| Combat footer | Add `\| Turn: {turn_id} \|` before Awaiting when `status.combat` present | Ticket AC combat subset; keeps exploration line stable |
| Helper home | `format_exploration_status` + strip helpers in `creation.py`; compose in `orchestrator.py` | Reuse APP-073 strip without duplication; mirror `format_creation_status` placement |
| Broad bracket strip | Extend `_LLM_STATUS_TAG_RE` for full exploration footer shape | Research flagged HP/Fortune/GP-only brackets not caught by APP-073 |
| Combat wire | All `_combat_turn` LLM narration paths compose; skip pure code failure/death | Research trace C/D — three `_narrate_text` exits + `_combat_llm_loop` |

## Self-critique

- **Session JSONL unverified** (gitignored) — wrong GP and meta leak evidence relies on ticket/research citations; human playtest should confirm.
- **Broad bracket regex** specified intent but not exact pattern — Dev must implement; QA should adversarially test over-stripping scene prose containing pipe characters.
- **`log_exploration_drift`** left optional (F11) — ticket marks optional; Dev plan may defer without blocking AC.
- **TTS vs display** — noted APP-041 sibling; did not change TTS spec — product may want status spoken later.
- **Double compose idempotency** — spec requires strip-before-append; Dev must verify `all_failed` inner path + `process_turn` does not duplicate footers in practice (research risk).

## Did I miss anything?

- [x] Ticket scope / Expected files — all seven paths + cross-link spec covered
- [x] Domain spec / registry_gap / AGENTS.md — exploration owner; no new domain file
- [x] Code paths not traced — relied on research A–F traces; pinned combat emit gaps in F9
- [x] Tests or AC not mapped — nine tests + AC table in spec.md; domain § Tests
- [x] Research risks — GP ambiguity, combat paths, idempotency, APP-087 footer-only, APP-083 ordering addressed
- [x] `system_prompt.py` — F10 + orchestrator before/after table documented

## Handoff

**Ready for:** QA spec review (adversarial round 1)  
**Escalate human if:** QA rejects GP/transit formatting, demands multi-PC footer aggregation, or requires TTS to speak footer before Dev plan
