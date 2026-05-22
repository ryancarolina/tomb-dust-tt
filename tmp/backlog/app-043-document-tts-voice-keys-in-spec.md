# APP-043: Document TTS voice keys in spec

| Field | Value |
|-------|-------|
| **ID** | APP-043 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | cancelled |
| **Superseded by** | [APP-084](app-084-key-npc-canon-registry.md) — key NPC registry + voice resolution order in TTS spec |
| **Domain spec** | [`app-tts-narration-spec.md`](../app-tts-narration-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Voice config keys undocumented in spec.

## Acceptance criteria

- [ ] Document voice keys from config.yaml in app-tts-narration-spec.md.

## Expected files

- `app/config.yaml`
- `tmp/app-tts-narration-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-tts-narration-spec.md`](../app-tts-narration-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

- **Cancelled (2026-05-22)** — Close voice-key documentation as part of APP-084 spec sync (registry schema, `edgeVoice`, config override policy). Do not implement separately.
