# Research Brief: APP-075-skills-parse-aliases-and-error-flavor

**Date:** 2026-05-20  
**Question:** Why does comma-separated skills input like `spellcasting, medicine, manacontrol` fail at SKILLS while sounding like a success, and what code paths must change for glued-token aliases plus error-path flavor?

**backlog_ticket:** APP-075  
**ticket_path:** tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) owns `app/gm/creation.py` (parsers, `SKILL_PARSE_ALIASES`, `format_skills_table`) and creation routing in `app/gm/orchestrator.py` (`_auto_present_skills`, `_handle_creation_response`, `_compose_creation_narration`). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Character creation** points to that spec. APP-075 expected files are a subset of the registered owner. Parser unit tests already live under `play/tomb_gm/tests/test_creation_gating.py` (imports `gm.creation`); ticket may add `app/tests/test_creation_parsers.py` — still within the same domain.

## Summary

The Supa session bug has **two independent gaps**:

1. **Parser gap:** `normalize_skill_slug` resolves spaced multi-word skills via `SKILL_PARSE_ALIASES` and hyphen substitution, but **not** glued forms (`manacontrol`). All nine hyphenated skill slugs fail the glued form today. Comma-separated parsing requires exactly three resolved slugs; two valid + one glued → `None` → FSM stays on `SKILLS` with no `creation_advanced`.

2. **Flavor gap:** `_auto_present_skills(..., error=...)` always calls `_narrate_flavor` with the **same first-time prompt** (“Ask {name} which three skills they trained in…”) regardless of `error`. The LLM sees the player’s input in the user message and often writes congratulatory copy (“Smart choices…”) while the code body prepends `**Note:**` + re-shows the full table — a contradictory double ask. The same pattern exists on `_auto_present_schools`, `_auto_present_spells`, and `_auto_present_equipment`; ticket AC scopes schools/spells alignment if the fix is shared.

**Verified repro (local):** `parse_player_skills("spellcasting, medicine, manacontrol", "apprentice")` → `None`; spaced `mana control` → `['spellcasting', 'medicine', 'mana-control']`. Compact matching (strip `-`/spaces, compare to canonical slugs) is **collision-free** across all 32 skills — safe general rule for implementation.

Error messages on parse failure are **generic** (“Name exactly 3 skills…”) and do not name unknown tokens (e.g. `bogus` in `spellcasting, medicine, bogus`).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Skill slugs & aliases | `app/gm/creation.py` | `ALL_SKILL_SLUGS`, `SKILL_PARSE_ALIASES` (8 spaced aliases), `SKILL_DISPLAY` |
| Normalization & parse | `app/gm/creation.py` | `normalize_skill_slug`, `parse_player_skills`, `validate_skill_picks` |
| Class key skills | `app/gm/creation.py` | `class_key_skill_slugs`, `CLASS_INFO["key_skills"]` labels |
| Skills table | `app/gm/creation.py` | `format_skills_table` — displays spaced titles (`Mana Control`) |
| Schools/spells parse | `app/gm/creation.py` | `normalize_school_id`, `normalize_spell_id` — hyphen/space only; spell ids like `ember-touch` fail glued |
| Turn routing | `app/gm/orchestrator.py` | `_creation_turn` → `_creation_turn_body` SKILLS branch |
| Code-first commit | `app/gm/orchestrator.py` | `_handle_creation_response` SKILLS → `parse_player_skills` → `_execute_creation_choice` |
| Error re-show | `app/gm/orchestrator.py` | `_auto_present_skills(player_input, error=...)` |
| Flavor LLM | `app/gm/orchestrator.py` | `_creation_flavor_messages`, `_narrate_flavor`, `_compose_creation_narration` |
| Engine validation | `play/tomb_gm/domain/character.py` | `validate_skills` — key-skill rule after parse |
| Parser unit tests | `play/tomb_gm/tests/test_creation_gating.py` | `test_normalize_skill_slug`, `test_parse_player_skills_comma_list` — no glued cases |
| Integration tests | `app/tests/test_creation_flow.py` | Golden path uses spaced skill names; mock flavor `"Test narration."` |
| Session evidence | `app/logs/session-2026-05-20.jsonl` | Referenced in ticket (~17:33 Supa); **gitignored** |

## Code-path traces

### A — Supa repro: glued token → parse fail → contradictory narration

1. **Entry:** `process_turn` with `creation.active` and `creation.step == "SKILLS"` → `_creation_turn` → `_creation_turn_body` (`orchestrator.py` ~776–786).
2. **Parse attempt:** `_handle_creation_response` at `step == "SKILLS"` calls `parse_player_skills(player_input, chosen_class)` (`orchestrator.py` ~933–944).
3. **Comma branch:** `parse_player_skills` splits on `,`, calls `normalize_skill_slug` per part (`creation.py` ~787–795):
   - `spellcasting` → `spellcasting`
   - `medicine` → `medicine`
   - `manacontrol` → `None` (not in `ALL_SKILL_SLUGS`, not in `SKILL_PARSE_ALIASES`, hyphen pass `manacontrol` not in slugs)
   - `len(slugs) == 2` → returns `None` (requires exactly 3).
4. **Error re-show:** `_auto_present_skills(player_input, error="Name exactly 3 skills from the table, comma-separated.")` (`orchestrator.py` ~941–944).
5. **Flavor (bug):** `_auto_present_skills` ignores `error` for instruction selection — always uses `"Ask {name} which three skills they trained in as a {class}."` (`orchestrator.py` ~1046–1057). `_creation_flavor_messages` includes `player_input` as user message; LLM may treat listed skills as accepted.
6. **Body:** `**Note:** {error}\n\n` + `format_skills_table(chosen_class)` (intro still says “Pick **3 skills**…”).
7. **Compose:** `_compose_creation_narration(flavor, body)` → footer `Awaiting: SKILLS_INPUT` via `format_creation_status()` (`creation.py` ~74).
8. **State:** `creation.step` remains `SKILLS`; no `creation.chosen_skills`; no advance to `SPELL_SCHOOLS`.

### B — Success path (contrast)

1. Input `Lore, Spellcasting, Arcana` (or spaced multi-word via aliases) → `parse_player_skills` returns 3 slugs.
2. `_execute_creation_choice("SKILLS", ...)` → `validate_skill_picks` → `creation.chosen_skills` set → `advance()` (`orchestrator.py` ~945–959, ~1388–1409).
3. `_chain_after_creation_choice` → `_auto_present_schools` same turn (`orchestrator.py` ~1026–1031).

### C — `normalize_skill_slug` resolution order

1. Lowercase strip (`creation.py` ~286–296).
2. Direct match in `ALL_SKILL_SLUGS`.
3. Match in `SKILL_PARSE_ALIASES` (keys are **spaced** display forms only).
4. Replace spaces with hyphens → match in `ALL_SKILL_SLUGS`.
5. Else `None`.

**Gap:** No compact/glue pass. `SKILL_PARSE_ALIASES` has `"mana control"` but not `"manacontrol"`. Table shows `Mana Control` (from `SKILL_DISPLAY`) — players naturally paste without space.

### D — `parse_player_skills` secondary path (no commas)

1. If no `,` in input, substring scan over `SKILL_PARSE_ALIASES.keys() | ALL_SKILL_SLUGS` sorted by length (`creation.py` ~797–807).
2. Pattern = token with `-` → space; requires `pattern in lower`.
3. `spellcasting medicine mana control` works; `... manacontrol` fails (substring `"mana control"` not in `"manacontrol"`).
4. Order of returned slugs follows discovery order, not input order (acceptable for set validation).

### E — Error-path flavor (systemic)

All gated `_auto_present_*` helpers follow the same shape:

```python
err = f"**Note:** {error}\n\n" if error else ""
flavor = self._narrate_flavor(self._creation_flavor_messages(<first-time instruction>, player_input))
body = err + format_*_table(...)
return self._compose_creation_narration(flavor, body)
```

Affected symbols: `_auto_present_skills` (~1046), `_auto_present_schools` (~1059), `_auto_present_spells` (~1075), `_auto_present_equipment` (~1088). `_auto_present_race` / `_auto_present_class` use the same pattern (~857–884) — out of ticket scope unless PM wants consistency.

**Existing mitigations do not fix this:** `sanitize_premature_completion_flavor` (APP-070) strips post-creation markers, not “congratulations on picks”; `_sanitize_creation_flavor` (APP-069) only blanks wrong race titles.

### F — Validation errors after partial parse success

If parse returns 3 slugs but `validate_skill_picks` fails (e.g. missing key skill ★), `_handle_creation_response` enriches error and calls `_auto_present_skills(..., error=err)` (`orchestrator.py` ~948–958). Same flavor bug applies.

## Existing specs & docs

- **Ticket:** `tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md` — repro, AC for aliases, error flavor, tests, spec changelog.
- **Domain spec:** `tmp/app-character-creation-spec.md` — § parsers (`parse_player_skills`), § Presentation pattern, APP-011 invalid-input re-show, APP-069/070 flavor guards (no § for validation-failure flavor tone yet).
- **Related done tickets:** APP-011 (re-show table on invalid input), APP-069 (flavor vs committed FSM), APP-070 (premature completion sanitizer).
- **Stretch (ticket notes):** schools/spells glued ids — `normalize_spell_id` fails `embertouch` for `ember-touch`; schools are single-word today.

## Tests & commands

```bash
# Parser unit tests (existing — extend for APP-075)
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q

# Integration (golden path — does not cover glued or error flavor)
python -m pytest app/tests/test_creation_flow.py -q

# Local repro (PYTHONPATH=play;app from repo root)
python -c "from gm.creation import parse_player_skills; print(parse_player_skills('spellcasting, medicine, manacontrol', 'apprentice'))"
```

**Coverage gaps for APP-075:**

| Area | Existing | Needed |
|------|----------|--------|
| `normalize_skill_slug` glued forms | Spaced alias only (`Sleight of Hand`) | `manacontrol`, other 8 hyphen slugs |
| `parse_player_skills` comma + glued | — | Ticket repro string |
| Error-path flavor | APP-070 tests **success** path with bad flavor | Invalid skills input → no congrats markers; step stays `SKILLS` |
| Unknown token message | — | e.g. `bogus` named in error |

**Test pattern (from APP-070):** Drive `process_turn` through turns 1–4, then invalid skills input; monkeypatch `_narrate_flavor` to return congratulatory prose **or** use real stub that mimics session; assert `**Note:**` present, `creation.step == "SKILLS"`, forbidden substrings absent in flavor portion.

## Risks & unknowns

- **Ambiguous compact matches:** None among current 32 skills; rule should still prefer exact slug/alias before compact fallback to avoid future collisions when skills are added.
- **Partial comma lists:** Today invalid tokens are dropped silently until count ≠ 3; AC asks to name unknown tokens when practical — may require `parse_player_skills` refactor or companion `diagnose_skill_input()` (return type today is `list[str] | None` only).
- **Error flavor fix scope:** Skipping LLM on `error=` is simplest and matches ticket “or skip LLM flavor”; correction-only instruction preserves clerk voice but still costs an LLM call.
- **Schools/spells stretch:** Spell ids are hyphenated; glued paste is plausible (`embertouch`). Schools are single-token; lower priority.
- **Table display vs parse:** `format_skills_table` shows `Mana Control` (title case, space) — players may paste table text; spaced forms already work via aliases/hyphen pass; glued is the main gap.
- **Session log:** Cannot re-read Supa JSONL in clone; repro confirmed via code + local Python.

## Raw notes

| Symbol | Location | Role |
|--------|----------|------|
| `SKILL_PARSE_ALIASES` | `creation.py:47–57` | 8 spaced multi-word mappings only |
| `normalize_skill_slug` | `creation.py:286–296` | No compact/glue pass |
| `parse_player_skills` | `creation.py:781–808` | Comma-first; exact count 3 |
| `_auto_present_skills` | `orchestrator.py:1046–1057` | `error` → body prefix only; flavor unchanged |
| `_handle_creation_response` SKILLS | `orchestrator.py:933–959` | Generic parse error string |
| `validate_skill_picks` | `creation.py:726–739` | Post-parse class/key rules |
| `test_parse_player_skills_comma_list` | `test_creation_gating.py:30–32` | Spaced multi-word only |

**Recommended implementation axes (for PM/plan):**

1. **Parser:** Add compact normalization in `normalize_skill_slug` after existing checks: `compact = lower.replace(" ", "").replace("-", "")` → lookup precomputed `{slug.replace("-",""): slug}` (+ alias keys compacted). Optionally auto-extend `SKILL_PARSE_ALIASES` from multi-word slugs for explicit documentation.
2. **Error detail:** In comma branch, collect parts where `normalize_skill_slug` is `None`; if `len(slugs) != 3`, build error naming unknown parts before generic count message.
3. **Flavor:** When `error` is set on `_auto_present_skills` (and schools/spells if aligned): either `flavor = ""` or instruction like “The last answer did not validate. One brief correction sentence only — do not congratulate, confirm picks, or re-ask; code shows the table and note.” Consider small shared helper to DRY four `_auto_present_*` methods.
4. **Spec:** Add § SKILLS input parsers (glued-token rule) and § gated-step flavor on validation failure to `app-character-creation-spec.md` on close.

**Multi-word skills (all fail glued today):**

`shield-use`, `unarmed-combat`, `dual-wielding`, `heavy-weapons`, `thrown-weapons`, `sleight-of-hand`, `magical-knowledge`, `mana-control`, `battlefield-awareness`
