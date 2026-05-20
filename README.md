# Tomb Dust

Hardcore extraction fantasy TTRPG — rules, world data, and a **PyGame standalone app** with an LLM Game Master.

## Repository layout

```
ttTomb-Dust/
  app/            ← PLAY the game (PyGame client — start here)
  build/          ← BUILD the game (canon — edit here)
  play/           ← Engine + saves (used by the app; not a player UI)
  AGENTS.md       ← Rules for content agents
```

| Directory | Use |
|-----------|-----|
| **[`app/`](app/README.md)** | **How to play** — PyGame window, LLM GM, TTS, map |
| **[`build/`](build/README.md)** | `data/`, `systems/`, validators, integration docs |
| **[`play/`](play/README.md)** | `tomb_gm/` engine, `workspace/` saves (developer reference) |

## Quick start (play)

```powershell
cd app
pip install -r requirements.txt
# Create app/.env with OPENROUTER_API_KEY=sk-or-v1-...
python main.py
```

In the game window, type **`new game`** to begin character creation, or continue if a save restores.

**To edit canon:** work under `build/` — see [AGENTS.md](AGENTS.md).
