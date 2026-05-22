"""Process table beats: parse player lines and apply mechanics."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from tomb_gm.cli.cmd_core import log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.domain import session as session_domain
from tomb_gm.services.content import ContentService
from tomb_gm.services.memory import remember_fact
from tomb_gm.services.memory.choice_facts import remember_beat_choices
from tomb_gm.services.encounters import wilderness_travel_roll
from tomb_gm.services.site import SiteError, enter_site, move_site, search_site, where_site
from tomb_gm.services.simulation.combat import combat_status
from tomb_gm.services.world import WorldService, resolve_surface_address

AV_ADDRESS_RE = re.compile(
    r"\b(\d{1,2}-[A-Z](?:-(?:UG-\d+|EP|BV|SK))*)\b"
)
SITE_ID_RE = re.compile(r"\b(breley-undercrypt)\b", re.I)
NODE_ID_RE = re.compile(
    r"\b(chapel-stairs|ossuary-hall|marshal-tomb|iron-seam|vault-landing|veil-niche)\b",
    re.I,
)
COMBAT_RE = re.compile(r"\b(attack|strike|shoot|stab|fight|engage)\b", re.I)
MONSTER_ID_RE = re.compile(
    r"\b(grave-ghoul|hollow-knight|rust-slime|thornwolf|ash-shade)(?::(\d+))?\b",
    re.I,
)
CAST_RE = re.compile(r"\b(cast|invoke|channel)\b", re.I)
SPELL_ID_RE = re.compile(r"\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b", re.I)
SEARCH_RE = re.compile(
    r"\b(search|investigate|scour|rifle|loot the|pick through)\b",
    re.I,
)
STABILIZE_RE = re.compile(r"\b(stabilize|stabilise|bind wounds|first aid)\b", re.I)


def _active_session(ctx: CommandContext) -> tuple[str, str, dict]:
    active = session_domain.read_active(ctx.config)
    if not active or not active.get("session_id"):
        raise ValueError("NO_ACTIVE_SESSION")
    session_id = active["session_id"]
    row = ctx.conn.execute(
        "SELECT campaign_slug, ended_at FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if not row or row["ended_at"] is not None:
        raise ValueError("NO_ACTIVE_SESSION")
    return session_id, row["campaign_slug"], active


def _party_snapshot(ctx: CommandContext, session_id: str) -> dict[str, Any]:
    party = ctx.conn.execute(
        "SELECT address, mode, site_id, site_node_id, phase FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not party:
        return {}
    return {
        "address": party["address"],
        "mode": party["mode"],
        "site_id": party["site_id"],
        "site_node_id": party["site_node_id"],
        "phase": party["phase"],
    }


def _parse_lines(actions: dict[str, Any]) -> list[dict[str, Any]]:
    lines = actions.get("lines") or []
    parsed: list[dict[str, Any]] = []
    for raw in lines:
        if not isinstance(raw, dict):
            continue
        slot = raw.get("slot")
        text = str(raw.get("raw") or raw.get("text") or "").strip()
        if not text:
            continue
        parsed.append(
            {
                "slot": slot,
                "raw": text,
                "lower": text.lower(),
            }
        )
    return parsed


def _find_address(text: str, content: ContentService) -> str | None:
    for match in AV_ADDRESS_RE.finditer(text.upper()):
        candidate = match.group(1)
        if content.get_cell(candidate):
            return candidate
    return None


def _intent_travel(text: str, lower: str) -> str | None:
    if any(k in lower for k in ("travel", "go to", "head to", "walk to", "move to")):
        return "travel"
    if re.search(r"\b(east|west|north|south)\b", lower) and "road" in lower:
        return "travel_hint"
    return None


def _extract_travel_destination(text: str) -> str:
    match = re.search(
        r"\b(?:travel|go|head|walk|move)\s+(?:to\s+)?(.+)$",
        text.strip(),
        re.I,
    )
    if match:
        return match.group(1).strip()
    return text.strip()


def _intent_site(lower: str) -> str | None:
    if "enter" in lower and ("undercrypt" in lower or "site" in lower or "delve" in lower):
        return "site_enter"
    if SITE_ID_RE.search(lower):
        if "enter" in lower:
            return "site_enter"
    if NODE_ID_RE.search(lower) and any(
        k in lower for k in ("move", "go", "enter", "head", "step", "into", "toward")
    ):
        return "site_move"
    return None


def _intent_look(lower: str) -> bool:
    return any(
        k in lower
        for k in (
            "look around",
            "where are we",
            "what do i see",
            "survey",
            "scan the",
            "examine the area",
        )
    )


def _maybe_wilderness_roll(
    ctx: CommandContext,
    *,
    to_address: str,
    stamp_json: str | None,
    auto_roll: bool,
    seed: int | None,
) -> dict[str, Any] | None:
    if not auto_roll:
        return None
    content = ContentService(ctx.config.content_root)
    world = WorldService(content)
    if not world.wilderness_travel_needed(to_address, stamp_json):
        return None
    cell = content.get_cell(to_address) or {}
    biomes = cell.get("biomes") or ["HL"]
    danger = str(cell.get("danger") or "skirmisher")
    import random

    rng = random.Random(seed) if seed is not None else random.Random()
    return wilderness_travel_roll(
        ctx.config.content_root,
        biomes=biomes,
        danger=danger,
        rng=rng,
    )


def _apply_travel(
    ctx: CommandContext,
    session_id: str,
    from_address: str,
    to_address: str,
    stamp_json: str | None,
    *,
    auto_roll_wilderness: bool = False,
    seed: int | None = None,
) -> dict[str, Any]:
    content = ContentService(ctx.config.content_root)
    world = WorldService(content)
    ok, code = world.can_travel(from_address, to_address)
    if not ok:
        return {"ok": False, "error": code, "from": from_address, "to": to_address}
    wilderness = world.wilderness_travel_needed(to_address, stamp_json)
    ctx.conn.execute(
        "UPDATE party_state SET address = ?, mode = 'surface', site_id = NULL, site_node_id = NULL "
        "WHERE session_id = ?",
        (to_address, session_id),
    )
    ctx.conn.commit()
    log_event(
        ctx.conn,
        session_id,
        "world_travel",
        {"from": from_address, "to": to_address, "wilderness_roll_pending": wilderness},
    )
    cell = content.cell_payload(to_address)
    out: dict[str, Any] = {
        "ok": True,
        "action": "travel",
        "from": from_address,
        "to": to_address,
        "cell": cell,
        "wilderness_roll_pending": wilderness,
    }
    if auto_roll_wilderness and wilderness:
        roll = _maybe_wilderness_roll(
            ctx,
            to_address=to_address,
            stamp_json=stamp_json,
            auto_roll=True,
            seed=seed,
        )
        if roll:
            out["wilderness"] = roll
            out["wilderness_roll_pending"] = False
            if roll.get("monster_specs"):
                out["wilderness_monster_specs"] = roll["monster_specs"]
    return out


def _build_narration(mechanical: list[dict[str, Any]], party: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    parts: list[str] = []
    addr = party.get("address", "?")
    if not mechanical:
        parts.append(f"The party holds at {addr}, waiting on the next move.")
    for m in mechanical:
        if not m.get("ok", True):
            parts.append(m.get("message") or m.get("error", "Something blocks that action."))
            continue
        act = m.get("action")
        if act == "travel":
            cell = m.get("cell") or {}
            name = cell.get("displayName") or m.get("to")
            parts.append(f"The party reaches {name} ({m.get('to')}).")
        elif act == "site_enter":
            node = m.get("node") or {}
            parts.append(f"You descend into {m.get('site_id', 'the site')} at {node.get('displayName', 'the entry')}.")
        elif act == "site_move":
            node = m.get("node") or {}
            parts.append(f"The party advances to {node.get('displayName', m.get('to'))}.")
            if m.get("hazard"):
                parts.append(f"Hazard: {m['hazard']}")
            if m.get("encounters"):
                parts.append("Something stirs in the dark.")
        elif act == "look":
            cell = m.get("cell") or {}
            node = m.get("node") or {}
            label = node.get("displayName") or cell.get("displayName") or m.get("address")
            parts.append(f"You take in the scene at {label}.")
        elif act == "site_search":
            if m.get("success"):
                parts.append("Your search turns up something useful.")
                granted = m.get("loot_granted") or {}
                if granted.get("ok"):
                    items = [g.get("itemId") for g in (granted.get("grants") or [])]
                    gp = int(granted.get("gp", 0))
                    if items or gp:
                        parts.append(f"Salvage secured: {', '.join(items) if items else 'coin'} (+{gp} gp).")
                elif m.get("loot"):
                    parts.append("Salvage worth claiming.")
            else:
                parts.append("The search yields nothing.")
        elif act == "combat_start":
            parts.append("Steel clears scabbards — combat is joined.")
        elif act == "wilderness":
            parts.append(m.get("result", "The road stays quiet."))
        elif act == "spell_cast":
            parts.append(f"A spell crackles: {m.get('displayName', 'magic')}.")
        elif act == "stabilize":
            parts.append("Wounds are bound; the delver holds at zero.")
        elif act == "note":
            parts.append(m.get("summary", "The moment passes."))
        else:
            parts.append(m.get("summary", "The action resolves without incident."))

    brief = " ".join(parts)
    speak_lines = [{"text": brief, "voice": "narrator"}]
    return brief, speak_lines


def process_beat(ctx: CommandContext, actions: dict[str, Any]) -> dict[str, Any]:
    beat_id = f"b-{uuid.uuid4().hex[:12]}"
    session_id, campaign_slug, _active = _active_session(ctx)
    party = _party_snapshot(ctx, session_id)
    content = ContentService(ctx.config.content_root)

    row = ctx.conn.execute(
        "SELECT address, stamp_json, mode FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    address = row["address"]
    stamp_json = row["stamp_json"]
    mode = row["mode"]

    lines = _parse_lines(actions)
    mechanical: list[dict[str, Any]] = []
    auto_roll_wilderness = bool(actions.get("auto_roll_wilderness"))
    beat_seed = actions.get("seed")

    for line in lines:
        text = line["raw"]
        lower = line["lower"]
        slot = line.get("slot")

        if _intent_look(lower):
            if mode == "site":
                try:
                    result = where_site(ctx)
                    mechanical.append({**result, "action": "look"})
                except SiteError as exc:
                    mechanical.append({"ok": False, "error": str(exc), "slot": slot})
            else:
                world = WorldService(content)
                payload = world.where_payload(address, mode=mode, stamp_json=stamp_json)
                mechanical.append({"ok": True, "action": "look", **(payload or {})})
            continue

        site_intent = _intent_site(lower)
        if site_intent == "site_enter":
            site_match = SITE_ID_RE.search(lower)
            site_id = site_match.group(1).lower() if site_match else "breley-undercrypt"
            try:
                result = enter_site(ctx, site_id)
                mechanical.append({**result, "action": "site_enter"})
                mode = "site"
            except SiteError as exc:
                mechanical.append({"ok": False, "error": str(exc), "slot": slot})
            continue

        if site_intent == "site_move" or (mode == "site" and NODE_ID_RE.search(lower)):
            node_match = NODE_ID_RE.search(lower)
            if node_match:
                try:
                    result = move_site(ctx, node_match.group(1).lower())
                    mechanical.append({**result, "action": "site_move"})
                except SiteError as exc:
                    mechanical.append({"ok": False, "error": str(exc), "slot": slot})
                continue

        if mode == "site" and SEARCH_RE.search(lower):
            try:
                result = search_site(ctx, dc=13, skill_mod=0, seed=beat_seed)
                mechanical.append(result)
            except SiteError as exc:
                mechanical.append({"ok": False, "error": str(exc), "slot": slot})
            continue

        monster_specs: list[str] = []
        for m in MONSTER_ID_RE.finditer(lower):
            mid = m.group(1).lower()
            count = m.group(2) or "1"
            monster_specs.append(f"{mid}:{count}")
        if monster_specs or (
            COMBAT_RE.search(lower) and mode != "site" and actions.get("auto_combat")
        ):
            specs = monster_specs or ["grave-ghoul:1"]
            mechanical.append(
                {
                    "ok": True,
                    "action": "combat_trigger",
                    "monster_specs": specs,
                    "include_party": actions.get("include_party", True),
                    "slot": slot,
                }
            )
            continue

        if COMBAT_RE.search(lower) and mode != "site":
            status = combat_status(ctx.conn, session_id)
            if status.get("ok"):
                mechanical.append(
                    {
                        "ok": True,
                        "action": "combat_hint",
                        "message": "Combat active — use combat attack / combat turn",
                        "turn_id": status.get("turn_id"),
                        "slot": slot,
                    }
                )
            else:
                mechanical.append(
                    {
                        "ok": True,
                        "action": "combat_hint",
                        "message": "Name monsters or set auto_combat in beat JSON to start combat",
                        "slot": slot,
                    }
                )
            continue

        if CAST_RE.search(lower):
            spell_match = SPELL_ID_RE.search(lower)
            spell_id = spell_match.group(1).lower() if spell_match else None
            if spell_id and content.load_spell(spell_id) and slot is not None:
                char_row = ctx.conn.execute(
                    "SELECT id FROM characters WHERE campaign_slug = ? AND slot = ?",
                    (campaign_slug, slot),
                ).fetchone()
                if char_row:
                    from tomb_gm.domain.spell_cast import cast_spell

                    cast_result = cast_spell(
                        ctx.conn,
                        log_event,
                        content_root=ctx.config.content_root,
                        campaign_slug=campaign_slug,
                        character_id=char_row["id"],
                        spell_id=spell_id,
                        session_id=session_id,
                    )
                    mechanical.append({**cast_result, "action": "spell_cast", "slot": slot})
                    continue
            mechanical.append(
                {
                    "ok": True,
                    "action": "spell_cast_hint",
                    "spell_id": spell_id,
                    "message": "Name a known spell (e.g. cast ember-touch) or use combat cast",
                    "slot": slot,
                }
            )
            continue

        if STABILIZE_RE.search(lower):
            mechanical.append(
                {
                    "ok": True,
                    "action": "stabilize_hint",
                    "message": "Use combat stabilize --character <id> --campaign <slug>",
                    "slot": slot,
                }
            )
            continue

        travel_intent = _intent_travel(text, lower)
        if travel_intent == "travel" or travel_intent == "travel_hint":
            dest = _find_address(text, content)
            if travel_intent == "travel_hint" and not dest:
                world = WorldService(content)
                exits = world.legal_exits(address) or []
                if exits:
                    dest = exits[0]
            if not dest and travel_intent == "travel":
                query = _extract_travel_destination(text)
                resolved = resolve_surface_address(content, query, from_address=address)
                if resolved.get("ok"):
                    dest = resolved["address"]
                else:
                    err = resolved.get("error")
                    beat_err = "NO_DESTINATION" if err == "UNKNOWN_ADDRESS" else err
                    mechanical.append(
                        {
                            "ok": False,
                            "action": "travel",
                            "error": beat_err,
                            "message": resolved.get("message", ""),
                            "query": resolved.get("query"),
                            "options": resolved.get("options"),
                            "slot": slot,
                        }
                    )
                    continue
            if dest:
                result = _apply_travel(
                    ctx,
                    session_id,
                    address,
                    dest,
                    stamp_json,
                    auto_roll_wilderness=auto_roll_wilderness,
                    seed=beat_seed,
                )
                mechanical.append(result)
                if result.get("wilderness"):
                    mechanical.append({**result["wilderness"], "action": "wilderness"})
                if result.get("ok"):
                    address = dest
                    mode = "surface"
            else:
                mechanical.append(
                    {
                        "ok": False,
                        "action": "travel",
                        "error": "NO_DESTINATION",
                        "message": f"P{slot or '?'}: name an AV-GRID destination (e.g. 33-C).",
                        "slot": slot,
                    }
                )
            continue

        mechanical.append(
            {
                "ok": True,
                "action": "note",
                "summary": f"P{slot or '?'}: {text[:80]}",
                "slot": slot,
                "recorded": True,
            }
        )
        if len(text) > 20 and any(k in lower for k in ("promise", "swear", "remember", "deal", "vow")):
            remember_fact(
                ctx.conn,
                campaign_slug,
                fact=text[:500],
                entities=[f"slot-{slot}"] if slot else [],
                address=address,
                importance=3,
                session_id=session_id,
            )

    party = _party_snapshot(ctx, session_id)
    remember_beat_choices(
        ctx.conn,
        campaign_slug,
        session_id,
        player_lines=lines,
        mechanical=mechanical,
        address=party.get("address"),
    )
    narration_brief, speak_lines = _build_narration(mechanical, party)

    log_event(
        ctx.conn,
        session_id,
        "beat",
        {
            "beat_id": beat_id,
            "lines": [ln["raw"] for ln in lines],
            "mechanical": mechanical,
            "narration_brief": narration_brief,
            "speak_lines": speak_lines,
        },
    )

    prompts: list[str] = []
    if any(m.get("wilderness_roll_pending") for m in mechanical if m.get("ok")):
        prompts.append("Roll wilderness: world travel --roll-wilderness or beat auto_roll_wilderness")
    if any(m.get("wilderness_monster_specs") for m in mechanical if m.get("ok")):
        specs = next(
            m["wilderness_monster_specs"]
            for m in mechanical
            if m.get("wilderness_monster_specs")
        )
        prompts.append(f"Encounter: combat start --monsters {' '.join(specs)} --include-party --campaign {campaign_slug}")
    if any(m.get("encounters") for m in mechanical if m.get("ok")):
        prompts.append("Resolve or skip encounter")
    if not prompts:
        prompts.append("Awaiting further player actions")

    return {
        "ok": True,
        "beat_id": beat_id,
        "mechanical_summary": mechanical,
        "narration_brief": narration_brief,
        "speak_lines": speak_lines,
        "prompts": prompts,
        "state_delta": party,
    }
