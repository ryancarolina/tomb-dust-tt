# APP-085: Quest system — key NPC quests, lifecycle, Quests tab UI

| Field | Value |
|-------|-------|
| **ID** | APP-085 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-quest-play-spec.md`](../app-quest-play-spec.md) _(create on claim)_ |
| **Created** | 2026-05-22 |

## Summary

Quests today are **memory-only** (`remember_fact` / LLM prose). There is no code-owned quest state, no opt-in accept/refuse, no quest log UI, and no inventory turn-in. Key NPCs ([APP-084](app-084-key-npc-canon-registry.md)) will offer quests defined in canon; this ticket adds the **quest engine**, **GM tools**, **persistence**, and a **Quests tab** on the left character panel (same tab pattern as [APP-062](app-062-left-character-panel-inventory-spells-tabs.md)).

**Design principle:** Quests are **never auto-assigned**. An NPC mention creates an **offer**; the player must **accept** (dialogue or tool) before the quest appears in the log. Refusing leaves the log unchanged (offer may remain available).

## Problem

| Today | Needed |
|-------|--------|
| Holt brother hook via narration + `remember_fact` | Code quest `holt-brothers-signet` tied to `marshal-garrick-holt` |
| No quest states | offered → accepted → (objectives) → completed / abandoned |
| No UI | **Quests** tab: title, giver, state, objective summary |
| `grant_loot` adds items | Quest detects `have_item`; **deliver** removes item ([APP-086](app-086-inventory-quest-item-bridge.md)) |

## Quest lifecycle

```text
hidden ──(trigger)──► offered ──(accept)──► accepted ──(objectives met)──► ready_to_turn_in
                              │                    │
                              │ refuse             ├──► completed (turn-in + rewards)
                              ▼                    └──► abandoned (player)
                           (not in log)                  failed (optional, quest-defined)
```

| State | In quest log UI? | Meaning |
|-------|------------------|---------|
| `hidden` | No | Prerequisites not met |
| `offered` | No | Player heard hook; can accept/refuse |
| `accepted` | Yes | Active; show objectives |
| `ready_to_turn_in` | Yes | All objectives done; return to giver |
| `completed` | Yes (collapsed / history) | Rewards applied |
| `abandoned` | Optional history | Player dropped |
| `failed` | Optional | Terminal (rare v1) |

**Refuse:** `offered` → stays offered or `declined` (hidden from log; may re-offer after time/phase — quest def flag).

## System architecture

```text
build/data/quests/quests.json          ← quest definitions (objectives, rewards, giver npc id)
build/data/npcs/key_npcs.json          ← questIds[] on key NPCs (APP-084)
        ↓
play/tomb_gm/services/quests.py      ← load defs, validate transitions
campaign.account_state_json.quests   ← per-campaign runtime state
        ↓
GameBridge                           ← list_quests, offer, accept, abandon, advance, complete, deliver
app/gm/tools.py                      ← LLM-callable quest tools ( gated )
app/ui/panels/character_panel.py     ← Backpack | Spells | Quests tabs (APP-062 + this ticket)
```

### Quest definition schema (canon JSON)

```json
{
  "id": "holt-brothers-signet",
  "displayName": "Brother's Signet",
  "giverNpcId": "marshal-garrick-holt",
  "summary": "Recover Marshal Holt's brother's signet ring from Breley undercrypt (32-C-UG-1).",
  "offerTrigger": { "type": "talk_to_npc", "npcId": "marshal-garrick-holt" },
  "objectives": [
    { "id": "enter-undercrypt", "type": "visit_site", "siteAddress": "32-C-UG-1", "label": "Reach the undercrypt" },
    { "id": "recover-ring", "type": "have_item", "itemId": "holt-signet-ring", "label": "Recover the signet ring" },
    { "id": "return-ring", "type": "deliver_item", "itemId": "holt-signet-ring", "npcId": "marshal-garrick-holt", "label": "Return the ring to Holt" }
  ],
  "rewards": { "goldGp": 50, "factionRep": { "knights-of-breley": 1 } },
  "docPath": "systems/quests/holt-brothers-signet.md"
}
```

Objective types **v1:**

| type | Auto-check | Complete via |
|------|------------|--------------|
| `visit_site` | On `enter_dungeon` / `site_enter` ok | engine hook |
| `have_item` | On pack change / `list_inventory` | engine hook |
| `deliver_item` | — | GM tool `deliver_quest_item` + APP-086 |
| `talk_to_npc` | On quest tool at hub | manual advance |

### Runtime state (per campaign, `account_state.quests`)

```json
{
  "holt-brothers-signet": {
    "state": "accepted",
    "offeredAt": "2026-05-22T…",
    "acceptedAt": "…",
    "objectives": {
      "enter-undercrypt": "done",
      "recover-ring": "active",
      "return-ring": "pending"
    }
  }
}
```

Persist in `campaigns.account_state_json` (same tier as stash). Survive save/resume.

### GM / player actions (tools)

| Action | Tool / API | Notes |
|--------|------------|-------|
| NPC mentions quest | `offer_quest(quest_id)` | Sets `offered`; **not** in log until accept |
| Player accepts | `accept_quest(quest_id)` | Player intent or LLM after "I'll help" |
| Player refuses | `decline_quest(quest_id)` | Optional; not in log |
| Abandon | `abandon_quest(quest_id)` | From UI or dialogue |
| Turn in item | `deliver_quest_item(quest_id, item_id)` | APP-086 removes from pack; completes deliver objective |
| Complete | `complete_quest(quest_id)` | After all objectives done; apply rewards |

**Mechanical truth:** Same as loot — do not narrate quest accept/complete without tool `ok: true`. TurnTruth verify (future) can cross-check key NPC + quest state.

### Holt example flow

1. Player meets Holt at Breley → dialogue mentions brother's ring in **32-C-UG-1**.
2. Orchestrator/LLM calls `offer_quest("holt-brothers-signet")` when hook is offered.
3. Player: *"I'll find the ring"* → `accept_quest` → **Quests tab** shows *Brother's Signet — Accepted — Recover the signet ring*.
4. Player refuses → no log entry; `offered` remains (can ask again).
5. Player delves, finds ring → site loot grants `holt-signet-ring` → objective `recover-ring` → done.
6. Player returns: *"I have the ring"* → `deliver_quest_item` → item removed from pack, quest **completed**, gold/rep applied, UI updates.

## UI — Quests tab (APP-062 pattern)

Extend left **character panel** ([APP-062](app-062-left-character-panel-inventory-spells-tabs.md)):

```text
[ Backpack | Spells | Quests ]   ← tab bar (same component pattern)
```

**Quests tab body:**

- List **accepted** + **ready_to_turn_in** quests (not `offered`, not `hidden`).
- Each row: **title**, **giver** display name (from key NPC registry), **state badge** (Active / Ready to turn in / Completed).
- Expand or subtitle: current **active objective** label from quest def.
- Empty state: *"No active quests."*
- Refresh on `status` queue event (same cadence as Backpack).
- **Abandon** button per quest (confirm dialog) → `abandon_quest` on main thread via bridge.

Out of scope v1: click-to-track on map, quest journal prose, multi-step branching trees.

## Acceptance criteria

### Canon

- [ ] `build/data/quests/quests.json` with at least `holt-brothers-signet`.
- [ ] `build/data/schemas/quest.schema.json` + validate in content tooling.
- [ ] `build/systems/quests/holt-brothers-signet.md` + README index.
- [ ] `marshal-garrick-holt` in key NPC registry lists `questIds: ["holt-brothers-signet"]` (APP-084 / APP-085).

### Engine + bridge

- [ ] Quest service + persistence in `account_state_json`.
- [ ] Bridge: `list_quests`, `offer_quest`, `accept_quest`, `decline_quest`, `abandon_quest`, `complete_quest`, `deliver_quest_item` (deliver delegates to APP-086).
- [ ] Objective hooks on site entry and pack mutation.
- [ ] Rewards applied atomically on complete (gold to sheet, rep to account if supported).

### Orchestrator + tools

- [ ] GM tools registered; exploration loop calls bridge; failures narrated honestly.
- [ ] System prompt: offer/accept/complete require tools; never auto-accept.

### UI

- [ ] **Quests** tab on character panel; states match bridge `list_quests`.
- [ ] Abandon from UI works.
- [ ] APP-062 layout includes third tab (implement together or APP-062 first then 085 adds tab).

### Tests

- [ ] Accept/refuse: refuse → empty log; accept → listed.
- [ ] Holt E2E: offer → accept → grant item → deliver → completed + item gone from pack.
- [ ] Abandon removes from active list.

### Specs

- [ ] Create [`app-quest-play-spec.md`](../app-quest-play-spec.md); register in [`app-master-spec.md`](../app-master-spec.md).
- [ ] Cross-update [`app-economy-inventory-play-spec.md`](../app-economy-inventory-play-spec.md), [`app-pygame-ui-spec.md`](../app-pygame-ui-spec.md), [`app-gamebridge-spec.md`](../app-gamebridge-spec.md).

## Expected files

- `build/data/quests/quests.json`, `build/data/schemas/quest.schema.json`, `build/data/quests/README.md`
- `build/systems/quests/holt-brothers-signet.md`, `build/systems/quests/README.md`
- `build/data/npcs/key_npcs.json` _(questIds on Holt — APP-084)_
- `play/tomb_gm/services/quests.py`
- `app/gm/bridge.py`, `app/gm/tools.py`, `app/gm/orchestrator.py`
- `app/ui/panels/character_panel.py` _(Quests tab)_
- `app/ui/app.py`
- `app/tests/test_quest_flow.py`
- `tmp/app-quest-play-spec.md` _(new)_
- `tmp/app-pygame-ui-spec.md`, `tmp/app-master-spec.md`

## Inventory readiness ([APP-086](app-086-inventory-quest-item-bridge.md))

Quest delivery **depends** on inventory bridge work:

| Capability | Status today |
|------------|--------------|
| List pack / `list_inventory` | ✅ Bridge |
| Add item / `grant_loot` | ✅ Bridge |
| Equip / unequip | ✅ Bridge |
| **Has item by itemId** | ❌ Need bridge |
| **Remove instance on turn-in** | ❌ Domain only |
| **`kind: quest` in pack schema** | ❌ Schema drift |
| **Quest item catalog** | ❌ No `holt-signet-ring` in gear |
| **use_item consumable** | ❌ APP-039 (unrelated to turn-in) |
| **Backpack UI tab** | ❌ APP-062 open |

**Recommended wave:** APP-062 (panel shell) → APP-086 (inventory quest ops) → APP-084 (key NPCs, can parallel) → **APP-085** (quests + Quests tab).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-086 | **blocks** deliver_item + pack checks |
| APP-062 | **blocks** or **parallel** — Quests tab shares character panel |
| APP-084 | related — quest giver NPC ids + `questIds[]` on key NPCs |
| APP-087 | **blocks** Holt quest surface dialogue / direction Q&A before E2E |
| APP-088 | related — interim `remember_fact` guard; APP-085 owns quest state long-term |
| APP-080 | related — tool arg normalization |
| APP-039 | soft — consumables separate from quest turn-in |
| APP-047 | related — document new bridge methods when 085/086 close |
| APP-025 | related — extend hub loop test with quest accept path after 085 |
| APP-040 | related — economy E2E may include quest reward + item turn-in after 086 |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-086 --task inventory-quest-bridge
python tmp/backlog/claim_ticket.py APP-062 --task character-panel-tabs
python tmp/backlog/claim_ticket.py APP-085 --task quest-system
python tmp/backlog/claim_ticket.py release APP-085 --done
```

## Notes

- **Offers vs log:** UI and `list_quests(active_only=true)` exclude `offered` — player must accept.
- **LLM flavor:** NPC can mention quest in prose; state change only via tools.
- **Memory:** `remember_fact` may supplement recap; quest state is authoritative in `account_state`.
- **v2:** Faction rep rewards, quest chains, timed quests, TurnTruth verify for quest dialogue.
