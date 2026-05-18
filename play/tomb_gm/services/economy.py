"""Campaign economy: character gold, buy/sell, account stash."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from tomb_gm.services.content import ContentService


class EconomyError(ValueError):
    pass


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


def get_account_state(conn: sqlite3.Connection, campaign_slug: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT account_state_json FROM campaigns WHERE slug = ?",
        (campaign_slug,),
    ).fetchone()
    if not row:
        raise EconomyError(f"Campaign not found: {campaign_slug}")
    state = json.loads(row["account_state_json"] or "{}")
    state.setdefault("stashGp", 0)
    state.setdefault("stashItems", [])
    state.setdefault("deed_counters", {})
    state.setdefault("flags", {})
    return state


def save_account_state(conn: sqlite3.Connection, campaign_slug: str, state: dict[str, Any]) -> None:
    conn.execute(
        "UPDATE campaigns SET account_state_json = ?, updated_at = ? WHERE slug = ?",
        (json.dumps(state), _now(), campaign_slug),
    )
    conn.commit()


def buy_item(
    conn: sqlite3.Connection,
    content: ContentService,
    *,
    campaign_slug: str,
    character_id: str,
    item_id: str,
    quantity: int = 1,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")
    weapon = content.load_weapon(item_id)
    if weapon:
        cost = int(weapon.get("costGp", weapon.get("cost", 0))) * quantity
        item_ref = item_id
    else:
        cost = 5 * quantity
        item_ref = item_id

    sheet = _load_sheet(row)
    gold = int(sheet.get("goldGp", 0))
    if gold < cost:
        raise EconomyError(f"Insufficient gold: need {cost}, have {gold}")
    sheet["goldGp"] = gold - cost
    pack = sheet.setdefault("inventory", {}).setdefault("pack", [])
    for _ in range(quantity):
        pack.append(item_ref)
    _save_sheet(conn, character_id, campaign_slug, sheet)
    return {"ok": True, "character_id": character_id, "item": item_ref, "cost_gp": cost, "gold_gp": sheet["goldGp"]}


def sell_item(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
    item_id: str,
    price_gp: int | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise EconomyError(f"Character not found: {character_id}")
    sheet = _load_sheet(row)
    pack = sheet.get("inventory", {}).get("pack", [])
    if item_id not in pack:
        raise EconomyError(f"Item not in pack: {item_id}")
    pack.remove(item_id)
    gain = price_gp if price_gp is not None else max(1, 5 // 2)
    sheet["goldGp"] = int(sheet.get("goldGp", 0)) + gain
    _save_sheet(conn, character_id, campaign_slug, sheet)
    return {"ok": True, "sold": item_id, "gained_gp": gain, "gold_gp": sheet["goldGp"]}


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
    state = get_account_state(conn, campaign_slug)
    body_gold = int(json.loads(row["sheet_json"]).get("goldGp", 0))
    result: dict[str, Any] = {
        "ok": True,
        "dead_character_id": character_id,
        "body_gold_lost": body_gold,
        "stash_gp": state.get("stashGp", 0),
    }
    if inherit_character_id:
        heir = conn.execute(
            "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ? AND alive = 1",
            (inherit_character_id, campaign_slug),
        ).fetchone()
        if not heir:
            raise EconomyError(f"Heir not found or dead: {inherit_character_id}")
        sheet = json.loads(heir["sheet_json"])
        sheet["goldGp"] = int(sheet.get("goldGp", 0)) + int(state.get("stashGp", 0))
        state["stashGp"] = 0
        _save_sheet(conn, inherit_character_id, campaign_slug, sheet)
        save_account_state(conn, campaign_slug, state)
        result["inherit_character_id"] = inherit_character_id
        result["heir_gold_gp"] = sheet["goldGp"]
    conn.commit()
    return result
