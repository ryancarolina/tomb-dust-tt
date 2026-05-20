"""Campaign economy: character gold, buy/sell, account stash (v3 pack)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from tomb_gm.domain.inventory import (
    INVENTORY_VERSION,
    add_item,
    clone_pack_entries,
    empty_inventory,
    ensure_normalized,
    get_pack,
    new_instance,
    remove_instance,
)
from tomb_gm.services.content import ContentService
from tomb_gm.services.hub import HubError, hub_services_available


class EconomyError(ValueError):
    pass


FENCE_REGISTRY_TAX = 0.10
FENCE_ASH_TITHE = 0.02


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_sheet(row: sqlite3.Row) -> dict[str, Any]:
    return json.loads(row["sheet_json"])


def _save_sheet(conn: sqlite3.Connection, char_id: str, campaign: str, sheet: dict[str, Any]) -> None:
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), char_id, campaign),
    )
    conn.commit()


def migrate_account_stash(state: dict[str, Any]) -> dict[str, Any]:
    """Map legacy stashItems → empty v3 stash pack; preserve stashGp."""
    state.setdefault("stashGp", 0)
    if "stash" not in state or not isinstance(state.get("stash"), dict):
        state["stash"] = empty_inventory()
    stash = state["stash"]
    stash.setdefault("inventoryVersion", INVENTORY_VERSION)
    stash.setdefault("pack", [])
    state.pop("stashItems", None)
    return state


def get_account_state(conn: sqlite3.Connection, campaign_slug: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT account_state_json FROM campaigns WHERE slug = ?",
        (campaign_slug,),
    ).fetchone()
    if not row:
        raise EconomyError(f"Campaign not found: {campaign_slug}")
    state = json.loads(row["account_state_json"] or "{}")
    state.setdefault("deed_counters", {})
    state.setdefault("flags", {})
    return migrate_account_stash(state)


def save_account_state(conn: sqlite3.Connection, campaign_slug: str, state: dict[str, Any]) -> None:
    migrate_account_stash(state)
    conn.execute(
        "UPDATE campaigns SET account_state_json = ?, updated_at = ? WHERE slug = ?",
        (json.dumps(state), _now(), campaign_slug),
    )
    conn.commit()


def _stash_pack(state: dict[str, Any]) -> list[dict[str, Any]]:
    migrate_account_stash(state)
    return state["stash"]["pack"]


def _item_in_pack(pack: list[dict[str, Any]], instance_id: str) -> dict[str, Any] | None:
    return next((i for i in pack if i.get("instanceId") == instance_id), None)


def _catalog_price(content: ContentService, item_id: str) -> int:
    item = content.load_item(item_id)
    if not item:
        return 0
    return int(item.get("costGp", item.get("cost", 0)))


def _sell_base_price(content: ContentService, item: dict[str, Any], *, sell_multiplier: float) -> int:
    item_id = str(item.get("itemId", ""))
    catalog = content.load_item(item_id) or {}
    base = _catalog_price(content, item_id)
    if base <= 0:
        base = 5
    qty = int(item.get("quantity", 1))
    return max(1, int(base * sell_multiplier * qty))


def _apply_fence_taxes(gross_gp: int) -> dict[str, Any]:
    registry = int(gross_gp * FENCE_REGISTRY_TAX)
    ash = int(gross_gp * FENCE_ASH_TITHE)
    net = gross_gp - registry - ash
    return {"gross_gp": gross_gp, "registry_tax_gp": registry, "ash_tithe_gp": ash, "net_gp": max(0, net)}


def buy_from_vendor(
    conn: sqlite3.Connection,
    content: ContentService,
    *,
    campaign_slug: str,
    session_id: str,
    character_id: str,
    vendor_id: str,
    item_id: str,
    quantity: int = 1,
) -> dict[str, Any]:
    _require_hub(conn, content, session_id, require_vendor=vendor_id)
    vendor = content.load_vendor(vendor_id)
    if not vendor:
        raise EconomyError(f"Unknown vendor: {vendor_id}")

    stock_entry = next((s for s in vendor.get("stock", []) if s.get("itemId") == item_id), None)
    if not stock_entry:
        raise EconomyError(f"{vendor_id} does not stock {item_id}")

    qty = max(1, int(quantity))
    stock_qty = stock_entry.get("qty")
    if stock_qty is not None and int(stock_qty) < qty:
        raise EconomyError(f"Insufficient stock: {stock_qty}")

    catalog = content.load_item(item_id)
    unit_cost = int((catalog or {}).get("costGp", 5))
    multiplier = float(vendor.get("buyMultiplier", 1.0))
    cost = int(unit_cost * multiplier * qty)

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")
    sheet = _load_sheet(row)
    gold = int(sheet.get("goldGp", 0))
    if gold < cost:
        raise EconomyError(f"Insufficient gold: need {cost}, have {gold}")

    sheet["goldGp"] = gold - cost
    add_item(sheet, item_id, quantity=qty, catalog=catalog)
    _save_sheet(conn, character_id, campaign_slug, sheet)
    return {
        "ok": True,
        "vendor_id": vendor_id,
        "character_id": character_id,
        "item": item_id,
        "quantity": qty,
        "cost_gp": cost,
        "gold_gp": sheet["goldGp"],
    }


def buy_item(
    conn: sqlite3.Connection,
    content: ContentService,
    *,
    campaign_slug: str,
    character_id: str,
    item_id: str,
    quantity: int = 1,
    session_id: str | None = None,
    vendor_id: str | None = None,
) -> dict[str, Any]:
    if session_id and vendor_id:
        return buy_from_vendor(
            conn,
            content,
            campaign_slug=campaign_slug,
            session_id=session_id,
            character_id=character_id,
            vendor_id=vendor_id,
            item_id=item_id,
            quantity=quantity,
        )

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")
    item = content.load_item(item_id)
    cost = _catalog_price(content, item_id) * quantity
    if cost <= 0:
        cost = 5 * quantity

    sheet = _load_sheet(row)
    gold = int(sheet.get("goldGp", 0))
    if gold < cost:
        raise EconomyError(f"Insufficient gold: need {cost}, have {gold}")
    sheet["goldGp"] = gold - cost
    add_item(sheet, item_id, quantity=quantity, catalog=item)
    _save_sheet(conn, character_id, campaign_slug, sheet)
    return {"ok": True, "character_id": character_id, "item": item_id, "cost_gp": cost, "gold_gp": sheet["goldGp"]}


def _appraisal_sell_multiplier(sheet: dict[str, Any]) -> float:
    """Appraisal skill improves fence offers (G2 — modest table bonus)."""
    for entry in sheet.get("skills") or []:
        if str(entry.get("skillId")) == "appraisal":
            lvl = int(entry.get("level", 0))
            return 1.0 + min(0.25, lvl * 0.05)
    return 1.0


def _require_hub(
    conn: sqlite3.Connection,
    content: ContentService,
    session_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    try:
        return hub_services_available(conn, content, session_id, **kwargs)
    except HubError as exc:
        raise EconomyError(str(exc)) from exc


def sell_item(
    conn: sqlite3.Connection,
    content: ContentService,
    *,
    campaign_slug: str,
    session_id: str,
    character_id: str,
    instance_id: str,
    quantity: int | None = None,
    vendor_id: str | None = None,
    use_fence: bool = True,
) -> dict[str, Any]:
    """Sell from personal pack by instanceId; hub gate required."""
    services = _require_hub(conn, content, session_id)
    address = services["address"]
    cell_services = services.get("services") or {}

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")

    sheet = _load_sheet(row)
    lookup = content.items_lookup()
    ensure_normalized(sheet, item_lookup=lookup)
    pack = get_pack(sheet)
    item = _item_in_pack(pack, instance_id)
    if not item:
        raise EconomyError(f"Instance not in pack: {instance_id}")
    if item.get("equipped"):
        raise EconomyError("Cannot sell equipped item — unequip first")

    catalog = content.load_item(str(item.get("itemId", ""))) or {}
    kind = str(item.get("kind") or catalog.get("kind", "gear"))

    sell_multiplier = 0.5
    fence_sale = bool(cell_services.get("fence")) and use_fence
    if vendor_id:
        _require_hub(conn, content, session_id, require_vendor=vendor_id)
        vendor = content.load_vendor(vendor_id) or {}
        sell_multiplier = float(vendor.get("sellMultiplier", 0.5))
        buys = vendor.get("buysCategories") or []
        if buys and kind not in buys and catalog.get("rarity") not in buys:
            raise EconomyError(f"Vendor {vendor_id} does not buy {kind} items")
        fence_sale = False
    elif not fence_sale:
        raise EconomyError("No fence or vendor available for sale at this location")

    qty = quantity
    if qty is None:
        qty = int(item.get("quantity", 1))
    qty = max(1, int(qty))
    if qty > int(item.get("quantity", 1)):
        raise EconomyError(f"Cannot sell {qty}; stack has {item.get('quantity', 1)}")

    partial = dict(item)
    partial["quantity"] = qty
    gross = _sell_base_price(content, partial, sell_multiplier=sell_multiplier)
    if fence_sale:
        gross = int(gross * _appraisal_sell_multiplier(sheet))
    payout = _apply_fence_taxes(gross) if fence_sale else {"net_gp": gross, "gross_gp": gross}

    remove_instance(pack, instance_id, quantity=qty if int(item.get("quantity", 1)) > qty else None)
    sheet["goldGp"] = int(sheet.get("goldGp", 0)) + payout["net_gp"]
    _save_sheet(conn, character_id, campaign_slug, sheet)

    return {
        "ok": True,
        "sold_instance_id": instance_id,
        "itemId": item.get("itemId"),
        "quantity": qty,
        "address": address,
        "fence": fence_sale,
        **payout,
        "gold_gp": sheet["goldGp"],
    }


def stash_deposit(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    gold_gp: int = 0,
) -> dict[str, Any]:
    if gold_gp < 0:
        raise EconomyError("gold_gp must be non-negative")
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")
    sheet = _load_sheet(row)
    available = int(sheet.get("goldGp", 0))
    if gold_gp > available:
        raise EconomyError(f"Cannot deposit {gold_gp} gp (have {available})")
    sheet["goldGp"] = available - gold_gp
    state = get_account_state(conn, campaign_slug)
    state["stashGp"] = int(state.get("stashGp", 0)) + gold_gp
    _save_sheet(conn, character_id, campaign_slug, sheet)
    save_account_state(conn, campaign_slug, state)
    return {"ok": True, "deposited_gp": gold_gp, "stash_gp": state["stashGp"]}


def stash_withdraw(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    gold_gp: int,
) -> dict[str, Any]:
    state = get_account_state(conn, campaign_slug)
    stash = int(state.get("stashGp", 0))
    if gold_gp > stash:
        raise EconomyError(f"Stash has {stash} gp")
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")
    sheet = _load_sheet(row)
    sheet["goldGp"] = int(sheet.get("goldGp", 0)) + gold_gp
    state["stashGp"] = stash - gold_gp
    _save_sheet(conn, character_id, campaign_slug, sheet)
    save_account_state(conn, campaign_slug, state)
    return {"ok": True, "withdrawn_gp": gold_gp, "stash_gp": state["stashGp"]}


def stash_deposit_item(
    conn: sqlite3.Connection,
    content: ContentService,
    *,
    campaign_slug: str,
    session_id: str,
    character_id: str,
    instance_id: str,
    quantity: int | None = None,
) -> dict[str, Any]:
    _require_hub(conn, content, session_id, require_stash=True)

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")

    sheet = _load_sheet(row)
    lookup = content.items_lookup()
    ensure_normalized(sheet, item_lookup=lookup)
    pack = get_pack(sheet)
    item = _item_in_pack(pack, instance_id)
    if not item:
        raise EconomyError(f"Instance not in pack: {instance_id}")
    if item.get("equipped"):
        raise EconomyError("Cannot deposit equipped item")

    stack_qty = int(item.get("quantity", 1))
    xfer_qty = stack_qty if quantity is None else max(1, int(quantity))
    if xfer_qty > stack_qty:
        raise EconomyError(f"Cannot deposit {xfer_qty}; stack has {stack_qty}")

    if xfer_qty == stack_qty:
        removed = remove_instance(pack, instance_id)
        moved = removed.get("removed")
    else:
        removed = remove_instance(pack, instance_id, quantity=xfer_qty)
        moved = new_instance(
            str(item.get("itemId")),
            kind=str(item.get("kind")),
            uses=item.get("uses"),
            quantity=xfer_qty,
            enchant_ids=item.get("enchantIds"),
            catalog=lookup.get(str(item.get("itemId"))),
        )

    if not moved or not isinstance(moved, dict):
        raise EconomyError("Failed to remove item from pack")

    state = get_account_state(conn, campaign_slug)
    stash_pack = _stash_pack(state)
    stash_pack.extend(clone_pack_entries([moved], reid=True))
    _save_sheet(conn, character_id, campaign_slug, sheet)
    save_account_state(conn, campaign_slug, state)

    remaining = stack_qty - xfer_qty
    return {
        "ok": True,
        "instanceId": instance_id,
        "transferred": xfer_qty,
        "remaining": remaining,
        "itemId": item.get("itemId"),
    }


def stash_withdraw_item(
    conn: sqlite3.Connection,
    content: ContentService,
    *,
    campaign_slug: str,
    session_id: str,
    character_id: str,
    instance_id: str,
    quantity: int | None = None,
) -> dict[str, Any]:
    _require_hub(conn, content, session_id, require_stash=True)

    state = get_account_state(conn, campaign_slug)
    stash_pack = _stash_pack(state)
    item = _item_in_pack(stash_pack, instance_id)
    if not item:
        raise EconomyError(f"Instance not in stash: {instance_id}")

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")

    sheet = _load_sheet(row)
    lookup = content.items_lookup()
    ensure_normalized(sheet, item_lookup=lookup)
    pack = get_pack(sheet)

    stack_qty = int(item.get("quantity", 1))
    xfer_qty = stack_qty if quantity is None else max(1, int(quantity))
    if xfer_qty > stack_qty:
        raise EconomyError(f"Cannot withdraw {xfer_qty}; stash stack has {stack_qty}")

    if xfer_qty == stack_qty:
        removed = remove_instance(stash_pack, instance_id)
        moved = removed.get("removed")
    else:
        removed = remove_instance(stash_pack, instance_id, quantity=xfer_qty)
        moved = new_instance(
            str(item.get("itemId")),
            kind=str(item.get("kind")),
            uses=item.get("uses"),
            quantity=xfer_qty,
            enchant_ids=item.get("enchantIds"),
            catalog=lookup.get(str(item.get("itemId"))),
        )

    if not moved or not isinstance(moved, dict):
        raise EconomyError("Failed to remove item from stash")

    pack.extend(clone_pack_entries([moved], reid=True))
    _save_sheet(conn, character_id, campaign_slug, sheet)
    save_account_state(conn, campaign_slug, state)

    return {
        "ok": True,
        "instanceId": instance_id,
        "transferred": xfer_qty,
        "remaining": stack_qty - xfer_qty,
        "itemId": item.get("itemId"),
    }


def list_stash(conn: sqlite3.Connection, campaign_slug: str) -> dict[str, Any]:
    state = get_account_state(conn, campaign_slug)
    return {
        "ok": True,
        "campaign": campaign_slug,
        "stashGp": int(state.get("stashGp", 0)),
        "stash": state.get("stash"),
    }


def mark_character_dead(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    inherit_character_id: str | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT sheet_json, slot FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")
    conn.execute(
        "UPDATE characters SET alive = 0, slot = NULL WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    )
    body_gold = int(json.loads(row["sheet_json"]).get("goldGp", 0))
    conn.commit()
    result: dict[str, Any] = {
        "ok": True,
        "dead_character_id": character_id,
        "body_gold_on_corpse": body_gold,
    }
    if inherit_character_id:
        result["inherit_ignored"] = True
        result["message"] = "Inheritance is disabled; use process_delver_death for corpse placement."
    return result
