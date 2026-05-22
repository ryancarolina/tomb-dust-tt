# Reflection: Dev — APP-075 WS1 implementation

**Agent:** Dev (impl)  
**Workstream:** WS1 — Compact parse + error helper + T1  
**Deliverables:** `app/gm/creation.py` P1/P3, `play/tomb_gm/tests/test_creation_gating.py` T1

## Completed

- **P1:** Added `_compact_skill_token`, `_build_skill_compact_map`, and module-level `_SKILL_COMPACT_MAP` built from `ALL_SKILL_SLUGS` and `SKILL_PARSE_ALIASES` keys at import.
- **P1:** Extended `normalize_skill_slug` with step 5 compact lookup after exact / alias / hyphen passes (resolution order unchanged for earlier steps).
- **P3:** Added `format_skill_parse_error(text, class_key)` — comma-path unknown-token messages with generic count fallback; `class_key` accepted but unused per spec.
- **T1:** Extended `test_normalize_skill_slug` (`manacontrol`, `sleightofhand`), `test_parse_player_skills_comma_list` (glued, spaced regression, bogus), and new `test_format_skill_parse_error`.

## Deviations

- None from plan. Did not change `parse_player_skills` return type or non-comma scan logic beyond benefiting from compact step in `normalize_skill_slug`.

## Self-critique

- Compact map overwrites alias keys onto slug keys when compact forms collide; catalog is collision-free today; exact/alias/hyphen still win because they run before step 5.
- `format_skill_parse_error` uses `text.lower()` for comma split only; original casing preserved in unknown-token messages from split parts (lowercased parts — acceptable for player-facing errors).

## Test gates

```text
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q — 13 passed
```

## Handoff to WS2

- `format_skill_parse_error` exported from `creation.py` for orchestrator SKILLS branch and integration tests.
- Glued input `spellcasting, medicine, manacontrol` parses to three slugs including `mana-control`.
