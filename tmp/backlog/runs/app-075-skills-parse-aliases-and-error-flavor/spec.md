# Spec: APP-075-skills-parse-aliases-and-error-flavor

**Status:** draft (PM round 2 — QA r1 fixes)  
**backlog_ticket:** APP-075  
**ticket_path:** [tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md](../../app-075-skills-parse-aliases-and-error-flavor.md)  
**domain_spec:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md)  
**registry_gap:** false (per research-brief)  
**Domain specs touched:** `tmp/app-character-creation-spec.md`

## Problem

At **SKILLS**, comma-separated input that matches table intent can fail parsing while narration sounds like success. Example: `spellcasting, medicine, manacontrol` — two slugs resolve, `manacontrol` does not (glued multi-word form) → `parse_player_skills` returns `None` → FSM stays on `SKILLS`. `_auto_present_skills(..., error=...)` still uses the first-time LLM instruction (“Ask which three skills…”), so the model may congratulate (“Smart choices…”) while the code body shows `**Note:**` + full skills table — a contradictory double ask.

**Root causes (independent):**

1. **Parser:** `normalize_skill_slug` accepts spaced aliases and hyphen substitution but not glued tokens (`manacontrol` → `mana-control`).
2. **Flavor:** `error=` only prefixes the code body; flavor instruction is unchanged on `_auto_present_skills`, `_auto_present_schools`, and `_auto_present_spells`.

## Goals

- **P0 parser:** Glued/compact skill tokens resolve to canonical slugs when unambiguous (all nine hyphenated skills + existing spaced/hyphen paths).
- **P0 parser:** Ticket repro `spellcasting, medicine, manacontrol` (apprentice) → three slugs and SKILLS advance when class rules pass.
- **P0 errors:** Name unrecognized comma-separated tokens when practical; no silent drop without feedback path.
- **P0 flavor:** Validation-failure re-show at SKILLS / SPELL_SCHOOLS / SPELLS must not congratulate, confirm picks, or imply step advanced.
- **P0 tests:** Parser unit cases in gating module + orchestrator tests for invalid skills/schools input (no success-tone markers; step unchanged).

## Non-goals

| Deferred | Notes |
|----------|--------|
| Glued `normalize_spell_id` / school ids | Stretch in ticket — only if trivial shared compact helper; not required for APP-075 close |
| `_auto_present_race` / `_auto_present_class` / `_auto_present_equipment` error flavor | Same code shape; out of ticket AC |
| Changing `parse_player_skills` return type to structured diagnostics | `format_skill_parse_error` helper owns messaging; parse API stays `list[str] \| None` |
| APP-059 table column standardization | Separate ticket |

## Requirements (summary)

Full behavior and test contracts: domain spec § **Skill slug normalization (APP-075)** and § **Gated-step flavor on validation failure (APP-075)**.

| ID | Summary | Domain spec |
|----|---------|-------------|
| **P1** | `normalize_skill_slug` compact pass after existing resolution; benefits comma and non-comma paths | § Skill slug normalization |
| **P2** | `parse_player_skills` comma path uses P1; ticket repro advances | § Skill slug normalization |
| **P3** | Unknown comma tokens surfaced via `format_skill_parse_error`; orchestrator passes result to `_auto_present_skills` | § Skill slug normalization — Parse error messaging |
| **E1** | When `error` set on `_auto_present_skills\|schools\|spells`, correction-only flavor or empty flavor (V2 preferred) | § Gated-step flavor on validation failure |
| **E2** | Single response: `**Note:**` + table + `Awaiting:` for current step; no contradictory “ask” framing | § Gated-step flavor on validation failure |
| **T1** | Unit tests: glued slugs + unknown token + P3 helper | § Tests APP-075 — `test_creation_gating.py` |
| **T2** | Integration: invalid SKILLS input + bad congratulatory stub → step stays `SKILLS` | § Tests APP-075 — `test_creation_flow.py` |
| **T2b** | Required positive regression: ticket repro advances to `SPELL_SCHOOLS` | § Tests APP-075 |
| **T3** | Schools (required) / spells (optional) error-path flavor same as V1–V5 | § Tests APP-075 |

## Acceptance criteria mapping

| Ticket AC | Spec / deliverable |
|-----------|-------------------|
| `manacontrol` → `mana-control`; consistent rule for hyphenated skills | P1 |
| `spellcasting, medicine, manacontrol` → 3 slugs + advance | P2, T2b |
| Invalid/unknown tokens fail cleanly with feedback | P3, T1 helper row |
| Error-path: no congratulate / confirm / advance tone on skills (and schools/spells) | E1–E2, T2, T3 |
| One response: note + table + correct `Awaiting:` | E2 |
| Error names unknown skills when practical | P3 (`format_skill_parse_error` + orchestrator wiring) |
| Unit tests for normalize/parse aliases | T1 → `play/tomb_gm/tests/test_creation_gating.py` |
| Integration/orchestrator test: invalid skills → no success flavor; step unchanged | T2 |
| Domain spec § parsers + § error flavor + changelog on close | Domain spec (PM r2) |

## PM round 2 changes (QA spec r1)

| Finding | Fix |
|---------|-----|
| **SPEC-001** | Added normative § Skill slug normalization and § Gated-step flavor on validation failure to domain spec (not changelog-only). |
| **TICKET-001** | Ticket Expected files now list `play/tomb_gm/tests/test_creation_gating.py` (T1) and `app/tests/test_creation_flow.py` (T2/T2b/T3) explicitly; removed ambiguous `test_creation_parsers.py` fork. |
| **SPEC-002** | P3 owner: `format_skill_parse_error` in `creation.py`; `_handle_creation_response` SKILLS branch must call it; normative example strings in domain spec. |
| **SPEC-003** | T2 documents flavor isolation: assert forbidden markers absent from full narration when V2 skips LLM; alt path documented. |
| **SPEC-004** | T3 covers `_auto_present_schools` error flavor; E1 lists all three symbols in normative §. |
| **SPEC-005** | T2b promoted to required positive regression. |
| **SPEC-006** | Non-comma glued input in scope via P1 in `normalize_skill_slug`. |

## Implementation pointers (Dev plan)

| Area | Path | Notes |
|------|------|-------|
| Compact lookup | `app/gm/creation.py` | Precompute `{slug.replace("-",""): slug}` (+ alias keys compacted); run **after** exact/alias/hyphen checks |
| Parse errors | `app/gm/creation.py` | `format_skill_parse_error(text, class_key)` — collect parts where `normalize_skill_slug` is `None`; specific message before generic count |
| Orchestrator wiring | `app/gm/orchestrator.py` | SKILLS branch ~939–944: `error=format_skill_parse_error(...)` when parse returns `None` |
| Error flavor | `app/gm/orchestrator.py` | `_auto_present_skills`, `_auto_present_schools`, `_auto_present_spells` — branch on `error`; V2 preferred: skip `_narrate_flavor` |
| Tests T1 | `play/tomb_gm/tests/test_creation_gating.py` | Extend existing parser tests |
| Tests T2/T2b/T3 | `app/tests/test_creation_flow.py` | Pattern from APP-070 `test_skills_turn_rejects_premature_completion_flavor` |

**Collision note (research):** Compact map is collision-free across current 32 skills; new skills must preserve exact-before-compact order.

## Test plan

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_flow.py -q -k "skill or school"
```

## Human playtest hints (Stage 7)

- **Glued repro:** Apprentice at SKILLS — enter `spellcasting, medicine, manacontrol` → advances to spell schools (or equipment if non-caster); no “Smart choices” tone with error note on same screen.
- **Spaced control:** Same three with `mana control` — still works (regression).
- **Unknown token:** `spellcasting, medicine, bogus` → stays on SKILLS; note mentions `bogus` (or equivalent); flavor is brief correction or absent, not congratulations.
- **Schools/spells invalid:** Wrong school count or spell id — correction tone only, table re-shown, footer matches step.

## References

- Research: [research-brief.md](./research-brief.md)
- QA r1: [qa-spec-report-1.md](./qa-spec-report-1.md)
- Related: APP-011 (re-show table), APP-069 (committed FSM flavor), APP-070 (premature completion — orthogonal to validation-failure congratulate bug)
