# Reflection: APP-068 scope isolation (IMPL-001 fix)

**Ticket:** APP-068  
**Trigger:** QA FAIL — scope gate (IMPL-001)  
**Agent:** Dev (post-QA fix)

## What QA blocked

- `app/gm/creation.py` modified with APP-067 `format_roll_stats_table` — **not** in APP-068 Expected files.
- `orchestrator.py` and `test_creation_flow.py` contained APP-066 drift-sync and APP-067 roll-stats refactors mixed with APP-068 NAME→RACE fix.

## Actions taken

| Path | Action |
|------|--------|
| `app/gm/creation.py` | `git checkout HEAD -- app/gm/creation.py` — full revert |
| `app/gm/orchestrator.py` | Reverted APP-066 (`_expected_creation_awaiting_label`, drift `expected_awaiting`) and APP-067 (`format_roll_stats_table` import, `_auto_roll_stats` rewrite, ROLL_STATS chain simplification). **Kept** APP-068 only: NAME success → `_auto_present_race(...)`; RACE fallthrough guard before `"The clerk waits."` |
| `app/tests/test_creation_flow.py` | Reverted APP-066 `drift_events` monkeypatch/assertions and APP-067 `human` turn + `FIXED_ROLL` shape. **Kept** APP-068: `test_name_advance_presents_race_table` + Dumpy turn assertions in full flow |

## Post-fix diff vs HEAD

**orchestrator.py** (+7 lines):

1. `_handle_creation_response` NAME success: `return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")` instead of `_chain_after_creation_choice("")`.
2. `_chain_after_creation_choice` before default: `if self.creation.step == "RACE" and not self.creation.race:` → `_auto_present_race`.

**test_creation_flow.py** (+22 lines):

1. `test_name_advance_presents_race_table` (new).
2. `test_full_creation_apprentice_caster`: Dumpy-turn race table + `Awaiting: RACE_INPUT` + not clerk-waits.

**creation.py:** no diff.

## Tests

```text
cd app && python -m pytest tests/test_creation_flow.py -q
..  [100%]
2 passed in 0.79s
```

## Lessons

- Batch tickets (066/067/068) must land in **separate commits or sequential release** with per-ticket diffs; do not carry forward unclaimed file edits when QA runs per-ticket scope gates.
- APP-068 fix is intentionally minimal in orchestrator: direct race presentation on NAME avoids empty `_chain_after_creation_choice("")` path that produced bare clerk-waits.

## Ready for QA re-run

Scope gate should pass: only Expected files touched; `creation.py` clean.
