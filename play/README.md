# Play — engine & saves

Runtime code and data for Tomb Dust sessions. **Players use the standalone app** — not this folder directly.

| Play the game | [`../app/README.md`](../app/README.md) — `python main.py` |
|---------------|-------------------------------------------------------------|

Canon (rules, world JSON) lives in **[`build/`](../build/)** — do not edit that tree during play.

```
play/
  workspace/       ← Saves, SQLite, campaigns (.local/ is gitignored)
  tomb_gm/         ← Python engine (used by app/gm/bridge.py)
  docs/            ← Pointer to tmp/ app specs (see README there)
```

## How the app uses this tree

The PyGame app (`app/main.py`) imports `play/tomb_gm/` via `GameBridge` and stores saves under `play/workspace/` (default workspace). You do not run `python -m tomb_gm` or use Cursor chat to play.

## Workspace config (advanced)

If debugging the engine directly, copy [`workspace/config.example.yaml`](workspace/config.example.yaml) → `workspace/config.yaml`.

- **`content_root`** points at [`build/`](../build/) (canon).
- **Saves** live under `workspace/.local/` and `workspace/campaigns/`.

## Developer docs

- **App specs:** [`tmp/app-master-spec.md`](../tmp/app-master-spec.md) (registry of all `tmp/app-*-spec.md`)
- **Canon ↔ engine:** [`build/docs/engine-integration.md`](../build/docs/engine-integration.md)
- [docs/README.md](docs/README.md) — legacy `play/docs/` specs removed
