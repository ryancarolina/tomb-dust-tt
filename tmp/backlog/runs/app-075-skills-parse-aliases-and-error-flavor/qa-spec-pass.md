# QA PASS: spec

**Task:** app-075-skills-parse-aliases-and-error-flavor  
**backlog_ticket:** APP-075  
**ticket_path:** tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md  
**Round:** 2  
**domain_spec_creation:** not_needed  
**Reviewer role:** QA (adversarial)

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Ticket valid (`in_progress`) | PASS | `tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md` |
| `registry_gap: false` | PASS | `research-brief.md`; owner `tmp/app-character-creation-spec.md` |
| `domain_spec_creation` | not_needed | No new `tmp/app-*-spec.md` |
| Domain spec matches run spec | PASS | Normative §§ at `tmp/app-character-creation-spec.md` L84–148; run `spec.md` P1–T3 pointers align |
| AC testable | PASS | T1–T3 tables with inputs, assertions, module paths |
| Code traces | PASS | Independent trace confirms r1 root causes still present pre-impl (see below) |
| Expected files ⊆ test plan | PASS | Ticket L40–44 matches domain spec T1/T2/T2b/T3 module table L543–548 |
| AGENTS.md drift policy | PASS | Behavior in domain spec, not changelog-only |

## Round 1 remediation verified

| Finding | r1 severity | r2 status | Evidence |
|---------|-------------|-----------|----------|
| SPEC-001 — normative §§ missing | blocker | **Fixed** | `### Skill slug normalization (APP-075)` L84–132; `### Gated-step flavor on validation failure (APP-075)` L134–148 |
| TICKET-001 — test path not in Expected files | blocker | **Fixed** | Ticket L42–43: `play/tomb_gm/tests/test_creation_gating.py`, `app/tests/test_creation_flow.py` |
| SPEC-002 — P3 error ownership | blocker | **Fixed** | Domain spec L115–132: `format_skill_parse_error` owner, orchestrator call site, example strings |
| SPEC-003 — T2 flavor isolation | major | **Fixed** | Domain spec T2 L561–567: full-narration assertions; V2 skip vs alt path documented |
| SPEC-004 — schools/spells flavor | major | **Fixed** | E1 L145 lists all three `_auto_present_*`; T3 L571–577 required schools path |
| SPEC-005 — positive regression | minor | **Fixed** | T2b L569 promoted required |
| SPEC-006 — non-comma glued input | minor | **Fixed** | P1 L109; non-comma scope L113 |

## Re-review focus (qa-spec-report-1)

1. **Domain § headings exist** — Confirmed L84–148 (resolution order table, nine hyphenated skills, P1–P3, V1–V5/E1–E2, regression target).
2. **Ticket paths match T1/T2/T3** — Confirmed ticket Expected files ↔ domain spec L543–548 ↔ run `spec.md` L47–50, L62–63, L85–86.
3. **P3 examples + builder** — Confirmed helper name, orchestrator wiring requirement, single/multiple unknown examples L126–130.
4. **T2 flavor isolation strategy** — Confirmed L567: forbidden markers on full narration when V2 skips LLM; alt path documented.
5. **Schools/spells in normative § + test** — Confirmed E1 L145; T3 schools required, spells optional mirror L577.

## Independent code traces (pre-implementation baseline)

| Claim | Verified |
|-------|----------|
| `normalize_skill_slug("manacontrol")` → `None` today | Yes (`app/gm/creation.py` L286–296 — no compact pass yet) |
| `_auto_present_skills` ignores `error` for flavor instruction | Yes (`orchestrator.py` L1046–1057 — always first-time ask) |
| Same pattern on schools/spells | Yes (`orchestrator.py` L1059–1086) |
| Generic parse error string at SKILLS | Yes (`orchestrator.py` L941–944 — fixed string, no helper) |
| `format_skill_parse_error` absent (spec-only) | Yes — expected; Dev adds per P3 |
| T1 anchor tests exist | Yes (`play/tomb_gm/tests/test_creation_gating.py` L24–35) |
| T2 pattern reference exists | Yes (`app/tests/test_creation_flow.py` `test_skills_turn_rejects_premature_completion_flavor`) |

## AC mapping (ticket → spec ready)

| Ticket AC | Spec ready? | Requirement IDs |
|-----------|-------------|-----------------|
| Glued aliases / consistent rule | Yes | P1, domain § resolution order |
| Ticket repro parses + advances | Yes | P2, T2b |
| Unknown tokens fail cleanly | Yes | P3, T1 helper row |
| Error-path no congratulate (skills + schools/spells) | Yes | E1–E2, V1–V5, T2, T3 |
| Single response note + table + Awaiting | Yes | V4–V5, E2 |
| Error names unknown skills | Yes | P3, `format_skill_parse_error` |
| Unit + integration tests | Yes | T1, T2, T2b, T3 |
| Domain spec changelog on close | Yes | Changelog L628 documents r2 §§ |

## Verified (checklist)

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates
- [x] Acceptance criteria testable
- [x] Code traces match repo (baseline for planned changes)
- [x] AGENTS.md / drift compliance — normative behavior in domain spec
- [x] Tests/commands listed (`pytest` commands in run `spec.md` L93–96, domain spec T1–T3)
- [x] `registry_gap: false` matches reality

## Notes (non-blocking)

- **T3 spells mirror** is optional (domain spec L577); ticket AC covers schools/spells pattern — schools path is the required minimum; acceptable for close.
- **Domain spec File map** (L597–603) does not yet list `format_skill_parse_error` or `test_creation_gating.py` — Dev may extend at drift check; not a spec gate blocker.
- Run `spec.md` status still `draft (PM round 2)` — orchestrator may flip to `approved` after this PASS.

**Verdict:** PASS — spec is implementation-ready for Dev plan (Stage 3).
