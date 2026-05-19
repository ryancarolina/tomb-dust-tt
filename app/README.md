# Tomb Dust — Standalone PyGame Application

A MUD-client style extraction-fantasy TTRPG powered by an LLM Game Master.

## Quick Start

```bash
cd app
pip install -r requirements.txt
python main.py
```

## Requirements

- Python 3.11+
- An OpenRouter API key in `app/.env` (format: `OPENROUTER_API_KEY=sk-or-v1-...`)
- The full `tomb-dust` project tree (this app imports directly from `play/tomb_gm/` and `build/`)

## Architecture

```
app/
├── main.py           # Entry point — sets sys.path, loads config, launches PyGame
├── config.yaml       # LLM model, TTS voices, UI sizing
├── .env              # OPENROUTER_API_KEY (not committed)
├── requirements.txt  # Python dependencies
├── gm/
│   ├── bridge.py     # Direct Python API over tomb_gm engine
│   ├── openrouter.py # OpenAI-compatible client for OpenRouter
│   ├── orchestrator.py  # Turn loop: player → LLM → tools → narration
│   ├── tools.py      # Tool schemas for LLM function calling
│   ├── system_prompt.py # GM persona and rules
│   └── context.py    # Build LLM context from game state
└── ui/
    ├── app.py        # Main loop, event handling, thread-safe updates
    ├── theme.py      # Colors, fonts, sizing
    ├── rich_text.py  # Word-wrapped styled text rendering
    └── panels/
        ├── narration.py  # Scrolling rich-text narration display
        ├── input_box.py  # Text input with history and suggestion buttons
        ├── stats.py      # HP bar, Fortune dots, Gold, Phase badge
        ├── map_view.py   # Clickable AV-GRID mini-map
        ├── npc_card.py   # Current speaker with voice animation
        └── sidebar.py    # Combines NPC card + stats + map
```

## Features

- **Rich narration panel** with per-voice colored text and scroll
- **Text-to-speech** via edgeTTS with distinct NPC voices
- **Clickable AV-GRID map** — click cells to travel
- **LLM GM** with full tool-calling (dice rolls, combat, travel, site exploration)
- **Session persistence** — auto-saves every 60s, restores on relaunch
- **d20 mechanics** enforced via tomb_gm engine (no fudging)

## Controls

| Key/Action | Effect |
|---|---|
| Type + Enter | Send action to GM |
| Up/Down arrows | Input history |
| Mouse wheel | Scroll narration |
| Click map cell | Travel to that address |
| Click suggestion | Send that action |
| Escape | Save and quit |

## Configuration

Edit `config.yaml` to change:
- LLM model (any OpenRouter model)
- TTS mode: `speak_all`, `speak_dialogue`, or `text_only`
- NPC voice assignments
- Window size and layout ratio
