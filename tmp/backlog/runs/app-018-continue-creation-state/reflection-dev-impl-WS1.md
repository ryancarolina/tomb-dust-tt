# Dev reflection — APP-018 WS1

**backlog_ticket:** APP-018  
**stream:** WS1 — Restore helper + G1 gate + G3 wiring  
**file:** `app/gm/orchestrator.py`

## What shipped

| Item | Notes |
|------|--------|
| `_creation_disk_restore_done` | Init `False`; reset in `_reset_creation_for_new_game` (covers `setup_new_game`) |
| `_creation_restore_gate` | G1d live roster, G1a saved/live awaiting, G1c snapshot roster, G1b active block + valid `CREATION_STEPS` step |
| `_restore_creation_from_session_state` | Once-only disk read → gate → `import_creation_state` → flag |
| G3a | After `new game` early return; before resume / creation routing |
| G3b | Resume fail path before `_resume_failure_message` |
| G3c | `_restore_history()` → restore helper → sync; NAME clobber removed; APP-017 inline placeholder kept |
| `_restore_history` | Narration + combat only; uses `_session_state_path()` |
| Import | `CREATION_STEPS` from `gm.creation` for gate step validation |

## Deviations / risks

- G3a runs on every non–`new game` turn (including resume success/fail). Second calls are no-ops via `_creation_disk_restore_done` — intentional per once-only guard.
- G3c force-active block remains for empty in-memory FSM after restore; APP-017 batch should replace with `_reconcile_empty_roster_on_load()` without reintroducing NAME reset.
- WS2 tests not written in this stream — T-018a–f still required before ticket close.

## Verification

- `python -m py_compile app/gm/orchestrator.py` — OK
- Full `from gm.orchestrator import Orchestrator` needs `tomb_gm` on `PYTHONPATH` (app runtime); not run in WS1

## Handoff to WS2

- Monkeypatch `Orchestrator._session_state_path` in `test_creation_restore.py`.
- Assert G3a on first desk input (T-018b), G3b variant B step from disk (T-018a), G3c no NAME clobber (T-018c), legacy no `engine_status` (T-018d), stale/post-finalize (T-018e/f).
