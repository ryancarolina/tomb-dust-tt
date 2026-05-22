# QA PASS: spec — round 2

**Task:** app-041-strip-status-tags-before-tts  
**backlog_ticket:** APP-041  
**ticket_path:** [tmp/backlog/app-041-strip-status-tags-before-tts.md](../../app-041-strip-status-tags-before-tts.md)  
**Round:** 2  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 remediation verified

| Finding | Round 1 | Round 2 |
|---------|---------|---------|
| **TICKET-001** Expected files / hook allow-list | FAIL — stale `app/gm/tts` placeholder | **PASS** — ticket lists `play/tomb_gm/services/tts/scene.py`, `play/tomb_gm/tests/test_tts_scene.py`, `tmp/app-tts-narration-spec.md`; matches `spec.md` § Expected files |
| **TICKET-002** Panel AC on ticket | WARN — display/speak split spec-only | **PASS** — ticket AC: panel shows Location / Phase / Awaiting; strip on TTS speak payload only |
| **SPEC-001** R3 CLI bypass | FAIL — “expected: no bypass” contradicted repo | **PASS** — R3 + Non-goals document `cmd_speak --text` / `--lines` as dev-only non-goal; domain spec § Out of scope aligned |

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-tts-narration-spec.md`)
- [x] Acceptance criteria testable (both ticket ACs mapped in `spec.md` § Acceptance criteria mapping)
- [x] Code traces match repo (display/speak split, `queue.py` L35 `lines` vs `parse_scene`, leak matrix probes pre-impl)
- [x] AGENTS.md / canon compliance (engine-owned strip in `play/`; no cross-import from `app/gm/creation.py`)
- [x] Tests/commands listed (`test_tts_scene.py` leak matrix + pytest command)
- [x] registry_gap false — domain spec § Status tag strip before TTS (APP-041) owns behavior
- [x] Ticket Expected files ⊆ run spec § Expected files (identical triple)

## AC coverage (ticket → spec → domain)

| Ticket AC | spec.md | Domain spec |
|-----------|---------|-------------|
| Strip status tags before TTS speak payload | R1 — `_strip_status_tags` in `parse_scene` pipeline; test plan leak matrix | § Strip scope; § Choke point |
| Panel still displays status tags; strip on speak only | R2 — `narration_text` raw; no `app/` strip | § Display vs speak table |

## Code evidence (pre-implementation baseline)

| Claim | Evidence |
|-------|----------|
| Raw narration → panel; parsed lines → TTS | `app/ui/app.py` L294–297 |
| `speak_scene` uses `lines` when set, else `parse_scene(text)` | `queue.py` L35 |
| Inline `Awaiting: SKILL_INPUT` still spoken today | Probe: `'The clerk nods. Awaiting: SKILL INPUT'` (underscore → space via `_strip_markup`) |
| Whole-line `Phase: preparation` still spoken | Probe: unchanged |
| Unclosed bracket fragment still spoken | Probe: full fragment retained |
| AV-GRID fiction preserved | Probe: `32-C-UG-1` line passes |
| CLI `--text` bypasses `parse_scene` | `cmd_speak.py` L134–143 → `lines=[{"text": …}]` |
| Holt regression fixture exists | `test_tts_scene.py` HOLT_SCENE |

## Adversarial notes (non-blocking)

1. **SPEC-002 (deferred)** — Inline unbracketed `Location: … | Phase: …` mid-sentence not in R1; PM r2 accepted as low-probability residual. Dev may add fixture if impl QA finds a leak; not a spec gate blocker.
2. **`cmd_speak --beat-id`** — Pre-built `speak_lines` bypasses `parse_scene` (same class as `--lines`); not named in Non-goals but covered by “dev bypass / canonical play uses app → `parse_scene`” intent.
3. **Research brief** — Still mentions optional `app/ui/app.py` wiring; run spec correctly forbids duplicate UI strip (R2). Research artifact only.

## Summary

PM r2 resolved all round 1 blockers. Ticket, run spec, and domain spec are aligned on scope, Expected files, display/speak split, CLI non-goals, test plan, and non-goals vs APP-073/077/042. Spec is implementation-ready for Dev plan (stage 3).

## Re-review focus

_None — proceed to Dev plan + QA plan._
