# Reflection: Research — APP-027 validate-monster-id-combat

**Agent:** Research  
**Round:** 1  
**Deliverables:** `research-brief.md`, `reflection-research.md`

## Completed

- Read ticket APP-027, domain spec `app-combat-play-spec.md`, dev-team research template, and APP-028 research for overlap context.
- Traced five entry paths: exploration `start_combat`, beat `combat_trigger`, `pending_start`, CLI `combat start`, and `ContentService.load_monster` reference pattern.
- Confirmed engine validates via `load_monster_json` before DB write; bridge maps exceptions to `{ok: false}`; APP-028 covers all-failed narration strip.
- Identified gaps: no `validate_tool_args` for `start_combat`, weak engine/bridge integration tests, CLI exception vs structured error, canon drift (`hollow-knight` markdown + beat regex, no JSON), mixed-tool narrate risk.
- Live-probed `start_combat` with `hollow-knight:1` — engine raises `FileNotFoundError` (bridge would catch in app context).
- Set `registry_gap: false` with app-combat-play-spec + app-master-spec citation.

## Self-critique

- Did not run full pytest suites — relied on existing test file reads and one live engine probe; QA should confirm green baselines.
- Mixed-tool fiction leak is inferred from `_llm_loop` depth+1 behavior, not reproduced with an integration test in this pass.
- Beat/content drift (`MONSTER_ID_RE`, `hollow-knight.md`) noted as risk but not deeply traced into encounter tables or site JSON links — may underestimate how often bad ids reach `combat_trigger`.

## Did I miss anything?

- [x] Ticket scope / Expected files — stayed within `app/gm/` + `play/tomb_gm/` analysis
- [x] Domain spec / registry_gap / AGENTS.md — combat spec owns; no registry gap
- [x] Code paths not traced — `_combat_llm_loop_inner` wrong-tool `start_combat` covered via APP-028 T9; empty specs edge noted
- [x] Tests or AC not mapped — listed engine/app gaps and commands
- [ ] Session log replay — not available (gitignored)
- [ ] APP-030 fixture details — referenced as test home but not read

## Escalation

- **PM:** Decide AC scope — validation-only + tests vs also blocking mixed-tool combat fiction; whether empty `monster_specs` is invalid; whether to fix `tools.py` / beat regex examples in this ticket or defer to content ticket.
- **Dev:** Prefer reusing `ContentService.load_monster` blocker pattern vs extending `load_monster_json`; align CLI with bridge `{ok: false}` if engine stops raising.
