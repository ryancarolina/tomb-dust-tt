# Play workspace (saves & sessions)

Runtime data for Tomb Dust. **Canon** is in [`build/`](../../build/) — never store rule edits or new monsters only in this folder.

The **PyGame app** (`app/main.py`) reads and writes this workspace via `GameBridge`. Players do not manage these files by hand.

| Path | Purpose |
|------|---------|
| `config.yaml` | Points `content_root` at `build/` (copy from `config.example.yaml`) |
| `.local/` | `memory.db`, `active.json`, TTS cache (gitignored) |
| `campaigns/` | Per-campaign logs and exports |

See [../README.md](../README.md) and [../../app/README.md](../../app/README.md).
