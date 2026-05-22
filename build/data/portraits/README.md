# Bundled portraits (`build/data/portraits/`)

Pre-approved PNGs for key entities. **`ImageService`** copies these into per-campaign cache on first resolve — no OpenRouter call.

| File | Entity id | Notes |
|------|-----------|-------|
| `marshal-garrick-holt.png` | `marshal-garrick-holt` | Spike prompt **H** — APP-098 |

Naming: `{entity_id}.png` matching cache keys (`npc/marshal-garrick-holt`, etc.).

Optional sidecar `{entity_id}.json` documents spike/source metadata only; campaign cache sidecar is written on seed.
