# Engine integration contract (TD-090)

Contract between **this repository** (canon rules + world data) and any **playable game codebase** (simulation, client, server). Update when either side changes ownership or ship cadence.

---

## Repository roles

| Repo | Owns | Does not own |
|------|------|--------------|
| **`build/`** | `systems/` rules prose, `data/av-grid/`, content JSON, validators, `tools/rules_engine/` | Session saves, player SQLite |
| **`play/`** | `workspace/` saves, `tomb_gm/` engine (used by the app) — [play/README.md](../../play/README.md) | Canon edits; does not replace `build/data` or `build/systems` |
| **Game project** (e.g. sibling Unity/Godot build) | Runtime sim, UI, persistence implementation, content hot-load | Authoritative rule changes without syncing this repo |
| **Standalone app** | [`app/main.py`](../../app/main.py) — PyGame + LLM GM via `GameBridge` | Rule changes without content PRs in `build/` |

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

## Inventory v3 (character sheet + account stash)

**Version:** `inventory.inventoryVersion === 3` on character sheets and `account_state.stash`.

| Concept | Location | Notes |
|---------|----------|--------|
| Personal pack | `characters.sheet_json.inventory.pack[]` | 14 equipment slots; stackables use `quantity` / `uses` |
| Account stash | `campaigns.account_state_json.stash.pack[]` | Persists on PC death; hub-only transfer |
| Instance IDs | `instanceId` (`it-xxxxxxxx`) | Re-issue on corpse→looter and stash cross-boundary via `clone_pack_entries(reid=True)` |
| Loot grants | `grant_loot()` in `play/tomb_gm/services/loot_resolver.py` | All mechanical loot; never narration-only |
| Hub gates | `party_state.mode === "surface"` + AV-GRID `services.stash` / `vendorIds` / `fence` | See `play/tomb_gm/services/hub.py` |

**CLI:** `inventory list|equip|unequip|use` · `economy buy|sell|stash` (by `--instance` where applicable)

**Migration:** v2→v3 on `ensure_normalized()` — `body`→`chest`, `rations-N`→`rations` + `uses`, stack merge.

**Deferred:** encumbrance (TD-023/TD-057); composable loot-table v2 JSON (v1 adapter active); ammo auto-decrement on ranged attacks (use `inventory use` manually).

---

## Drift prevention

| Change type | Required action |
|-------------|----------------|
| New location | `av-grid.json` + validate + location markdown AV-GRID field |
| New weapon/spell | JSON + schema + `systems/magic/` doc sync |
| Rule math change | Bump `rulesVersion`; update `tools/rules_engine` tests |
| Breaking grid | Bump `av-grid.json` `version` |

Do **not** fork parallel rule files (`option-d-*`). One d20 system only.

---

## Related

- [AGENTS.md](../../AGENTS.md) — agent and content workflow
- [data/schemas/README.md](../data/schemas/README.md) — entity schemas
- [RULESCHANGELOG.md](../RULESCHANGELOG.md) — semver history (when bumped)
- [app/README.md](../../app/README.md) — **how to play** (PyGame client)
- [tmp/app-gamebridge-spec.md](../../tmp/app-gamebridge-spec.md) — app ↔ engine API
- [tmp/app-master-spec.md](../../tmp/app-master-spec.md) — app development spec registry
