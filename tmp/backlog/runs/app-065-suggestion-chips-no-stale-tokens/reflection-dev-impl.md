# Reflection: Dev — APP-065 implementation

**Agent:** Dev (impl)  
**Workstream:** WS1 — code-owned chips + turn-loop refresh  
**Deliverables:** `app/ui/suggestions.py`, `Orchestrator.get_player_suggestions()`, `app/ui/app.py` turn path, `app/tests/test_ui_suggestions.py`

## Completed

- **`app/ui/suggestions.py`:** Added `PLAYER_SUGGESTIONS_BY_CREATION_STEP`, `PLAYER_SUGGESTIONS_BY_AWAITING`, `is_blocked_chip_token()` (UPPER_SNAKE, `*_INPUT` / `*_CONFIRMATION`, engine enums + `CREATION_STATUS_LABELS` + `RECEPTION_CHOICE`), `filter_player_suggestions()`, and `build_player_suggestions()` with spec lookup order (active creation step → SETUP / SESSION_ENDED guards → awaiting map → `[]`).
- **`app/gm/orchestrator.py`:** Added `get_player_suggestions()` delegating to builder with `creation.active`, `creation.step`, `bridge.status()["awaiting"]`, and `bridge.has_save()`.
- **`app/ui/app.py`:** Removed narration regex scrape (`_extract_suggestions` deleted). Added `_queue_turn_suggestions(turn_id)` called unconditionally from `_process_turn` `finally`; preserves `return` in `except` (no TTS on error) while still clearing stale chips.
- **Tests:** New `app/tests/test_ui_suggestions.py` — blocklist, equipment chips, inactive-creation guard, SETUP maps, post-finalize orchestrator integration, `_queue_turn_suggestions` empty-list queue, exception-path refresh via `_process_turn`.

## Deviations

- None from plan. Startup `_init_orchestrator` hardcoded seed unchanged (spec allows).
- `input_box.py` untouched (v1 label == submit).

## Self-critique

- Import path `from ui.suggestions import build_player_suggestions` in orchestrator matches existing `ui.*` convention and pytest `APP` on `sys.path`.
- Post-finalize guard relies on `creation.active is False` before reading `creation.step` — aligned with `_auto_finalize` behavior; integration test drives full INPUTS golden path.
- App exception test uses `SDL_VIDEODRIVER=dummy` + minimal layout (same pattern as `test_engine_status_on_save.py`).

## Test gates

```text
python -m pytest tests/test_ui_suggestions.py -q — 17 passed
python -m pytest tests/test_creation_flow.py tests/test_session_resume_failure.py -q — 11 passed
```

## Handoff

- Domain spec checklist/changelog (`tmp/app-pygame-ui-spec.md`) deferred to ticket close / release.
- Manual Bumpy repro: equipment chips at `EQUIPMENT_GOLD`; post-finalize no stale token; objection chip re-presents kit.
