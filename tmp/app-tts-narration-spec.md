# Spec — App TTS & Narration

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress (baseline shipped)  
**Owns:** TTS integration in UI/orchestrator, voice config, narration panel behavior, engine scene parse (`play/tomb_gm/services/tts/`)

---

## Spec

- TTS via **edgeTTS** when `config.yaml` `tts.mode` is `speak_all` or `speak_dialogue`.
- `text_only` skips audio; narration panel still updates.
- NPC voices from `config.yaml` → `tts.npc_voices`; narrator default voice.
- Narration lines tagged with `voice` key for panel coloring + TTS voice selection.
- Speak queue serial; **stop on player interrupt** — when `_turn_state == "speaking"`, `_submit()` calls `request_stop()` before the next turn (APP-042).

### Creation + combat

- Speak after GM narration each turn unless `text_only`.
- Fiction-only text to TTS (no roll math, no status tags in the **speak payload**).

### Status tag strip before TTS (APP-041)

**Problem:** Location / Phase / Awaiting metadata must be visible in the narration panel but must not be synthesized.

**Choke point:** `play/tomb_gm/services/tts/scene.py` — `parse_scene()` builds the speak payload. The PyGame client calls it once per turn; `speak_scene(..., lines=…)` uses those lines, not the raw narration string.

**Display vs speak**

| Consumer | Source | Status tags |
|----------|--------|-------------|
| Narration panel | Raw string from `orchestrator.process_turn()` via `("narration_text", narration)` in `app/ui/app.py` | **Shown** (footers, `Awaiting:`, bracket lines) |
| TTS / `speak_scene` | `parse_scene(narration)` → `{text, voice}[]` | **Stripped** |

Do **not** strip status tags in the UI layer or before queuing `narration_text`. All TTS sanitization for status tags lives in `parse_scene` (and helpers it calls).

**Strip scope (speak payload only)**

After `_strip_ui`, `parse_scene` runs a status-tag pass (`_strip_status_tags`) then existing `_strip_brackets` / `_strip_markup`. The pass must remove:

- Bracket blocks `[Location: …]`, `[Phase: …]` (including inline in prose).
- Inline `Awaiting: TOKEN` (`TOKEN` = `[A-Z0-9_]+`).
- Unclosed `[Location:…` / `[Phase:…` fragments through end of line.
- Whole-line unbracketed footers (`Location: …`, `Phase: …`, pipe-separated `Location: … | Phase: … | Awaiting: …`) via line metadata rules in `_strip_ui` / `_is_ui_metadata`.

**Out of scope here:** creation compose sanitizers (`strip_llm_status_tags` in `app/gm/creation.py` — APP-073), code-owned exploration footers (APP-077), tomb_gm CLI `cmd_speak --text` / `--lines` (dev bypass of `parse_scene` — canonical play always uses `parse_scene`). Those reduce upstream drift; APP-041 is the last line of defense before audio on the **player path**.

**Tests:** `play/tomb_gm/tests/test_tts_scene.py` — leak-matrix fixtures (inline `Awaiting:`, unbracketed Location/Phase lines, unclosed brackets); existing Holt scene voice-split tests must not regress.

---

## Task checklist

- [x] edgeTTS dependency
- [x] Narration panel per-voice colors
- [x] NPC card voice animation hook
- [x] APP-041 — status tag strip in `parse_scene` (speak only; panel unchanged)
- [x] APP-042 — TTS stop on player interrupt (`app/ui/app.py` `_submit`)
- [ ] APP-043 — document TTS voice keys in spec
- [ ] APP-058 — UI toggle narration TTS on/off

**Open work:** [APP-043](backlog/app-043-document-tts-voice-keys-in-spec.md) (cancelled → APP-084), [APP-058](backlog/app-058-ui-toggle-narration-tts-on-off.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Tests

```bash
PYTHONPATH=play python -m pytest play/tomb_gm/tests/test_tts_scene.py play/tomb_gm/tests/test_tts.py -q
```

- Manual: `speak_all` — panel shows status footers; audio does not read Location/Phase/Awaiting.
- `text_only`: no TTS call, panel still updates.
- APP-041: parametrized `parse_scene` fixtures for inline/unbracketed/unclosed status (see run spec).

---

## File map

| File | Role |
|------|------|
| `app/config.yaml` | `tts.mode`, `tts.npc_voices` |
| `app/ui/app.py` | Turn loop: `parse_scene` → TTS thread; raw `narration` → panel |
| `app/ui/panels/narration.py` | Display full narration text |
| `app/ui/panels/npc_card.py` | Speaker display |
| `app/gm/orchestrator.py` | Narration string assembly (may include status footers) |
| `play/tomb_gm/services/tts/scene.py` | `parse_scene`, status strip, voice split |
| `play/tomb_gm/services/tts/queue.py` | `speak_scene` queue |
| `play/tomb_gm/tests/test_tts_scene.py` | Scene parse + APP-041 status strip |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created |
| 2026-05-21 | APP-041 done: `_strip_status_tags` in `parse_scene` after `_strip_ui`, before `_strip_brackets`; inline Location/Phase/Awaiting removed from TTS only; `test_tts_scene.py` regression |
| 2026-05-21 | APP-041 PM: § Status tag strip before TTS; file map + tests; display/speak split |
| 2026-05-21 | APP-041 PM r2: panel AC on ticket; CLI `--text`/`--lines` dev-only non-goal |
| 2026-05-22 | **APP-042 done:** player submit during TTS calls `request_stop()` in `app/ui/app.py` before next turn starts |
