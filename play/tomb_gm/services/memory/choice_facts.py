"""Format player choice facts for campaign memory."""

from __future__ import annotations

from typing import Any

# Actions that resolve state or commitments — worth remembering.
_REMEMBER_ACTIONS = frozenset(
    {
        "travel",
        "site_enter",
        "site_move",
        "search",
        "combat_start",
        "wilderness",
        "spell_cast",
        "stabilize",
        "note",
        "loot_granted",
    }
)

_SKIP_ACTIONS = frozenset(
    {
        "look",
        "spell_cast_hint",
        "stabilize_hint",
    }
)


def mechanical_impact_fact(
    *,
    player_action: str,
    mechanical: dict[str, Any],
    address: str | None = None,
) -> str | None:
    """Build a memory fact from one successful beat mechanical result."""
    if not mechanical.get("ok"):
        return None
    action = mechanical.get("action")
    if action in _SKIP_ACTIONS or action not in _REMEMBER_ACTIONS:
        return None

    where = f" at {address}" if address else ""
    action_text = player_action.strip() or mechanical.get("summary", "")

    if action == "travel":
        cell = mechanical.get("cell") or {}
        name = cell.get("displayName") or mechanical.get("to", "?")
        dest = mechanical.get("to", "?")
        impact = f"Party location is now {dest} ({name})."
        wilderness = mechanical.get("wilderness")
        if wilderness:
            impact += f" Wilderness: {wilderness.get('result', 'travel hazard resolved')}."
        return f"Player chose to travel{where}: \"{action_text}\". {impact}"

    if action == "site_enter":
        site = mechanical.get("site_id", "site")
        node = (mechanical.get("node") or {}).get("displayName", "entry")
        return (
            f"Player chose to enter {site}{where}: \"{action_text}\". "
            f"Impact: party is now inside the site at {node}."
        )

    if action == "site_move":
        node = (mechanical.get("node") or {}).get("displayName", mechanical.get("to", "?"))
        hazard = mechanical.get("hazard")
        impact = f"Party moved to {node} within the site."
        if hazard:
            impact += f" Hazard: {hazard}."
        return f"Player chose site movement{where}: \"{action_text}\". Impact: {impact}"

    if action == "search" or action == "site_search":
        found = mechanical.get("found") or mechanical.get("success")
        loot = mechanical.get("loot")
        granted = mechanical.get("loot_granted") or {}
        impact = "Search found something useful." if found else "Search yielded nothing."
        if loot:
            items = [g.get("itemId") for g in (loot.get("grants") or []) if g.get("itemId")]
            gp = int(loot.get("gp", 0))
            if items or gp:
                impact += f" Loot rolled: {items or 'currency'} +{gp} gp."
        if granted.get("ok"):
            gitems = [g.get("itemId") for g in (granted.get("grants") or [])]
            impact += f" Granted to {granted.get('character_id', 'delver')}: {gitems or 'currency'}."
        return f"Player chose to search{where}: \"{action_text}\". Impact: {impact}"

    if action == "loot_granted":
        gitems = [g.get("itemId") for g in (mechanical.get("grants") or [])]
        gp = int(mechanical.get("gp", 0))
        return (
            f"Mechanical loot grant{where}: {gitems or 'items'} +{gp} gp "
            f"to {mechanical.get('character_id', 'active delver')}."
        )

    if action == "combat_start":
        monsters = mechanical.get("monsters") or mechanical.get("monster_specs") or []
        return (
            f"Player chose to fight{where}: \"{action_text}\". "
            f"Impact: combat started against {monsters or 'hostiles'}."
        )

    if action == "wilderness":
        return (
            f"Wilderness travel resolved{where} after \"{action_text}\". "
            f"Impact: {mechanical.get('result', 'encounter or hazard on the road')}."
        )

    if action == "spell_cast":
        spell = mechanical.get("displayName") or mechanical.get("spell_id", "magic")
        return f"Player cast {spell}{where}: \"{action_text}\"."

    if action == "stabilize":
        target = mechanical.get("character_id") or "an ally"
        return f"Player stabilized {target}{where}: \"{action_text}\"."

    summary = mechanical.get("summary") or action_text
    return f"Player action{where}: \"{summary}\"."


def tool_impact_fact(tool_name: str, args: dict[str, Any], result: dict[str, Any]) -> str | None:
    """Build a memory fact from a non-beat tool call that changed game state."""
    if not result.get("ok"):
        return None
    if tool_name == "process_beat":
        return None  # beat.py handles beat memory

    if tool_name == "world_travel":
        cell = result.get("cell") or {}
        name = cell.get("displayName") or result.get("to", "?")
        return (
            f"Player traveled from {result.get('from', '?')} to {result.get('to', '?')} ({name}). "
            f"Impact: party location updated."
        )

    if tool_name == "site_enter":
        node = (result.get("node") or {}).get("displayName", "entry")
        return (
            f"Player entered site {result.get('site_id', 'site')} at {node}. "
            f"Impact: party is now in site mode."
        )

    if tool_name == "site_move":
        node = (result.get("node") or {}).get("displayName", result.get("to", "?"))
        return f"Player moved within site to {node}."

    if tool_name == "start_combat":
        return f"Player started combat. Impact: {result.get('monsters') or result.get('message', 'fight joined')}."

    if tool_name == "combat_attack":
        return (
            f"Combat attack: {result.get('attacker', '?')} vs {result.get('target', '?')} — "
            f"{result.get('summary') or result.get('outcome', 'strike resolved')}."
        )

    if tool_name == "set_phase":
        return f"Delve phase changed to {result.get('phase') or args.get('phase', '?')}."

    if tool_name == "enter_dungeon":
        room = result.get("room_id") or result.get("room", "?")
        return f"Player entered dungeon at room {room}."

    if tool_name == "move_room":
        return f"Player moved to dungeon room {result.get('room_id') or result.get('to', '?')}."

    if tool_name == "interact_feature":
        feature = args.get("feature_id") or result.get("feature_id", "feature")
        return f"Player interacted with {feature}: {result.get('summary') or result.get('message', 'action resolved')}."

    if tool_name == "cast_spell":
        return f"Player cast {args.get('spell_id') or result.get('spell_id', 'spell')}."

    if tool_name == "fortune_spend":
        return f"Player spent {args.get('amount', 1)} Fortune point(s)."

    if tool_name == "grant_loot":
        granted = result.get("granted") or result
        gitems = [g.get("itemId") for g in (granted.get("grants") or [])]
        gp = int(granted.get("gp", 0))
        return f"GM granted loot: {gitems or 'items'} +{gp} gp to {granted.get('character_id', 'delver')}."

    if tool_name == "buy_item":
        return (
            f"Player bought {result.get('item') or args.get('item_id', 'item')} "
            f"×{result.get('quantity', 1)} for {result.get('cost_gp', '?')} gp."
        )

    if tool_name == "sell_item":
        return (
            f"Player sold {result.get('itemId', 'item')} instance "
            f"for {result.get('net_gp', result.get('gross_gp', '?'))} gp (after taxes)."
        )

    if tool_name in ("equip_item", "unequip_item"):
        return f"Player {tool_name.replace('_', ' ')}: {args.get('instance_id', '?')} → {result.get('slot', 'pack')}."

    if tool_name == "skill_check":
        skill = result.get("skill_id") or args.get("skill_id", "skill")
        outcome = "success" if result.get("success") else "failure"
        margin = result.get("margin")
        margin_text = f" (margin {margin})" if margin is not None else ""
        return f"Social {skill} check: {outcome}{margin_text} — total {result.get('total')} vs DC {result.get('dc')}."

    if tool_name == "negotiate_quest_advance":
        gp = result.get("advance_gp", 0)
        quest = args.get("quest_id", "quest")
        skill = args.get("skill_id", "skill")
        return f"Negotiated {quest} advance via {skill}: {gp} gp granted (margin {result.get('margin')})."

    if tool_name == "grant_quest_advance":
        return (
            f"Quest advance granted: {result.get('granted_gp', args.get('gold_gp', 0))} gp "
            f"for {args.get('quest_id', 'quest')} (total advancePaidGp {result.get('advancePaidGp')})."
        )

    if tool_name == "accept_quest":
        return f"Player accepted quest {args.get('quest_id', result.get('quest_id', 'quest'))}."

    if tool_name == "offer_quest":
        return f"Quest offered: {args.get('quest_id', result.get('quest_id', 'quest'))}."

    return None


def remember_beat_choices(
    conn,
    campaign_slug: str,
    session_id: str,
    *,
    player_lines: list[dict[str, Any]],
    mechanical: list[dict[str, Any]],
    address: str | None,
) -> list[int]:
    """Write successful beat mechanical results to campaign memory."""
    from tomb_gm.services.memory import remember_fact

    combined_action = " | ".join(
        str(line.get("raw") or line.get("text") or "") for line in player_lines
    )
    memory_ids: list[int] = []
    for mech in mechanical:
        fact = mechanical_impact_fact(
            player_action=combined_action,
            mechanical=mech,
            address=address,
        )
        if not fact:
            continue
        entities = [
            f"slot-{line['slot']}"
            for line in player_lines
            if line.get("slot") is not None
        ]
        memory_ids.append(
            remember_fact(
                conn,
                campaign_slug,
                fact,
                entities=entities or None,
                address=address,
                importance=3,
                session_id=session_id,
            )
        )
    return memory_ids
