# QA PASS: spec — round 2

**Task:** app-026-combat-attack-gating  
**backlog_ticket:** APP-026  
**ticket_path:** [tmp/backlog/app-026-combat-attack-gating.md](../../app-026-combat-attack-gating.md)  
**Round:** 2 (re-review after `qa-spec-report-1.md`)  
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| SPEC-001 | blocker | **Fixed** | `spec.md` R3 + domain § Wire points: `action.upper().strip() == "ATTACK"`; **Case rule** explains anti-pattern; **G8** asserts lowercase `"attack"` hits gate before bridge |
| SPEC-002 | minor | **Fixed** | G4 pass criteria explicit: `error: "no active combat for session"`; R3 notes ATTACK path runs gate first |
| SPEC-003 | minor | **Fixed** | G5 setup: monkeypatch `turn_id="pc1"` with `initiative=[{id:"m1"}]` |
| SPEC-004 | minor | **Fixed** | **G6b** — combat-loop happy path; gate passes → `bridge.combat_action` called once |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-combat-play-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` Affected paths (`orchestrator.py`, optional `tools.py`, `test_combat_attack_gating.py`)
- [x] Acceptance criteria testable (R1–R5, G1–G8 + G6b, pytest commands)
- [x] Code traces match repo (engine `action.upper().strip()` at `combat.py` 714–715; app `tool_args._normalize_combat_action` does not uppercase ~129–135; exploration `combat_attack` direct bridge ~2530–2531; combat loop partial pre-check ~2323–2328)
- [x] AGENTS.md / canon compliance (app-layer gate only; engine validation unchanged; non-goals scoped)
- [x] Tests/commands listed (`test_combat_attack_gating.py`, APP-028 regression, engine tests unchanged)
- [x] registry_gap false — combat domain spec owns § Combat attack gating (APP-026)
- [x] Every ticket AC row mapped in run spec + domain spec (G8 closes lowercase initiative bypass)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | Including lowercase ATTACK path (G8) |
| Code traces | **PASS** | R3 gate condition mirrors engine normalization |
| Expected files ⊆ plan scope | **PASS** | Domain spec sync on close per ticket § Spec sync |
| ATTACK gate completeness | **PASS** | SPEC-001 resolved — case-normalized gate + G8 |
| Domain spec sync | **PASS** | § APP-026 mirrors run spec; r2 changelog dated |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Before attack: require `status.combat` | R1 step 1; R2/R3; G1, G4 | pytest + mock bridge not called | **PASS** |
| Attacker in initiative | R1 step 3; G2, G5, G8, G6b | unit + integration mocks | **PASS** |
| Wire both attack paths | R2, R3; domain wire table | G1, G4–G6, G6b, G8 | **PASS** |
| Spec sync on close | Ticket § Spec sync; domain § APP-026 | review | **PASS** |

## Adversarial notes (non-blocking)

1. **G6b fixture detail** — Spec requires turn match but does not enumerate minimal `status` dict keys; Dev plan should list required fields (`combat`, `turn_id`, `initiative`, `combatants`).
2. **Dual no-combat strings** — Non-ATTACK combat actions may still return `"no active combat"` from existing `_execute_combat_action` check; ATTACK path gate returns `"no active combat for session"` — documented in R3; acceptable for APP-028 alignment.
3. **G7 regression** — “Re-run or import T4” is loose; regression command `test_combat_failure_narration.py -q` is sufficient for Dev plan.
4. **Attacker resolution duplication** — R1 mirrors engine `_resolve_combatant_id` semantics; whether to extract shared helper is Dev discretion (PM r1 reflection).
5. **Research brief stale wire** — `research-brief.md` still mentions `action == "ATTACK"`; run spec + domain spec are authoritative for implementation.

## Summary

Round 1 blocker **SPEC-001** and minors **SPEC-002** / **SPEC-003** / **SPEC-004** are fully addressed in `spec.md` (PM r2), `reflection-pm-r2.md`, and `tmp/app-combat-play-spec.md`. Case-normalized ATTACK gating closes the lowercase initiative bypass identified in round 1. Spec is implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
