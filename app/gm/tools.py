"""Tool schemas for LLM function calling — maps to GameBridge methods."""

from __future__ import annotations

SET_CREATION_CHOICE_TOOL = {
    "type": "function",
    "function": {
        "name": "set_creation_choice",
        "description": "Record the player's choice for the current creation step. Extract the choice from what the player said and pass it here. You MUST call this tool — it is the only way to advance.",
        "parameters": {
            "type": "object",
            "properties": {
                "step": {"type": "string", "description": "The current creation step", "enum": ["NAME", "RACE", "CLASS", "SKILLS", "SPELL_SCHOOLS", "SPELLS", "EQUIPMENT_GOLD"]},
                "value": {"type": "string", "description": "The player's choice. NAME: character name. RACE: race id (e.g. 'undead'). CLASS: class id (e.g. 'militia'). SKILLS: comma-separated skill names. SPELL_SCHOOLS: comma-separated school ids. SPELLS: comma-separated spell ids. EQUIPMENT_GOLD: 'confirmed'."},
            },
            "required": ["step", "value"],
        },
    },
}

COMBAT_ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "combat_action",
        "description": (
            "Submit the active PC's combat action. ONLY call on the current turn actor's turn. "
            "Use combatant ids from game state. After success, narrate mechanical results only."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["ATTACK", "CAST", "END_TURN"],
                    "description": "Combat action type",
                },
                "actor_id": {"type": "string", "description": "Must match current turn_id"},
                "target_id": {"type": "string", "description": "Target combatant id (ATTACK/CAST)"},
                "weapon_id": {"type": "string", "description": "Weapon id for ATTACK"},
                "spell_id": {"type": "string", "description": "Spell id from knownSpells for CAST"},
            },
            "required": ["action", "actor_id"],
        },
    },
}

FORTUNE_SPEND_TOOL = {
    "type": "function",
    "function": {
        "name": "fortune_spend",
        "description": "Spend 1 Fortune point to grant advantage on the next d20 roll. Pool = max(1, 1 + LUC mod). Refreshes at session start only.",
        "parameters": {
            "type": "object",
            "properties": {
                "character_id": {"type": "string", "description": "Character spending Fortune"},
            },
            "required": ["character_id"],
        },
    },
}

COMBAT_PC_TOOLS = [COMBAT_ACTION_TOOL, FORTUNE_SPEND_TOOL]

TOOLS = [
    # SET_CREATION_CHOICE_TOOL is injected separately during creation — not in normal play tools
    {
        "type": "function",
        "function": {
            "name": "roll_d20",
            "description": "Roll a d20 + modifier against a DC. YOU (the GM) roll all dice — the player never rolls. Use this for skill checks, saves, ability tests, and any uncertain outcome.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mod": {"type": "integer", "description": "Total modifier (attribute + PB + skill bonus). Use 0 if unknown."},
                    "dc": {"type": "integer", "description": "Difficulty class (easy=8, medium=12, hard=15, very hard=18)"},
                    "reason": {"type": "string", "description": "What the roll is for (e.g. 'Stealth check to sneak past guards')"},
                },
                "required": ["mod", "dc", "reason"],
            },
        },
    },
    # roll_attributes removed — now auto-executed by code during creation
    {
        "type": "function",
        "function": {
            "name": "process_beat",
            "description": "PRIMARY PLAY TOOL. Call this for EVERY player action during gameplay. Handles travel (detects 'go to', AV-GRID addresses, directions), site entry/movement, combat triggers, and search actions automatically. Always pass the player's raw action text. Returns narration_brief and mechanical_summary — base your narration on these. If this returns ok:false, narrate the failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "slot": {"type": "integer", "description": "Player slot (1-4)"},
                                "raw": {"type": "string", "description": "Player action text"},
                            },
                            "required": ["slot", "raw"],
                        },
                        "description": "Player action lines",
                    },
                    "auto_roll_wilderness": {"type": "boolean", "description": "Auto-roll wilderness encounters on travel"},
                    "auto_combat": {"type": "boolean", "description": "Auto-start combat if monsters are named"},
                    "include_party": {"type": "boolean", "description": "Include party roster in combat initiative"},
                },
                "required": ["lines"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "world_travel",
            "description": "Move the party to a new AV-GRID surface address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_address": {"type": "string", "description": "Destination AV-GRID address (e.g. '33-C')"},
                },
                "required": ["to_address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "world_where",
            "description": "Get current location info — cell data, nearby features, description.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "world_exits",
            "description": "List legal travel exits from current address.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "site_enter",
            "description": "Enter a delve site at the current address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_id": {"type": "string", "description": "Site identifier (e.g. 'breley-undercrypt')"},
                },
                "required": ["site_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "site_move",
            "description": "Move to a node within the current site.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Target node (e.g. 'ossuary-hall')"},
                },
                "required": ["node_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_combat",
            "description": (
                "Begin combat encounter with specified monsters. "
                "Blocked until encounter phase is engaged or ambush (APP-089)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "monster_specs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Monster specs as 'id:count' (e.g. ['grave-ghoul:2', 'ash-shade:1'])",
                    },
                    "include_party": {"type": "boolean", "description": "Add party to initiative"},
                },
                "required": ["monster_specs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "combat_attack",
            "description": "Make an attack roll in active combat. Use combatant ids from game state (e.g. character id for PCs, grave-ghoul-1 for monsters).",
            "parameters": {
                "type": "object",
                "properties": {
                    "attacker_id": {"type": "string", "description": "Attacker combatant id (PC character id or monster instance id)"},
                    "target_id": {"type": "string", "description": "Target combatant id"},
                    "weapon_id": {"type": "string", "description": "Optional weapon id from inventory"},
                },
                "required": ["attacker_id", "target_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "combat_end",
            "description": "End the current combat encounter.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_status",
            "description": "Get current session state: party location, phase, roster HP, combat, awaiting.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    # character_create removed — now auto-executed by code in _auto_finalize
    {
        "type": "function",
        "function": {
            "name": "memory_recall",
            "description": "Search campaign memory for relevant facts (NPCs, events, locations mentioned before). ALWAYS use this before answering questions about objectives, quests, or past events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Number of results (default 5)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Store an important fact in campaign memory (quest given, NPC met, item found, decision made). Use after significant events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The fact to remember (e.g. 'Marshal Holt tasked party with retrieving his brother's signet ring')"},
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Related entity names (NPCs, items, places)",
                    },
                    "importance": {"type": "integer", "description": "1-5 scale (3=default, 5=critical quest info)"},
                },
                "required": ["fact"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cast_spell",
            "description": "Cast a spell from the caster's knownSpells list only. Never invent spell ids. Canon examples: mend-light, consecrate-ground, ember-touch, static-lash.",
            "parameters": {
                "type": "object",
                "properties": {
                    "character_id": {"type": "string", "description": "Caster character ID"},
                    "spell_id": {"type": "string", "description": "Spell id from knownSpells (e.g. mend-light)"},
                    "target_id": {"type": "string", "description": "Target combatant ID (if attack/targeted spell)"},
                },
                "required": ["character_id", "spell_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_known_spells",
            "description": "List spells the character knows from the database. Call when the player asks what spells they know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "character_id": {"type": "string", "description": "Character ID"},
                },
                "required": ["character_id"],
            },
        },
    },
    FORTUNE_SPEND_TOOL,
    {
        "type": "function",
        "function": {
            "name": "short_rest",
            "description": "Take a short rest (~1 hr). HP += SPI mod + Endurance level. MP += SPI mod + Mana Control level. Once per delving day.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_phase",
            "description": (
                "Change extraction phase. Valid transitions: preparation→ingress, "
                "ingress→delve|preparation, delve→extract, extract→aftermath|delve, "
                "aftermath→preparation. Do NOT use set_phase to enter a dungeon — "
                "call enter_dungeon(site_address) instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "description": "Target phase: preparation, ingress, delve, extract, aftermath",
                    },
                },
                "required": ["phase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clock_tick",
            "description": "Tick the threat clock (from noise, time, veil disturbance). At 6/6 = danger escalation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clock": {"type": "string", "description": "Which clock: ingress, delve, or extract"},
                    "segments": {"type": "integer", "description": "How many segments to tick (default 1)"},
                },
                "required": ["clock"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_site",
            "description": "Search current site node for clues, traps, or loot. Investigation check vs DC (default 13).",
            "parameters": {
                "type": "object",
                "properties": {
                    "dc": {"type": "integer", "description": "Investigation DC (default 13)"},
                    "skill_mod": {"type": "integer", "description": "Character's Investigation/Perception modifier"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wilderness_encounter",
            "description": "Roll for wilderness encounter during travel (d6, on 1 = encounter from biome table).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "advance_scene",
            "description": "Move the party one scene forward in their current direction within the current cell. Each cell has 2-4 scenes (~3 miles each). If at the last scene, this crosses into the adjacent cell. Returns revealed features and terrain description. Call when the player says 'keep going', 'continue', 'explore further', or any directional movement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Compass direction: N, S, E, W. If omitted, continues in current heading.",
                        "enum": ["N", "S", "E", "W"],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compass_exits",
            "description": "Get compass-labeled exits from the current cell with terrain, population, danger, and visited status for each adjacent cell. Use to inform the player what lies in each direction.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enter_dungeon",
            "description": (
                "Enter a dungeon/underground site from the current surface cell. "
                "Transitions to room-based navigation and advances phase to delve. "
                "Use compass_exits to list available below addresses first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "site_address": {
                        "type": "string",
                        "description": (
                            "Site to enter: AV-GRID address (e.g. '32-C-UG-1'), site slug "
                            "(e.g. 'breley-undercrypt'), or display name when unambiguous "
                            "(e.g. 'undercrypt'). Prefer AV-GRID from compass_exits below list."
                        ),
                    },
                    "site_id": {
                        "type": "string",
                        "description": "Alias for site_address (same resolution rules).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_room",
            "description": "Move to an adjacent room in the current dungeon. Use exit directions from the current room's exits list (e.g. 'archway', 'stairs', 'forward', 'back').",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Exit direction or target room name from the room's exits list",
                    },
                },
                "required": ["direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "exit_dungeon",
            "description": "Leave the current dungeon and return to the surface. Call when the player heads back to the entrance and wants to leave.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "interact_feature",
            "description": (
                "Interact with a feature in the current scene or room. "
                "For delver corpses, use the exact id from Room features (starts with corpse-). "
                "After loot, narrate ONLY items in the tool result transferred field — never invent loot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_id": {
                        "type": "string",
                        "description": "ID of the feature to interact with (from features_revealed in advance_scene or compass_exits results)",
                    },
                    "action": {
                        "type": "string",
                        "description": "What the player is doing: 'search', 'loot', 'examine', 'activate', 'destroy'",
                    },
                },
                "required": ["feature_id", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_inventory",
            "description": "List the active delver's inventory from the database. Call when the player asks what they are carrying.",
            "parameters": {
                "type": "object",
                "properties": {
                    "character_id": {
                        "type": "string",
                        "description": "Optional character id; defaults to active roster slot",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "equip_item",
            "description": "Equip a pack instance to a slot (14-slot model). Use instanceId from list_inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string"},
                    "slot": {
                        "type": "string",
                        "description": "mainHand, offHand, chest, helm, etc.",
                    },
                    "character_id": {"type": "string"},
                },
                "required": ["instance_id", "slot"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unequip_item",
            "description": "Unequip a pack instance by instanceId.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string"},
                    "character_id": {"type": "string"},
                },
                "required": ["instance_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "use_item",
            "description": (
                "Use or consume a pack item by instanceId. Decrements uses (rations, scrolls) "
                "or quantity (ammo). Call list_inventory first for instanceId. "
                "Does not apply HP or spell effects — inventory state only. Unequip before use."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string"},
                    "quantity": {
                        "type": "integer",
                        "description": "Units to consume; default 1",
                    },
                    "character_id": {"type": "string"},
                },
                "required": ["instance_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "has_pack_item",
            "description": (
                "Check whether the active delver's pack contains a catalog item by itemId. "
                "Read-only — use before deliver_quest_item or quest narration."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "character_id": {"type": "string"},
                },
                "required": ["item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_pack_item",
            "description": (
                "Remove one pack row by instanceId or first matching itemId. "
                "Unequip first. Persists sheet on success."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "character_id": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deliver_quest_item",
            "description": (
                "Turn in a quest item at an NPC when a deliver_item objective is pending. "
                "Removes the item and advances quest objectives — does not pay rewards."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "quest_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "npc_id": {"type": "string"},
                    "character_id": {"type": "string"},
                },
                "required": ["quest_id", "item_id", "npc_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grant_loot",
            "description": "Roll and persist loot to the active delver's pack. Never narrate loot without calling this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tier": {
                        "type": "string",
                        "description": "hazard, skirmisher, elite, or boss",
                    },
                    "character_id": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buy_item",
            "description": "Buy from hub vendor (surface + vendor at address). Deducts personal goldGp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "vendor_id": {"type": "string"},
                    "character_id": {"type": "string"},
                },
                "required": ["item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sell_item",
            "description": "Sell pack item by instanceId at hub fence/vendor. Cannot sell equipped items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "vendor_id": {"type": "string"},
                    "character_id": {"type": "string"},
                },
                "required": ["instance_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "skill_check",
            "description": (
                "Sheet-backed social skill check (persuasion, intimidation, deception, etiquette, "
                "leadership, insight). Engine computes modifiers from character sheet — do NOT pass mod. "
                "Required before narrating social pass/fail or NPC compliance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "enum": [
                            "persuasion",
                            "intimidation",
                            "deception",
                            "etiquette",
                            "leadership",
                            "insight",
                        ],
                    },
                    "character_id": {"type": "string"},
                    "dc": {"type": "integer", "description": "Optional DC; opposed NPC used when omitted"},
                    "opposed_npc_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "advantage": {"type": "boolean"},
                    "disadvantage": {"type": "boolean"},
                },
                "required": ["skill_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "negotiate_quest_advance",
            "description": (
                "Haggle quest advance payment after accept_quest. Rolls sheet-backed skill_check, "
                "maps margin to advance GP tier, grants gold via engine. Required before narrating "
                "NPC paying upfront quest gold (e.g. Holt advance)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "quest_id": {"type": "string"},
                    "skill_id": {
                        "type": "string",
                        "enum": ["persuasion", "intimidation", "deception"],
                    },
                    "approach": {"type": "string", "description": "Player-facing approach phrase"},
                    "character_id": {"type": "string"},
                    "advantage": {"type": "boolean"},
                },
                "required": ["quest_id", "skill_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "offer_quest",
            "description": "Offer a canon quest to the player (creates offered state; not in log until accept).",
            "parameters": {
                "type": "object",
                "properties": {
                    "quest_id": {"type": "string"},
                },
                "required": ["quest_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "accept_quest",
            "description": "Player accepts an offered quest; adds to active quest log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quest_id": {"type": "string"},
                },
                "required": ["quest_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grant_quest_advance",
            "description": (
                "Grant quest advance GP directly (capped by quest maxAdvanceGp). "
                "Prefer negotiate_quest_advance for haggle flows."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "quest_id": {"type": "string"},
                    "gold_gp": {"type": "integer"},
                    "character_id": {"type": "string"},
                },
                "required": ["quest_id", "gold_gp"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_quests",
            "description": "List campaign quest runtime state from engine.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_stash",
            "description": "Show account stash (persists across character deaths). Hub surface only for transfers.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_factions",
            "description": "List canon factions and current campaign reputation (−3 to +3 per faction).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_vendor",
            "description": "List vendor stock at current hub (requires surface mode at vendor address).",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor_id": {"type": "string"},
                },
            },
        },
    },
]
