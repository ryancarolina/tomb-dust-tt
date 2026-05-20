from __future__ import annotations

import argparse
import json

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.domain.inventory import ensure_normalized, equip, format_inventory_summary, get_pack, unequip, use_item
from tomb_gm.services.content import ContentService


def register(sub: argparse._SubParsersAction) -> None:
    inv = sub.add_parser("inventory", help="Equip, unequip, list pack")
    actions = inv.add_subparsers(dest="inventory_action", required=True)

    lst = actions.add_parser("list", help="List character inventory")
    lst.add_argument("--campaign", required=True)
    lst.add_argument("--character", required=True, dest="character_id")
    lst.set_defaults(handler=handle_list)

    eq = actions.add_parser("equip", help="Equip pack instance to slot")
    eq.add_argument("--campaign", required=True)
    eq.add_argument("--character", required=True, dest="character_id")
    eq.add_argument("--instance", required=True, dest="instance_id")
    eq.add_argument("--slot", required=True)
    eq.set_defaults(handler=handle_equip)

    ueq = actions.add_parser("unequip", help="Unequip pack instance")
    ueq.add_argument("--campaign", required=True)
    ueq.add_argument("--character", required=True, dest="character_id")
    ueq.add_argument("--instance", required=True, dest="instance_id")
    ueq.set_defaults(handler=handle_unequip)

    use = actions.add_parser("use", help="Use/decrement consumable or ammo stack")
    use.add_argument("--campaign", required=True)
    use.add_argument("--character", required=True, dest="character_id")
    use.add_argument("--instance", required=True, dest="instance_id")
    use.add_argument("--quantity", type=int, default=1)
    use.set_defaults(handler=handle_use)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    return CommandContext(config=load_config(ws), conn=connect(load_config(ws).db_path))


def _load_sheet(ctx: CommandContext, campaign: str, character_id: str) -> tuple[dict, dict[str, dict]]:
    row = ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign),
    ).fetchone()
    if not row:
        return {"ok": False, "error": f"Character not found: {character_id}"}, {}
    content = ContentService(ctx.config.content_root)
    lookup = content.items_lookup()
    sheet = json.loads(row["sheet_json"])
    ensure_normalized(sheet, item_lookup=lookup)
    return sheet, lookup


def _save_sheet(ctx: CommandContext, campaign: str, character_id: str, sheet: dict) -> None:
    ctx.conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), character_id, campaign),
    )
    ctx.conn.commit()


def handle_list(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    sheet, lookup = _load_sheet(ctx, args.campaign, args.character_id)
    if sheet.get("ok") is False:
        return sheet
    content = ContentService(ctx.config.content_root)
    display = {iid: content.item_display_name(iid) for iid in lookup}
    return {
        "ok": True,
        "character_id": args.character_id,
        "goldGp": int(sheet.get("goldGp", 0)),
        "pack": get_pack(sheet),
        "summary": format_inventory_summary(sheet, item_display=display),
    }


def handle_equip(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    sheet, lookup = _load_sheet(ctx, args.campaign, args.character_id)
    if sheet.get("ok") is False:
        return sheet
    result = equip(get_pack(sheet), args.instance_id, args.slot, item_lookup=lookup)
    if not result.get("ok"):
        return result
    _save_sheet(ctx, args.campaign, args.character_id, sheet)
    return {"ok": True, "character_id": args.character_id, **result}


def handle_unequip(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    sheet, _lookup = _load_sheet(ctx, args.campaign, args.character_id)
    if sheet.get("ok") is False:
        return sheet
    result = unequip(get_pack(sheet), args.instance_id)
    if not result.get("ok"):
        return result
    _save_sheet(ctx, args.campaign, args.character_id, sheet)
    return {"ok": True, "character_id": args.character_id, **result}


def handle_use(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    sheet, lookup = _load_sheet(ctx, args.campaign, args.character_id)
    if sheet.get("ok") is False:
        return sheet
    result = use_item(
        get_pack(sheet),
        args.instance_id,
        quantity=args.quantity,
        item_lookup=lookup,
    )
    if not result.get("ok"):
        return result
    _save_sheet(ctx, args.campaign, args.character_id, sheet)
    return {"ok": True, "character_id": args.character_id, **result}


add_command_module(register)
