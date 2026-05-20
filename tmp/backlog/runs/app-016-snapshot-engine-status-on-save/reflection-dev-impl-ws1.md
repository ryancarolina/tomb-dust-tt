# Reflection: Dev — APP-016 WS1

**backlog_ticket:** APP-016  
**workstream:** WS1 — `_save_session` engine_status snapshot  
**date:** 2026-05-20

## What shipped

- Extended `App._save_session()` in `app/ui/app.py` to persist the full `Orchestrator.get_status()` dict under `engine_status` when status is success-shaped.
- Reused the existing single `get_status()` call for `session_id`, `campaign_slug`, and the snapshot (S5c).
- On failure (exception, `ok is False`, or `"_error" in status`), `engine_status` is left unset and the key is omitted from save JSON (S5d).
- Docstring note added: save-time engine truth for APP-017/018; read path out of scope.

## Design choices

- **`engine_status: dict | None = None`** initialized before the `data` dict build; conditional `data["engine_status"] = engine_status` after — never writes `engine_status: null`.
- **Success gate:** `status.get("ok") is not False and "_error" not in status` matches plan B3 and finalize logging pattern; `handle_status` normally returns `ok: True` even with empty roster / `CHARACTER_CREATION`.
- **No load-path edits:** `_load_session`, orchestrator resume, and reconcile unchanged per ticket scope.
- **No trigger changes:** autosave, Escape quit, post-turn `finally` still call `_save_session()` only.

## Verification

```bash
cd app && python -c "from ui.app import App; print('import ok')"   # passed
cd app && python -m pytest tests -q                                   # 11 passed
```

WS2 tests (`test_engine_status_on_save.py` T4a–d) not implemented in this stream.

## Handoff to WS2

- Add `app/tests/test_engine_status_on_save.py` with headless App fixtures and `SAVE_PATH` monkeypatch.
- **T4a:** mid-creation save → assert `engine_status.awaiting == "CHARACTER_CREATION"`, `roster == []`.
- **T4b:** post-finalize save → non-empty `roster`, `awaiting != "CHARACTER_CREATION"`.
- **T4c:** legacy JSON without key → `_load_session()` no raise.
- **T4d:** monkeypatch `get_status` raise → file written, `"engine_status" not in data`.

## Risks / notes

- Batch coordination: APP-015 C2 clears stale `engine_status` on `setup_new_game` entry — not in WS1 scope.
- Deep-copy of status dict not required per plan; JSON serialize/deserialize on write is sufficient.
