# QA PASS: implementation — round 1

**Task:** app-075-skills-parse-aliases-and-error-flavor  
**backlog_ticket:** APP-075  
**ticket_path:** [tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md](../../app-075-skills-parse-aliases-and-error-flavor.md)  
**Round:** 1  
**domain_spec:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md) § Skill slug normalization (APP-075), § Gated-step flavor on validation failure (APP-075)

## Verdict

**PASS** — APP-075 acceptance criteria and run `spec.md` P1–P3, E1–E2, V1–V5, T1–T3 are satisfied in code and automated tests.

## Automated tests

```text
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
.............                                                            [100%]
13 passed in 0.03s

python -m pytest app/tests/test_creation_flow.py -q -k "skill or school or glued"
....                                                                     [100%]
4 passed, 4 deselected in 1.12s

python -m pytest app/tests/test_creation_flow.py -q
........                                                                 [100%]
8 passed in 1.75s
```

| Module | APP-075 tests | Result |
|--------|---------------|--------|
| `play/tomb_gm/tests/test_creation_gating.py` | T1 — `test_normalize_skill_slug`, `test_parse_player_skills_comma_list`, `test_format_skill_parse_error` | ✓ |
| `app/tests/test_creation_flow.py` | T2 — `test_skills_error_path_skips_congratulatory_flavor` | ✓ |
| `app/tests/test_creation_flow.py` | T2b — `test_skills_glued_alias_advances_to_schools` | ✓ |
| `app/tests/test_creation_flow.py` | T3 — `test_schools_error_path_skips_congratulatory_flavor` | ✓ |
| Regression | `test_full_creation_apprentice_caster`, APP-070 `test_skills_turn_rejects_premature_completion_flavor` | ✓ (full suite) |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| `normalize_skill_slug` / `parse_player_skills` accept glued multi-word forms | `creation.py` L60–73 `_SKILL_COMPACT_MAP`; L312–314 compact pass after exact/alias/hyphen; T1 `manacontrol`, `sleightofhand` | ✓ |
| `spellcasting, medicine, manacontrol` → 3 slugs + SKILLS advance | `parse_player_skills` comma branch; T1 + T2b integration → `SPELL_SCHOOLS` | ✓ |
| Invalid/unknown tokens fail cleanly (no silent drop) | `parse_player_skills` returns `None`; `format_skill_parse_error` names unknown parts | ✓ |
| Error-path `_auto_present_skills\|schools\|spells`: no congratulate / confirm / advance tone | `_creation_table_flavor` L1070–1071 returns `""` when `error` set; T2/T3 assert stub + forbidden markers absent | ✓ |
| Single response: note + table + correct `Awaiting:` | `_auto_present_*` L1079/1094/1106 `**Note:**` prefix + `format_*_table` + `_compose_creation_narration` footer; T2/T3 assert footers | ✓ |
| Error names unknown skills when practical | `format_skill_parse_error` L874–878; orchestrator L962–964; T1 + T2 `bogus` in narration | ✓ |
| Unit tests for alias cases | `test_creation_gating.py` extended per domain spec T1 table | ✓ |
| Integration: invalid skills → no success flavor; step unchanged | `test_skills_error_path_skips_congratulatory_flavor` | ✓ |
| Domain spec § parsers + § error flavor updated | Domain spec L84–148, L541–577 present | ✓ (changelog “done” row pending at `release --done`) |

## Spec P1–P3, E1–E2, V1–V5 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **P1** | Compact pass after exact/alias/hyphen | `normalize_skill_slug` L305–314; map built L64–73 | ✓ |
| **P2** | Comma path + ticket repro | `parse_player_skills` comma branch; T1/T2b | ✓ |
| **P3** | `format_skill_parse_error` + orchestrator wiring | L866–879; `orchestrator.py` L962–964 | ✓ |
| **E1** | V1–V3 on skills, schools, spells | `_creation_table_flavor` used by all three `_auto_present_*` | ✓ |
| **E2** | Post-validate errors inherit V2 | `validate_skill_picks` fail path L979 → `_auto_present_skills(..., error=err)` uses same helper | ✓ |
| **V2** | Skip `_narrate_flavor` when `error` set | `_creation_table_flavor` L1070–1071 | ✓ |
| **V4** | Body: `**Note:**` + table unchanged | L1079, 1094, 1106 | ✓ |
| **V5** | Footer matches current step | T2 `SKILLS_INPUT`; T2b/T3 `SPELL_SCHOOLS_INPUT` | ✓ |
| **T1** | Parser unit cases | `test_creation_gating.py` | ✓ |
| **T2** | Invalid skills error flavor | `test_skills_error_path_skips_congratulatory_flavor` | ✓ |
| **T2b** | Glued alias advances | `test_skills_glued_alias_advances_to_schools` | ✓ |
| **T3** | Schools error flavor | `test_schools_error_path_skips_congratulatory_flavor` | ✓ |

## Independent code traces

| Flow | Path | Result |
|------|------|--------|
| Supa repro (glued success) | `parse_player_skills` → `_execute_creation_choice` → `_chain_after_creation_choice` → `_auto_present_schools` (no error) | T2b: `SPELL_SCHOOLS`, no `**Note:**` |
| Unknown token failure | `parse_player_skills` → `None` → `format_skill_parse_error` → `_auto_present_skills(error=...)` → empty flavor | T2: note + `bogus`, stub absent |
| Schools parse failure | `parse_player_schools` → `None` → `_auto_present_schools(error=...)` → empty flavor | T3: step unchanged, stub absent |
| Out-of-scope steps | `_auto_present_equipment` L1119 still calls `_narrate_flavor` directly | Unchanged per non-goals |
| Resolution order | Exact → alias → hyphen → compact → `None` | Matches domain spec table |

## Plan notes — resolution

| Plan note | Impl resolution |
|-----------|-----------------|
| `_creation_table_flavor` DRY helper | Implemented L1067–1074; three call sites updated |
| `class_key` unused in helper | `_ = class_key` L868 — API stable per spec |
| T2b depends on WS1 | Glued parse + advance covered in integration test |
| Optional SPELLS T3 mirror | Not implemented — spec marks optional; non-blocking |
| `validate_skill_picks` error path | Inherits V2 via shared `_auto_present_skills`; no dedicated test (plan regression guard only) |

## Scope notes (non-blocking for APP-075 PASS)

| Item | Note |
|------|------|
| **Batch overlap in working tree** | Same diff hunk includes APP-073 (`strip_flavor_stats_table`, `_LLM_STATUS_TAG_RE`) and `get_player_suggestions` — outside ticket Expected files; does not affect APP-075 AC |
| **Release / drift** | Ticket still `in_progress`; domain spec has APP-075 normative § but no dated “APP-075 done” changelog row — required at `release --done` |
| **Human playtest** | Not run this round (Stage 7: glued repro + unknown token + schools invalid) |
| **Multi-unknown helper** | `format_skill_parse_error` handles `len(unknown) > 1`; only single-unknown case covered in T1/T2 |
| **Spells error flavor** | `_auto_present_spells` wired to `_creation_table_flavor`; no dedicated T3 mirror test (optional per spec) |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-075 --done` (ticket AC checkboxes, Closed date, spec changelog row).  
**Human playtest:** Apprentice SKILLS — `spellcasting, medicine, manacontrol` advances without error note; `spellcasting, medicine, bogus` stays on SKILLS with correction-only body (no congratulatory flavor).
