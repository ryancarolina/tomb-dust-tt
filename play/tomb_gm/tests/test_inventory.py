"""Tests for inventory v3: AC, equip rules, stacking."""

from __future__ import annotations

from pathlib import Path

import pytest

from tomb_gm.domain.creation import starting_kit_inventory
from tomb_gm.domain.inventory import (
    INVENTORY_VERSION,
    apply_loot_to_sheet,
    compute_ac,
    ensure_normalized,
    equip,
    get_pack,
    kit_to_pack,
    loot_snapshot,
    main_weapon_id,
    new_instance,
    transfer_all,
    unequip,
)
from tomb_gm.services.content import ContentService

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "build"


@pytest.fixture()
def content():
    return ContentService(CONTENT)


@pytest.fixture()
def lookup(content):
    return content.items_lookup()


def test_novice_starter_kit_has_equipped_gear(content):
    inv = starting_kit_inventory(CONTENT, "novice")
    assert inv["inventoryVersion"] == INVENTORY_VERSION
    pack = inv["pack"]
    assert len(pack) >= 5
    assert main_weapon_id(pack) == "warhammer"
    lookup = content.items_lookup()
    sheet = {"attributes": {"AGI": 10, "STR": 9, "STA": 11, "INT": 4, "SPI": 10, "LUC": 3}, "inventory": inv}
    ac = compute_ac(sheet, item_lookup=lookup)
    assert ac == 12  # 10 + leather(2) + AGI mod 0


def test_ninja_ac_alert_and_flat_footed(lookup):
    pack = [
        new_instance("studded-leather", kind="armor", equipped=True, slot="chest", catalog=lookup["studded-leather"]),
    ]
    sheet = {
        "attributes": {"AGI": 18},
        "skills": [{"skillId": "dodge", "level": 3}],
        "inventory": {"inventoryVersion": INVENTORY_VERSION, "pack": pack},
    }
    assert compute_ac(sheet, item_lookup=lookup) == 19  # 10+3+4+2
    assert compute_ac(sheet, item_lookup=lookup, flat_footed=True) == 13


def test_knight_ac_plate_and_shield(lookup):
    pack = [
        new_instance("plate", kind="armor", equipped=True, slot="chest", catalog=lookup["plate"]),
        new_instance("shield", kind="shield", equipped=True, slot="offHand", catalog=lookup["shield"]),
    ]
    sheet = {
        "attributes": {"AGI": 10},
        "skills": [],
        "inventory": {"inventoryVersion": INVENTORY_VERSION, "pack": pack},
    }
    assert compute_ac(sheet, item_lookup=lookup) == 20
    assert compute_ac(sheet, item_lookup=lookup, flat_footed=True) == 20


def test_two_hand_weapon_clears_offhand(lookup):
    pack = [
        new_instance("quarterstaff", kind="weapon", equipped=True, slot="mainHand", catalog=lookup["quarterstaff"]),
        new_instance("buckler", kind="shield", equipped=True, slot="offHand", catalog=lookup["buckler"]),
    ]
    off = next(i for i in pack if i["itemId"] == "buckler")
    assert off["equipped"] is True
    result = equip(pack, pack[0]["instanceId"], "mainHand", item_lookup=lookup)
    assert result["ok"] is True
    assert next(i for i in pack if i["itemId"] == "buckler")["equipped"] is False


def test_shield_blocked_with_two_hand_main(lookup):
    pack = [
        new_instance("quarterstaff", kind="weapon", equipped=True, slot="mainHand", catalog=lookup["quarterstaff"]),
        new_instance("buckler", kind="shield", equipped=False, catalog=lookup["buckler"]),
    ]
    buckler = next(i for i in pack if i["itemId"] == "buckler")
    result = equip(pack, buckler["instanceId"], "offHand", item_lookup=lookup)
    assert result["ok"] is False


def test_legacy_sheet_migration(content):
    legacy = {
        "goldGp": 50,
        "armor": {"wornId": "leather", "shieldId": None},
        "inventory": {"pack": ["holy-symbol"], "weapons": ["warhammer"], "body": []},
        "attributes": {"AGI": 10, "STR": 10, "STA": 10, "INT": 10, "SPI": 10, "LUC": 10},
    }
    ensure_normalized(legacy, item_lookup=content.items_lookup())
    pack = get_pack(legacy)
    assert legacy.get("armor") is None
    assert any(i["itemId"] == "warhammer" for i in pack)
    assert any(i["itemId"] == "leather" and i.get("equipped") for i in pack)
    assert legacy["inventory"]["inventoryVersion"] == INVENTORY_VERSION


def test_corpse_loot_reids_instances(content):
    inv = starting_kit_inventory(CONTENT, "novice")
    sheet = {
        "displayName": "Sammy",
        "classId": "novice",
        "goldGp": 100,
        "inventory": inv,
        "attributes": {"AGI": 4, "STR": 9, "STA": 11, "INT": 4, "SPI": 10, "LUC": 3},
    }
    snap = loot_snapshot(sheet)
    source_ids = {i["instanceId"] for i in snap["pack"]}

    looter = {
        "goldGp": 0,
        "inventory": {"inventoryVersion": INVENTORY_VERSION, "pack": []},
        "attributes": {"AGI": 10, "STR": 10, "STA": 10, "INT": 10, "SPI": 10, "LUC": 10},
    }
    apply_loot_to_sheet(looter, snap, item_lookup=content.items_lookup())
    dest_ids = {i["instanceId"] for i in get_pack(looter)}
    assert source_ids.isdisjoint(dest_ids)


def test_kit_to_pack_instances(content):
    kit_items = [
        {"itemId": "dagger", "equipped": True, "slot": "mainHand"},
        {"itemId": "leather", "equipped": True, "slot": "chest"},
    ]
    pack = kit_to_pack(kit_items, item_lookup=content.items_lookup())
    assert all("instanceId" in i for i in pack)
    assert pack[0]["itemId"] == "dagger"


def test_unequip_instance(lookup):
    pack = [
        new_instance("leather", kind="armor", equipped=True, slot="chest", catalog=lookup["leather"]),
    ]
    iid = pack[0]["instanceId"]
    assert unequip(pack, iid)["ok"] is True
    assert pack[0]["equipped"] is False
    assert "slot" not in pack[0]


def test_transfer_all_clears_source():
    source = [{"instanceId": "it-1", "itemId": "dagger", "kind": "weapon", "equipped": False}]
    dest: list = []
    moved = transfer_all(source, dest)
    assert len(moved) == 1
    assert len(source) == 0
    assert len(dest) == 1


def test_use_consumable_decrements_uses(lookup):
    from tomb_gm.domain.inventory import new_instance, use_item

    pack = [
        new_instance("rations", kind="consumable", uses=3, catalog=lookup.get("rations")),
    ]
    iid = pack[0]["instanceId"]
    result = use_item(pack, iid, item_lookup=lookup)
    assert result["ok"] is True
    assert result["remaining"] == 2
    assert len(pack) == 1


def test_use_consumable_depletes_row(lookup):
    from tomb_gm.domain.inventory import new_instance, use_item

    pack = [new_instance("rations", kind="consumable", uses=1, catalog=lookup.get("rations"))]
    iid = pack[0]["instanceId"]
    result = use_item(pack, iid, item_lookup=lookup)
    assert result["depleted"] is True
    assert len(pack) == 0
