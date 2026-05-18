from __future__ import annotations

import argparse

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.domain.character import CharacterError, create_character, get_character, list_characters


def register(sub: argparse._SubParsersAction) -> None:
    char = sub.add_parser("character", help="Player character sheets")
    char_sub = char.add_subparsers(dest="character_command", required=True)

    create_p = char_sub.add_parser("create", help="Create a character (MVP flags)")
    create_p.add_argument("--campaign", required=True, help="Campaign slug")
    create_p.add_argument("--name", required=True, help="Display name")
    create_p.add_argument(
        "--class",
        dest="base_class",
        required=True,
        choices=["peasant", "laborer", "urchin", "apprentice", "militia", "novice"],
        help="Tier-1 base class",
    )
    create_p.add_argument("--id", dest="character_id", default=None, help="Character id slug override")
    for attr in ("str", "agi", "sta", "int", "spi", "luc"):
        create_p.add_argument(f"--{attr}", type=int, default=None, help=f"{attr.upper()} score")
    create_p.add_argument(
        "--skill",
        action="append",
        dest="skills",
        default=None,
        help="Starting skill slug (repeat 3 times; defaults by class)",
    )
    create_p.add_argument(
        "--roll-attributes",
        action="store_true",
        help="GM rolls 1d10 per attribute via CLI (do not ask players to roll)",
    )
    create_p.add_argument("--race", default=None, help="Race id from build/data/races/races.json")
    create_p.add_argument(
        "--human-bonus",
        default=None,
        help="For human: comma-separated attrs for +1 each (e.g. STR,INT)",
    )
    create_p.add_argument(
        "--life-flex",
        dest="life_flex",
        default=None,
        help="For flexible life events: comma-separated attrs",
    )
    create_p.add_argument(
        "--full",
        action="store_true",
        help="Full creation: 1d10, genetics, life event, race, kit, starting gold",
    )
    create_p.add_argument("--no-kit", action="store_true", help="Skip starting kit with --full")
    create_p.set_defaults(handler=handle_create)

    show_p = char_sub.add_parser("show", help="Show character sheet JSON")
    show_p.add_argument("--campaign", required=True)
    show_p.add_argument("--id", required=True, dest="character_id")
    show_p.set_defaults(handler=handle_show)

    list_p = char_sub.add_parser("list", help="List characters in a campaign")
    list_p.add_argument("--campaign", required=True)
    list_p.set_defaults(handler=handle_list)

    fortune = char_sub.add_parser("fortune", help="Fortune pool on a character")
    fortune_sub = fortune.add_subparsers(dest="fortune_cmd", required=True)
    f_show = fortune_sub.add_parser("show", help="Show Fortune pool")
    f_show.add_argument("--campaign", required=True)
    f_show.add_argument("--id", required=True, dest="character_id")
    f_show.set_defaults(handler=handle_fortune_show)
    f_spend = fortune_sub.add_parser("spend", help="Spend Fortune points")
    f_spend.add_argument("--campaign", required=True)
    f_spend.add_argument("--id", required=True, dest="character_id")
    f_spend.add_argument("--amount", type=int, default=1)
    f_spend.set_defaults(handler=handle_fortune_spend)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def _attributes_from_args(args: argparse.Namespace) -> dict[str, int]:
    attrs: dict[str, int] = {}
    mapping = {
        "str": "STR",
        "agi": "AGI",
        "sta": "STA",
        "int": "INT",
        "spi": "SPI",
        "luc": "LUC",
    }
    for flag, key in mapping.items():
        value = getattr(args, flag, None)
        if value is not None:
            if value < 1 or value > 30:
                raise CharacterError(f"{key} must be between 1 and 30")
            attrs[key] = value
    return attrs


def _csv_attrs(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [p.strip().upper() for p in value.split(",") if p.strip()]


def handle_create(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    import random

    from tomb_gm.domain.character import roll_attribute_scores
    from tomb_gm.domain.creation import run_creation_pipeline

    ctx = _ctx(args)
    attrs = _attributes_from_args(args)
    roll_detail: list | None = None
    race_id = getattr(args, "race", None)
    gold_gp = 0
    inventory = None
    armor = None
    creation_audit = None

    if getattr(args, "full", False):
        if attrs and not getattr(args, "roll_attributes", False):
            return {"ok": False, "error": "Use --full without manual --str flags, or omit --full"}
        rng = random.Random(args.seed) if getattr(args, "seed", None) is not None else random.Random()
        pipeline = run_creation_pipeline(
            content_root=ctx.config.content_root,
            base_class=args.base_class,
            race_id=race_id,
            human_bonus=_csv_attrs(getattr(args, "human_bonus", None)),
            life_event_flexible=_csv_attrs(getattr(args, "life_flex", None)),
            rng=rng,
            attributes=attrs if attrs else None,
        )
        attrs = pipeline["attributes"]
        race_id = pipeline.get("raceId") or race_id
        gold_gp = int(pipeline.get("goldGp", 0))
        creation_audit = pipeline.get("audit")
        if not getattr(args, "no_kit", False):
            kit = pipeline["kit"]
            inventory = {
                "body": [],
                "pack": list(kit.get("items", [])),
                "weapons": list(kit.get("weapons", [])),
            }
            armor = dict(kit.get("armor") or {})
    elif getattr(args, "roll_attributes", False):
        if attrs:
            return {
                "ok": False,
                "error": "Use either --roll-attributes or explicit --str/--agi/... flags, not both",
            }
        rng = random.Random(args.seed) if getattr(args, "seed", None) is not None else random.Random()
        attrs, roll_detail = roll_attribute_scores(rng)

    try:
        result = create_character(
            ctx.conn,
            campaign_slug=args.campaign,
            display_name=args.name,
            base_class=args.base_class,
            attributes=attrs or None,
            skill_ids=args.skills,
            character_id=args.character_id,
            race_id=race_id,
            gold_gp=gold_gp,
            inventory=inventory,
            armor=armor,
            creation_audit=creation_audit,
        )
    except CharacterError as exc:
        return {"ok": False, "error": str(exc)}
    sheet = result["sheet"]
    out: dict = {
        "ok": True,
        "character_id": result["id"],
        "campaign": args.campaign,
        "display_name": sheet["displayName"],
        "class_id": sheet["classId"],
        "race_id": sheet.get("raceId"),
        "attributes": sheet["attributes"],
        "hp": sheet["hp"],
        "mp": sheet["mp"],
        "fortune": sheet["fortune"],
        "gold_gp": sheet.get("goldGp", 0),
        "skills": sheet["skills"],
        "inventory": sheet.get("inventory"),
    }
    if roll_detail is not None:
        out["attribute_rolls"] = roll_detail
    if creation_audit is not None:
        out["creation_audit"] = creation_audit
    return out


def handle_show(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    record = get_character(
        ctx.conn,
        campaign_slug=args.campaign,
        character_id=args.character_id,
    )
    if not record:
        return {"ok": False, "error": f"Character not found: {args.character_id}"}
    return {"ok": True, **record}


def handle_list(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    characters = list_characters(ctx.conn, campaign_slug=args.campaign)
    return {"ok": True, "campaign": args.campaign, "characters": characters}


def handle_fortune_show(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    record = get_character(ctx.conn, campaign_slug=args.campaign, character_id=args.character_id)
    if not record:
        return {"ok": False, "error": f"Character not found: {args.character_id}"}
    fortune = record["sheet"].get("fortune", {})
    return {
        "ok": True,
        "character_id": args.character_id,
        "fortune": fortune,
    }


def handle_fortune_spend(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    from tomb_gm.domain.combat_player import spend_fortune

    ctx = _ctx(args)
    try:
        return spend_fortune(
            ctx.conn,
            campaign_slug=args.campaign,
            character_id=args.character_id,
            amount=args.amount,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


add_command_module(register)
