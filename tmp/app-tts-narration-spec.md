# Spec — App TTS & Narration

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress (baseline shipped)  
**Owns:** TTS integration in UI/orchestrator, voice config, narration panel behavior

---

## Spec

- TTS via **edgeTTS** when `config.yaml` `tts.mode` is `speak_all` or `speak_dialogue`.
- `text_only` skips audio; narration panel still updates.
- NPC voices from `config.yaml` → `tts.npc_voices`; narrator default voice.
- Narration lines tagged with `voice` key for panel coloring + TTS voice selection.
- Speak queue serial; interrupt/stop on new turn (if implemented).

### Creation + combat

- Speak after GM narration each turn unless `text_only`.
- Fiction-only text to TTS (no roll math, no `[Awaiting:` tags).

---

## Task checklist

- [x] edgeTTS dependency
- [x] Narration panel per-voice colors
- [x] NPC card voice animation hook
- [ ] Strip status tags before TTS payload
- [ ] `speak --stop` equivalent on player interrupt (optional)
- [ ] Document voice keys in config.yaml in this spec

---

## Tests

- Manual: `speak_all` speaks last narration line.
- `text_only`: no TTS call, panel still updates.

---

## File map

| File | Role |
|------|------|
| `config.yaml` | `tts.mode`, `tts.npc_voices` |
| `ui/panels/narration.py` | Display |
| `ui/panels/npc_card.py` | Speaker display |
| `gm/orchestrator.py` | Narration line `{text, voice}` assembly |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created |
