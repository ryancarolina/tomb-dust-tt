# Engine integration contract (TD-090)

Contract between **this repository** (canon rules + world data) and any **playable game codebase** (simulation, client, server). Update when either side changes ownership or ship cadence.

---

## Repository roles

| Repo | Owns | Does not own |
|------|------|--------------|
| **`build/`** | `systems/` rules prose, `data/av-grid/`, content JSON, validators, `tools/rules_engine/` | Session saves, player SQLite |
| **`play/`** | `workspace/` saves, `tomb_gm/` engine, Cursor AI GM — [play/README.md](../../play/README.md) | Canon edits; does not replace `build/data` or `build/systems` |
| **Game project** (e.g. sibling Unity/Godot build) | Runtime sim, UI, persistence implementation, content hot-load | Authoritative rule changes without syncing this repo |
| **Cursor AI GM** (planned) | Agent + `play/tomb_gm` CLI — [play/docs/cursor-tomb-gm-spec.md](../../play/docs/cursor-tomb-gm-spec.md) | Rule changes without content PRs in `build/` |

**Rule of thumb:** if it affects **d20 math**, **AV-GRID**, or **mechanical content IDs**, it lands here first; the game **consumes** pinned exports.

---

## Version pinning

Every mechanical JSON record includes **`rulesVersion`** (semver, currently `1.0.0`). AV-GRID dataset has separate top-level **`version`** on `av-grid.json` (topology).

| Field | Scope | Game behavior |
|-------|-------|---------------|
| `rulesVersion` | Combat, skills, spells, items | **Warn** on minor mismatch; **reject** on major (engine policy) |
| `av-grid.json` `version` | World addresses | Rebuild nav/index on change |
| Git tag / commit | Full bundle | CI pins `content-manifest.json` (future) with commit hash |

---

## Content ship pipeline

1. Edit canon here → run validators:
   ```bash
   python build/tools/validate_content.py
   python build/tools/av_grid.py validate
   python build/tools/av_grid.py build-index
   python -m pytest build/tools/rules_engine
   ```
2. Export or submodule-copy `build/data/` + `build/systems/` (or generated bundles) into game project.
3. Game loads:
   - `data/av-grid/av-grid.json` + `index.json`
   - `data/weapons/weapons.json`, `data/monsters/*.json`, `data/spells/spells.json`
   - `data/sites/*.json`, `data/loot/tables.json`, `data/deeds/promotions.json`
   - `data/encounters/wilderness.json`, `data/av-grid/ledger-examples.json`
4. Human docs (`build/systems/`) remain reference for GMs and designers; **JSON wins** over prose when parsers disagree ([AGENTS.md](../../AGENTS.md)).

---

## Reference rules engine

`build/tools/rules_engine/` is a **minimal regression harness**, not the production sim. The game engine should:

- Reimplement or wrap the same formulas (skill bonus tiers, gritty crits, Magical Defense, PB by tier).
- Use `build/tools/rules_engine/test_core.py` as golden tests or port assertions to native tests.
- Extend for full combat rounds, spell effects, and extraction state machines.

---

## Site and encounter resolution

```
AvAddress (av-grid.json)
    → dangerRating, links.monsters
    → optional Site graph (data/sites/*.json)
    → Loot table tier (data/loot/tables.json siteLinks)
    → Monster stat blocks (data/monsters/*.json)
```

Engines should resolve monster **`id`** slugs, not display names.

---

## Drift prevention

| Change type | Required action |
|-------------|----------------|
| New location | `av-grid.json` + validate + location markdown AV-GRID field |
| New weapon/spell | JSON + schema + `systems/` doc sync |
| Rule math change | Bump `rulesVersion`; update `tools/rules_engine` tests |
| Breaking grid | Bump `av-grid.json` `version` |

Do **not** fork parallel rule files (`option-d-*`). One d20 system only.

---

## Related

- [AGENTS.md](../../AGENTS.md) — agent and content workflow
- [data/schemas/README.md](../data/schemas/README.md) — entity schemas
- [RULESCHANGELOG.md](../RULESCHANGELOG.md) — semver history (when bumped)
- [play/docs/cursor-tomb-gm-spec.md](../../play/docs/cursor-tomb-gm-spec.md) — Cursor AI GM
