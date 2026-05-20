# Reflection: Dev — APP-015 WS2 (tests T-015a–d)

**Agent:** Dev  
**Workstream:** WS2 — `app/tests/test_creation_block_on_new_game.py`  
**Deliverables:** test module, reflection-dev-impl-ws2.md

## Completed

- Added `app/tests/test_creation_block_on_new_game.py` with helpers:
  - `_patch_session_state_path` — binds orchestrator disk ops to `tmp_path / session_state.json` (never dev `app/session_state.json`).
  - `seed_stale_creation` — SKILLS + `Flupps` + `roll_result`, dummy `narration_lines` / `input_history`, optional stale `engine_status`.
- **T-015a** (`test_t015a_setup_new_game_clears_stale_creation_on_disk`): real isolated bridge success; `_delete_save_file` no-op so post-success disk remains assertable; NAME-fresh `creation_state`, preserved narration/history.
- **T-015b** (`test_t015b_campaign_new_failure_still_clears_creation`): mocked `campaign_new` failure; disk + memory NAME-fresh on early return.
- **T-015c** (`test_t015c_load_game_after_new_game_uses_name_not_stale_disk`): after successful `setup_new_game`, `load game` variant B cites NAME (`[Awaiting: NAME_INPUT]`), not SKILLS / `Flupps`.
- **T-015d** (two cases): success and `campaign_new` failure both pop `engine_status` while preserving `narration_lines`.

## Self-critique

- **T-015a / T-015d success:** Monkeypatch `_delete_save_file` to no-op is required because L7 unlinks the file on happy path — without it, disk assertions after full success would be vacuous. Matches plan intent (C2 surgical write) without changing production code.
- **T-015d split:** Two tests cover success + early-return branches per plan PLAN-002 / domain T-015d.
- **No conftest churn:** Helpers kept module-local per plan (“otherwise keep helpers in test module”).

## Tests

```bash
cd app
python -m pytest tests/test_creation_block_on_new_game.py -q
# 5 passed in 0.88s

python -m pytest tests -q -k "creation_block or new_game_creation"
# 5 passed

python -m pytest tests -q -k "creation_flow or session_resume"
# 6 passed
```

## Handoff

**Ready for:** ticket close / spec changelog (WS3 or PM)  
**Escalate human if:** Stage 7 manual playtest shows autosave reintroducing stale `engine_status` before first post-session `_save_session`.
