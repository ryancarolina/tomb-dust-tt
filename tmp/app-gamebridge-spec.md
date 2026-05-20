# Spec — GameBridge (App ↔ Engine)

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/bridge.py`  
**Engine contract:** [`build/docs/engine-integration.md`](../build/docs/engine-integration.md)

---

## Spec

`GameBridge` is the **only** app path to mechanical truth. Wraps `play/tomb_gm` with a stable Python API — no raw CLI from UI.

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
- [ ] Document each method’s `{ok, error}` shapes in § API appendix below
- [ ] Thread-safe / single-connection policy (llm-orchestrator spec)
- [ ] `memory_recall` param names match engine (`top_k` not broken)

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
| 2026-05-20 | Spec created; method inventory from bridge.py |
