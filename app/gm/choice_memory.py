"""Persist character creation choices to campaign memory."""

from __future__ import annotations

from gm.creation import CLASS_INFO, CreationState, RACES


def creation_choice_fact(completed_step: str, state: CreationState) -> str | None:
    """Build a memory fact after a successful creation step advance."""
    name = state.name or "the delver"

    if completed_step == "NAME":
        return (
            f"Character creation: player registered the delver name '{name}' "
            f"at the Delver's Registry in Breley Keep."
        )

    if completed_step == "RACE":
        race_key = state.race.replace("-", " ").title()
        race_info = RACES.get(state.race, {})
        mods = race_info.get("mods") or {}
        mod_text = ", ".join(f"{attr} {val:+d}" for attr, val in mods.items()) or "flexible bonuses"
        return (
            f"Character creation: {name} chose {race_key} lineage ({mod_text}). "
            f"Impact: racial modifiers applied to rolled attributes."
        )

    if completed_step == "ROLL_STATS":
        attrs = state.roll_result.get("final_attributes", {})
        eligible = state.roll_result.get("eligible_classes", [])
        sta = attrs.get("STA", 10)
        hp = 10 + (sta * 5)
        attr_text = ", ".join(f"{k} {v}" for k, v in attrs.items())
        return (
            f"Character creation: attribute roll for {name} — {attr_text}. "
            f"Impact: {hp} HP; eligible Tier-1 classes: {', '.join(eligible)}."
        )

    if completed_step == "CLASS":
        cls = state.chosen_class
        info = CLASS_INFO.get(cls, {})
        return (
            f"Character creation: {name} chose {cls.title()} ({info.get('requirement', 'none')}). "
            f"Impact: {info.get('description', '')} "
            f"Starting kit: {info.get('kit', 'standard gear')}. "
            f"Base gold before life-event roll: {info.get('base_gp', 0)} gp."
        )

    if completed_step == "SKILLS":
        skills = ", ".join(s.title() for s in state.chosen_skills)
        cls = state.chosen_class
        key_skills = ", ".join(CLASS_INFO.get(cls, {}).get("key_skills", []))
        return (
            f"Character creation: {name} selected starting skills {skills} (level 1 each). "
            f"Impact: foundations for skill checks; at least one should match {cls.title()} "
            f"key skills ({key_skills})."
        )

    if completed_step == "SPELL_SCHOOLS":
        schools = ", ".join(state.chosen_schools)
        return (
            f"Character creation: {name} chose spell schools [{schools}]. "
            f"Impact: defines which tier-1 spells they may learn at creation."
        )

    if completed_step == "SPELLS":
        spells = ", ".join(state.chosen_spells)
        return (
            f"Character creation: {name} learned starting spells [{spells}]. "
            f"Impact: these are the only spells on their sheet unless they find scrolls or deeds."
        )

    if completed_step == "EQUIPMENT_GOLD":
        cls = state.chosen_class.title()
        return (
            f"Character creation: {name} accepted the standard {cls} kit and "
            f"{state.starting_gold} gp starting coin."
        )

    if completed_step == "FINALIZE":
        attrs = state.roll_result.get("final_attributes", {})
        sta = attrs.get("STA", 10)
        hp = 10 + (sta * 5)
        int_score = attrs.get("INT", 10)
        base_mp = CLASS_INFO.get(state.chosen_class, {}).get("base_mp", 5)
        mp = base_mp + (int_score * 3)
        skills = ", ".join(state.chosen_skills)
        attr_text = ", ".join(f"{k} {v}" for k, v in attrs.items())
        return (
            f"Character registered: {name}, {state.race.replace('-', ' ')} {state.chosen_class}, "
            f"attributes {attr_text}, skills [{skills}], {hp} HP, {mp} MP, "
            f"{state.starting_gold} gp. Impact: active delver at Breley Keep (32-C)."
        )

    return None
