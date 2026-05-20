"""Unified pack inventory — single source of truth for carried gear (v3)."""

from __future__ import annotations

import copy
import uuid
from typing import Any

INVENTORY_VERSION = 3

# Legacy alias — migrated to chest
SLOT_BODY = "body"
SLOT_CHEST = "chest"
SLOT_MAIN_HAND = "mainHand"
SLOT_OFF_HAND = "offHand"

ALL_SLOTS = frozenset(
    {
        SLOT_MAIN_HAND,
        SLOT_OFF_HAND,
        "helm",
        "shoulders",
        SLOT_CHEST,
        "bracers",
        "gloves",
        "legs",
        "boots",
        "ring1",
        "ring2",
        "trinket1",
        "trinket2",
        SLOT_BODY,
    }
)

ARMOR_SLOTS = frozenset({"helm", "shoulders", SLOT_CHEST, "bracers", "gloves", "legs", "boots"})
JEWELRY_SLOTS = frozenset({"ring1", "ring2", "trinket1", "trinket2"})

_ARMOR_AGI_CAP = {
    "light": None,
    "medium": 2,
    "heavy": 0,
}

_CATEGORY_RANK = {"light": 1, "medium": 2, "heavy": 3}


def _new_instance_id() -> str:
    return f"it-{uuid.uuid4().hex[:8]}"


def _normalize_slot(slot: str | None) -> str | None:
    if slot == SLOT_BODY:
        return SLOT_CHEST
    return slot


def _item_kind_from_catalog(item_id: str, catalog: dict[str, Any] | None) -> str:
    if catalog:
        kind = catalog.get("kind")
        if kind:
            return str(kind)
        if catalog.get("damage"):
            return "weapon"
    if item_id in ("buckler",):
        return "shield"
    if item_id in ("padded", "leather", "studded-leather", "hide", "chain-shirt", "plate"):
        return "armor"
    if item_id == "arrows":
        return "ammo"
    if item_id in ("rations",) or item_id.startswith("rations-"):
        return "consumable"
    if item_id.endswith("-junk"):
        return "material"
    return "gear"


def _is_stackable(catalog: dict[str, Any] | None, kind: str) -> bool:
    if catalog is not None:
        return bool(catalog.get("stackable"))
    return kind in ("ammo", "consumable", "material")


def _stack_merge_key(item_id: str, enchant_ids: list[str] | None) -> tuple[str, tuple[str, ...]]:
    ids = tuple(sorted(enchant_ids or []))
    return (item_id, ids)


def _skill_level(sheet: dict[str, Any], skill_id: str) -> int:
    for entry in sheet.get("skills") or []:
        if str(entry.get("skillId")) == skill_id:
            return int(entry.get("level", 0))
    return 0


def _dodge_ac_bonus(sheet: dict[str, Any], *, flat_footed: bool) -> int:
    if flat_footed:
        return 0
    lvl = _skill_level(sheet, "dodge")
    if lvl >= 7:
        return 3
    if lvl >= 3:
        return 2
    if lvl >= 1:
        return 1
    return 0


def _weapon_two_hand(catalog: dict[str, Any]) -> bool:
    props = catalog.get("properties") or []
    return "two-hand" in props or "two_hand" in props


def _allowed_slots_for_item(catalog: dict[str, Any], kind: str) -> frozenset[str]:
    explicit = catalog.get("allowedSlots")
    if explicit:
        return frozenset(_normalize_slot(s) or s for s in explicit)
    slot = catalog.get("slot")
    if slot:
        return frozenset({_normalize_slot(str(slot)) or str(slot)})
    if kind == "weapon":
        return frozenset({SLOT_MAIN_HAND, SLOT_OFF_HAND})
    if kind == "armor":
        return ARMOR_SLOTS
    if kind == "shield":
        return frozenset({SLOT_OFF_HAND})
    if kind == "jewelry":
        return JEWELRY_SLOTS
    return frozenset()


def new_instance(
    item_id: str,
    *,
    kind: str | None = None,
    equipped: bool = False,
    slot: str | None = None,
    uses: int | None = None,
    quantity: int | None = None,
    enchant_ids: list[str] | None = None,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_kind = kind or _item_kind_from_catalog(item_id, catalog)
    entry: dict[str, Any] = {
        "instanceId": _new_instance_id(),
        "itemId": item_id,
        "kind": resolved_kind,
        "equipped": bool(equipped),
    }
    norm_slot = _normalize_slot(slot)
    if norm_slot:
        entry["slot"] = norm_slot
    if enchant_ids:
        entry["enchantIds"] = list(enchant_ids)
    if uses is not None:
        entry["uses"] = int(uses)
    elif resolved_kind == "consumable" and catalog and catalog.get("defaultUses"):
        entry["uses"] = int(catalog["defaultUses"])
    elif catalog and catalog.get("defaultUses") and resolved_kind == "gear":
        entry["uses"] = int(catalog["defaultUses"])
    if quantity is not None and _is_stackable(catalog, resolved_kind):
        entry["quantity"] = max(1, int(quantity))
    return entry


def empty_inventory() -> dict[str, Any]:
    return {"inventoryVersion": INVENTORY_VERSION, "pack": []}


def get_pack(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    inv = sheet.setdefault("inventory", empty_inventory())
    pack = inv.setdefault("pack", [])
    if not isinstance(pack, list):
        pack = []
        inv["pack"] = pack
    return pack


def clone_pack_entries(pack: list[dict[str, Any]], *, reid: bool = True) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in pack:
        copy_item = copy.deepcopy(item)
        if reid:
            copy_item["instanceId"] = _new_instance_id()
        out.append(copy_item)
    return out


def kit_to_pack(
    kit_items: list[dict[str, Any] | str],
    *,
    item_lookup: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    lookup = item_lookup or {}
    pack: list[dict[str, Any]] = []
    for raw in kit_items:
        if isinstance(raw, str):
            raw = {"itemId": raw}
        item_id = str(raw["itemId"])
        if item_id.startswith("rations-"):
            try:
                uses = int(item_id.split("-", 1)[1])
                item_id = "rations"
            except ValueError:
                uses = raw.get("uses")
        else:
            uses = raw.get("uses")
        catalog = lookup.get(item_id)
        entry = new_instance(
            item_id,
            kind=raw.get("kind"),
            equipped=bool(raw.get("equipped")),
            slot=raw.get("slot"),
            uses=uses,
            catalog=catalog,
        )
        if _is_stackable(catalog, entry["kind"]):
            entry["quantity"] = 1
        pack.append(entry)
    return pack


def pack_snapshot(pack: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return copy.deepcopy(pack)


def equipped_items(
    pack: list[dict[str, Any]],
    *,
    kind: str | None = None,
    slot: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    norm_slot = _normalize_slot(slot) if slot else None
    for item in pack:
        if not item.get("equipped"):
            continue
        if kind and item.get("kind") != kind:
            continue
        item_slot = _normalize_slot(item.get("slot"))
        if norm_slot and item_slot != norm_slot:
            continue
        out.append(item)
    return out


def main_weapon_id(pack: list[dict[str, Any]]) -> str | None:
    weapons = equipped_items(pack, kind="weapon", slot=SLOT_MAIN_HAND)
    if weapons:
        return str(weapons[0]["itemId"])
    weapons = [i for i in pack if i.get("kind") == "weapon" and i.get("equipped")]
    if weapons:
        return str(weapons[0]["itemId"])
    carried = [i for i in pack if i.get("kind") == "weapon"]
    return str(carried[0]["itemId"]) if carried else None


def _agi_cap_for_armor(category: str | None) -> int | None:
    if not category:
        return None
    cap = _ARMOR_AGI_CAP.get(str(category).lower())
    return cap if cap is not None else None


def compute_ac(
    sheet: dict[str, Any],
    *,
    item_lookup: dict[str, dict[str, Any]] | None = None,
    flat_footed: bool = False,
) -> int:
    """AC = 10 + sum(armor slots) + shield + AGI (capped) + Dodge (alert)."""
    from tomb_gm.domain.character import ability_modifier

    lookup = item_lookup or {}
    pack = get_pack(sheet)
    attrs = sheet.get("attributes", {})
    agi_mod = 0 if flat_footed else ability_modifier(int(attrs.get("AGI", 10)))

    armor_bonus = 0
    shield_bonus = 0
    agi_cap: int | None = None

    for item in equipped_items(pack):
        item_id = str(item.get("itemId", ""))
        catalog = lookup.get(item_id, {})
        kind = item.get("kind") or _item_kind_from_catalog(item_id, catalog)
        slot = _normalize_slot(item.get("slot"))
        ac_bonus = int(catalog.get("acBonus", 0))
        if kind == "shield" and slot == SLOT_OFF_HAND:
            shield_bonus += ac_bonus
        elif kind in ("armor", "jewelry") and slot in ARMOR_SLOTS | JEWELRY_SLOTS:
            armor_bonus += ac_bonus
            if kind == "armor":
                cap = _agi_cap_for_armor(catalog.get("category"))
                if cap is not None:
                    agi_cap = cap if agi_cap is None else min(agi_cap, cap)

    if agi_cap is not None:
        agi_mod = min(agi_mod, agi_cap)

    dodge = _dodge_ac_bonus(sheet, flat_footed=flat_footed)
    return 10 + armor_bonus + shield_bonus + agi_mod + dodge


def movement_penalty_from_sheet(
    sheet: dict[str, Any],
    *,
    item_lookup: dict[str, Any] | None = None,
) -> int:
    """Medium −2, heavy −4 move (min 2 enforced by caller)."""
    lookup = item_lookup or {}
    heaviest = 0
    for item in equipped_items(get_pack(sheet)):
        if item.get("kind") != "armor":
            continue
        slot = _normalize_slot(item.get("slot"))
        if slot not in ARMOR_SLOTS:
            continue
        catalog = lookup.get(str(item.get("itemId", "")), {})
        rank = _CATEGORY_RANK.get(str(catalog.get("category", "light")).lower(), 1)
        heaviest = max(heaviest, rank)
    if heaviest >= 3:
        return 4
    if heaviest >= 2:
        return 2
    return 0


def _unequip_slot(pack: list[dict[str, Any]], slot: str) -> None:
    norm = _normalize_slot(slot) or slot
    for item in pack:
        if item.get("equipped") and _normalize_slot(item.get("slot")) == norm:
            item["equipped"] = False
            item.pop("slot", None)


def equip(
    pack: list[dict[str, Any]],
    instance_id: str,
    slot: str,
    *,
    item_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lookup = item_lookup or {}
    target = next((i for i in pack if i.get("instanceId") == instance_id), None)
    if not target:
        return {"ok": False, "error": f"Instance not found: {instance_id}"}

    norm_slot = _normalize_slot(slot)
    if not norm_slot or norm_slot not in ALL_SLOTS:
        return {"ok": False, "error": f"Invalid slot: {slot}"}

    item_id = str(target.get("itemId", ""))
    catalog = lookup.get(item_id, {})
    kind = str(target.get("kind") or _item_kind_from_catalog(item_id, catalog))
    allowed = _allowed_slots_for_item(catalog, kind)
    if norm_slot not in allowed:
        return {"ok": False, "error": f"{kind} cannot equip to {norm_slot}"}
    if kind in ("gear", "ammo", "consumable", "material"):
        return {"ok": False, "error": f"Cannot equip {kind} items"}

    main = equipped_items(pack, kind="weapon", slot=SLOT_MAIN_HAND)
    if kind == "shield" or (kind == "weapon" and norm_slot == SLOT_OFF_HAND):
        if main:
            main_cat = lookup.get(str(main[0].get("itemId", "")), {})
            if _weapon_two_hand(main_cat):
                return {"ok": False, "error": "Two-hand weapon blocks offHand"}

    if kind == "weapon" and norm_slot == SLOT_MAIN_HAND and _weapon_two_hand(catalog):
        _unequip_slot(pack, SLOT_OFF_HAND)

    _unequip_slot(pack, norm_slot)
    if kind == "armor" and norm_slot == SLOT_CHEST:
        _unequip_slot(pack, SLOT_BODY)

    target["equipped"] = True
    target["slot"] = norm_slot
    return {"ok": True, "instanceId": instance_id, "slot": norm_slot}


def unequip(pack: list[dict[str, Any]], instance_id: str) -> dict[str, Any]:
    target = next((i for i in pack if i.get("instanceId") == instance_id), None)
    if not target:
        return {"ok": False, "error": f"Instance not found: {instance_id}"}
    target["equipped"] = False
    target.pop("slot", None)
    return {"ok": True, "instanceId": instance_id}


def add_item(
    sheet: dict[str, Any],
    item_id: str,
    *,
    quantity: int = 1,
    equipped: bool = False,
    slot: str | None = None,
    uses: int | None = None,
    enchant_ids: list[str] | None = None,
    catalog: dict[str, Any] | None = None,
) -> list[str]:
    pack = get_pack(sheet)
    qty = max(1, int(quantity))
    resolved = catalog or {}
    kind = _item_kind_from_catalog(item_id, resolved)

    if _is_stackable(resolved, kind) and not equipped:
        key = _stack_merge_key(item_id, enchant_ids)
        max_stack = int(resolved.get("maxStack", 99))
        for item in pack:
            if item.get("equipped"):
                continue
            iid = str(item.get("itemId", ""))
            ikey = _stack_merge_key(iid, item.get("enchantIds"))
            if ikey == key:
                current = int(item.get("quantity", 1))
                room = max_stack - current
                add = min(qty, room)
                if add > 0:
                    item["quantity"] = current + add
                    qty -= add
                if qty <= 0:
                    return [item["instanceId"]]
        if qty > 0:
            while qty > 0:
                chunk = min(qty, max_stack)
                entry = new_instance(
                    item_id,
                    kind=kind,
                    uses=uses,
                    quantity=chunk,
                    enchant_ids=enchant_ids,
                    catalog=resolved,
                )
                pack.append(entry)
                qty -= chunk
            return [entry["instanceId"]]

    ids: list[str] = []
    for _ in range(qty):
        entry = new_instance(
            item_id,
            kind=kind,
            equipped=equipped,
            slot=slot,
            uses=uses,
            enchant_ids=enchant_ids,
            catalog=resolved,
        )
        pack.append(entry)
        ids.append(entry["instanceId"])
    return ids


def remove_instance(pack: list[dict[str, Any]], instance_id: str, *, quantity: int | None = None) -> dict[str, Any]:
    for idx, item in enumerate(pack):
        if item.get("instanceId") != instance_id:
            continue
        if quantity is not None and int(item.get("quantity", 1)) > int(quantity):
            item["quantity"] = int(item["quantity"]) - int(quantity)
            return {"ok": True, "removed": {"itemId": item.get("itemId"), "quantity": quantity}}
        removed = pack.pop(idx)
        return {"ok": True, "removed": removed}
    return {"ok": False, "error": f"Instance not found: {instance_id}"}


def remove_first_by_item_id(pack: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for idx, item in enumerate(pack):
        if item.get("itemId") == item_id:
            removed = pack.pop(idx)
            return {"ok": True, "removed": removed}
    return {"ok": False, "error": f"Item not in pack: {item_id}"}


def transfer_all(
    source_pack: list[dict[str, Any]],
    dest_pack: list[dict[str, Any]],
    *,
    reid: bool = False,
) -> list[dict[str, Any]]:
    if reid:
        transferred = clone_pack_entries(source_pack, reid=True)
    else:
        transferred = pack_snapshot(source_pack)
    dest_pack.extend(transferred)
    source_pack.clear()
    return transferred


def _merge_stackables_in_pack(pack: list[dict[str, Any]], lookup: dict[str, dict[str, Any]]) -> None:
    """Collapse duplicate stackable rows after migration."""
    merged: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    carry: list[dict[str, Any]] = []
    for item in pack:
        if item.get("equipped"):
            carry.append(item)
            continue
        item_id = str(item.get("itemId", ""))
        catalog = lookup.get(item_id, {})
        kind = str(item.get("kind") or _item_kind_from_catalog(item_id, catalog))
        if not _is_stackable(catalog, kind):
            carry.append(item)
            continue
        key = _stack_merge_key(item_id, item.get("enchantIds"))
        qty = int(item.get("quantity", 1))
        uses = item.get("uses")
        if key not in merged:
            merged[key] = copy.deepcopy(item)
            merged[key]["quantity"] = qty
        else:
            merged[key]["quantity"] = int(merged[key].get("quantity", 1)) + qty
            if uses is not None:
                merged[key]["uses"] = int(merged[key].get("uses", 0)) + int(uses)
    carry.extend(merged.values())
    pack.clear()
    pack.extend(carry)


def _migrate_item_ids(pack: list[dict[str, Any]]) -> None:
    for item in pack:
        iid = str(item.get("itemId", ""))
        if iid.startswith("rations-"):
            try:
                uses = int(iid.split("-", 1)[1])
                item["itemId"] = "rations"
                item["uses"] = uses
                item["quantity"] = int(item.get("quantity", 1))
            except ValueError:
                pass


def _migrate_slots_v3(pack: list[dict[str, Any]]) -> None:
    for item in pack:
        slot = item.get("slot")
        if slot == SLOT_BODY:
            item["slot"] = SLOT_CHEST


def migrate_v2_to_v3(
    sheet: dict[str, Any],
    *,
    item_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lookup = item_lookup or {}
    inv = sheet.setdefault("inventory", empty_inventory())
    pack = get_pack(sheet)
    _migrate_slots_v3(pack)
    _migrate_item_ids(pack)
    _merge_stackables_in_pack(pack, lookup)
    inv["inventoryVersion"] = INVENTORY_VERSION
    sheet.pop("armor", None)
    sheet.pop("weapons", None)
    return sheet


def _legacy_string_to_instance(item_ref: str | dict[str, Any], lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if isinstance(item_ref, dict) and item_ref.get("instanceId"):
        return copy.deepcopy(item_ref)
    item_id = item_ref if isinstance(item_ref, str) else str(item_ref.get("itemId", ""))
    catalog = lookup.get(item_id)
    kind = _item_kind_from_catalog(item_id, catalog)
    return new_instance(item_id, kind=kind, catalog=catalog)


def normalize_legacy_sheet(
    sheet: dict[str, Any],
    *,
    item_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Migrate hybrid / string pack sheets to unified inventory v2 base."""
    lookup = item_lookup or {}
    inv = sheet.get("inventory") or {}
    if int(inv.get("inventoryVersion", 0)) >= INVENTORY_VERSION:
        get_pack(sheet)
        sheet.pop("armor", None)
        sheet.pop("weapons", None)
        return sheet

    pack: list[dict[str, Any]] = []
    seen_weapon_ids: set[str] = set()

    if int(inv.get("inventoryVersion", 0)) >= 2:
        for raw in inv.get("pack") or []:
            if isinstance(raw, dict) and raw.get("instanceId"):
                pack.append(copy.deepcopy(raw))
        sheet["inventory"] = {"inventoryVersion": 2, "pack": pack}
        return migrate_v2_to_v3(sheet, item_lookup=lookup)

    for raw in inv.get("pack") or []:
        if isinstance(raw, dict) and raw.get("instanceId"):
            pack.append(copy.deepcopy(raw))
            continue
        item_id = raw if isinstance(raw, str) else str(raw.get("itemId", ""))
        if item_id:
            pack.append(_legacy_string_to_instance(item_id, lookup))

    for raw in inv.get("body") or []:
        item_id = raw if isinstance(raw, str) else str(raw.get("itemId", ""))
        if item_id:
            inst = _legacy_string_to_instance(item_id, lookup)
            inst["equipped"] = True
            if inst["kind"] == "armor":
                inst["slot"] = SLOT_CHEST
            pack.append(inst)

    for wid in inv.get("weapons") or sheet.get("weapons") or []:
        wid = str(wid)
        if wid in seen_weapon_ids:
            continue
        seen_weapon_ids.add(wid)
        if any(i.get("itemId") == wid for i in pack):
            continue
        pack.append(new_instance(wid, kind="weapon", catalog=lookup.get(wid)))

    armor = sheet.get("armor") or {}
    worn = armor.get("wornId")
    if worn:
        worn = str(worn)
        existing = next((i for i in pack if i.get("itemId") == worn), None)
        if existing:
            existing["equipped"] = True
            existing["kind"] = "armor"
            existing["slot"] = SLOT_CHEST
        else:
            pack.append(
                new_instance(worn, kind="armor", equipped=True, slot=SLOT_CHEST, catalog=lookup.get(worn))
            )
    shield = armor.get("shieldId")
    if shield:
        shield = str(shield)
        existing = next((i for i in pack if i.get("itemId") == shield), None)
        if existing:
            existing["equipped"] = True
            existing["kind"] = "shield"
            existing["slot"] = SLOT_OFF_HAND
        else:
            pack.append(
                new_instance(shield, kind="shield", equipped=True, slot=SLOT_OFF_HAND, catalog=lookup.get(shield))
            )

    sheet["inventory"] = {"inventoryVersion": 2, "pack": pack}
    sheet.pop("armor", None)
    sheet.pop("weapons", None)
    return migrate_v2_to_v3(sheet, item_lookup=lookup)


def ensure_normalized(sheet: dict[str, Any], item_lookup: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    inv = sheet.get("inventory") or {}
    version = int(inv.get("inventoryVersion", 0))
    if version >= INVENTORY_VERSION:
        get_pack(sheet)
        _migrate_slots_v3(get_pack(sheet))
        sheet.pop("armor", None)
        sheet.pop("weapons", None)
        return sheet
    if version >= 2:
        migrate_v2_to_v3(sheet, item_lookup=item_lookup)
        return sheet
    return normalize_legacy_sheet(sheet, item_lookup=item_lookup)


def format_inventory_summary(
    sheet: dict[str, Any],
    *,
    item_display: dict[str, str] | None = None,
) -> str:
    display = item_display or {}
    pack = get_pack(sheet)
    if not pack:
        return "Inventory: empty"

    lines: list[str] = []
    equipped: list[str] = []
    carried: list[str] = []
    for item in pack:
        item_id = str(item.get("itemId", "?"))
        name = display.get(item_id, item_id.replace("-", " ").title())
        uses = item.get("uses")
        qty = item.get("quantity")
        label = name
        if qty and int(qty) > 1:
            label = f"{name} ×{qty}"
        elif uses is not None:
            label = f"{name} (uses {uses})"
        if item.get("equipped"):
            slot = item.get("slot", "?")
            equipped.append(f"{label} [{slot}]")
        else:
            carried.append(label)

    if equipped:
        lines.append("Equipped: " + ", ".join(equipped))
    if carried:
        lines.append("Carried: " + ", ".join(carried))
    lines.append(f"Gold: {int(sheet.get('goldGp', 0))} gp")
    return "\n".join(lines)


def loot_snapshot(sheet: dict[str, Any]) -> dict[str, Any]:
    ensure_normalized(sheet)
    return {
        "goldGp": int(sheet.get("goldGp", 0)),
        "pack": clone_pack_entries(get_pack(sheet), reid=False),
        "displayName": sheet.get("displayName", "Unknown delver"),
        "classId": sheet.get("classId"),
    }


def apply_loot_to_sheet(sheet: dict[str, Any], loot: dict[str, Any], *, item_lookup: dict | None = None) -> dict[str, Any]:
    """Merge corpse loot onto a living character sheet (re-ids instances)."""
    ensure_normalized(sheet, item_lookup=item_lookup)
    sheet["goldGp"] = int(sheet.get("goldGp", 0)) + int(loot.get("goldGp", 0))
    dest = get_pack(sheet)
    lookup = item_lookup or {}

    legacy_pack = loot.get("pack") or []
    if legacy_pack and isinstance(legacy_pack[0], str):
        transferred_items: list[dict[str, Any]] = []
        for item_id in legacy_pack:
            ids = add_item(sheet, str(item_id), catalog=lookup.get(str(item_id)))
            transferred_items.append({"itemId": item_id, "instanceIds": ids})
        transferred = {"goldGp": int(loot.get("goldGp", 0)), "pack": transferred_items}
    else:
        source = clone_pack_entries(legacy_pack, reid=True)
        dest.extend(source)
        transferred = {"goldGp": int(loot.get("goldGp", 0)), "pack": source}

    for wid in loot.get("weapons") or []:
        add_item(sheet, str(wid), catalog=lookup.get(str(wid)))
        transferred.setdefault("pack", []).append({"itemId": wid, "kind": "weapon"})

    armor = loot.get("armor") or {}
    for slot_key, slot_name in (("wornId", SLOT_CHEST), ("shieldId", SLOT_OFF_HAND)):
        item_id = armor.get(slot_key)
        if item_id:
            kind = "shield" if slot_key == "shieldId" else "armor"
            add_item(sheet, str(item_id), catalog=lookup.get(str(item_id)))
            transferred.setdefault("pack", []).append({"itemId": item_id, "kind": kind})

    return transferred


def use_item(
    pack: list[dict[str, Any]],
    instance_id: str,
    *,
    quantity: int = 1,
    item_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Decrement consumable uses or ammo/material quantity. Removes row when depleted."""
    lookup = item_lookup or {}
    target = next((i for i in pack if i.get("instanceId") == instance_id), None)
    if not target:
        return {"ok": False, "error": f"Instance not found: {instance_id}"}
    if target.get("equipped"):
        return {"ok": False, "error": "Cannot use equipped item — unequip first"}

    item_id = str(target.get("itemId", ""))
    catalog = lookup.get(item_id, {})
    kind = str(target.get("kind") or _item_kind_from_catalog(item_id, catalog))
    qty = max(1, int(quantity))

    if kind == "ammo" or (kind == "material" and target.get("quantity")):
        current = int(target.get("quantity", 1))
        if qty > current:
            return {"ok": False, "error": f"Only {current} available"}
        remaining = current - qty
        if remaining <= 0:
            pack.remove(target)
            return {"ok": True, "instanceId": instance_id, "itemId": item_id, "used": qty, "depleted": True}
        target["quantity"] = remaining
        return {"ok": True, "instanceId": instance_id, "itemId": item_id, "used": qty, "remaining": remaining}

    if kind in ("consumable", "gear") and target.get("uses") is not None:
        current = int(target["uses"])
        if qty > current:
            return {"ok": False, "error": f"Only {current} uses remaining"}
        remaining = current - qty
        if remaining <= 0:
            pack.remove(target)
            return {"ok": True, "instanceId": instance_id, "itemId": item_id, "used": qty, "depleted": True}
        target["uses"] = remaining
        return {"ok": True, "instanceId": instance_id, "itemId": item_id, "used": qty, "remaining": remaining}

    return {"ok": False, "error": f"Item {item_id} is not consumable or has no uses/quantity"}


def normalize_campaign_sheets(
    conn,
    *,
    campaign_slug: str,
    item_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    import json

    rows = conn.execute(
        "SELECT id, sheet_json FROM characters WHERE campaign_slug = ?",
        (campaign_slug,),
    ).fetchall()
    updated: list[str] = []
    for row in rows:
        original = row["sheet_json"]
        sheet = json.loads(original)
        ensure_normalized(sheet, item_lookup=item_lookup)
        if json.dumps(sheet, sort_keys=True) != json.dumps(json.loads(original), sort_keys=True):
            conn.execute(
                "UPDATE characters SET sheet_json = ? WHERE id = ?",
                (json.dumps(sheet), row["id"]),
            )
            updated.append(row["id"])
    if updated:
        conn.commit()
    return {"ok": True, "updated": updated}
