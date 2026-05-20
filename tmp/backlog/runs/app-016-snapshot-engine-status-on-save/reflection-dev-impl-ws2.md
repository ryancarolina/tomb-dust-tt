# Reflection: Dev — APP-016 WS2

**backlog_ticket:** APP-016  
**workstream:** WS2 — Save snapshot tests (T4a–d)  
**date:** 2026-05-20

## What shipped

- New module `app/tests/test_engine_status_on_save.py` with four tests mapping to domain T4a–d.
- Fixtures inline in module: `save_path` (monkeypatch `ui.app.SAVE_PATH`), `headless_app` (`SDL_VIDEODRIVER=dummy`, pygame init/quit, attach orchestrator), `read_save` helper.
- **T4a** `test_save_includes_engine_status_mid_creation`: `new game` + `Dumpy` → `_save_session()` → `engine_status.awaiting == "CHARACTER_CREATION"`, `roster == []`, matches live `get_status()`.
- **T4b** `test_save_includes_engine_status_after_finalize`: full `INPUTS` from `test_creation_flow.py` with `FIXED_ROLL` patch → non-empty roster, `awaiting != "CHARACTER_CREATION"`.
- **T4c** `test_load_session_legacy_without_engine_status`: minimal legacy JSON without `engine_status` → `_load_session()` no raise; narration restored; creation import smoke.
- **T4d** `test_save_omits_engine_status_on_get_status_failure`: monkeypatch `get_status` → raise → save file exists, key omitted (not `null`), `creation_state` still present.

## Design choices

- Fixtures kept in test module (not `conftest.py`) — only this file needs headless App + isolated save path.
- Reused `FIXED_ROLL` / `INPUTS` from `test_creation_flow.py` for T4b to avoid attribute-roll drift.
- T4c uses explicit legacy `creation_state` blob (mid-creation RACE step) rather than running turns first — isolates load-path behavior.
- T4d asserts key **omitted**, not `engine_status: null`, per S5d.

## Verification

```bash
cd app && python -m pytest tests/test_engine_status_on_save.py -q   # 4 passed in 2.16s
cd app && python -m pytest tests -q -k "engine_status or save_session"  # 4 passed
```

WS1 (`_save_session` snapshot) was prerequisite on branch; all T4a–d green without code changes in WS2.

## Handoff to WS3

- Tick `tmp/app-session-persistence-spec.md` AC checklist + changelog on ticket close.
- `python tmp/backlog/claim_ticket.py release APP-016 --done` after QA PASS.

## Risks / notes

- T4b runtime ~2s (full creation FSM); acceptable for CI given existing `test_creation_flow` pattern.
- Batch QA: coordinate APP-015 T-015d with T4a if both land same batch (stale `engine_status` on failed `new game`).
