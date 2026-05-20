# Dev implementation reflection — APP-070

**backlog_ticket:** APP-070  
**Date:** 2026-05-20

## What shipped

1. **`sanitize_premature_completion_flavor`** (`app/gm/creation.py`) — case-insensitive markers for `PRE_DELVE`, `RECEPTION_CHOICE`, registered-delver phrases, and `Phase: preparation` while `active` and `step != WORLD_INTRO`. Any hit blanks the entire flavor string.

2. **`_compose_creation_narration`** (`app/gm/orchestrator.py`) — after `strip_llm_status_tags`, applies the sanitizer when `creation.active` or `roster_len == 0`; re-runs tag strip if the sanitizer mutated the string (C5); then existing race-table / race-mismatch sanitizers.

3. **`_check_creation_drift`** — `_PRE_DELVE_PHASES`, D1a–D1c when `roster_len == 0`, optional D2 `premature_completion_copy` on registration phrases in full narration.

4. **`test_skills_turn_rejects_premature_completion_flavor`** — patches `_narrate_flavor` with `BAD_PREMATURE_FLAVOR` on skills commit turn; asserts FSM at `SPELL_SCHOOLS`, empty roster, no leak strings, desk footer `SPELL_SCHOOLS_INPUT`.

## Deviations / notes

- Compose pipeline already had APP-072 `strip_flavor_race_table` and APP-069 `_sanitize_creation_flavor`; premature sanitizer slots **between** first tag strip and those helpers per plan order.
- `_narrate_creation_flavor` calls `_sanitize_creation_flavor` on raw flavor before compose; compose applies premature sanitizer on the tag-stripped path only (flavor layer, not `body`/`footer`).
- Golden path `test_full_creation_apprentice_caster` still passes — legitimate `RECEPTION_CHOICE` / `Phase: preparation` come from `footer=` after roster populated; premature gate uses `roster_len == 0` on compose.

## Verification

```text
cd app && python -m pytest tests/test_creation_flow.py -q
7 passed in 1.61s
```

## Risks / follow-ups

- Drift D2 may still fire if sanitizer misses a novel completion phrase; extend `_PREMATURE_FLAVOR_MARKERS` if logs show leaks.
- Domain spec changelog deferred to ticket `release --done` (not in impl file list).
