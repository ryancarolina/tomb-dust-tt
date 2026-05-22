# QA Report: spec — round 1

**Task:** app-075-skills-parse-aliases-and-error-flavor  
**backlog_ticket:** APP-075  
**ticket_path:** tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Ticket valid (`in_progress`) | PASS | `tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md` |
| `registry_gap: false` | PASS | `research-brief.md`; owner `tmp/app-character-creation-spec.md` |
| `domain_spec_creation` | not_needed | No new `tmp/app-*-spec.md` |
| Domain spec matches run spec | **FAIL** | Phantom § references (below) |
| AC testable | PARTIAL | Tests drafted; normative behavior missing in domain spec |
| Code traces | PASS | Independent trace matches research (see verified paths) |
| Expected files ⊆ plan scope | **FAIL** | T1 targets `play/tomb_gm/tests/` not in ticket Expected files |

## Findings

### SPEC-001 — blocker — Domain spec normative sections missing

- **Location:** `tmp/app-character-creation-spec.md` (entire file); `run-folder/spec.md` lines 38–48; changelog line 544
- **Issue:** PM and run `spec.md` claim normative sections **§ Skill slug normalization (APP-075)** and **§ Gated-step flavor on validation failure (APP-075)** with requirement IDs P1–P3, E1–E2, V1–V5. Repository search shows **no such headings or requirement tables** in the domain spec — only `#### Tests — APP-075 (T1–T2)` (lines 475–493) and a changelog line asserting those sections were added.
- **Implementation gap:** Dev has no authoritative domain-spec contract for resolution order (exact → alias → hyphen → compact), collision policy, unknown-token error priority, or validation-failure flavor rules (empty vs correction-only, schools/spells parity). Violates AGENTS.md drift policy: behavior must live in domain spec, not only run-folder `spec.md`.
- **Suggested fix:** Add two normative sections to `tmp/app-character-creation-spec.md` before plan QA:
  1. **Skill slug normalization (APP-075)** — resolution order table; list of nine hyphenated skills; compact map rule; `parse_player_skills` comma vs non-comma behavior; P3 error message priority (`unknown token` before generic count).
  2. **Gated-step flavor on validation failure (APP-075)** — V1–V5 (or E1–E2) covering `_auto_present_skills`, `_auto_present_schools`, `_auto_present_spells` when `error=` is set; forbid first-time “ask which three skills” instruction; single-response contract (`**Note:**` + table + canonical `Awaiting:`).
  - Mirror requirement IDs from run `spec.md` so AC mapping stays stable.
  - Remove or correct changelog until sections exist.

### TICKET-001 — blocker — Test file path not in Expected files

- **Location:** Ticket **Expected files** vs `spec.md` test plan vs domain spec T1
- **Issue:** Ticket authorizes only `app/tests/test_creation_flow.py` or `app/tests/test_creation_parsers.py`. Run `spec.md` and domain spec T1 primary path is `play/tomb_gm/tests/test_creation_gating.py` (existing `test_normalize_skill_slug`, `test_parse_player_skills_comma_list`). Hooks enforce Expected files on `app/` edits; extending gating tests may be denied or force ticket amendment mid-impl.
- **Suggested fix:** Either (a) add `play/tomb_gm/tests/test_creation_gating.py` to ticket Expected files, or (b) mandate all new T1 cases in `app/tests/test_creation_parsers.py` and state gating file is read-only regression. Pick one path in domain spec T1 table.

### SPEC-002 — blocker — P3 error ownership unspecified

- **Location:** Domain spec T1 row “Unknown token”; run `spec.md` P3; `orchestrator.py` 941–944
- **Issue:** Ticket AC: “error message names the problem when practical.” Today `_handle_creation_response` passes a **fixed** string on parse failure (`"Name exactly 3 skills from the table, comma-separated."`). `parse_player_skills` returns only `list[str] | None` — no token diagnostics. Spec does not require **where** unknown-token text is built (parser helper vs orchestrator) or example strings (e.g. `Unrecognized skill: bogus`).
- **Implementation gap:** Dev may implement P3 only in tests via monkeypatch or skip naming `manacontrol` failures distinctly from count failures.
- **Suggested fix:** In domain spec § Skill slug normalization — errors: require orchestrator (or documented helper) to list unrecognized comma-separated parts before generic count message; give 1–2 normative examples.

### SPEC-003 — major — T2 “flavor portion” not testable as written

- **Location:** Domain spec T2 steps 4; run `spec.md` T2
- **Issue:** Assertions forbid substrings in “flavor portion” (`smart choices`, `excellent`, `moving on`) but no spec defines how tests isolate flavor from code `body` (`**Note:**`, `format_skills_table`, footer). `_compose_creation_narration` concatenates flavor + body; forbidden words could appear in table intro (“Pick **3 skills**”) without being LLM congratulation.
- **Suggested fix:** Specify test strategy in domain spec T2: e.g. monkeypatch `_narrate_flavor` return only (already implied), assert forbidden strings **not** in returned stub path, or assert full narration excludes markers only when stub is the sole flavor source; document allowed phrases in correction-only flavor.

### SPEC-004 — major — Schools/spells error flavor untested

- **Location:** Ticket AC “`_auto_present_schools` / `_auto_present_spells` if same pattern”; run spec E1
- **Issue:** E1 requires alignment on three presenters; T2 only covers SKILLS. Code trace confirms identical bug on `_auto_present_schools` / `_auto_present_spells` (`orchestrator.py` 1065–1086) — flavor ignores `error`.
- **Suggested fix:** Add T3 (unit or minimal integration) stubbing invalid school/spell input + bad flavor, or explicit manual-only row in spec with “required for close” flag. Minimum: normative § Gated-step flavor lists all three symbols as in-scope for E1.

### SPEC-005 — minor — Positive regression after parser fix underspecified

- **Location:** Domain spec T2 “After implementation, repeat turn 5 with ticket repro…”
- **Issue:** Post-fix turn 5 with `spellcasting, medicine, manacontrol` should advance to `SPELL_SCHOOLS` for apprentice (verified: `validate_skill_picks('apprentice', [...])` → `None` when slugs valid). Optional sentence is easy to drop in impl.
- **Suggested fix:** Promote to required T2b or extend `test_full_creation_apprentice_caster` with glued third skill variant.

### SPEC-006 — minor — Non-comma glued input

- **Location:** `parse_player_skills` non-comma branch (`creation.py` 797–807)
- **Issue:** Ticket emphasizes comma repro; `spellcasting medicine manacontrol` (no commas) still fails today. P1 on `normalize_skill_slug` fixes comma path only unless substring path also benefits.
- **Suggested fix:** State in § Skill slug normalization whether non-comma glued tokens are in scope (recommend: in scope if compact pass is in `normalize_skill_slug` and substring scan uses normalized tokens).

## Verified code traces (independent)

| Claim | Verified |
|-------|----------|
| `normalize_skill_slug("manacontrol")` → `None` | Yes (`creation.py` 286–296; local PYTHONPATH=play;app) |
| `parse_player_skills("spellcasting, medicine, manacontrol", "apprentice")` → `None` | Yes |
| `_auto_present_skills` ignores `error` for flavor instruction | Yes (`orchestrator.py` 1046–1057) |
| Same pattern on schools/spells | Yes (`orchestrator.py` 1059–1086) |
| Compact collision-free (32 skills) | Yes (script: no collisions) |
| Generic parse error string | Yes (`orchestrator.py` 941–944) |

## AC mapping (ticket → spec readiness)

| Ticket AC | Spec ready? | Blocker |
|-----------|-------------|---------|
| Glued aliases / consistent rule | No | SPEC-001 |
| Ticket repro parses + advances | Partial (tests only) | SPEC-001, SPEC-005 |
| Unknown tokens fail cleanly | No | SPEC-002 |
| Error-path no congratulate (skills + schools/spells) | No | SPEC-001, SPEC-004 |
| Single response note + table + Awaiting | No | SPEC-001 |
| Error names unknown skills | No | SPEC-002 |
| Unit + integration tests | Partial | TICKET-001, SPEC-003 |
| Domain spec changelog on close | N/A at spec stage | SPEC-001 |

## Summary

Run-folder `spec.md` is coherent and research-backed, but **domain spec is not the source of truth yet**: normative APP-075 behavior sections are referenced but absent, and test placement conflicts with ticket Expected files. PM revision round 2 must land domain sections P1–E2 (and V1–V5 if used), resolve T1 file path in the ticket, and nail P3 error ownership before spec QA re-review.

## Re-review focus

1. Confirm `tmp/app-character-creation-spec.md` contains full **Skill slug normalization** and **Gated-step flavor on validation failure** sections (not changelog-only).
2. Ticket Expected files match T1/T2 module paths exactly.
3. P3 error examples and builder location (orchestrator vs `creation.py` helper).
4. T2 test strategy for flavor isolation documented.
5. Schools/spells covered in normative flavor § and at least one automated or explicitly required manual check.
