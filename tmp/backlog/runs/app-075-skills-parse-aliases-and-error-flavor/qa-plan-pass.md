# QA PASS: plan — round 1

**Task:** app-075-skills-parse-aliases-and-error-flavor  
**backlog_ticket:** APP-075  
**ticket_path:** [tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md](../../app-075-skills-parse-aliases-and-error-flavor.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (spec QA round 2 confirmed `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches plan (`tmp/app-character-creation-spec.md` §§ Skill slug normalization + Gated-step flavor APP-075)
- [x] Acceptance criteria testable (P1–P3, E1–E2, V1–V5, T1–T3 mapped below)
- [x] Code traces match repo (symbols and line refs spot-checked independently)
- [x] AGENTS.md / drift compliance (behavior in domain spec; changelog deferred to Stage 6 per plan §5)
- [x] Tests/commands listed (`pytest` gating + flow; `-k` filter documented)
- [x] Plan files ⊆ ticket Expected files (strict equality on impl set)
- [x] registry_gap N/A at plan gate — spec QA confirmed `false`

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/creation.py` — `_SKILL_COMPACT_MAP`, compact pass, `format_skill_parse_error` | Yes |
| `app/gm/orchestrator.py` — `_creation_table_flavor`, SKILLS wiring, schools/spells/skills flavor skip | Yes |
| `play/tomb_gm/tests/test_creation_gating.py` — T1 | Yes |
| `app/tests/test_creation_flow.py` — T2, T2b, T3 | Yes |
| `tmp/app-character-creation-spec.md` — changelog on close | Yes |

Explicit non-goals honored: no `normalize_spell_id` / school compact; no `_auto_present_race|class|equipment` changes; no `parse_player_skills` return-type change; no APP-059 table work; no edits outside Expected files.

## Code trace audit (independent)

| Claim | File:lines | Verified |
|-------|------------|----------|
| `normalize_skill_slug` ends at hyphen pass, no compact | `creation.py` L286–296 | Yes |
| Comma branch requires exactly 3 slugs | `creation.py` L787–795 | Yes |
| Non-comma path calls `normalize_skill_slug` per discovered token | `creation.py` L797–807 | Yes |
| SKILLS parse fail uses fixed generic error | `orchestrator.py` L939–944 | Yes |
| `_auto_present_skills` always first-time flavor when `error` set | `orchestrator.py` L1046–1057 | Yes |
| Same pattern on schools/spells | `orchestrator.py` L1059–1086 | Yes |
| `validate_skill_picks` failure re-shows with `error=` | `orchestrator.py` L948–958 | Yes (inherits planned V2) |
| `format_skill_parse_error` absent pre-impl | `creation.py` | Yes (planned) |
| T1 anchor tests exist | `test_creation_gating.py` L24–37 | Yes |
| T2 pattern reference exists | `test_creation_flow.py` L133–162 | Yes |
| Golden path INPUTS + apprentice flow | `test_creation_flow.py` L26–35 | Yes |

Planned resolution order (steps 1–5 then compact) matches domain spec L88–99. Orchestrator wiring at L939–944 matches spec P3 owner requirement.

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| Glued aliases / consistent hyphenated rule | §1 P1 compact map (all slugs + alias keys) | T1 `manacontrol`, `sleightofhand` |
| Ticket repro parses + advances | §1 P1 + Flow B | T2b turn 5 → `SPELL_SCHOOLS` |
| Unknown tokens fail cleanly | P3 helper + parse `None` | T1 bogus row; T2 integration |
| Error-path no congratulate (skills + schools/spells) | §3 `_creation_table_flavor` V2 | T2, T3 |
| Single response: note + table + `Awaiting:` | V4–V5 preserved | T2/T3 footer asserts |
| Error names unknown skills when practical | §2 `format_skill_parse_error` | T1 helper row; T2 `bogus` in narration |
| Unit tests normalize/parse | §4.1 T1 | `test_creation_gating.py` |
| Integration invalid skills → no success flavor | §4.2 T2 | monkeypatched stub absent |
| Domain spec changelog on close | §5 Stage 6 | release / drift gate |

### Spec ID map

| ID | Plan locus | Test |
|----|------------|------|
| P1 | `creation.py` compact map + step 5 in `normalize_skill_slug` | T1 glued rows |
| P2 | Comma + non-comma via P1 (no separate parse change) | T1 repro + T2b |
| P3 | `format_skill_parse_error` + orchestrator L939–944 | T1 helper; T2 narration |
| E1–E2, V1–V5 | `_creation_table_flavor` on skills/schools/spells | T2, T3 |
| T1 | `test_creation_gating.py` extensions | pytest gating |
| T2 | `test_skills_error_path_skips_congratulatory_flavor` | flow |
| T2b | `test_skills_glued_alias_advances_to_schools` | flow (after WS1) |
| T3 | `test_schools_error_path_skips_congratulatory_flavor` | flow |

## Workstream / dependency review

| WS | Scope | Gate |
|----|-------|------|
| WS1 | `creation.py` P1 + P3 + T1 | gating pytest green |
| WS2 | `orchestrator.py` E1 + T2/T2b/T3 | T2b after WS1; T2/T3 can land with WS2 |

Dependency ordering is correct: T2b requires compact parse; T2 (`bogus`) is stable without WS1 and validates P3 + V2 together once WS2 lands.

## Verification commands (plan § Verification)

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_flow.py -q -k "skill or school or glued"
python -m pytest app/tests/test_creation_flow.py -q
```

Pre/post smoke (`parse_player_skills` one-liner) is appropriate for local repro.

## Notes (non-blocking)

- **T3 input `pyromancy`:** Valid school id with wrong count (apprentice needs 2) — `parse_player_schools` returns `None` and triggers generic schools error; suitable for flavor-isolation test, not “unknown school” messaging (out of APP-075 P3 scope).
- **P3 non-comma failures:** `format_skill_parse_error` correctly scoped to comma path per domain spec L119–130; non-comma parse failures keep generic count message until a follow-up ticket.
- **Forbidden markers list:** Plan T2 uses case-insensitive `smart choices` / `excellent` / `moving on` — aligns with domain spec T2 L567; Dev may extend if flaky LLM stubs appear in tests.
- **Optional SPELLS mirror:** Plan marks optional; ticket AC satisfied by schools path (T3 required).
- **Line refs:** Flow A cites SKILLS block `933–944`; parse-failure wiring is `939–944` — acceptable ±few lines.

**Verdict:** PASS — plan is implementation-ready for workstreams (Stage 4 after `impl-check`).
