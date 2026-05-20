# APP-074: Remove dead get_step_prompt LLM instructions

| Field | Value |
|-------|-------|
| **ID** | APP-074 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | done |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

`get_step_prompt()` in `creation.py` still contains legacy LLM instructions (race Description column, `set_creation_choice` tool mandates) but is **never called** in `app/`. Dead code risks agents re-wiring the old LLM-driven creation path.

## Evidence (code)

- `get_step_prompt` defined at `creation.py` ~639–728; grep shows no callers under `app/`.
- Session early segment used `set_creation_choice` via LLM tools (pre-code-first); current path uses `_creation_turn` + `_execute_creation_choice` only.

## Acceptance criteria

- [x] Remove `get_step_prompt()` or move a minimal step hint into code-first docs only.
- [x] Grep `app/` confirms no references.
- [x] Domain spec states creation prompts live in `_auto_present_*` / `format_*_table` only.

## Expected files

- `app/gm/creation.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Changelog note: removed legacy prompt builder.

## Notes

Low risk cleanup; do after APP-069/067 to avoid confusion during refactors.
