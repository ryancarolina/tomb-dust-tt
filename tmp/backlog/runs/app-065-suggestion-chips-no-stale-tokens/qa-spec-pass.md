# QA PASS: spec — round 2

**Task:** app-065-suggestion-chips-no-stale-tokens
**backlog_ticket:** APP-065
**ticket_path:** [tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md](../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md)
**Round:** 2 (re-review after `qa-spec-report-1.md`)
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| TICKET-001 | blocker | **Fixed** | Ticket Expected files include `app/ui/suggestions.py`, `app/tests/test_ui_suggestions.py`; `spec.md` § Affected paths aligned |
| SPEC-001 | blocker | **Fixed** | R3 + domain § Curated map: objection via `not is_equipment_confirm`; AC forbids `EQUIPMENT_OBJECTION_RE` / `is_equipment_objection("I need different gear")`; matches `orchestrator.py` ~1004–1008 |
| SPEC-002 | major | **Fixed** | R2 post-finalize paragraph; `CHARACTER_CREATION` row → `[]` when inactive; orchestrator reads `creation.step` only when `creation.active`; domain § Lookup order mirrors |
| SPEC-003 | major | **Fixed** | R1 requires refresh on success **or** exception; AC + test for `process_turn` raise; domain § Always refresh |
| SPEC-004 | minor | **Fixed** | Domain § Tests lists `test_ui_suggestions.py` + regression pair; file map adds both modules |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` Affected paths (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R6, ticket AC, pytest commands)
- [x] Code traces match repo (stale `if suggestions:` at `app/ui/app.py` 315–317; equipment branch 1004–1008; confirm/objection regex in `creation.py` 93–103)
- [x] AGENTS.md / canon compliance (app-only UI; no mechanics drift)
- [x] Tests/commands listed (`test_ui_suggestions.py`, creation-flow regression)
- [x] registry_gap false — pygame-ui domain spec owns § Suggestion chips
- [x] Every ticket AC row mapped in run spec + domain spec

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 bug; in_progress |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | Including equipment non-confirm and inactive-creation guard |
| Code traces | **PASS** | Unchanged root-cause lines; spec matches handler semantics |
| Expected files ⊆ plan scope | **PASS** | TICKET-001 resolved |
| Equipment chip semantics | **PASS** | SPEC-001 resolved |
| Domain spec sync (R6) | **PASS** | r2 changelog; Tests § pytest commands |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Empty extract → clear chips | R1 always refresh; domain § Always refresh | pytest + manual Bumpy | **PASS** |
| Never show internal tokens | R2–R4; domain § Blocklist | `test_ui_suggestions` | **PASS** |
| Player-facing actions only | R2–R3 maps | builder + blocklist tests | **PASS** |
| Equipment confirm examples | R3 non-confirm path | `is_equipment_confirm` false for objection chip | **PASS** |
| Startup load/new game | R3 SETUP row | manual + unit map | **PASS** |
| Click submits label not token | R5 | manual | **PASS** |
| Domain spec documents rules | R6; domain § Suggestion chips | review | **PASS** |

## Adversarial notes (non-blocking)

1. **Ticket AC wording** — Ticket still cites `_extract_suggestions` empty → clear; run spec correctly mandates removing narration scrape. Dev should implement orchestrator path; ticket AC satisfied by outcome.
2. **Ticket vs spec on `suggest.py`** — Ticket Notes mention mirroring `play/tomb_gm/suggest.py`; run spec Non-goals exclude it. Spec wins for impl.
3. **`creation_active` in builder** — Test plan uses conceptual flag; gating may live only in `get_player_suggestions()` — acceptable per PM r2 reflection.
4. **Resume desync** — `CHARACTER_CREATION` + `creation.active` false → `[]`; no recovery chips (PM flagged; out of ticket AC).
5. **NAME_INPUT resume** — After fix, `NAME` → `[]` clears bad chips; optional explicit test case in plan phase (minor).
6. **Chip order** — “per existing UX” for SETUP; not asserted in test plan (minor).

## Summary

Round 1 blockers **TICKET-001** and **SPEC-001** and majors **SPEC-002** / **SPEC-003** are fully addressed in ticket, `spec.md` (r2), and `tmp/app-pygame-ui-spec.md`. Spec is implementation-ready for Dev plan. Prefer batch order APP-073 before APP-065 impl per batch board.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
