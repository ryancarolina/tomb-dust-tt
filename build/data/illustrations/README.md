# Bundled illustrations (`build/data/illustrations/`)

Static UI art shipped with the game — not per-campaign generated assets.

| File | Use | Notes |
|------|-----|-------|
| `tomb-dust-title.png` | Default **IllustrationPanel** slot (boot + idle) | Flux Klein 4B, H module-cover style — APP-099 |
| `tomb-dust-title.json` | Sidecar metadata (prompt, model, date) | Dev reference only |

**Portraits** for NPCs live in [`../portraits/`](../portraits/) and seed campaign cache via `ImageService`.
