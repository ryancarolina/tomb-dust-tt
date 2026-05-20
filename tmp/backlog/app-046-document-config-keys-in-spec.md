# APP-046: Document config keys in spec

| Field | Value |
|-------|-------|
| **ID** | APP-046 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | done |
| **Domain spec** | [`app-shell-config-spec.md`](../app-shell-config-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

New config keys added without spec updates.

## Acceptance criteria

- [x] Document all config keys in app-shell-config-spec.md when present.

## Expected files

- `app/config.yaml`
- `tmp/app-shell-config-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-shell-config-spec.md`](../app-shell-config-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-046-document-config-keys-in-spec`

Default LLM switched to `google/gemini-3.1-flash-lite` in `app/config.yaml` (player trial). Full key table in `tmp/app-shell-config-spec.md` § `config.yaml` keys.
