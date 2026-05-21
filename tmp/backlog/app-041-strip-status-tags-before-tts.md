# APP-041: Strip status tags before TTS

| Field | Value |
|-------|-------|
| **ID** | APP-041 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | done |
| **Domain spec** | [`app-tts-narration-spec.md`](../app-tts-narration-spec.md) |
| **Created** | 2026-05-20 |

## Summary

TTS reads [Location:/Phase: tags aloud.

## Acceptance criteria

- [ ] Strip status tags before TTS speak payload (`parse_scene` output has no Location / Phase / Awaiting fingerprints).
- [ ] Narration panel still displays status tags (Location / Phase / Awaiting); strip applies to TTS speak payload only — raw `narration_text` queue unchanged.

## Expected files

- `play/tomb_gm/services/tts/scene.py`
- `play/tomb_gm/tests/test_tts_scene.py`
- `tmp/app-tts-narration-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-tts-narration-spec.md`](../app-tts-narration-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

**Grooming 2026-05-20 — partial:** `play/tomb_gm/services/tts/scene.py` has `_SKIP_LINE` (skips `Awaiting:` lines) and `_strip_brackets()` before TTS. **Still open:** bracket tags like `[Location:…]` / `[Phase:…]` in narration body may still reach TTS; APP-077 covers code-owned exploration status footers (display layer). Keep ticket until spec + tests confirm full strip path.
