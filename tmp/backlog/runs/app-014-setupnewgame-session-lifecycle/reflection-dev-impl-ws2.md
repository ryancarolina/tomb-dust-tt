# Reflection: Dev impl WS2 — APP-014

**backlog_ticket:** APP-014  
**workstream:** WS2 — Lifecycle pytest T-014a–c  
**agent:** Dev (implementation stream)

## What changed

Added `app/tests/test_setup_new_game_lifecycle.py` with:

| Test | Coverage |
|------|----------|
| **T-014a** `test_setup_new_game_from_mid_creation` | Mid-creation (`SKILLS` + name) → `setup_new_game()` → `ok`, `creation.step == NAME`, active session in `status()`, exactly one open session |
| **T-014b** `test_setup_new_game_closes_prior_session` | Prior `session_start` + `active.json` → setup → prior closed or replaced, new `current` row open, `creation.step == NAME`, no stray open sessions |
| **T-014c** `test_setup_new_game_preserves_corpses` | `character_create` + `process_delver_death` → corpse count unchanged after `setup_new_game()` |

Module helpers: `count_open_sessions(conn)`, `count_corpses(conn)`, `_ensure_salt_road_campaign(bridge)`.

Docstring enables `-k "setup_new_game or session_lifecycle"`.

## Constraints honored

| Constraint | How |
|------------|-----|
| WS1 prerequisite | Tests assert WS1 L1/L1b + L2–L7 behavior without orchestrator edits |
| T-014b style | Asserts open-session count and `current` row state — no log substring matching |
| T-014c fixture | Minimal bridge path: `character_create` → `process_delver_death` (mirrors `test_death_rules.py` pattern) |
| No bridge/orch edits | Only new test module |
| Conftest unchanged | Helpers kept module-local per plan |

## Verification

```bash
cd app && python -m pytest tests/test_setup_new_game_lifecycle.py -q
# 3 passed

cd app && python -m pytest tests -q -k "setup_new_game or session_lifecycle or creation_flow"
# 8 passed, 6 deselected

cd app && python -m pytest ../play/tomb_gm/tests -q -k session
# 5 passed, 131 deselected
```

All green on first run — no orchestrator or bridge fixes required.

## Handoff

- Ticket release: domain spec checklist + changelog in `tmp/app-session-persistence-spec.md`; `release APP-014 --done`.
- Stage 7 manual: APP-064 partial creation → `new game` → NAME (human-test-plan).
