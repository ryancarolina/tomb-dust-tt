from __future__ import annotations

from gm.image_resolver import ImageResolver


def test_voice_to_npc_id_maps_only_key_npcs():
    resolver = ImageResolver()
    assert resolver.voice_to_npc_id("marshal-garrick-holt") == "marshal-garrick-holt"
    assert resolver.voice_to_npc_id("isla-brack") == "isla-brack"
    assert resolver.voice_to_npc_id("npc") is None
    assert resolver.voice_to_npc_id("postern-clerk") is None
    assert resolver.voice_to_npc_id("unknown-voice") is None


def test_primary_key_npc_from_lines_uses_last_key_voice():
    resolver = ImageResolver()
    lines = [
        {"voice": "narrator", "text": "Intro"},
        {"voice": "isla-brack", "text": "Welcome"},
        {"voice": "player", "text": "Reply"},
        {"voice": "marshal-garrick-holt", "text": "Orders"},
    ]
    assert resolver.primary_key_npc_from_lines(lines) == "marshal-garrick-holt"
    assert resolver.primary_key_npc_from_lines([{"voice": "narrator"}]) is None


def test_pick_winner_prefers_npc_over_location_and_site():
    resolver = ImageResolver()
    winner = resolver.pick_winner(
        [
            {"entity_type": "location", "entity_id": "32-C", "priority": 5},
            {"entity_type": "site", "entity_id": "breley-undercrypt", "priority": 5},
        ],
        item_selected=False,
        npc_id="marshal-garrick-holt",
    )
    assert winner is not None
    assert winner["entity_type"] == "npc"
    assert winner["entity_id"] == "marshal-garrick-holt"
