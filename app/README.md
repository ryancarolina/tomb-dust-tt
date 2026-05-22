# Tomb Dust — Standalone PyGame Application

**This is the canonical way to play Tomb Dust.** The Cursor `@tomb-gm` chat flow and manual `tomb_gm` CLI are obsolete for players — they remain developer tools only.

A MUD-client style extraction-fantasy TTRPG powered by an LLM Game Master.

## Quick Start

```bash
cd app
pip install -r requirements.txt
python main.py
```

Type **`new game`** in the input box to start character creation. If you previously **finished** creation and have a living character saved, relaunch offers **`load game`** — use that to continue. If creation feels stuck, see **Stuck during character creation?** below.

## Stuck during character creation?

Use this when the creation desk feels broken — not when you quit mid-desk and the clerk resumes normally on the next answer.

**Common symptoms:**

- Relaunch after a mid-creation quit shows only **`new game`**, but you expected autosave to restore a finished character.
- Repeated clerk prompts, blank GM text, or the footer stuck on the wrong creation step.
- A setup error or `[Awaiting: new game]` after a failed reset.
- **`load game`** says there is no finished save yet (partial creation).

**Try once first:** if a single clerk input glitched (LLM hiccup), retry that answer once before wiping.

**Recovery:** type **`new game`** in the input box (also accepts **`start`** or **`new`**). This starts a fresh NAME desk and wipes in-progress creation (name, race, rolls, choices) and the current campaign session — it cannot be undone.

**Partial vs finished saves:**

- **Partial creation** (no living character on roster yet): relaunch shows **`new game`** only. Use **`new game`** when stuck. If the clerk desk resumes when you keep answering after relaunch, continue — you do **not** need **`new game`** unless something is wrong.
- **Finished save:** relaunch shows **`load game`**. Use that to resume exploration with your living character.

**Commands:**

| Command | When | Effect |
|---------|------|--------|
| **`new game`** (`start`, `new`) | New campaign or stuck creation reset | Fresh NAME desk; wipes in-progress creation and session data on success |
| **`load game`** (`continue`, `load`, `resume`) | Relaunch with a finished save | Restores your slotted living character run |

If **`new game`** fails to start a session, retry it once; if it keeps failing, quit and relaunch the app.

**Do not:** edit save files by hand or use developer CLI tools (`python -m tomb_gm`, Cursor `@tomb-gm`).

## Requirements

- Python 3.11+
- An OpenRouter API key in `app/.env` (format: `OPENROUTER_API_KEY=sk-or-v1-...`)
- The full `tomb-dust` project tree (this app imports directly from `play/tomb_gm/` and `build/`)

## Architecture

**Development specs:** [`tmp/app-master-spec.md`](../tmp/app-master-spec.md) — mandatory for all `app/` changes; spec ↔ code drift is never allowed.

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
- **Session persistence** — auto-saves every 60s and on quit; **finished** saves resume when you type **`load game`** at relaunch (not automatic from app autosave alone)
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
