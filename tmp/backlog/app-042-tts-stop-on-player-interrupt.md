# APP-042: TTS stop on player interrupt

| Field | Value |
|-------|-------|
| **ID** | APP-042 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-tts-narration-spec.md`](../app-tts-narration-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Optional: stop speech when player sends new input.

## Acceptance criteria

- [x] speak --stop equivalent on player interrupt (optional).

## Expected files

- `app/ui/app.py` (`_submit` → `request_stop()` when `_turn_state == "speaking"`)

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-tts-narration-spec.md`](../app-tts-narration-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

Player submit during TTS calls `tomb_gm.services.tts.queue.request_stop()` before starting the next turn.
