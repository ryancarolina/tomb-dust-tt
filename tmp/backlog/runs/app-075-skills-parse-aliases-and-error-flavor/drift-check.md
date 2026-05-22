# Drift Check: APP-075-skills-parse-aliases-and-error-flavor



**backlog_ticket:** APP-075  

**Verdict:** PASS



## Specs compared



| Spec | Drift? | Action |

|------|--------|--------|

| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | no | § Skill slug normalization (APP-075) L84–132 and § Gated-step flavor on validation failure (APP-075) L134–148 match code; changelog **APP-075 done** added |

| Run [`spec.md`](./spec.md) P1–P3, E1–E2, V1–V5, T1–T3 | no | Verified against `creation.py`, `orchestrator.py`, gating + flow tests |

| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | No registry row change required — behavior stays under character-creation spec |



## Code ↔ domain spec (summary)



| Requirement | Code | Match |

|-------------|------|-------|

| **P1** Resolution order: exact → alias → hyphen → compact → `None` | `normalize_skill_slug` L302–315; `_SKILL_COMPACT_MAP` L64–73 | yes |

| **P2** Comma path; ticket repro three slugs | `parse_player_skills` L842–850; T1 + T2b | yes |

| **P3** `format_skill_parse_error`; orchestrator passes to `_auto_present_skills` | L866–879; `orchestrator.py` L960–964 | yes |

| **V1–V3** No first-time ask / congratulate when `error` set | `_creation_table_flavor` L1070–1071 returns `""` | yes |

| **V4** `**Note:**` + code table body | `_auto_present_skills\|schools\|spells` L1079/1094/1106 | yes |

| **V5** Footer matches current step | T2 `SKILLS_INPUT`; T2b/T3 `SPELL_SCHOOLS_INPUT` | yes |

| **E1** skills, schools, spells share helper | All three `_auto_present_*` use `_creation_table_flavor` | yes |

| **E2** Post-`validate_skill_picks` errors | L979 → `_auto_present_skills(..., error=err)` same path | yes |

| **T1** Parser unit | `test_creation_gating.py` glued + unknown + P3 helper | yes |

| **T2** Invalid skills error flavor | `test_skills_error_path_skips_congratulatory_flavor` | yes |

| **T2b** Glued alias advances | `test_skills_glued_alias_advances_to_schools` | yes |

| **T3** Schools error flavor | `test_schools_error_path_skips_congratulatory_flavor` | yes |



## Ticket AC → verification



| Ticket AC | Result |

|-----------|--------|

| Glued multi-word skill forms (`manacontrol` → `mana-control`) | ✓ |

| `spellcasting, medicine, manacontrol` → 3 slugs + SKILLS advance | ✓ |

| Unknown tokens fail cleanly (no silent partial accept) | ✓ |

| Error-path `_auto_present_skills\|schools\|spells` — no success tone | ✓ |

| Single response: note + table + correct `Awaiting:` | ✓ |

| Error names unknown skill when practical | ✓ |

| Unit tests for alias cases | ✓ |

| Integration: invalid skills → no success flavor; step unchanged | ✓ |

| Domain spec § + changelog on close | ✓ |



## Tests run



```bash

python -m pytest play/tomb_gm/tests/test_creation_gating.py -q

python -m pytest app/tests/test_creation_flow.py -q -k "skill or school or glued"

python -m pytest app/tests/test_creation_flow.py -q

```



**Result:** 13 + 4 + 8 = **25 passed** (gating 0.03s; flow subset 1.03s; full flow 1.63s)



| Module | APP-075 tests | Result |

|--------|---------------|--------|

| `play/tomb_gm/tests/test_creation_gating.py` | T1 — normalize, comma list, `format_skill_parse_error` | ✓ |

| `app/tests/test_creation_flow.py` | T2, T2b, T3 | ✓ |

| Regression | `test_full_creation_apprentice_caster`, APP-070 skills test | ✓ (full suite) |



## Ticket close



- [x] Ticket acceptance criteria checked in ticket file

- [x] Status `done`, **Closed** 2026-05-20

- [x] `python tmp/backlog/claim_ticket.py release APP-075 --done` — session cleared

- [ ] Stage 7 commit + `human-test-plan.md`



## Notes



- **V2 implementation:** empty flavor on `error=` (preferred path in domain spec); monkeypatched congratulatory stub absent in T2/T3.

- **Non-blocking gaps:** multi-unknown `format_skill_parse_error` not unit-tested (code handles `len(unknown) > 1`); optional SPELLS T3 mirror test not added (spec marks optional); `_auto_present_equipment` still narrates on error (out of scope per E1).

- **Stretch deferred:** glued-token rule for school/spell id parsers (ticket Notes) — not required for APP-075 close.

- **Batch overlap:** working tree may include APP-073 sanitizer changes in same modules — does not affect APP-075 AC mapping.

- Human PyGame playtest not run in drift round; see qa-implementation-pass handoff for manual checks.


