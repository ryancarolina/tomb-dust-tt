#!/usr/bin/env python3
"""Validate Tomb Dust weapon, monster, spell, deed, and site JSON content."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEAPONS_PATH = ROOT / "data" / "weapons" / "weapons.json"
SPELLS_PATH = ROOT / "data" / "spells" / "spells.json"
SCHOOLS_PATH = ROOT / "data" / "spells" / "schools.json"
STARTING_SPELLS_PATH = ROOT / "data" / "character" / "starting-spells.json"
DEEDS_PATH = ROOT / "data" / "deeds" / "promotions.json"
LOOT_PATH = ROOT / "data" / "loot" / "tables.json"
ENCOUNTERS_PATH = ROOT / "data" / "encounters" / "wilderness.json"
LEDGER_PATH = ROOT / "data" / "av-grid" / "ledger-examples.json"
SITES_DIR = ROOT / "data" / "sites"
MONSTERS_DIR = ROOT / "data" / "monsters"
SCHEMA_DIR = ROOT / "data" / "schemas"

SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
DICE_RE = re.compile(r"^\d+d\d+(?:\s*[+\-]\s*\d+)?$")
RECHARGE_RE = re.compile(r"^[1-6](?:-[1-6])?$")

WEAPON_CATEGORIES = frozenset({"simple", "martial", "ranged"})
WEAPON_ABILITIES = frozenset({"STR", "AGI"})
WEAPON_PROPERTIES = frozenset({
    "finesse", "light", "thrown", "versatile", "two-hand", "reach",
    "loading", "ranged", "concealable",
})
SPELL_SCHOOLS = frozenset({"pyromancy", "ward", "biomancy", "necromancy", "ether", "divine"})
SPELL_TRADITIONS = frozenset({"arcane", "divine"})
SPELL_CAST_TIMES = frozenset({"action", "bonus action", "reaction"})
SITE_EDGE_TYPES = frozenset({"door", "archway", "stairs", "secret", "hatch", "collapse"})
THREAT_TIERS = frozenset({"hazard", "skirmisher", "elite", "boss"})
SAVE_ABILITIES = frozenset({"STR", "AGI", "STA", "INT", "SPI"})
ATTR_KEYS = ("STR", "AGI", "STA", "INT", "SPI")
EXPECTED_WEAPON_COUNT = 17
EXPECTED_SPELL_COUNT = 41
EXPECTED_SCHOOL_COUNT = 6
EXPECTED_PROMOTION_COUNT = 8


class ContentValidationError(Exception):
    pass


def _err(path: str, message: str) -> None:
    raise ContentValidationError(f"{path}: {message}")


def _check_slug(value: str, path: str, label: str = "id") -> None:
    if not isinstance(value, str) or not SLUG_RE.match(value):
        _err(path, f"invalid {label} slug: {value!r}")


def _check_semver(value: str, path: str) -> None:
    if not isinstance(value, str) or not SEMVER_RE.match(value):
        _err(path, f"invalid rulesVersion: {value!r}")


def _check_dice(value: str, path: str, field: str) -> None:
    if not isinstance(value, str) or not DICE_RE.match(value):
        _err(path, f"invalid {field}: {value!r}")


def _check_int(value, path: str, field: str, minimum: int | None = None, maximum: int | None = None) -> None:
    if not isinstance(value, int):
        _err(path, f"{field} must be integer")
    if minimum is not None and value < minimum:
        _err(path, f"{field} must be >= {minimum}")
    if maximum is not None and value > maximum:
        _err(path, f"{field} must be <= {maximum}")


def _check_ability_modifiers(attrs: dict, path: str) -> None:
    if not isinstance(attrs, dict):
        _err(path, "attributes must be object")
    extra = set(attrs) - set(ATTR_KEYS)
    if extra:
        _err(path, f"unknown attribute keys: {sorted(extra)}")
    for key in ATTR_KEYS:
        if key not in attrs:
            _err(path, f"missing attribute {key}")
        _check_int(attrs[key], path, key, minimum=-5, maximum=10)


def _validate_named_ability(ability: dict, path: str) -> None:
    if not isinstance(ability, dict):
        _err(path, "ability entry must be object")
    for key in ("name", "text"):
        if key not in ability:
            _err(path, f"missing {key}")
        if not isinstance(ability[key], str) or not ability[key].strip():
            _err(path, f"{key} must be non-empty string")
    allowed = {"name", "text", "recharge", "attack", "save"}
    extra = set(ability) - allowed
    if extra:
        _err(path, f"unknown ability fields: {sorted(extra)}")
    if "recharge" in ability and not RECHARGE_RE.match(ability["recharge"]):
        _err(path, f"invalid recharge: {ability['recharge']!r}")
    if "attack" in ability:
        atk = ability["attack"]
        if not isinstance(atk, dict):
            _err(path, "attack must be object")
        if "damage" in atk:
            _check_dice(atk["damage"], path, "attack.damage")
        if "toHit" in atk and not isinstance(atk["toHit"], int):
            _err(path, "attack.toHit must be integer")
    if "save" in ability:
        save = ability["save"]
        if not isinstance(save, dict):
            _err(path, "save must be object")
        if "dc" in save:
            _check_int(save["dc"], path, "save.dc", minimum=1)
        if "ability" in save and save["ability"] not in SAVE_ABILITIES:
            _err(path, f"invalid save ability: {save['ability']!r}")


def _validate_stat_block(block: dict, path: str) -> None:
    if not isinstance(block, dict):
        _err(path, "stat block must be object")
    for key in ("id", "tier", "ac", "hp", "move", "pb", "attributes"):
        if key not in block:
            _err(path, f"missing stat block field {key}")
    _check_slug(block["id"], path, "stat block id")
    if block["tier"] not in THREAT_TIERS:
        _err(path, f"invalid tier: {block['tier']!r}")
    _check_int(block["ac"], path, "ac", minimum=5, maximum=30)
    _check_int(block["hp"], path, "hp", minimum=1)
    _check_int(block["move"], path, "move", minimum=0)
    _check_int(block["pb"], path, "pb", minimum=0, maximum=6)
    _check_ability_modifiers(block["attributes"], path)
    for list_key in ("traits", "actions", "reactions", "legendary"):
        if list_key in block:
            items = block[list_key]
            if not isinstance(items, list):
                _err(path, f"{list_key} must be array")
            for i, item in enumerate(items):
                _validate_named_ability(item, f"{path}/{list_key}[{i}]")


def validate_weapon(weapon: dict, path: str) -> None:
    if not isinstance(weapon, dict):
        _err(path, "weapon must be object")
    for key in ("id", "rulesVersion", "displayName", "category", "damage", "ability", "skillId"):
        if key not in weapon:
            _err(path, f"missing required field {key}")
    _check_slug(weapon["id"], path)
    _check_semver(weapon["rulesVersion"], path)
    if not isinstance(weapon["displayName"], str) or not weapon["displayName"].strip():
        _err(path, "displayName must be non-empty string")
    if weapon["category"] not in WEAPON_CATEGORIES:
        _err(path, f"invalid category: {weapon['category']!r}")
    _check_dice(weapon["damage"], path, "damage")
    if weapon["ability"] not in WEAPON_ABILITIES:
        _err(path, f"invalid ability: {weapon['ability']!r}")
    _check_slug(weapon["skillId"], path, "skillId")
    allowed = {
        "id", "rulesVersion", "displayName", "docPath", "category", "damage",
        "ability", "skillId", "costGp", "properties", "versatileDamage", "rangeFt", "tags",
    }
    extra = set(weapon) - allowed
    if extra:
        _err(path, f"unknown fields: {sorted(extra)}")
    if "costGp" in weapon:
        if not isinstance(weapon["costGp"], (int, float)) or weapon["costGp"] < 0:
            _err(path, "costGp must be number >= 0")
    if "properties" in weapon:
        props = weapon["properties"]
        if not isinstance(props, list):
            _err(path, "properties must be array")
        for p in props:
            if p not in WEAPON_PROPERTIES:
                _err(path, f"invalid property: {p!r}")
    if "versatileDamage" in weapon:
        _check_dice(weapon["versatileDamage"], path, "versatileDamage")
    if "rangeFt" in weapon:
        rng = weapon["rangeFt"]
        if not isinstance(rng, dict):
            _err(path, "rangeFt must be object")
        for rk in ("normal", "long"):
            if rk not in rng:
                _err(path, f"rangeFt missing {rk}")
            _check_int(rng[rk], path, f"rangeFt.{rk}", minimum=0)


def validate_monster(monster: dict, path: str) -> None:
    if not isinstance(monster, dict):
        _err(path, "monster must be object")
    for key in ("id", "rulesVersion", "displayName", "statBlocks"):
        if key not in monster:
            _err(path, f"missing required field {key}")
    _check_slug(monster["id"], path)
    _check_semver(monster["rulesVersion"], path)
    if not isinstance(monster["displayName"], str) or not monster["displayName"].strip():
        _err(path, "displayName must be non-empty string")
    blocks = monster["statBlocks"]
    if not isinstance(blocks, list) or not blocks:
        _err(path, "statBlocks must be non-empty array")
    for i, block in enumerate(blocks):
        _validate_stat_block(block, f"{path}/statBlocks[{i}]")


def _load_array_or_wrapper(path: Path, key: str | None = None) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if key and isinstance(data, dict) and isinstance(data.get(key), list):
        return data[key]
    label = key or "array"
    raise ContentValidationError(f"{path}: root must be a JSON array or object with {label!r}")


def validate_spell(spell: dict, path: str) -> None:
    if not isinstance(spell, dict):
        _err(path, "spell must be object")
    for key in ("id", "rulesVersion", "displayName", "school", "tier", "mpCost", "castingTime", "range", "effectType"):
        if key not in spell:
            _err(path, f"missing required field {key}")
    _check_slug(spell["id"], path)
    _check_semver(spell["rulesVersion"], path)
    if spell["school"] not in SPELL_SCHOOLS:
        _err(path, f"invalid school: {spell['school']!r}")
    if "tradition" in spell and spell["tradition"] not in SPELL_TRADITIONS:
        _err(path, f"invalid tradition: {spell['tradition']!r}")
    _check_int(spell["tier"], path, "tier", minimum=1, maximum=6)
    _check_int(spell["mpCost"], path, "mpCost", minimum=0)
    if spell["castingTime"] not in SPELL_CAST_TIMES:
        _err(path, f"invalid castingTime: {spell['castingTime']!r}")
    if not any(k in spell for k in ("attack", "save", "effect", "heal", "summon")):
        _err(path, "spell must include attack, save, heal, summon, or effect")
    if "attack" in spell:
        atk = spell["attack"]
        if not isinstance(atk, dict):
            _err(path, "attack must be object")
        if "damage" in atk:
            _check_dice(atk["damage"], path, "attack.damage")
    if "effectType" in spell and spell["effectType"] not in (
        "attack", "save", "heal", "buff", "utility", "summon", "counter", "terrain",
    ):
        _err(path, f"invalid effectType: {spell['effectType']!r}")
    if "save" in spell:
        save = spell["save"]
        if not isinstance(save, dict):
            _err(path, "save must be object")
        if "dc" in save:
            _err(path, "save.dc is obsolete; use caster spell save DC")
        if "ability" not in save:
            _err(path, "save.ability is required")
        elif save["ability"] not in SAVE_ABILITIES:
            _err(path, f"invalid save ability: {save['ability']!r}")
    if spell.get("heal"):
        heal = spell["heal"]
        if not isinstance(heal, dict):
            _err(path, "heal must be object")
        if "dice" in heal:
            _check_dice(heal["dice"], path, "heal.dice")


def validate_schools_file(path: Path | None = None) -> list[str]:
    path = path or SCHOOLS_PATH
    errors: list[str] = []
    try:
        schools = _load_array_or_wrapper(path)
    except (OSError, json.JSONDecodeError, ContentValidationError) as exc:
        return [str(exc)]
    if len(schools) != EXPECTED_SCHOOL_COUNT:
        errors.append(f"{path}: expected {EXPECTED_SCHOOL_COUNT} schools, got {len(schools)}")
    seen: set[str] = set()
    for i, school in enumerate(schools):
        item_path = f"{path}[{i}]"
        if not isinstance(school, dict):
            errors.append(f"{item_path}: school must be object")
            continue
        sid = school.get("id")
        if sid not in SPELL_SCHOOLS:
            errors.append(f"{item_path}: invalid school id {sid!r}")
        if sid in seen:
            errors.append(f"{item_path}: duplicate id {sid!r}")
        seen.add(sid)
    return errors


def validate_spells_file(path: Path | None = None) -> list[str]:
    path = path or SPELLS_PATH
    errors: list[str] = []
    try:
        spells = _load_array_or_wrapper(path)
    except (OSError, json.JSONDecodeError, ContentValidationError) as exc:
        return [str(exc)]
    if len(spells) != EXPECTED_SPELL_COUNT:
        errors.append(f"{path}: expected {EXPECTED_SPELL_COUNT} spells, got {len(spells)}")
    seen: set[str] = set()
    for i, spell in enumerate(spells):
        item_path = f"{path}[{i}]"
        try:
            validate_spell(spell, item_path)
            sid = spell["id"]
            if sid in seen:
                errors.append(f"{item_path}: duplicate id {sid!r}")
            seen.add(sid)
        except ContentValidationError as exc:
            errors.append(str(exc))
    return errors


def validate_promotion(promo: dict, path: str) -> None:
    if not isinstance(promo, dict):
        _err(path, "promotion must be object")
    for key in ("id", "fromTier", "toClassId", "toTier", "counters"):
        if key not in promo:
            _err(path, f"missing required field {key}")
    _check_slug(promo["id"], path)
    _check_int(promo["fromTier"], path, "fromTier", minimum=1, maximum=5)
    _check_int(promo["toTier"], path, "toTier", minimum=2, maximum=6)
    _check_slug(promo["toClassId"], path, "toClassId")
    if "fromClassId" in promo:
        _check_slug(promo["fromClassId"], path, "fromClassId")
    counters = promo["counters"]
    if not isinstance(counters, list) or not counters:
        _err(path, "counters must be non-empty array")
    for i, counter in enumerate(counters):
        cp = f"{path}/counters[{i}]"
        if not isinstance(counter, dict) or "type" not in counter:
            _err(cp, "counter must be object with type")
        if counter["type"] == "flag" and "name" not in counter:
            _err(cp, "flag counter requires name")


def validate_deeds_file(path: Path | None = None) -> list[str]:
    path = path or DEEDS_PATH
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: root must be object"]
    _check_semver(data.get("rulesVersion", ""), path)
    promotions = data.get("promotions")
    if not isinstance(promotions, list):
        return [f"{path}: promotions must be array"]
    if len(promotions) != EXPECTED_PROMOTION_COUNT:
        errors.append(f"{path}: expected {EXPECTED_PROMOTION_COUNT} promotions, got {len(promotions)}")
    seen: set[str] = set()
    for i, promo in enumerate(promotions):
        item_path = f"{path}/promotions[{i}]"
        try:
            validate_promotion(promo, item_path)
            pid = promo["id"]
            if pid in seen:
                errors.append(f"{item_path}: duplicate id {pid!r}")
            seen.add(pid)
        except ContentValidationError as exc:
            errors.append(str(exc))
    return errors


def validate_site(site: dict, path: str) -> None:
    if not isinstance(site, dict):
        _err(path, "site must be object")
    for key in ("id", "rulesVersion", "displayName", "primaryAddress", "nodes", "edges"):
        if key not in site:
            _err(path, f"missing required field {key}")
    _check_slug(site["id"], path)
    _check_semver(site["rulesVersion"], path)
    if "dangerRating" in site and site["dangerRating"] not in THREAT_TIERS:
        _err(path, f"invalid dangerRating: {site['dangerRating']!r}")
    nodes = site["nodes"]
    if not isinstance(nodes, list) or len(nodes) < 5:
        _err(path, "nodes must be array with at least 5 rooms")
    node_ids: set[str] = set()
    for i, node in enumerate(nodes):
        np = f"{path}/nodes[{i}]"
        if not isinstance(node, dict):
            _err(np, "node must be object")
        for nk in ("id", "address"):
            if nk not in node:
                _err(np, f"missing {nk}")
        _check_slug(node["id"], np)
        node_ids.add(node["id"])
    edges = site["edges"]
    if not isinstance(edges, list):
        _err(path, "edges must be array")
    for i, edge in enumerate(edges):
        ep = f"{path}/edges[{i}]"
        if not isinstance(edge, dict):
            _err(ep, "edge must be object")
        for ek in ("from", "to", "type"):
            if ek not in edge:
                _err(ep, f"missing {ek}")
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            _err(ep, "edge references unknown node id")
        if edge["type"] not in SITE_EDGE_TYPES:
            _err(ep, f"invalid edge type: {edge['type']!r}")


def validate_encounters_file(path: Path | None = None) -> list[str]:
    path = path or ENCOUNTERS_PATH
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: root must be object"]
    _check_semver(data.get("rulesVersion", ""), str(path))
    biomes = data.get("biomes")
    if not isinstance(biomes, dict):
        return [f"{path}: biomes must be object"]
    for code in ("HL", "WM", "SF"):
        if code not in biomes:
            errors.append(f"{path}: missing biome {code!r}")
    return errors


def validate_ledger_file(path: Path | None = None) -> list[str]:
    path = path or LEDGER_PATH
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: root must be object"]
    ledgers = data.get("ledgers")
    if not isinstance(ledgers, list) or len(ledgers) < 3:
        errors.append(f"{path}: expected at least 3 ledger entries")
    for i, entry in enumerate(ledgers or []):
        ep = f"{path}/ledgers[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{ep}: must be object")
            continue
        for key in ("id", "addressId", "displayName", "stamp"):
            if key not in entry:
                errors.append(f"{ep}: missing {key}")
    return errors


def validate_loot_file(path: Path | None = None) -> list[str]:
    path = path or LOOT_PATH
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: root must be object"]
    _check_semver(data.get("rulesVersion", ""), str(path))
    tables = data.get("tables")
    if not isinstance(tables, dict):
        return [f"{path}: tables must be object"]
    for tier in ("hazard", "skirmisher", "elite", "boss"):
        if tier not in tables:
            errors.append(f"{path}: missing table {tier!r}")
    for tier, table in tables.items():
        tp = f"{path}/tables/{tier}"
        if tier not in THREAT_TIERS:
            errors.append(f"{tp}: unknown tier {tier!r}")
        if not isinstance(table, dict):
            errors.append(f"{tp}: must be object")
            continue
        currency = table.get("currencyGp")
        if not isinstance(currency, dict):
            errors.append(f"{tp}: currencyGp must be object")
        else:
            for key in ("min", "max"):
                if key not in currency:
                    errors.append(f"{tp}: currencyGp missing {key}")
            if "min" in currency and "max" in currency and currency["min"] > currency["max"]:
                errors.append(f"{tp}: currencyGp min > max")
        items = table.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"{tp}: items must be non-empty array")
        elif isinstance(items, list):
            for i, item in enumerate(items):
                ip = f"{tp}/items[{i}]"
                if not isinstance(item, dict):
                    errors.append(f"{ip}: must be object")
                    continue
                if "id" not in item or "weight" not in item:
                    errors.append(f"{ip}: missing id or weight")
                else:
                    _check_slug(item["id"], ip)
                    _check_int(item["weight"], ip, "weight", minimum=1)
    return errors


def validate_sites_dir(directory: Path | None = None) -> list[str]:
    directory = directory or SITES_DIR
    errors: list[str] = []
    if not directory.is_dir():
        return [f"{directory}: not a directory"]
    files = sorted(directory.glob("*.json"))
    if len(files) < 1:
        errors.append(f"{directory}: expected at least 1 site JSON file")
    for file_path in files:
        try:
            with file_path.open(encoding="utf-8") as f:
                site = json.load(f)
            validate_site(site, str(file_path))
            if site.get("id") != file_path.stem:
                errors.append(
                    f"{file_path}: id {site.get('id')!r} does not match filename stem {file_path.stem!r}"
                )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{file_path}: {exc}")
        except ContentValidationError as exc:
            errors.append(str(exc))
    return errors


def _load_weapons(path: Path) -> list[dict]:
    return _load_array_or_wrapper(path, "weapons")


def validate_weapons_file(path: Path | None = None) -> list[str]:
    path = path or WEAPONS_PATH
    errors: list[str] = []
    try:
        weapons = _load_weapons(path)
    except (OSError, json.JSONDecodeError, ContentValidationError) as exc:
        return [str(exc)]
    if len(weapons) != EXPECTED_WEAPON_COUNT:
        errors.append(f"{path}: expected {EXPECTED_WEAPON_COUNT} weapons, got {len(weapons)}")
    seen: set[str] = set()
    for i, weapon in enumerate(weapons):
        item_path = f"{path}[{i}]"
        try:
            validate_weapon(weapon, item_path)
            wid = weapon["id"]
            if wid in seen:
                errors.append(f"{item_path}: duplicate id {wid!r}")
            seen.add(wid)
        except ContentValidationError as exc:
            errors.append(str(exc))
    return errors


def validate_monsters_dir(directory: Path | None = None) -> list[str]:
    directory = directory or MONSTERS_DIR
    errors: list[str] = []
    if not directory.is_dir():
        return [f"{directory}: not a directory"]
    files = sorted(directory.glob("*.json"))
    if len(files) < 3:
        errors.append(f"{directory}: expected at least 3 monster JSON files, got {len(files)}")
    for file_path in files:
        try:
            with file_path.open(encoding="utf-8") as f:
                monster = json.load(f)
            validate_monster(monster, str(file_path))
            if monster.get("id") != file_path.stem:
                errors.append(
                    f"{file_path}: id {monster.get('id')!r} does not match filename stem {file_path.stem!r}"
                )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{file_path}: {exc}")
        except ContentValidationError as exc:
            errors.append(str(exc))
    return errors


def _try_jsonschema(weapons: list[dict]) -> list[str]:
    """Optional full schema validation via check-jsonschema when installed."""
    errors: list[str] = []
    try:
        subprocess.run(
            ["check-jsonschema", "--version"],
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    weapon_schema = SCHEMA_DIR / "weapon.schema.json"
    monster_schema = SCHEMA_DIR / "monster.schema.json"

    for i, weapon in enumerate(weapons):
        payload = json.dumps(weapon)
        result = subprocess.run(
            ["check-jsonschema", "--schemafile", str(weapon_schema), "--instance-document", payload],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(
                f"jsonschema weapon[{i}] {weapon.get('id')}: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

    for file_path in sorted(MONSTERS_DIR.glob("*.json")):
        result = subprocess.run(
            ["check-jsonschema", "--schemafile", str(monster_schema), str(file_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"jsonschema {file_path.name}: {result.stderr.strip() or result.stdout.strip()}")
    return errors


def validate_loot_catalog_refs(path: Path | None = None) -> list[str]:
    path = path or LOOT_PATH
    errors: list[str] = []
    migration_path = ROOT / "data" / "loot" / "lootIdMigration.json"
    migrations: dict[str, str] = {}
    if migration_path.is_file():
        migrations = json.loads(migration_path.read_text(encoding="utf-8")).get("migrations") or {}

    def _load_items() -> set[str]:
        ids: set[str] = set()
        for rel in ("weapons/weapons.json", "armor/armor.json", "gear/gear.json"):
            p = ROOT / "data" / rel
            if p.is_file():
                for row in json.loads(p.read_text(encoding="utf-8")):
                    if isinstance(row, dict) and "id" in row:
                        ids.add(str(row["id"]))
        return ids

    catalog = _load_items()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: {exc}"]

    for tier, table in (data.get("tables") or {}).items():
        for i, item in enumerate(table.get("items") or []):
            raw_id = str(item.get("id", ""))
            resolved = migrations.get(raw_id, raw_id)
            if resolved not in catalog and raw_id not in catalog:
                errors.append(
                    f"{path}/tables/{tier}/items[{i}]: itemId {raw_id!r} "
                    f"(resolved {resolved!r}) not in catalog or migration target"
                )
    return errors


def validate_starting_kit_item_refs() -> list[str]:
    kits_path = ROOT / "data" / "character" / "starting-kits.json"
    errors: list[str] = []
    if not kits_path.is_file():
        return errors
    data = json.loads(kits_path.read_text(encoding="utf-8"))
    catalog: set[str] = set()
    for rel in ("weapons/weapons.json", "armor/armor.json", "gear/gear.json"):
        p = ROOT / "data" / rel
        if p.is_file():
            for row in json.loads(p.read_text(encoding="utf-8")):
                if isinstance(row, dict) and "id" in row:
                    catalog.add(str(row["id"]))
    catalog.add("rations")
    for class_id, kit in (data.get("kits") or {}).items():
        for i, item in enumerate(kit.get("items") or []):
            item_id = str(item.get("itemId", ""))
            if item_id.startswith("rations-"):
                continue
            if item_id not in catalog:
                errors.append(f"{kits_path}: kits/{class_id}/items[{i}] unknown itemId {item_id!r}")
    return errors


def main() -> int:
    weapon_errors = validate_weapons_file()
    monster_errors = validate_monsters_dir()
    spell_errors = validate_spells_file()
    school_errors = validate_schools_file()
    deed_errors = validate_deeds_file()
    site_errors = validate_sites_dir()
    loot_errors = validate_loot_file()
    loot_catalog_errors = validate_loot_catalog_refs()
    kit_errors = validate_starting_kit_item_refs()
    encounter_errors = validate_encounters_file()
    ledger_errors = validate_ledger_file()
    errors = (
        weapon_errors + monster_errors + spell_errors + school_errors + deed_errors
        + site_errors + loot_errors + loot_catalog_errors + kit_errors
        + encounter_errors + ledger_errors
    )

    if not errors:
        try:
            weapons = _load_weapons(WEAPONS_PATH)
        except ContentValidationError:
            weapons = []
        errors.extend(_try_jsonschema(weapons))

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        print(f"validate_content: {len(errors)} error(s)", file=sys.stderr)
        return 1

    monster_count = len(list(MONSTERS_DIR.glob("*.json")))
    site_count = len(list(SITES_DIR.glob("*.json")))
    print(
        f"validate_content: OK — {EXPECTED_WEAPON_COUNT} weapons, {monster_count} monsters, "
        f"{EXPECTED_SPELL_COUNT} spells, {EXPECTED_PROMOTION_COUNT} promotions, {site_count} sites, "
        f"loot + encounters + ledger OK"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
