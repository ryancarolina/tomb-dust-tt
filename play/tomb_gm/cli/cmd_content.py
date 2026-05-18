from __future__ import annotations

import argparse

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services.content import ContentService


def register(sub: argparse._SubParsersAction) -> None:
    content = sub.add_parser("content", help="Read-only canon content lookups")
    actions = content.add_subparsers(dest="content_action", required=True)

    cell = actions.add_parser("cell", help="AV-GRID cell record")
    cell.add_argument("address", metavar="ADDRESS")
    cell.set_defaults(handler=handle_cell)

    monster = actions.add_parser("monster", help="Monster stat block JSON")
    monster.add_argument("monster_id", metavar="ID")
    monster.add_argument("--tier", default=None, help="Stat block tier or id")
    monster.set_defaults(handler=handle_monster)

    weapon = actions.add_parser("weapon", help="Weapon definition")
    weapon.add_argument("weapon_id", metavar="ID")
    weapon.set_defaults(handler=handle_weapon)

    spell = actions.add_parser("spell", help="Spell definition")
    spell.add_argument("spell_id", metavar="ID")
    spell.set_defaults(handler=handle_spell)

    npc = actions.add_parser("npc", help="NPC doc excerpt")
    npc.add_argument("npc_id", metavar="ID")
    npc.set_defaults(handler=handle_npc)

    site = actions.add_parser("site", help="Site graph JSON")
    site.add_argument("site_id", metavar="ID")
    site.set_defaults(handler=handle_site)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def _content(args: argparse.Namespace) -> ContentService:
    ctx = _ctx(args)
    return ContentService(ctx.config.content_root)


def handle_cell(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    svc = _content(args)
    address = args.address.strip()
    cell = svc.cell_payload(address)
    if cell is None:
        return {
            "ok": False,
            "error": "UNKNOWN_ADDRESS",
            "address": address,
            "message": f"Unknown AV-GRID address: {address}",
        }
    return {"ok": True, "address": address, "cell": cell}


def handle_monster(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    svc = _content(args)
    monster_id = args.monster_id.strip()
    data, blocker = svc.load_monster(monster_id, tier=args.tier)
    if blocker:
        return {"ok": False, "blocked": True, "blockers": [blocker]}
    return {"ok": True, "monster_id": monster_id, "monster": data}


def handle_weapon(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    svc = _content(args)
    weapon_id = args.weapon_id.strip()
    weapon = svc.load_weapon(weapon_id)
    if weapon is None:
        return {
            "ok": False,
            "error": "UNKNOWN_WEAPON",
            "weapon_id": weapon_id,
            "message": f"Unknown weapon id: {weapon_id}",
        }
    return {"ok": True, "weapon_id": weapon_id, "weapon": weapon}


def handle_spell(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    svc = _content(args)
    spell_id = args.spell_id.strip()
    spell = svc.load_spell(spell_id)
    if spell is None:
        return {"ok": False, "error": "UNKNOWN_SPELL", "spell_id": spell_id}
    return {"ok": True, "spell_id": spell_id, "spell": spell}


def handle_npc(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    svc = _content(args)
    npc_id = args.npc_id.strip()
    doc = svc.load_npc_doc(npc_id)
    if doc is None:
        return {"ok": False, "error": "UNKNOWN_NPC", "npc_id": npc_id}
    return {"ok": True, **doc}


def handle_site(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    svc = _content(args)
    site_id = args.site_id.strip()
    data = svc.load_site(site_id)
    if data is None:
        return {"ok": False, "error": "UNKNOWN_SITE", "site_id": site_id}
    return {"ok": True, "site_id": site_id, "site": data}


add_command_module(register)
