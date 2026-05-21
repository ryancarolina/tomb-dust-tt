# Spec — GameBridge (App ↔ Engine)

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/bridge.py`  
**Engine contract:** [`build/docs/engine-integration.md`](../build/docs/engine-integration.md)

---

## Spec

`GameBridge` is the **only** app path to mechanical truth. Wraps `play/tomb_gm` with a stable Python API — no raw CLI from UI.

### Typed args from orchestrator (APP-080)

Methods invoked via LLM tools receive **already-normalized** Python types from the orchestrator (`normalize_tool_args` in [`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md) § Tool argument normalization). Bridge methods do **not** strip XML/tool markup or coerce string integers — that boundary lives in `app/gm/tool_args.py`. Bridge may still accept documented aliases (e.g. `enter_dungeon` `site_id` / `site_address`) when normalized by orchestrator before `**args` dispatch.

### Surface areas (must stay in sync with this spec)

| Area | Methods |
|------|---------|
| Health | `init`, `status`, `check`, `suggest` |
| Campaign/session | `campaign_new`, `session_start`, `session_resume`, `has_save`, `end_session`, `wipe_all_data`, `force_close_all_sessions` |
| Character | `roll_attributes`, `character_create`, `roster_set`, `list_known_spells` |
| Rolls | `roll_d20` |
| World | `world_travel`, `world_where`, `world_exits`, `wilderness_encounter`, `compass_exits`, `enter_dungeon`, `exit_dungeon`, `move_room`, `advance_scene` |
| Site | `site_enter`, `site_move`, `search_site`, `interact_feature` |
| Combat | `start_combat`, `combat_attack`, `combat_action`, `combat_end`, `run_combat_monster_turns`, `start_combat_from_trigger`, `cast_spell`, `fortune_spend` |
| Extraction | `set_phase`, `clock_tick`, `short_rest` |
| Economy/inventory | `list_inventory`, `equip_item`, `unequip_item`, `grant_loot`, `buy_item`, `sell_item`, `list_stash`, `list_vendor` |
| Death | `process_delver_death`, `extract_death_from_mechanical` |
| Memory | `memory_recall`, `remember_fact`, `build_recap` |
| Beat | `process_beat` |

New engine features **must** land here before orchestrator/tools expose them.

---

## Task checklist

- [x] Core bridge methods wired to tomb_gm services
- [x] Inventory v3 + economy methods (see app-economy-inventory-play-spec + engine-integration.md)
- [x] `enter_dungeon` accepts `site_address` and `site_id` alias
- [x] LLM tool methods receive typed args from orchestrator normalizer (APP-080)

**Open work:** [APP-033](backlog/app-033-sqlite-threading-policy.md), [APP-047](backlog/app-047-gamebridge-api-appendix.md), [APP-048](backlog/app-048-fix-memoryrecall-topk-param.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Tests

```bash
python -m pytest play/tomb_gm/tests -q
```

- Bridge smoke: `status()` → `ok: true` after init.
- Each new method: golden JSON fixture in `app/tests/test_bridge.py` (when added).

---

## File map

| File | Role |
|------|------|
| `gm/bridge.py` | All engine calls |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | APP-080 done: typed-args contract — orchestrator normalizes before `**args` dispatch; bridge does not strip markup or coerce scalars |
| 2026-05-21 | APP-080 cross-link: orchestrator supplies typed tool args; bridge assumes clean types (no markup stripping) |
| 2026-05-20 | Spec created; method inventory from bridge.py |
| 2026-05-20 | APP-048: `memory_recall(query, top_k=5)` passes `top=top_k` to engine `recall_facts()` |
