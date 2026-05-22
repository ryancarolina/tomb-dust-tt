# Reflection: PM — APP-041 strip-status-tags-before-tts (r2)

**Agent:** PM  
**Round:** 2 (QA spec report 1 remediation)  
**Deliverables:** `spec.md`, `tmp/app-tts-narration-spec.md`, `tmp/backlog/app-041-strip-status-tags-before-tts.md`, `reflection-pm-r2.md`

## QA findings addressed

| ID | Fix |
|----|-----|
| **TICKET-001** | Ticket Expected files → `play/tomb_gm/services/tts/scene.py`, `play/tomb_gm/tests/test_tts_scene.py`, `tmp/app-tts-narration-spec.md`; run spec § Expected files aligned (removed stale placeholder note). |
| **TICKET-002** | Second ticket AC: panel still shows Location / Phase / Awaiting; strip on speak payload only. Run spec AC mapping updated. |
| **SPEC-001** | R3 scoped: `cmd_speak --text` / `--lines` documented as **dev-only non-goal** (bypass `parse_scene`); in-scope paths are `--scene` / `cmd_narrate push`. Non-goals table + domain spec out-of-scope bullet. |

## Decisions

- **CLI bypass:** Chose non-goal over requiring strip on `--text`/`--lines` — player path is `app/ui/app.py` → `parse_scene`; dev CLI is not acceptance surface for APP-041.
- **SPEC-002 (inline unbracketed mid-line):** Not expanded in r2 — whole-line + bracket/inline `Awaiting` covered; residual mid-sentence `Location: … | Phase: …` left as low-probability; Dev may add fixture if QA impl flags a leak.

## Self-critique

- Ticket Notes still mention grooming partial state — accurate; no change until impl closes.
- Domain spec already had display/speak split; r2 only added CLI non-goal line for parity with run spec.

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001 resolved
- [x] Domain spec / registry_gap — extended out-of-scope; changelog r2
- [x] Code paths — R3 cites `queue.py` lines-when-set behavior explicitly
- [x] Tests or AC mapped — panel AC on ticket; pytest paths in Expected files
- [x] QA round 1 blockers — TICKET-001, TICKET-002, SPEC-001 addressed

## Handoff

**Ready for:** QA spec re-review (round 2)

**Escalate human if:** Product wants dev `cmd_speak --text` to strip status (new ticket; not APP-041).
