# Play — run Tomb Dust

Everything here is **runtime**: sessions, saves, and the engine that drives the AI GM.  
Canon (rules, world JSON) lives in **[`build/`](../build/)** — do not edit that tree during play.

```
play/
  workspace/       ← Saves, config, campaigns (.local/ is gitignored)
  tomb_gm/         ← Python engine + CLI (invoked by @tomb-gm agent)
  docs/            ← AI GM spec and build roadmap
```

## How to play

1. Open the **repository root** in Cursor.
2. Invoke **`@tomb-gm`** — the agent sets up `workspace/`, resumes or starts a campaign, and runs all mechanics.
3. Players only chat: `[P1 Name] …` through `[P4]`, `[PARTY]`, `[OOC]`.

No terminal setup required for players.

## Workspace config

Copy [`workspace/config.example.yaml`](workspace/config.example.yaml) → `workspace/config.yaml` (the agent can do this on first invoke).

- **`content_root`** points at [`build/`](../build/) (canon).
- **Saves** live under `workspace/.local/` and `workspace/campaigns/`.

## Docs

- **[docs/tomb-gm-implementation-spec.md](docs/tomb-gm-implementation-spec.md)** — **full implementation spec** (CLI, DB, beats, memory, combat)
- [docs/tomb-gm-build-roadmap.md](docs/tomb-gm-build-roadmap.md) — section-by-section delivery order
- [docs/cursor-tomb-gm-spec.md](docs/cursor-tomb-gm-spec.md) — short architecture summary

## Engine status

`tomb_gm` CLI covers campaigns, travel, full character creation (race/genetics/life events/kit), combat, economy, encounters, memory, beat loop, and TTS. Invoke **`@tomb-gm`** in Cursor to play.
