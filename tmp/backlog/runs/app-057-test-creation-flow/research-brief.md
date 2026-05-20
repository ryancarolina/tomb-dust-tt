# Research Brief: APP-057-test-creation-flow

**Date:** 2026-05-20
**Question:** How should `app/tests/test_creation_flow.py` drive the full creation FSM through finalize without a live LLM, and what should it assert?

**backlog_ticket:** APP-057
**ticket_path:** tmp/backlog/app-057-test-creation-flow.md
**domain_spec:** tmp/app-character-creation-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

[`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) owns `app/gm/creation.py`, the creation branch of `app/gm/orchestrator.py`, and already lists `python -m pytest app/tests/test_creation_flow.py -q` under Tests. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Character creation** maps to that spec. APP-057 adds a test module under the existing owner — no new domain spec.

## Summary

Character creation is a code-enforced FSM in `CreationState` (`app/gm/creation.py`) driven by `Orchestrator._creation_turn` / `_creation_turn_body` (`app/gm/orchestrator.py`). Player text is parsed in `_handle_creation_response`; validated commits go through `_execute_creation_choice`, which calls `creation.advance()` and chains deterministic follow-ups via `_chain_after_creation_choice`. `ROLL_STATS` and `FINALIZE` are fully code-driven (`_auto_roll_stats`, `_auto_finalize`); gated steps (`SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, `EQUIPMENT_GOLD`) require code tables shown first, then deterministic parsers. LLM is thin flavor only (`_narrate_flavor` / mock stub). APP-049 conftest already provides `orchestrator`, `bridge`, `isolated_workspace`, and `mock_openrouter_client` — sufficient for an integration test via `process_turn("new game")` plus step inputs. Recommend one primary **Apprentice + Spellcasting** path (full FSM) and optional **Militia non-caster** path (spell steps auto-skipped). Patch `bridge.roll_attributes` for deterministic eligible classes; gold roll randomness does not block finalize.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Step enum + parsers | `app/gm/creation.py` | `CREATION_STEPS`, `parse_player_*`, `format_*_table`, `needs_spell_picks`, `skip_inapplicable_spell_steps` |
| Turn routing | `app/gm/orchestrator.py` | `_creation_turn`, `_creation_turn_body`, `_handle_creation_response`, `_execute_creation_choice`, `_chain_after_creation_choice` |
| Auto steps | `app/gm/orchestrator.py` | `_auto_roll_stats` (ROLL_STATS→CLASS), `_auto_finalize` (FINALIZE→WORLD_INTRO) |
| Engine bridge | `app/gm/bridge.py` | `roll_attributes`, `character_create`, `status`, `roster_set` |
| Test fixtures | `app/tests/conftest.py`, `app/tests/helpers.py` | `orchestrator`, `bridge`, `mock_openrouter_client`, `make_isolated_workspace` |
| Parser unit tests | `play/tomb_gm/tests/test_creation_gating.py` | Parsers/tables/state — no orchestrator integration |
| Canon spell/kit data | `build/data/character/starting-spells.json`, `starting-kits.json` | School/spell pick counts; apprentice kit `costGp: 74` |
| Domain spec | `tmp/app-character-creation-spec.md` | Step order, caster rules, test command |

## Code-path traces

### Entry: new game → creation active

1. Entry: `Orchestrator.process_turn("new game")` → `setup_new_game()` (`orchestrator.py:398–403`)
2. `setup_new_game`: `bridge.wipe_all_data()`, `init()`, `campaign_new`, `session_start`, `CreationState(active=True, step="NAME")` (`251–264`)
3. `_creation_turn("[SYSTEM: New game started…]")` → `_auto_present_name` (NAME + system trigger)

### Per-step routing (`_creation_turn_body`)

| Step | First visit (no input / system) | Valid player input | On success advances to |
|------|----------------------------------|--------------------|-------------------------|
| `NAME` | `_auto_present_name` | ≥2 chars, not `[…]`, not yes/ready | `RACE` (+ auto-present race table via chain) |
| `RACE` | `_auto_present_race` if no race yet | `parse_player_race` → race id | `ROLL_STATS` → `_auto_roll_stats` → `CLASS` |
| `ROLL_STATS` | `_auto_roll_stats` (always) | N/A — code rolls via `bridge.roll_attributes` | `CLASS` |
| `CLASS` | `_auto_present_class` if no class | `parse_player_class(text, eligible)` | `SKILLS` (+ skills table) |
| `SKILLS` | `_auto_present_skills` if table not shown | 3 comma-separated skills; ≥1 class key skill | `SPELL_SCHOOLS` or skip to `EQUIPMENT_GOLD` |
| `SPELL_SCHOOLS` | `_auto_present_schools` | 2 schools (apprentice: arcane only; novice: divine + 1) | `SPELLS` |
| `SPELLS` | `_auto_present_spells` | 2 tier-1 spells from chosen schools | `EQUIPMENT_GOLD` |
| `EQUIPMENT_GOLD` | `_auto_present_equipment` on system trigger | `is_equipment_confirm` (yes/ready/confirm…) | `FINALIZE` → `_auto_finalize` |
| `FINALIZE` | `_auto_finalize` | N/A — runs on step entry | `WORLD_INTRO`, `creation.active=False` |
| `WORLD_INTRO` | delegates to `process_turn("look around")` when inactive | exploration | — |

**Spell skip:** After CLASS+SKILLS, `advance()` calls `skip_inapplicable_spell_steps`. If class ∉ `{apprentice, novice}` or `"spellcasting"` ∉ skills, steps `SPELL_SCHOOLS`/`SPELLS` are jumped (`creation.py:318–325`).

**Table gate:** `_execute_creation_choice` rejects SKILLS/SCHOOLS/SPELLS if `skills_table_shown` / `schools_table_shown` / `spells_table_shown` is false (`orchestrator.py:1212–1247`). Normal `process_turn` flow auto-presents tables before accepting picks.

### `_execute_creation_choice` commit flow

1. Validate `step == creation.step`
2. Step-specific parse + validate (e.g. `validate_skill_picks`, `validate_school_picks`, `validate_spell_picks`)
3. `creation.advance()` + `_remember_creation_step` + `log_creation_advanced`
4. Return `{"ok": True, "advanced_to": …}` → caller runs `_chain_after_creation_choice`

### `_auto_finalize` (character_create)

1. `ensure_equipment_gold(self.creation)` — kit + GP if not set
2. `starting_kit(content_root, chosen_class)` → `remaining_gp = starting_gold - kit.costGp`
3. `_creation_spell_defaults()` — uses player picks or fallbacks for caster classes
4. `bridge.character_create(name, background=class, attrs, skill_ids, race_id, gold_gp=remaining_gp, known_spell_ids, spell_school_ids, creation_audit=…)`
5. On failure: revert to `EQUIPMENT_GOLD`, re-present equipment with error
6. On success but empty roster: stay on `FINALIZE`, error narration
7. On success + roster: `creation.active=False`, `step=WORLD_INTRO`, world-intro narration with footer `[Location: 32-C | Phase: preparation | …] Awaiting: RECEPTION_CHOICE`

## Creation step sequence with example inputs

### Primary path — Apprentice caster (matches domain spec scenario)

Mock `bridge.roll_attributes` to return `INT ≥ 8` and `eligible_classes` including `apprentice` (see Recommended test structure).

| # | `process_turn(input)` | Expected `creation.step` after | Notes |
|---|------------------------|--------------------------------|-------|
| 1 | `"new game"` | `NAME` | `creation.active=True` |
| 2 | `"Dumpy"` | `RACE` | Name stored title-cased |
| 3 | `"human"` | `CLASS` | Auto ROLL_STATS + class table in narration |
| 4 | `"apprentice"` | `SKILLS` | Skills table shown |
| 5 | `"Lore, Spellcasting, Arcana"` | `SPELL_SCHOOLS` | Spellcasting triggers spell steps |
| 6 | `"pyromancy, ether"` | `SPELLS` | Arcane schools for apprentice |
| 7 | `"ember-touch, static-lash"` | `EQUIPMENT_GOLD` | Tier-1 from chosen schools |
| 8 | `"yes"` | `WORLD_INTRO` | `creation.active=False`; roster populated |

### Alternate path — Militia non-caster (spell skip)

Same roll mock; use class `militia`, skills `"Swordsmanship, Perception, Lore"` (no Spellcasting). After SKILLS confirm, step jumps to `EQUIPMENT_GOLD` (skips schools/spells). Confirm `"ready"` → finalize.

## Existing specs & docs

- Ticket: `tmp/backlog/app-057-test-creation-flow.md` — AC: full FSM, non-empty roster, pytest green
- Domain spec: `tmp/app-character-creation-spec.md` — step order, caster rules, acceptance scenario (Apprentice + Spellcasting)
- Logging spec: `tmp/app-logging-qa-spec.md` — owns `app/tests/`; APP-049 conftest is dependency
- APP-049 run: `orchestrator` fixture patches `GameBridge` to isolated workspace + mocks `create_client`

## Fixtures (APP-049 conftest)

| Fixture | Purpose |
|---------|---------|
| `isolated_workspace` | Tmp workspace; never touches `play/workspace` |
| `bridge` | `GameBridge(workspace=…)` + `init()` |
| `app_config` | Loads `app/config.yaml` |
| `mock_openrouter_client` | Stubs `gm.orchestrator.create_client`; LLM returns `"Test narration."` |
| `orchestrator` | Full `Orchestrator(app_config)` with patched `GameBridge` → isolated workspace |

No new fixture required unless roll mock is shared across multiple modules (inline monkeypatch in test is fine for APP-057).

## Tests & commands

```bash
# Target (APP-057)
python -m pytest app/tests/test_creation_flow.py -q

# Related existing tests
python -m pytest app/tests/test_smoke.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q

# Domain spec gate (both)
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_flow.py -q
```

## Reusable patterns from `test_creation_gating.py`

| Pattern | Example | Use in APP-057 |
|---------|---------|----------------|
| Comma-separated skill picks | `parse_player_skills("Stealth, Sleight of Hand, Perception", "urchin")` | Same input strings in orchestrator turns |
| Novice schools/spells | `"divine, ward"` + `"mend-light, consecrate-ground"` | Optional second parametrized case |
| Apprentice schools/spells | `"pyromancy, ether"` + tier-1 ids | Primary integration path |
| `skip_inapplicable_spell_steps` | militia → `EQUIPMENT_GOLD` | Assert step after skills without spell picks |
| `ensure_equipment_gold` stable | fixed `gold_roll=3` | Optional assert on GP; not required for roster AC |
| Equipment confirm regex | `is_equipment_confirm("yes, ready to go")` | Use `"yes"` / `"ready"` in turns |
| State roundtrip | `CreationState.to_dict()` | Not needed for integration test |

**Key difference:** `test_creation_gating.py` tests **parsers and tables in isolation**. APP-057 must drive **`orchestrator.process_turn`** end-to-end through `_auto_finalize` and engine `bridge.status()`.

## Recommended test structure

```python
# app/tests/test_creation_flow.py (sketch — not implemented in research)

FIXED_ROLL = {
    "ok": True,
    "race": "human",
    "racial_adjustments": {"STR": 1, "INT": 1},
    "base_rolls": {...},
    "genetic_factors": {...},
    "life_event": {"roll": 20, "name": "Unremarkable Youth", "mods": {}},
    "final_attributes": {"STR": 10, "AGI": 10, "STA": 10, "INT": 12, "SPI": 10, "LUC": 10},
    "eligible_classes": ["peasant", "laborer", "urchin", "apprentice", "militia", "novice"],
}

def test_full_creation_apprentice_caster(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator.bridge, "roll_attributes", lambda race: {**FIXED_ROLL, "race": race})

    inputs = [
        "new game",
        "Dumpy",
        "human",
        "apprentice",
        "Lore, Spellcasting, Arcana",
        "pyromancy, ether",
        "ember-touch, static-lash",
        "yes",
    ]
    last = ""
    for text in inputs:
        last = orchestrator.process_turn(text)

    status = orchestrator.bridge.status()
    assert not orchestrator.creation.active
    assert orchestrator.creation.step == "WORLD_INTRO"
    assert len(status["roster"]) >= 1
    assert status["roster"][0].get("name") == "Dumpy"  # or display_name field — verify at impl
    assert status.get("awaiting") == "PLAYER_ACTIONS"
    assert "RECEPTION_CHOICE" in last
    assert "Phase: preparation" in last

def test_creation_militia_skips_spells(orchestrator, monkeypatch):
    # same roll mock; militia + non-caster skills; assert step never SPELL_* ; roster non-empty after yes
    ...
```

**Assertions beyond non-empty roster (recommended):**

| Assert | Why |
|--------|-----|
| `creation.active is False` | Finalize gate — spec regression for “registered delver, empty roster” |
| `creation.step == "WORLD_INTRO"` | FSM completed |
| `status["awaiting"] == "PLAYER_ACTIONS"` | Engine left `CHARACTER_CREATION` |
| Roster entry name/class/skills match picks | Proves `character_create` + `roster_set` |
| `"Awaiting: RECEPTION_CHOICE"` in final narration | Code-owned footer after finalize |
| `"Phase: preparation"` in final narration | Not premature `PRE_DELVE` / explore |
| Optional: `status["party"]["phase"]` | UI/engine phase alignment |

**Not required for APP-057 AC:** JSONL log inspection, LLM table content match, resume mid-creation (APP-010 territory).

## Risks & unknowns

- **`roll_attributes` is random** — without monkeypatch, class eligibility varies; test may flake or need fallback class (`peasant` always eligible). **Mitigation:** patch `orchestrator.bridge.roll_attributes` (recommended).
- **`ensure_equipment_gold` uses `random.randint(1, 6)`** — does not block finalize; optional `monkeypatch` on `random.randint` if asserting exact GP.
- **Roster field names** — verify whether status uses `name`, `display_name`, or nested sheet key when asserting character identity.
- **LLM in ROLL_STATS** — `_auto_roll_stats` calls `_narrate_only` (not `_narrate_flavor`); mock returns fixed string; stats/class table come from code path after roll, not LLM output.
- **Ticket Expected files include `conftest.py`** — extend only if roll-fixture is shared; inline monkeypatch keeps scope minimal.
- **`test_creation_gating.py` import path** — lives under `play/tomb_gm/tests` with `gm.*` imports; app test should import via `orchestrator` fixture, not duplicate parser tests.

## Raw notes

- `CREATION_STEPS`: NAME → RACE → ROLL_STATS → CLASS → SKILLS → SPELL_SCHOOLS → SPELLS → EQUIPMENT_GOLD → FINALIZE → WORLD_INTRO (`creation.py:20–31`)
- `"Yes"` at SPELL_SCHOOLS rejected as equipment confirm (`orchestrator.py:782–786`) — regression called out in domain spec
- `_execute_creation_choice` EQUIPMENT_GOLD requires `is_equipment_confirm` on player text (`1260–1265`)
- Apprentice kit cost 74 GP (`starting-kits.json`); remaining GP passed to `character_create`
- `_creation_spell_defaults` fallback for apprentice: `["pyromancy","ether"]`, `["ember-touch","static-lash"]` (`orchestrator.py:959–960`)
- `mock_openrouter_client` patches `gm.orchestrator.create_client` — covers `_narrate_flavor` and `_narrate_only`
- Engine `awaiting=CHARACTER_CREATION` when roster empty (`cmd_core.py:179–180`)
