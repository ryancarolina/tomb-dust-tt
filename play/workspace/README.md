# Play workspace (saves & sessions)

Runtime data for Tomb Dust lives here. **Canon** is in [`build/`](../../build/) — never store rule edits or new monsters only in this folder.

| Path | Purpose |
|------|---------|
| `config.yaml` | Points `content_root` at `build/` (copy from `config.example.yaml`) |
| `.local/` | `memory.db`, `active.json`, TTS cache (gitignored) |
| `campaigns/` | Per-campaign logs and exports |

The **`@tomb-gm`** agent uses `--workspace play/workspace` (or equivalent) for all CLI calls.

See [../README.md](../README.md) and [../docs/cursor-tomb-gm-spec.md](../docs/cursor-tomb-gm-spec.md).
