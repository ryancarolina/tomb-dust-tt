# QA PASS: spec — round 2

**Task:** app-023-friendly-travel-av-grid
**backlog_ticket:** APP-023
**ticket_path:** [tmp/backlog/app-023-friendly-travel-name-to-av-grid.md](../../app-023-friendly-travel-name-to-av-grid.md)
**Round:** 2 (re-review after `qa-spec-report-1.md`)
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| SPEC-001 | blocker | **Fixed** | Domain § Matching adds apostrophe folding (strip `'`/`'` before substring + slug); § Scoring proof table pins `kings road` @ `32-C` → `33-C` at scores **60** / **70** without exit `tradeRoute`. Verified with standalone scoring script: score **70** (was **0** without fold). Live JSON: `33-C` `displayName` "King's Road (east bend)", no `tradeRoute`; `32-C` excluded from candidate set. |
| TICKET-001 | blocker | **Fixed** | Ticket Expected files now include `beat.py`, `test_world.py`, `test_beat.py`, optional `tools.py`; aligned with `spec.md` § Affected paths / R6. |
| SPEC-002 | blocker | **Fixed** | Domain § Layered fallback: pass 1 surface-only; pass 2 scores non-surface `legal_exits` with same table; single match → `USE_ENTER_DUNGEON`. T5 + domain UG row pinned to **`USE_ENTER_DUNGEON`** for `undercrypt` → `32-C-UG-1` (score **70** verified). |
| SPEC-003 | major | **Fixed** | Domain § Wiring `process_beat` row maps **`UNKNOWN_ADDRESS` → `NO_DESTINATION`**; pass through `AMBIGUOUS_ADDRESS` / `USE_ENTER_DUNGEON`. T7 + domain beat error-map test row added. |
| SPEC-004 | minor | **Fixed** | `spec.md` Non-goals + R1 naming note distinguish engine **`resolve_surface_address`** from `build/tools/av_grid.py:resolve_surface`. |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-exploration-delve-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` Affected paths (hook allow-list complete for code paths)
- [x] Acceptance criteria testable (R1–R7, T1–T7, King's Road + undercrypt fixtures)
- [x] Code traces match repo (`bridge.world_travel` passthrough; `beat.py` regex-only dest + `NO_DESTINATION`; `world.legal_exits` includes `33-C` adjacent + `32-C-UG-*` children from `32-C`)
- [x] AGENTS.md / canon compliance (exit-scoped resolver; no global name index; optional JSON change deferred)
- [x] Tests/commands listed (`test_world.py`, `test_beat.py`, `test_site_resolve.py` regression)
- [x] registry_gap false — exploration domain spec owns § Friendly surface travel resolution (APP-023)
- [x] Every ticket AC row mapped in run spec + domain spec
- [x] Scoring proof reproducible against live `av-grid.json` with documented normalization

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | Primary fixture `kings road` → `33-C` mathematically consistent |
| Code traces | **PASS** | Unchanged root-cause lines; spec wiring matches |
| Expected files ⊆ plan scope | **PASS** | TICKET-001 resolved |
| Layered fallback algorithm | **PASS** | SPEC-002 resolved; T5 single outcome |
| Beat error enum mapping | **PASS** | SPEC-003 resolved |
| Domain spec sync | **PASS** | PM r2 changelog; § APP-023 complete |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Map friendly place names to AV-GRID for surface travel via engine `world.py` | R1–R4; T1/T2/T6; domain King's Road row | pytest + human Breley hub | **PASS** |
| Spec sync on close | Domain § APP-023 + changelog; optional `tools.py` | drift gate Stage 6 | **PASS** (intent) |

## Adversarial notes (non-blocking)

1. **T4 ambiguity fixture** — Still no concrete grid cell pinned for two tied surface exits; Dev/PM should pick one in plan phase (same deferral as round 1; algorithm specified).
2. **Apostrophe variants** — PM r2 notes Unicode apostrophe edge cases; fold set may grow in impl if playtest finds gaps.
3. **`app-gamebridge-spec.md`** — Not updated pre-impl; deferred to ticket close per normal drift workflow (same as APP-022).
4. **Rationale vs layered fallback** — § Candidate rationale still says layered exits belong to `enter_dungeon`; § Layered fallback clarifies travel resolver returns `USE_ENTER_DUNGEON` without surface travel — consistent in behavior, slightly redundant prose.

## Summary

Round 1 blockers **SPEC-001**, **TICKET-001**, **SPEC-002** and majors **SPEC-003** / minor **SPEC-004** are fully addressed in ticket, `spec.md` (PM r2), and `tmp/app-exploration-delve-spec.md`. Primary acceptance fixture is provably testable. Spec is implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
