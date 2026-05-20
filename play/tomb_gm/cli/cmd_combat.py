from __future__ import annotations

import argparse
import json

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.domain.combat_sheet import (
    attack_modifiers_from_sheet,
    find_combatant,
    load_character_sheet,
    target_ac_from_monster,
)
from tomb_gm.services.content import ContentService
from tomb_gm.services.simulation.combat import (
    advance_turn,
    apply_damage_to_combatant,
    combat_status,
    end_combat,
    start_combat,
)
from tomb_gm.services.simulation.rolls import perform_attack_roll


def register(sub: argparse._SubParsersAction) -> None:
    combat = sub.add_parser("combat", help="Encounter combat")
    combat_sub = combat.add_subparsers(dest="combat_cmd", required=True)

    start = combat_sub.add_parser("start", help="Start combat from monster specs")
    start.add_argument(
        "--monsters",
        nargs="+",
        required=True,
        metavar="SPEC",
        help="Monster id or id:count (e.g. grave-ghoul:2)",
    )
    start.add_argument("--tier", default=None, help="Stat block tier (default: first block)")
    start.add_argument(
        "--include-party",
        action="store_true",
        default=True,
        help="Add roster PCs to initiative (default: true)",
    )
    start.add_argument(
        "--no-party",
        action="store_true",
        help="Omit roster from combat",
    )
    start.add_argument("--campaign", default=None, help="Campaign slug (required with --include-party)")
    start.set_defaults(handler=handle_start)

    combat_sub.add_parser("status", help="Active combat snapshot").set_defaults(handler=handle_status)
    turn = combat_sub.add_parser("turn", help="Advance combat turn")
    turn.set_defaults(handler=handle_turn)
    combat_sub.add_parser("end", help="End active combat").set_defaults(handler=handle_end)

    atk = combat_sub.add_parser("attack", help="Attack from character sheet vs combatant")
    atk.add_argument("--attacker", required=True, dest="character_id")
    atk.add_argument("--target", required=True, dest="target_id")
    atk.add_argument("--campaign", required=True)
    atk.add_argument("--weapon", default=None)
    atk.set_defaults(handler=handle_attack)

    cast = combat_sub.add_parser("cast", help="Cast spell from character sheet")
    cast.add_argument("--caster", required=True, dest="character_id")
    cast.add_argument("--spell", required=True, dest="spell_id")
    cast.add_argument("--campaign", required=True)
    cast.add_argument("--target", default=None, dest="target_id")
    cast.set_defaults(handler=handle_cast)

    dmg = combat_sub.add_parser("damage", help="Apply damage to a combatant")
    dmg.add_argument("--target", required=True, dest="target_id")
    dmg.add_argument("--amount", type=int, required=True)
    dmg.add_argument("--campaign", default=None)
    dmg.set_defaults(handler=handle_damage)

    stab = combat_sub.add_parser("stabilize", help="Stabilize a dying PC")
    stab.add_argument("--character", required=True, dest="character_id")
    stab.add_argument("--campaign", required=True)
    stab.set_defaults(handler=handle_stabilize)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def _require_session(ctx: CommandContext) -> str:
    path = ctx.config.active_path
    if not path.exists():
        raise ValueError("no active session — start a play session first")
    data = json.loads(path.read_text(encoding="utf-8"))
    session_id = data.get("session_id")
    if not session_id:
        raise ValueError("active.json missing session_id")
    return session_id


def _campaign_from_session(ctx: CommandContext, session_id: str) -> str | None:
    row = ctx.conn.execute(
        "SELECT campaign_slug FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    return row["campaign_slug"] if row else None


def handle_start(args: argparse.Namespace, _ctx_unused: CommandContext | None) -> dict:
    ctx = _ctx(args)
    session_id = _require_session(ctx)
    campaign = args.campaign or _campaign_from_session(ctx, session_id)
    include_party = bool(args.include_party) and not bool(getattr(args, "no_party", False))
    if include_party and not campaign:
        return {"ok": False, "error": "campaign required when including party"}
    return start_combat(
        ctx.conn,
        session_id=session_id,
        content_root=ctx.config.content_root,
        monster_specs=args.monsters,
        tier=args.tier,
        seed=args.seed,
        include_party=include_party,
        campaign_slug=campaign,
    )


def handle_status(args: argparse.Namespace, _ctx_unused: CommandContext | None) -> dict:
    ctx = _ctx(args)
    session_id = _require_session(ctx)
    return combat_status(ctx.conn, session_id)


def handle_end(args: argparse.Namespace, _ctx_unused: CommandContext | None) -> dict:
    ctx = _ctx(args)
    session_id = _require_session(ctx)
    campaign = _campaign_from_session(ctx, session_id)
    return end_combat(ctx.conn, session_id, campaign_slug=campaign)


def handle_cast(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    from tomb_gm.cli.cmd_core import log_event
    from tomb_gm.domain.spell_cast import cast_spell

    ctx = _ctx(args)
    session_id = _require_session(ctx)
    return cast_spell(
        ctx.conn,
        log_event,
        content_root=ctx.config.content_root,
        campaign_slug=args.campaign,
        character_id=args.character_id,
        spell_id=args.spell_id,
        session_id=session_id,
        target_id=args.target_id,
        seed=args.seed,
    )


def handle_damage(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id = _require_session(ctx)
    campaign = args.campaign or _campaign_from_session(ctx, session_id)
    return apply_damage_to_combatant(
        ctx.conn,
        session_id,
        args.target_id,
        args.amount,
        campaign_slug=campaign,
    )


def handle_stabilize(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    from tomb_gm.domain.combat_player import stabilize_character

    ctx = _ctx(args)
    session_id = _require_session(ctx)
    return stabilize_character(
        ctx.conn,
        campaign_slug=args.campaign,
        character_id=args.character_id,
        session_id=session_id,
    )


def handle_turn(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    from tomb_gm.cli import cmd_combat_handlers

    ctx = _ctx(args)
    return cmd_combat_handlers.handle_turn(ctx, _require_session(ctx))


def handle_attack(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    from tomb_gm.cli import cmd_combat_handlers

    ctx = _ctx(args)
    return cmd_combat_handlers.handle_attack(ctx, _require_session(ctx), args)


add_command_module(register)
