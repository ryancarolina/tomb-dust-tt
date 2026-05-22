# QA PASS: spec — round 2

**Task:** app-037-block-map-travel-during-creation
**backlog_ticket:** APP-037
**ticket_path:** [tmp/backlog/app-037-block-map-travel-during-creation.md](../../app-037-block-map-travel-during-creation.md)
**Round:** 2 (re-review after `qa-spec-report-1.md`)
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| TICKET-001 | blocker | **Fixed** | Ticket Expected files now include `app/gm/orchestrator.py` and `app/tests/test_ui_map_creation_gate.py`; matches run `spec.md` § File map (six impl paths + domain spec) |
| SPEC-001 | major | **Fixed** | R1 AC mandates `Orchestrator.is_map_travel_blocked()` in `app/gm/orchestrator.py`; domain § Implementation files lists same path set — no orchestrator-or-`app.py` ambiguity |
| SPEC-002 | minor | **Fixed** | R2 AC names `_process_turn` `finally` enriched status queue alongside `_queue_turn_suggestions` (APP-065 parity); domain § Travel-blocked signal UI refresh row matches |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § File map (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R7, ticket AC, pytest commands)
- [x] Code traces match repo (map click → `_submit` at `app/ui/app.py` 68–71; status success-only L299–300; suggestions in `finally` L319–320; stub `handle_click` at `map_view.py` 94–95; init status push `_init_orchestrator` L126)
- [x] AGENTS.md / canon compliance (UI defense-in-depth; APP-008 engine gate unchanged)
- [x] Tests/commands listed (`test_ui_map_creation_gate.py`, `test_ui_suggestions.py`, `test_creation_flow.py`)
- [x] registry_gap false — pygame-ui domain spec owns § Map travel during creation
- [x] Every ticket AC row mapped in run spec + domain spec

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | R1–R7 + dual-condition desync guard |
| Code traces | **PASS** | Exception-path asymmetry correctly targeted by R2 |
| APP-008 mirror | **PASS** | Three-layer defense documented; typed travel non-goal |
| Expected files ⊆ plan scope | **PASS** | TICKET-001 resolved |
| PM artifact consistency | **PASS** | SPEC-001 resolved — ticket, run spec, domain § Implementation files aligned |
| AGENTS.md / drift policy | **PASS** | Domain draft + r2 changelog; finalize on close |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Travel disabled when `creation.active` or creation-scoped `awaiting` | R1 dual condition; domain § Travel-blocked signal | unit + integration tests | **PASS** |
| Tooltip / label *"Finish Registry intake first"* | R4; domain § Player copy | MapView state + headless helper | **PASS** |
| Re-enable after finalize / live delver on surface | R6; domain § Re-enable | `test_creation_flow` regression | **PASS** |
| Map still displays hub cell; travel only blocked | R4–R5; domain intro paragraph | draw + `update_position` AC | **PASS** |
| Compatible with APP-062 narrowed map column | R5, R7; domain § Layout (APP-062) | resize AC | **PASS** |
| Domain spec sync | R7; domain § Map travel during creation | review | **PASS** |

## Adversarial notes (non-blocking)

1. **Path prefix convention** — Domain bottom § File map uses `ui/` relative paths; ticket/run spec use `app/` prefix. Matches APP-065 precedent; hooks use ticket Expected files.
2. **Helper naming** — `_queue_turn_status(turn_id)` in R2 is guidance; AC is outcome-based (blocked overlay refreshes after turn errors).
3. **APP-036 overlap** — Creation step badge may share enriched status payload via Option A; orthogonal ticket; compatible.
4. **Resume edge** — `CHARACTER_CREATION` + non-empty roster + inactive creation → travel allowed (APP-065 parity); not deep-replayed against APP-018 restore scenarios in this round.
5. **Typed travel** — Input-box `travel to …` remains orchestrator-gated only; explicit non-goal in run spec.

## Summary

Round 1 blocker **TICKET-001**, major **SPEC-001**, and minor **SPEC-002** are fully addressed in ticket, `spec.md` (r2), and `tmp/app-pygame-ui-spec.md`. Spec is implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
