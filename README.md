# Tomb Dust

Hardcore extraction fantasy TTRPG — rules, world data, and (in development) a **Cursor AI Game Master**.

## Repository layout

```
ttTomb-Dust/
  build/          ← BUILD the game (canon — edit here)
  play/           ← PLAY the game (sessions — never commit saves)
  .cursor/        ← Agent skills (tomb-gm)
  AGENTS.md       ← Rules for content agents
```

| Directory | Use |
|-----------|-----|
| **[`build/`](build/README.md)** | `data/`, `systems/`, validators, design docs, backlog |
| **[`play/`](play/README.md)** | `workspace/` saves, `tomb_gm/` engine, play docs |

**To play (when built):** `@tomb-gm` in Cursor — see [play/README.md](play/README.md).  
**Full spec:** [play/docs/tomb-gm-implementation-spec.md](play/docs/tomb-gm-implementation-spec.md)

**To edit canon:** work under `build/` — see [AGENTS.md](AGENTS.md).
