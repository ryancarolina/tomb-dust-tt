# APP-044: Startup health logging

| Field | Value |
|-------|-------|
| **ID** | APP-044 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-shell-config-spec.md`](../app-shell-config-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Startup should log workspace, model, content_root for support.

## Acceptance criteria

- [ ] Log workspace path, model id, content_root pin at startup.

## Expected files

- `app/main.py`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-shell-config-spec.md`](../app-shell-config-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

_Add implementation notes, blockers, or PR links here._
