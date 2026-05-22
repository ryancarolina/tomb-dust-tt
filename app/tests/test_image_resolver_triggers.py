from __future__ import annotations

from gm.image_resolver import ImageResolver


def _resolver() -> ImageResolver:
    return ImageResolver()


def _entity_tuples(entities: list[dict]) -> list[tuple[str, str, int]]:
    return [
        (str(entry["entity_type"]), str(entry["entity_id"]), int(entry["priority"]))
        for entry in entities
    ]


def test_detect_entities_table_driven_status_deltas():
    resolver = _resolver()
    cases = [
        {
            "name": "combat appeared uses monsterId",
            "prev": {"party": {"address": "32-C", "mode": "surface"}},
            "curr": {
                "party": {"address": "32-C", "mode": "surface"},
                "combat": {
                    "turn_kind": "pc",
                    "turn_id": "pc-1",
                    "combatants": [
                        {"id": "pc-1", "kind": "pc"},
                        {"id": "grave-ghoul-1", "kind": "monster", "monsterId": "grave-ghoul"},
                    ],
                },
            },
            "expected": [("monster", "grave-ghoul", 2)],
        },
        {
            "name": "monster turn picks active monster",
            "prev": {
                "combat": {
                    "turn_kind": "pc",
                    "turn_id": "pc-1",
                    "combatants": [
                        {"id": "pc-1", "kind": "pc"},
                        {"id": "grave-ghoul-1", "kind": "monster", "monsterId": "grave-ghoul"},
                    ],
                }
            },
            "curr": {
                "combat": {
                    "turn_kind": "monster",
                    "turn_id": "grave-ghoul-1",
                    "combatants": [
                        {"id": "pc-1", "kind": "pc"},
                        {"id": "grave-ghoul-1", "kind": "monster", "monsterId": "grave-ghoul"},
                    ],
                }
            },
            "expected": [("monster", "grave-ghoul", 2)],
        },
        {
            "name": "surface address change triggers location",
            "prev": {"party": {"address": "32-C", "mode": "surface"}},
            "curr": {"party": {"address": "23-A", "mode": "surface"}},
            "expected": [("location", "23-A", 5)],
        },
        {
            "name": "entering dungeon resolves site from address",
            "prev": {"party": {"address": "32-C", "mode": "surface", "site_id": None}},
            "curr": {"party": {"address": "32-C-UG-1", "mode": "dungeon", "site_id": "32-C-UG-1"}},
            "expected": [("site", "breley-undercrypt", 5)],
        },
        {
            "name": "room change triggers room illustration id",
            "prev": {
                "party": {
                    "address": "32-C-UG-1",
                    "mode": "dungeon",
                    "site_id": "32-C-UG-1",
                    "dungeon_room_id": "chapel-stairs",
                }
            },
            "curr": {
                "party": {
                    "address": "32-C-UG-1",
                    "mode": "dungeon",
                    "site_id": "32-C-UG-1",
                    "dungeon_room_id": "ossuary-hall",
                }
            },
            "expected": [("room", "breley-undercrypt__ossuary-hall", 4)],
        },
        {
            "name": "first hub arrival when roster appears at 32-C",
            "prev": {
                "party": {"address": "32-C", "mode": "surface"},
                "roster": [],
                "creation_active": True,
            },
            "curr": {
                "party": {"address": "32-C", "mode": "surface"},
                "roster": [{"character_id": "pc-1", "name": "Test Delver"}],
                "creation_active": False,
            },
            "expected": [("location", "32-C", 5)],
        },
        {
            "name": "creation ends at 32-C without address delta",
            "prev": {
                "party": {"address": "32-C", "mode": "surface"},
                "roster": [{"character_id": "pc-1", "name": "Test Delver"}],
                "creation_active": True,
                "creation_step": "FINALIZE",
            },
            "curr": {
                "party": {"address": "32-C", "mode": "surface"},
                "roster": [{"character_id": "pc-1", "name": "Test Delver"}],
                "creation_active": False,
                "creation_step": None,
            },
            "expected": [("location", "32-C", 5)],
        },
        {
            "name": "no repeat hub arrival while staying at 32-C",
            "prev": {
                "party": {"address": "32-C", "mode": "surface"},
                "roster": [{"character_id": "pc-1", "name": "Test Delver"}],
                "creation_active": False,
            },
            "curr": {
                "party": {"address": "32-C", "mode": "surface"},
                "roster": [{"character_id": "pc-1", "name": "Test Delver"}],
                "creation_active": False,
            },
            "expected": [],
        },
    ]

    for case in cases:
        entities = resolver.detect_entities(case["prev"], case["curr"])
        assert _entity_tuples(entities) == case["expected"], case["name"]


def test_pick_winner_respects_priority_and_item_selection():
    resolver = _resolver()
    entities = [
        {"entity_type": "location", "entity_id": "32-C", "priority": 5},
        {"entity_type": "room", "entity_id": "breley-undercrypt__chapel-stairs", "priority": 4},
        {"entity_type": "monster", "entity_id": "grave-ghoul", "priority": 2},
    ]
    winner = resolver.pick_winner(entities, item_selected=False, npc_id="marshal-garrick-holt")
    assert winner is not None
    assert winner["entity_type"] == "monster"
    assert winner["entity_id"] == "grave-ghoul"

    skipped = resolver.pick_winner(entities, item_selected=True, npc_id="marshal-garrick-holt")
    assert skipped is None
