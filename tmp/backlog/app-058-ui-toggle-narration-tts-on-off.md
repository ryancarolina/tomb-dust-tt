# APP-058: UI toggle for narration (TTS) on/off

| Field | Value |
|-------|-------|
| **ID** | APP-058 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) |
| **Created** | 2026-05-20 |

## Summary

Players need a **runtime control** to turn GM **spoken narration (TTS) on or off** without editing `config.yaml`. When off, the narration **panel still shows text**; audio playback is skipped (same effect as `tts.mode: text_only` for playback only). Config default (`speak_dialogue`, `speak_all`, etc.) applies when the toggle is on.

## Acceptance criteria

- [ ] A visible **Narration** (or **Voice**) toggle control in the PyGame UI (sidebar or narration header — match existing panel styling).
- [ ] **On:** TTS runs per current `config.yaml` `tts.mode` after each GM turn (existing behavior).
- [ ] **Off:** no `speak_scene` / TTS queue calls; narration lines still appear in the panel with voice colors.
- [ ] Toggling **off** while speaking stops current audio immediately (`request_stop` or equivalent).
- [ ] Toggle state **persists for the session** (survives turns; restore on resume if app save includes UI prefs — document choice in domain spec).
- [ ] Clear visual state (label, icon, or chip) so the player knows whether voice is on or off.
- [ ] Domain specs updated: [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) (control + layout), [`app-tts-narration-spec.md`](../app-tts-narration-spec.md) (runtime mute vs config `text_only`).

## Expected files

- `app/ui/app.py`
- `app/ui/panels/sidebar.py` and/or `app/ui/panels/narration.py`
- `app/config.yaml` _(optional: default for toggle if persisted to config)_
- `tmp/app-pygame-ui-spec.md`
- `tmp/app-tts-narration-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update the domain spec checklist / changelog in [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md) and [`app-tts-narration-spec.md`](../app-tts-narration-spec.md).
3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.

## Notes

- **Not in scope:** hiding the narration text panel — only **audio** toggle unless product decides otherwise during implementation.
- **Related:** [APP-041](app-041-strip-status-tags-before-tts.md) (strip tags before TTS), [APP-042](app-042-tts-stop-on-player-interrupt.md) (interrupt on input).
- Config `tts.mode: text_only` remains the global default for users who never want voice; this toggle is for in-session control when config allows speech.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-042 | related — both affect stop/interrupt behavior |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-058 --task narration-tts-toggle
python tmp/backlog/claim_ticket.py release APP-058 --done
```
