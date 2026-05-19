"""Tool schemas for LLM function calling — maps to GameBridge methods."""

from __future__ import annotations

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "roll_d20",
            "description": "Roll a d20 + modifier against a DC. Use for skill checks, saves, and ability tests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mod": {"type": "integer", "description": "Total modifier (attribute + PB + skill bonus)"},
                    "dc": {"type": "integer", "description": "Difficulty class"},
                    "reason": {"type": "string", "description": "What the roll is for (e.g. 'Persuasion check')"},
                },
                "required": ["mod", "dc", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_beat",
            "description": "Process player action lines as a narrative beat. Handles travel, site, combat intents automatically.",
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
            "description": "Begin combat encounter with specified monsters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monster_specs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Monster specs as 'id:count' (e.g. ['grave-ghoul:2', 'hollow-knight:1'])",
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
            "description": "Make an attack roll in active combat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attacker_id": {"type": "string", "description": "ID of the attacker"},
                    "target_id": {"type": "string", "description": "ID of the target"},
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
    {
        "type": "function",
        "function": {
            "name": "character_create",
            "description": "Create a new player character with given attributes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Character name"},
                    "background": {"type": "string", "description": "Background (e.g. 'soldier', 'scholar', 'street-rat')"},
                    "str_score": {"type": "integer", "description": "STR score (8-18)"},
                    "agi_score": {"type": "integer", "description": "AGI score (8-18)"},
                    "end_score": {"type": "integer", "description": "END score (8-18)"},
                    "wil_score": {"type": "integer", "description": "WIL score (8-18)"},
                    "int_score": {"type": "integer", "description": "INT score (8-18)"},
                    "luc_score": {"type": "integer", "description": "LUC score (8-18)"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_recall",
            "description": "Search campaign memory for relevant facts (NPCs, events, locations mentioned before).",
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
]
