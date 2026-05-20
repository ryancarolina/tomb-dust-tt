# Spec — PyGame UI

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress (baseline shipped)  
**Owns:** `app/ui/**`

---

## Spec

### Layout

- Split: narration (left), sidebar (right) — stats, map, NPC card, input.
- Configurable ratio via `config.yaml`.

### Panels

| Panel | Behavior |
|-------|----------|
| **Narration** | Scrollable rich text; per-voice colors; wheel scroll |
| **Input** | Enter to send; Up/Down history; suggestion chips |
| **Stats** | HP bar, Fortune, Gold, Phase badge — **from engine status, not LLM tags** |
| **Map** | AV-GRID clickable cells; visited highlight; click → travel action |
| **NPC card** | Current speaker + voice animation when TTS active |
| **Sidebar** | Composes stats + map + NPC |

### Controls

| Input | Action |
|-------|--------|
| Enter | Submit to orchestrator |
| Escape | Save + quit |
| Map click | Travel to cell (orchestrator handles) |

---

## Task checklist

- [x] Narration panel + rich text
- [x] Input box + history
- [x] Stats panel (HP, Fortune, Gold, Phase)
- [x] Map view + click travel
- [x] NPC card + sidebar
- [ ] Stats panel reads `GameBridge.status()` each turn (ignore LLM `[Phase:` tags)
- [ ] Show creation-step badge during `creation.active`
- [ ] Block map travel during character creation
- [ ] Inventory/stash summary strip (when economy-inventory-play spec UI tasks land)

---

## Tests

- Manual: scroll, history, map click sends travel string to orchestrator.
- Future: headless panel unit tests for `rich_text.py` wrap logic.

---

## File map

| Path | Role |
|------|------|
| `ui/app.py` | Main loop, thread-safe narration updates |
| `ui/theme.py` | Colors, fonts |
| `ui/rich_text.py` | Wrapped styled text |
| `ui/panels/*.py` | Panel widgets |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created from app/README architecture |
