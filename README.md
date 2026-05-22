# Tomb Dust

**Hardcore extraction fantasy** — a d20 TTRPG where delvers buy Registry stamps, push into dangerous sites, and try to leave with salvage before the map wins. Death is common; progress is deeds, skills, and what you extract—not character levels alone.

**Play today:** a standalone **PyGame client** with an **LLM Game Master**, voice narration, and a clickable world map. No Cursor chat, no manual CLI at the table—launch the app and type at the clerk.

---

## Play

```powershell
cd app
pip install -r requirements.txt
# Create app/.env with: OPENROUTER_API_KEY=sk-or-v1-...
python main.py
```

| Command | Effect |
|---------|--------|
| **`new game`** | Start at the Registry desk — character creation (name, race, stats, skills, spells) |
| **`load game`** | Resume a **finished** save with a living character on the roster |

Full controls, recovery tips, and config: **[`app/README.md`](app/README.md)**

### What you get in the client

- **Narration panel** — scrolling GM prose with per-speaker colors (clerk, sergeant, delver voices)
- **Text-to-speech** — optional edgeTTS; distinct voices per NPC
- **Sidebar** — HP, Fortune, gold, phase, **Registry creation step** during intake, current speaker
- **AV-GRID map** — 3×3 clickable cells; travel by click or typed commands (`travel to …`)
- **Mechanical truth** — d20 resolution, combat, travel, and site entry run through the **`tomb_gm` engine**; the GM narrates outcomes, not inventing rolls
- **Saves** — auto-save on quit and periodic save; resume with **`load game`** when a run is on the roster

Typical loop: **Registry hub (Breley)** → buy your claim → **enter the undercrypt** → fight, loot, retreat → **extract** to surface → fence salvage and train skills.

---

## Setting (one paragraph)

The **Registry** sells map stamps tied to **AV-GRID** addresses (`32-C` surface, `32-C-UG-1` undercrypt, veil layers, and deeper). Wrong layer or a blown threat clock means **Tomb Dust**—ash left behind when the party does not extract. Tone and economy: [`build/systems/world/extraction.md`](build/systems/world/extraction.md).

---

## Repository layout

```
ttTomb-Dust/
  app/       ← PLAY — PyGame client (start here)
  build/     ← BUILD — canon rules, AV-GRID JSON, monsters, tools
  play/      ← ENGINE + saves — tomb_gm Python engine, workspace SQLite
  AGENTS.md  ← Agent/content rules (AV-GRID, d20, backlog workflow)
```

| Tree | Purpose |
|------|---------|
| **[`app/`](app/README.md)** | Player entry — UI, LLM orchestrator, GameBridge |
| **[`build/`](build/README.md)** | Canon data and rules; validate with `build/tools/` |
| **[`play/`](play/README.md)** | Engine package and campaign workspace (used by the app) |

**Obsolete for players:** Cursor `@tomb-gm` chat GM and `python -m tomb_gm` as a table session. Those remain **developer** debugging paths only.

---

## Develop

| Task | Where |
|------|--------|
| Edit world, monsters, grid | `build/data/`, `build/systems/` — see [AGENTS.md](AGENTS.md) |
| App behavior | `app/` — specs and backlog live under local **`tmp/`** (gitignored) |
| Engine / bridge | `play/tomb_gm/`, `app/gm/bridge.py` |
| Tests | `python -m pytest app/tests` · `python -m pytest play/tomb_gm/tests` |

After AV-GRID changes:

```powershell
python build/tools/av_grid.py validate
python build/tools/av_grid.py build-index
```

Content validation: `python build/tools/validate_content.py`

---

## License / status

Active development. Setting and mechanics under **`build/`** are the source of truth; the app is the canonical player experience.
