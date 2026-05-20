# APP-070: Block premature PRE_DELVE / registered-delver narration

| Field | Value |
|-------|-------|
| **ID** | APP-070 |
| **Type** | bug |
| **Priority** | P0 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

First-session **Dumpy** run reached `[Phase: PRE_DELVE | Awaiting: RECEPTION_CHOICE]` and “You are now a registered Delver” after skills input and “Yes”, **without** any `character_create` tool call or roster entry — empty roster / false completion.

## Evidence (session log)

- `14:09:34` — skills chosen; narration shows equipment confirm, not schools.
- `14:10:04` — “registered Delver”, `PRE_DELVE`, `RECEPTION_CHOICE`; no `character_create`, `roster_len` 0 in prior drift events.
- Code today: `_auto_finalize()` owns `character_create`; `character_create` removed from `tools.py` — log predates or bypassed code path.

## Acceptance criteria

- [x] Narration must not emit `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” until `_auto_finalize()` succeeds and `bridge.status()["roster"]` is non-empty (extends APP-009).
- [x] `_check_creation_drift` flags `premature_exploration_phase` for `PRE_DELVE` / `preparation` reception copy when `roster_len == 0`.
- [x] Regression test: mock LLM returning PRE_DELVE prose during SKILLS does not change `creation.step` or show false completion in UI.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/creation.py`
- `app/tests/test_creation_flow.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Changelog + cross-link APP-009 in spec.

## Notes

**Session:** `app/logs/session-2026-05-20.jsonl` (Dumpy, lines 27–34).  
**Related:** APP-009 (finalize gate — marked done; log shows regression or pre-fix session).
