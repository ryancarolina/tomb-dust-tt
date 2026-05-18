#!/usr/bin/env python3
"""Split Tomb Dust Game System.md into systems/ (one-off migration)."""
from __future__ import annotations

import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Tomb Dust Game System.md"
ARCHIVE = ROOT / "assets" / "tomb-dust-source-archive.md"
SYSTEMS = ROOT / "systems"
ASSETS = ROOT / "assets"


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "untitled"


def normalize(text: str) -> str:
    text = text.replace("\\*", "*")
    text = re.sub(r"pythonCopy", "", text)
    text = re.sub(r"Copy", "", text)
    return text


def slice_lines(lines: list[str], start: int, end: int) -> str:
    """1-based inclusive start/end."""
    return normalize("".join(lines[start - 1 : end]))


def write(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = body.strip()
    if not content.startswith("#"):
        content = f"# {title}\n\n{content}"
    path.write_text(content + "\n", encoding="utf-8")


def parse_bold_entities(lines: list[str], start: int, end: int) -> list[tuple[str, str]]:
    """Split section into entities keyed by **Name** lines."""
    chunk = lines[start - 1 : end]
    entities: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name and current_lines:
            entities.append((current_name, normalize("".join(current_lines))))
        current_name = None
        current_lines = []

    skip_headers = {
        "npcs",
        "gods:",
        "gods",
        "monsters",
        "monsters:",
        "races:",
        "races",
    }

    for line in chunk:
        m = re.match(r"^\*\*([^*]+)\*\*\s*:?\s*$", line.strip())
        if m:
            name = m.group(1).strip()
            if name.lower().rstrip(":") in skip_headers or name.lower() in skip_headers:
                flush()
                continue
            flush()
            current_name = name.rstrip(":")
            current_lines = []
        elif m := re.match(r"^\*\*([^*]+)\*\*\s*:?\s*(.*)$", line.strip()):
            name = m.group(1).strip().rstrip(":")
            rest = m.group(2)
            if name.lower() in skip_headers:
                flush()
                continue
            flush()
            current_name = name
            current_lines = [rest + "\n"] if rest else []
        else:
            if current_name:
                current_lines.append(line)
    flush()
    return entities


def parse_location_entities(lines: list[str], start: int, end: int) -> list[tuple[str, str]]:
    return parse_bold_entities(lines, start, end)


def parse_faction_entities(lines: list[str], start: int, end: int) -> list[tuple[str, str]]:
    chunk = lines[start - 1 : end]
    entities: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name and current_lines:
            entities.append((current_name, normalize("".join(current_lines))))
        current_name = None
        current_lines = []

    section_labels = ("origins:", "goals:", "activities:", "challenges:", "role in aventhar:")

    for line in chunk:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        low = stripped.lower()
        if any(low.startswith(label) for label in section_labels):
            if current_name:
                current_lines.append(line)
            continue
        is_title = (
            stripped[0].isupper()
            and ":" not in stripped
            and not stripped.startswith(("-", "|", "**"))
            and len(stripped) < 80
        )
        if is_title:
            flush()
            current_name = stripped
            current_lines = []
            continue
        if current_name:
            current_lines.append(line)
    flush()
    return entities


def parse_event_entities(lines: list[str], start: int, end: int) -> list[tuple[str, str]]:
    chunk = lines[start - 1 : end]
    entities: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name and current_lines:
            entities.append((current_name, normalize("".join(current_lines))))
        current_name = None
        current_lines = []

    for line in chunk:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and stripped[0].isupper():
            if stripped.endswith("Festival") or stripped.startswith("Dance"):
                flush()
                current_name = stripped
                current_lines = []
                continue
        if current_name:
            current_lines.append(line)
    flush()
    return entities


def extract_image(lines: list[str]) -> bool:
    for line in lines:
        if line.startswith("[image1]:") and "base64," in line:
            b64 = line.split("base64,", 1)[1].rstrip(">")
            ASSETS.mkdir(parents=True, exist_ok=True)
            (ASSETS / "tomb-dust-logo.png").write_bytes(base64.b64decode(b64))
            return True
    return False


def write_readme(folder: Path, title: str, children: list[str]) -> None:
    links = "\n".join(f"- [{Path(c).name}]({Path(c).name})" for c in sorted(children))
    write(folder / "README.md", title, f"## {title}\n\n{links}")


def main() -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    if len(source_text) > 5000 and "# Core Mechanics" in source_text:
        ASSETS.mkdir(parents=True, exist_ok=True)
        ARCHIVE.write_text(source_text, encoding="utf-8")
    raw_lines = source_text.splitlines(keepends=True)
    content_lines = [ln for ln in raw_lines if not ln.startswith("[image1]:")]
    extract_image(raw_lines)
    lines = content_lines

    # --- Mechanics ---
    write(SYSTEMS / "core" / "README.md", "Core", "## Core\n\nAttributes, derived stats, and resolution.")
    write(SYSTEMS / "core" / "attributes.md", "Tomb Dust Attribute System", slice_lines(lines, 37, 45))
    write(
        SYSTEMS / "core" / "derived-stats.md",
        "Attribute Impact on Gameplay",
        slice_lines(lines, 46, 118),
    )
    write(
        SYSTEMS / "core" / "resolution.md",
        "Combat Resolution",
        slice_lines(lines, 48, 92),
    )
    write(SYSTEMS / "combat" / "README.md", "Combat", "## Combat\n\n[calculations.md](calculations.md)")
    write(SYSTEMS / "combat" / "calculations.md", "Combat Calculations", slice_lines(lines, 119, 145))

    write(SYSTEMS / "character" / "README.md", "Character", "## Character\n\nCreation and races.")
    write(
        SYSTEMS / "character" / "creation.md",
        "Creating a Character",
        slice_lines(lines, 31, 36) + "\n\n" + slice_lines(lines, 146, 257),
    )
    write(SYSTEMS / "character" / "races.md", "Playable Races", slice_lines(lines, 146, 213))
    write(SYSTEMS / "character" / "genetic-factors.md", "Genetic Factors", slice_lines(lines, 258, 266))
    write(SYSTEMS / "character" / "life-events.md", "Life Events", slice_lines(lines, 267, 310))

    write(SYSTEMS / "skills" / "README.md", "Skills", "## Skills\n\nSee skill category files.")
    write(SYSTEMS / "skills" / "progression.md", "Skill Progression", slice_lines(lines, 315, 329))
    write(SYSTEMS / "skills" / "skill-checks.md", "Skill Check System", slice_lines(lines, 330, 369))
    write(SYSTEMS / "skills" / "combat-skills.md", "Combat Skills", slice_lines(lines, 370, 619))
    write(SYSTEMS / "skills" / "physical-skills.md", "Physical Skills", slice_lines(lines, 620, 699))
    write(SYSTEMS / "skills" / "social-skills.md", "Social Skills", slice_lines(lines, 700, 791))
    write(SYSTEMS / "skills" / "mental-skills.md", "Mental Skills", slice_lines(lines, 792, 898))
    write(SYSTEMS / "skills" / "subterfuge-skills.md", "Subterfuge Skills", slice_lines(lines, 899, 990))
    write(SYSTEMS / "skills" / "magic-skills.md", "Magic Skills", slice_lines(lines, 991, 1053))

    write(SYSTEMS / "classes" / "README.md", "Classes", "## Classes\n\n[progression.md](progression.md) | [classes.md](classes.md)")
    write(SYSTEMS / "classes" / "progression.md", "Classes and Progression", slice_lines(lines, 1178, 1234))
    write(
        SYSTEMS / "classes" / "classes.md",
        "Class Definitions",
        slice_lines(lines, 1235, 1350),
    )

    write(SYSTEMS / "equipment" / "README.md", "Equipment", "## Equipment\n\nWeapons, armor, gear, economy.")
    write(SYSTEMS / "equipment" / "economy.md", "Starting Gold", slice_lines(lines, 1054, 1083))
    write(SYSTEMS / "equipment" / "weapons.md", "Weapons", slice_lines(lines, 1084, 1110))
    write(SYSTEMS / "equipment" / "armor.md", "Armor and Shields", slice_lines(lines, 1110, 1130))
    write(SYSTEMS / "equipment" / "gear.md", "Adventuring Gear", slice_lines(lines, 1130, 1177))

    write(SYSTEMS / "lore" / "README.md", "Lore", "## Lore\n\n[aventhar-creation.md](aventhar-creation.md)")
    write(
        SYSTEMS / "lore" / "aventhar-creation.md",
        "The Creation of Aventhar",
        slice_lines(lines, 1353, 1367),
    )

    ether_bits = []
    for i, ln in enumerate(lines, 1):
        if re.search(r"\bEther\b", ln, re.I):
            ether_bits.append(f"<!-- source line {i} -->\n{ln}")
    write(
        SYSTEMS / "world" / "ether.md",
        "The Ether",
        "## The Ether\n\nCross-references from the game system document.\n\n" + "".join(ether_bits[:80]),
    )
    write(SYSTEMS / "world" / "README.md", "World", "## World\n\n[ether.md](ether.md)")

    # Characters section entities
    char_end = 1578
    npcs = parse_bold_entities(lines, 1372, 1406)
    deities = parse_bold_entities(lines, 1407, 1426)
    monsters = parse_bold_entities(lines, 1427, 1484)
    races_lore = parse_bold_entities(lines, 1485, char_end)

    for name, body in npcs:
        write(SYSTEMS / "npcs" / f"{slugify(name)}.md", name, body)
    for name, body in deities:
        write(SYSTEMS / "deities" / f"{slugify(name)}.md", name, body)
    for name, body in monsters:
        path = SYSTEMS / "monsters" / f"{slugify(name)}.md"
        if name in ("Etherwraiths", "Shadowkin") and len(body.strip()) < 20:
            body += "\n\n<!-- TODO: stub in source document — expand when rules are written. -->\n"
        write(path, name, body)
    for name, body in races_lore:
        b = body + f"\n\n> **Mechanics:** See [character/races.md](../character/races.md).\n"
        write(SYSTEMS / "races" / f"{slugify(name)}.md", name, b)

    locs = parse_location_entities(lines, 1580, 1686)
    for name, body in locs:
        write(SYSTEMS / "locations" / f"{slugify(name)}.md", name, body)

    factions = parse_faction_entities(lines, 1688, 1722)
    for name, body in factions:
        write(SYSTEMS / "factions" / f"{slugify(name)}.md", name, body)

    events = parse_event_entities(lines, 1724, 1738)
    for name, body in events:
        path = SYSTEMS / "events" / f"{slugify(name)}.md"
        if "Dance with the Dead" in name:
            body += (
                "\n\n<!-- TODO: source duplicates Eclipse Festival text; "
                "replace with unique event description when available. -->\n"
            )
        write(path, name, body)

    # READMEs for entity folders
    for folder, title in [
        ("npcs", "NPCs"),
        ("deities", "Deities"),
        ("monsters", "Monsters"),
        ("races", "Races (Lore)"),
        ("locations", "Locations"),
        ("factions", "Factions"),
        ("events", "Events"),
    ]:
        d = SYSTEMS / folder
        if d.exists():
            children = [f.name for f in d.glob("*.md") if f.name != "README.md"]
            if children:
                write_readme(d, title, children)

    # Root systems index
    top_dirs = sorted(
        p.name for p in SYSTEMS.iterdir() if p.is_dir()
    )
    index_links = "\n".join(f"- [{d}/]({d}/README.md)" for d in top_dirs)
    logo = "![Tomb Dust](../../assets/tomb-dust-logo.png)" if (ASSETS / "tomb-dust-logo.png").exists() else ""
    write(
        SYSTEMS / "README.md",
        "Tomb Dust Game Systems",
        f"{logo}\n\n## Tomb Dust Game Systems\n\nModular documentation split from `Tomb Dust Game System.md`.\n\n### Systems\n\n{index_links}\n\n### Dependency notes\n\n- [character/races.md](character/races.md) — mechanical race adjustments\n- [races/](races/) — lore and world role per race\n- [core/resolution.md](core/resolution.md) + [combat/calculations.md](combat/calculations.md) — combat math\n- [world/ether.md](world/ether.md) — Ether references across the setting",
    )

    # Replace monolith with pointer
    pointer = f"""# Tomb Dust Game System

> **This document has been split into modular files.** See [systems/README.md](systems/README.md) for the full game system.

The original monolithic export is preserved in git history. All rules and lore now live under `systems/` by domain (combat, character, skills, locations, NPCs, monsters, etc.).

![Tomb Dust](assets/tomb-dust-logo.png)
"""
    SOURCE.write_text(pointer, encoding="utf-8")
    print(f"Done. systems/ files: {sum(1 for _ in SYSTEMS.rglob('*.md'))}")


if __name__ == "__main__":
    main()
