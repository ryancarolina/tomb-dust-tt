# Build — game content & tooling

Everything here defines **what Tomb Dust is**. Agents and tools treat this tree as **canon** during play (read-only unless you are authoring).

| Path | Contents |
|------|----------|
| [`data/`](data/av-grid/README.md) | AV-GRID JSON, weapons, monsters, spells, sites, loot, deeds |
| [`systems/`](systems/README.md) | Rules and lore markdown |
| [`tools/`](tools/) | `av_grid.py`, `validate_content.py`, `rules_engine/` |
| [`docs/`](docs/engine-integration.md) | Engine integration, content pipeline |
| [`backlog/`](backlog/README.md) | Design backlog and checklists |
| [`assets/`](assets/) | Art and reference archives (not runtime canon) |

## Common commands (from repo root)

```powershell
python build/tools/validate_content.py
python build/tools/av_grid.py validate
python build/tools/av_grid.py build-index
python -m pytest build/tools/rules_engine
```

## Do not put here

- Player saves, SQLite, or session logs → [`play/workspace/`](../play/workspace/)
- Active campaign state → `play/workspace/.local/`
