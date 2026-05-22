# Reflection: PM — APP-075 skills-parse-error-flavor (round 2)

**Agent:** PM  
**Round:** 2 (QA spec r1 remediation)  
**Input:** [qa-spec-report-1.md](./qa-spec-report-1.md) — FAIL (SPEC-001, TICKET-001, SPEC-002 blockers)  
**Deliverables:** domain spec normative §§, ticket Expected files, run `spec.md` r2, this reflection

## QA findings addressed

| ID | Severity | Resolution |
|----|----------|------------|
| SPEC-001 | blocker | Added full **§ Skill slug normalization (APP-075)** and **§ Gated-step flavor on validation failure (APP-075)** to `tmp/app-character-creation-spec.md` under `## Spec` — resolution order table, P1–P3, V1–V5/E1–E2, nine hyphenated skills, non-comma scope. Changelog corrected to “spec r2”. |
| TICKET-001 | blocker | Ticket Expected files now explicitly authorize `play/tomb_gm/tests/test_creation_gating.py` (T1) and `app/tests/test_creation_flow.py` (T2/T2b/T3). Removed ambiguous `test_creation_parsers.py` fork. Domain spec T1 table matches. |
| SPEC-002 | blocker | Named **`format_skill_parse_error`** in `creation.py` as P3 owner; orchestrator SKILLS branch must call it. Normative example strings for single/multiple unknown tokens. |
| SPEC-003 | major | T2 flavor isolation: assert forbidden congratulation markers on **full narration** when V2 skips LLM; document V2 alt correction-only path. |
| SPEC-004 | major | T3 added for `_auto_present_schools` error flavor; E1 lists all three `_auto_present_*` symbols in normative §. |
| SPEC-005 | minor | T2b promoted to **required** positive regression (ticket repro → `SPELL_SCHOOLS`). |
| SPEC-006 | minor | Non-comma glued input declared in-scope via P1 in `normalize_skill_slug`. |

## Decisions made

1. **V2 preferred path:** empty flavor on `error=` (skip `_narrate_flavor`) — simplest, deterministic for T2/T3; correction-only LLM allowed but secondary.
2. **P3 helper name:** `format_skill_parse_error` — keeps `parse_player_skills` API stable; orchestrator owns the call site, helper owns token diagnostics.
3. **Test placement:** T1 stays in existing gating module (research + prior tests); integration stays in `test_creation_flow.py` per APP-070 pattern — no new `test_creation_parsers.py` unless Dev splits later with ticket amendment.

## Self-critique

- Example error strings use English prose shape, not locked punctuation — Dev may tune clerk voice if `bogus` / token list remains visible.
- T3 spells mirror marked optional — ticket AC emphasizes schools/spells alignment; schools path is required minimum.
- Did not re-run QA spec review in this round — handoff expects adversarial re-review against re-review focus list in qa-spec-report-1.

## Handoff

**Ready for:** QA spec review round 2 — verify domain § headings exist (not changelog-only), ticket paths match T1/T2/T3, P3 examples + helper ownership clear.

**Escalate human if:** QA mandates non-empty correction flavor (V2 alt only) or wants spell-id glued parsing in APP-075 scope.
