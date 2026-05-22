# Reflection: PM — APP-041 strip-status-tags-before-tts

**Agent:** PM  
**Round:** 1  
**Deliverables:** `spec.md`, `tmp/app-tts-narration-spec.md` (§ APP-041), `reflection-pm.md`

## Completed

- Wrote run-local `spec.md` with problem/leak matrix, R1–R4, test table, corrected expected files (`scene.py` + tests, not fictional `app/gm/tts` path).
- Updated domain spec: display vs speak split, `_strip_status_tags` in `parse_scene` after `_strip_ui`, file map, checklist item, pytest commands.
- Mapped ticket AC to engine choke point; documented non-goals (APP-073/077/042) and no `play/` → `app/gm` import.
- `registry_gap: false` — no new domain spec row; extended existing TTS owner.

## Self-critique

- Regex edge cases (AV-GRID vs `Location:` footer) need Dev/QA adversarial review — spec says preserve coordinates in fiction but whole-line `Location:` drops; ambiguous lines like `Location: 32-C` without pipes may need fixture in tests.
- Did not update ticket **Expected files** in `app-041-strip-status-tags-before-tts.md` — flagged in spec; orchestrator or Dev should amend ticket before impl if hooks enforce Expected files strictly.
- `_strip_markup` underscore→space interaction (“SKILL INPUT” residue) called out in research; spec requires strip **before** markup — Dev plan should confirm order in `parse_scene`.

## Did I miss anything?

- [x] Ticket scope / Expected files — corrected in spec; ticket file still stale
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths — research traces A–B incorporated
- [x] Tests or AC mapped — leak matrix → pytest table
- [ ] CLI bypass check — delegated to Dev plan (R3 note only)

## Handoff

**Ready for:** QA spec gate (adversarial review of `spec.md` + domain spec § APP-041)  
**Escalate human if:** QA blocks on ticket Expected files mismatch — human/orchestrator should edit ticket paths to `play/tomb_gm/services/tts/scene.py` and `play/tomb_gm/tests/test_tts_scene.py`
