# APP-071: Friendly load-game message when no save exists

| Field | Value |
|-------|-------|
| **ID** | APP-071 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-session-persistence-spec.md`](../app-session-persistence-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

`load game` with no resumable session logs `error` to JSONL and returns a terse string; players mid-creation (Supa) had no in-app guidance to use `new game` or continue.

## Evidence (session log)

- `16:08:18` — `load game` → `{"context":"session_resume","error":"no save session found"}` only in log; no structured player recovery in narration panel.
- `16:43:56` — repeat after partial Supa creation.

## Acceptance criteria

- [x] `process_turn("load game")` returns player-facing narration: no save found, suggest `new game` or finishing current creation; do not leave UI silent.
- [x] JSONL `error` event retained for QA; optional `log_player_message` with same text.
- [x] If mid-creation in memory, message distinguishes “no save file” vs “unsaved in-progress creation”.
- [x] **APP-019 scope (not bundled):** APP-071 closes via narration panel + JSONL `gm_narration` for **`load game`** resume failure. APP-019 remains open for **toast / UI error channel** on **`new game`** failures — coordinate copy tone only; do not require toast in APP-071.

## Scope notes (PM r2)

- Resume failure emit: `_emit_recovery_narration` (drift-safe), not `_emit_narration` on failure paths.
- Mid-creation footer: `format_creation_status` bracket token; evaluate variant B before variant A.

## Expected files

- `app/gm/orchestrator.py`
- `app/tests/test_session_resume_failure.py` _(recommended before impl)_
- `app/ui/app.py` _(optional — suggestion queue fallback only; not required for close)_
- `tmp/app-session-persistence-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update session-persistence spec resume failure behavior.

## Notes

**Related:** APP-019 (surface new game failure errors), APP-064 (startup save prompt).
