"""Build LLM context from game state and campaign memory."""

from __future__ import annotations

from typing import Any


def build_state_context(
    status: dict,
    recap: dict | None = None,
    check: dict | None = None,
    suggest: dict | None = None,
    exploration: dict | None = None,
    inventory_summary: str | None = None,
) -> str:
    """Turn status + recap + check + suggest + exploration into authoritative context for the LLM.

    This is the SINGLE SOURCE OF TRUTH for the game state. The LLM must not
    contradict anything here. Chat history is NOT the save game.
    """
    parts: list[str] = []

    parts.append("## AUTHORITATIVE GAME STATE (from database — do NOT contradict)")

    party = status.get("party")
    if party:
        loc = party.get("display_address") or party.get("address", "?")
        parts.append(f"Location: {loc} (mode: {party.get('mode', 'surface')})")
        if party.get("grid_address"):
            parts.append(f"Grid: {party['grid_address']}")
        parts.append(f"Phase: {party.get('phase', '?')}")
        if party.get("site_id"):
            parts.append(f"Site: {party['site_id']} node: {party.get('site_node_id', '?')}")
        clocks = party.get("clocks")
        if clocks:
            parts.append(f"Clocks: {clocks}")

    roster = status.get("roster", [])
    if roster:
        roster_lines = []
        for r in roster:
            line = (
                f"  Slot {r['slot']}: {r['display_name']} (id: {r['character_id']}) "
                f"HP {r['hp']} MP {r.get('mp', '?')} Fortune {r.get('fortune', '?')}"
            )
            spell_lines = r.get("spell_lines") or []
            if spell_lines:
                line += f" | Spells: {'; '.join(spell_lines)}"
            elif r.get("known_spells"):
                line += f" | Spells: {', '.join(r['known_spells'])}"
            if r.get("concentration"):
                line += f" | Concentrating: {r['concentration'].get('displayName', '?')}"
            roster_lines.append(line)
        parts.append("Party:\n" + "\n".join(roster_lines))

    if inventory_summary:
        parts.append(f"\n## Inventory\n{inventory_summary}")

    combat = status.get("combat")
    if combat:
        parts.append(f"COMBAT ACTIVE — Round {combat['round']}, Turn index {combat['turn_index']}")
        turn_id = combat.get("turn_id")
        if turn_id:
            parts.append(f"Active combatant id: {turn_id} (kind: {combat.get('turn_kind', '?')})")
        parts.append(f"Initiative this round: {combat['initiative']}")
        combatants = combat.get("combatants") or []
        if combatants:
            parts.append("Combatants (use these ids for combat_action targets):")
            for c in combatants:
                parts.append(
                    f"  - {c.get('id')}: {c.get('displayName', '?')} "
                    f"({c.get('kind', '?')}) HP {c.get('hp', '?')}/{c.get('maxHp', '?')} AC {c.get('ac', '?')}"
                )
        parts.append(
            "During combat call combat_action ONLY. Do NOT use process_beat, start_combat, or travel tools."
        )

    awaiting = status.get("awaiting", "SETUP")
    parts.append(f"Awaiting: {awaiting}")
    if awaiting == "COMBAT_TURN" and combat:
        parts.append(f"COMBAT_TURN — waiting for action from: {combat.get('turn_id', '?')}")

    # Exploration context (surroundings, scene position, features)
    if exploration:
        parts.append("\n## Surroundings")
        if exploration.get("scene_info"):
            si = exploration["scene_info"]
            parts.append(f"Scene: {si.get('scene_index', '?')}/{si.get('scene_max', '?')} heading {si.get('heading', '?')}")
        if exploration.get("cell_info"):
            ci = exploration["cell_info"]
            parts.append(f"Terrain: {ci.get('terrain', '?')}, Population: {ci.get('population', '?')}")
            hooks = ci.get("loreHooks", [])
            if hooks:
                parts.append(f"Lore: {'; '.join(hooks)}")
        if exploration.get("discovered_features"):
            parts.append("Nearby features (discovered):")
            for f in exploration["discovered_features"]:
                parts.append(f"  - {f['display_name']} ({f['feature_type']}) [{f.get('state', 'pristine')}] id:{f['id']}")
        if exploration.get("compass"):
            parts.append("Adjacent cells:")
            for direction, info in exploration["compass"].items():
                if direction == "below":
                    for below in info:
                        parts.append(f"  Below: {below['displayName']} ({below['address']})")
                else:
                    visited_tag = "visited" if info.get("visited") else "unvisited"
                    danger_tag = f", {info['dangerRating']}" if info.get("dangerRating") else ""
                    parts.append(f"  {direction}: {info['displayName']} ({info['terrain']}, {info['population']}, {visited_tag}{danger_tag})")
        if exploration.get("dungeon_info"):
            di = exploration["dungeon_info"]
            room = di.get("room", {})
            parts.append(f"\n## Current Room: {room.get('display_name', '?')}")
            parts.append(f"Description: {room.get('description', '')}")
            exits = []
            import json as _json
            try:
                exits = _json.loads(room.get("exits_json", "[]"))
            except Exception:
                pass
            if exits:
                parts.append("Exits:")
                for ex in exits:
                    lock_tag = " [LOCKED]" if ex.get("locked") and ex.get("state") != "unlocked" else ""
                    hidden_tag = " [HIDDEN]" if ex.get("hidden") else ""
                    parts.append(f"  - {ex.get('direction', '?')} → {ex.get('target_room_id', '?')}{lock_tag}{hidden_tag}")
            features = di.get("features", [])
            if features:
                parts.append("Room features (use exact id for interact_feature):")
                for f in features:
                    parts.append(
                        f"  - {f['display_name']} ({f['feature_type']}) "
                        f"[{f.get('state', 'pristine')}] id:{f['id']}"
                    )

    if check and check.get("blocked"):
        parts.append(f"\n## BLOCKED — do not advance fiction")
        parts.append(f"Blockers: {check.get('blockers', [])}")

    if suggest:
        suggested_cmds = suggest.get("commands", [])
        prompts = suggest.get("prompts", [])
        if prompts:
            parts.append(f"\n## Suggested Actions")
            for p in prompts:
                parts.append(f"  - {p}")

    if recap:
        recap_text = recap.get("recap_text", "")
        if recap_text:
            parts.append(f"\n## Campaign Memory\n{recap_text}")

        recent = recap.get("recent_events", [])
        if recent:
            parts.append("\n## Recent Events (from database)")
            for ev in recent[-10:]:
                etype = ev.get("event_type", "?")
                payload = ev.get("payload", {})
                if etype == "roll":
                    parts.append(f"  - Roll: {payload.get('reason','?')} → {payload.get('total','?')} vs DC {payload.get('dc','?')} ({'pass' if payload.get('success') else 'fail'})")
                elif etype == "world_travel":
                    parts.append(f"  - Traveled: {payload.get('from','?')} → {payload.get('to','?')}")
                elif etype == "site_enter":
                    parts.append(f"  - Entered site: {payload.get('site_id','?')}")
                elif etype == "beat":
                    brief = payload.get("narration_brief", str(payload)[:60])
                    parts.append(f"  - Beat: {brief[:80]}")
                else:
                    summary = str(payload)[:80]
                    parts.append(f"  - {etype}: {summary}")

    return "\n".join(parts)


def build_messages(
    system_prompt: str,
    state_context: str,
    history: list[dict[str, str]],
    player_input: str,
) -> list[dict[str, Any]]:
    """Assemble the messages array for the LLM."""
    combined_system = f"{system_prompt}\n\n## Current Game State\n{state_context}"
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": combined_system},
    ]

    for msg in history[-20:]:
        messages.append(msg)

    messages.append({"role": "user", "content": player_input})
    return messages
