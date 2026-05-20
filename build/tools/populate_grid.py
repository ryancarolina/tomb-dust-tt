"""
Populate the full AV-GRID with seed data for all 1,560 surface cells.

Usage:
    python build/tools/populate_grid.py              # preview stats
    python build/tools/populate_grid.py --write      # write expanded av-grid.json
    python build/tools/populate_grid.py --validate   # write + validate

Does NOT overwrite hand-authored cells (those already in av-grid.json).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GRID_PATH = REPO_ROOT / "build" / "data" / "av-grid" / "av-grid.json"

ROWS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]  # A-Z
COLS = list(range(1, 61))  # 1-60

# Region assignment priority (checked in order; first match wins)
# More specific regions first, catch-all regions last.
REGION_PRIORITY = [
    {
        "key": "frostspire",
        "colMin": 10, "colMax": 20, "rowMin": "N", "rowMax": "P",
    },
    {
        "key": "skyreach",
        "colMin": 15, "colMax": 22, "rowMin": "G", "rowMax": "K",
    },
    {
        "key": "whispering_marches",
        "colMin": 20, "colMax": 28, "rowMin": "A", "rowMax": "D",
    },
    {
        "key": "heartlands",
        "colMin": 28, "colMax": 36, "rowMin": "B", "rowMax": "F",
    },
    {
        "key": "transition",
        "colMin": 37, "colMax": 44, "rowMin": "A", "rowMax": "D",
    },
    {
        "key": "shadowfen",
        "colMin": 45, "colMax": 52, "rowMin": "A", "rowMax": "D",
    },
    {
        "key": "silversea_coast",
        "colMin": 1, "colMax": 9, "rowMin": "A", "rowMax": "Z",
    },
    {
        "key": "eastern_wastes",
        "colMin": 53, "colMax": 60, "rowMin": "A", "rowMax": "Z",
    },
    {
        "key": "northern_highlands",
        "colMin": 10, "colMax": 52, "rowMin": "L", "rowMax": "Z",
    },
    {
        "key": "central_plains",
        "colMin": 10, "colMax": 52, "rowMin": "E", "rowMax": "K",
    },
]

# Terrain distribution weights per region
TERRAIN_WEIGHTS: dict[str, dict[str, int]] = {
    "silversea_coast": {"coast": 50, "plains": 15, "hills": 10, "settlement": 5, "forest": 10, "marsh": 5, "cliff": 5},
    "frostspire": {"tundra": 50, "mountains": 20, "cliff": 15, "settlement": 3, "lake": 7, "hills": 5},
    "skyreach": {"cliff": 35, "mountains": 30, "hills": 15, "settlement": 3, "forest": 10, "lake": 7},
    "whispering_marches": {"forest": 45, "lake": 10, "marsh": 10, "hills": 10, "settlement": 5, "river": 10, "road": 5, "ruins": 5},
    "heartlands": {"farmland": 35, "road": 10, "hills": 15, "settlement": 10, "plains": 15, "forest": 10, "river": 5},
    "transition": {"forest": 30, "hills": 20, "marsh": 15, "ruins": 10, "plains": 10, "river": 5, "road": 5, "cavern-mouth": 5},
    "shadowfen": {"marsh": 50, "ruins": 20, "lake": 10, "forest": 5, "road": 5, "settlement": 3, "river": 7},
    "eastern_wastes": {"steppe": 40, "desert": 20, "ruins": 15, "hills": 10, "plains": 10, "cliff": 5},
    "northern_highlands": {"hills": 25, "mountains": 20, "cliff": 15, "tundra": 15, "forest": 15, "lake": 5, "settlement": 2, "ruins": 3},
    "central_plains": {"plains": 30, "farmland": 20, "hills": 15, "forest": 15, "river": 5, "road": 5, "settlement": 5, "marsh": 5},
}

# Population weights per region
POP_WEIGHTS: dict[str, dict[str, int]] = {
    "silversea_coast": {"uninhabited": 30, "sparse": 40, "village": 20, "town": 8, "fortress": 2},
    "frostspire": {"uninhabited": 60, "sparse": 25, "village": 10, "fortress": 5},
    "skyreach": {"uninhabited": 55, "sparse": 30, "village": 10, "fortress": 5},
    "whispering_marches": {"uninhabited": 35, "sparse": 35, "village": 20, "town": 8, "fortress": 2},
    "heartlands": {"uninhabited": 10, "sparse": 25, "village": 35, "town": 20, "fortress": 8, "city": 2},
    "transition": {"uninhabited": 55, "sparse": 30, "village": 10, "town": 5},
    "shadowfen": {"uninhabited": 65, "sparse": 25, "village": 8, "town": 2},
    "eastern_wastes": {"uninhabited": 75, "sparse": 20, "village": 5},
    "northern_highlands": {"uninhabited": 60, "sparse": 25, "village": 10, "fortress": 5},
    "central_plains": {"uninhabited": 20, "sparse": 35, "village": 25, "town": 15, "fortress": 5},
}

# Scene count by terrain
SCENE_COUNTS: dict[str, int] = {
    "road": 2, "settlement": 2,
    "farmland": 3, "plains": 3, "coast": 3, "steppe": 3, "desert": 3,
    "forest": 4, "hills": 4, "marsh": 4, "mountains": 4,
    "cliff": 4, "tundra": 4, "ruins": 4, "cavern-mouth": 3,
    "lake": 3, "river": 3,
}

# Danger rating distribution by region
DANGER_WEIGHTS: dict[str, dict[str | None, int]] = {
    "silversea_coast": {None: 40, "hazard": 35, "skirmisher": 20, "elite": 5},
    "frostspire": {None: 10, "hazard": 15, "skirmisher": 30, "elite": 35, "boss": 10},
    "skyreach": {None: 15, "hazard": 20, "skirmisher": 35, "elite": 25, "boss": 5},
    "whispering_marches": {None: 25, "hazard": 30, "skirmisher": 30, "elite": 13, "boss": 2},
    "heartlands": {None: 45, "hazard": 35, "skirmisher": 15, "elite": 5},
    "transition": {None: 15, "hazard": 20, "skirmisher": 35, "elite": 25, "boss": 5},
    "shadowfen": {None: 5, "hazard": 15, "skirmisher": 30, "elite": 35, "boss": 15},
    "eastern_wastes": {None: 5, "hazard": 10, "skirmisher": 25, "elite": 40, "boss": 20},
    "northern_highlands": {None: 20, "hazard": 25, "skirmisher": 30, "elite": 20, "boss": 5},
    "central_plains": {None: 40, "hazard": 30, "skirmisher": 20, "elite": 8, "boss": 2},
}

# Trade routes as lists of (col, row) waypoints (simplified paths)
TRADE_ROUTES: dict[str, list[tuple[int, str]]] = {
    "kings-road": [(28, "C"), (29, "C"), (30, "C"), (31, "C"), (32, "C"), (33, "C"), (34, "C"), (35, "C"), (36, "C"),
                   (28, "D"), (29, "D"), (30, "D"), (31, "D"), (32, "D")],
    "silverlake-run": [(20, "A"), (21, "A"), (22, "A"), (23, "A"), (24, "A"), (25, "A"), (26, "A"), (27, "A"), (28, "A"),
                       (22, "B"), (23, "B"), (24, "B")],
    "fen-causeway": [(44, "C"), (45, "C"), (46, "C"), (47, "C"), (48, "C"), (49, "C"), (50, "C"),
                     (45, "B"), (46, "B"), (47, "B"), (48, "B"), (49, "B")],
    "high-pass": [(15, "G"), (16, "G"), (17, "G"), (18, "G"), (19, "G"), (20, "G"), (21, "G"),
                  (16, "H"), (17, "H"), (18, "H"), (19, "H")],
    "coast-trail": [(1, "E"), (2, "E"), (3, "E"), (4, "E"), (5, "E"), (6, "E"), (7, "E"), (8, "E"), (9, "E"),
                    (1, "F"), (2, "F"), (3, "F"), (4, "F"), (5, "F")],
    "north-pass": [(10, "M"), (11, "M"), (12, "M"), (13, "M"), (14, "M"), (14, "N"), (14, "O"), (14, "P"),
                   (15, "N"), (16, "N"), (17, "N")],
}

# Lore hook templates per region (randomly selected and parameterized)
LORE_HOOKS: dict[str, list[str]] = {
    "silversea_coast": [
        "Aquarid traders surface here at high tide to barter pearls for iron",
        "Bleached whale bones form an arch marking an ancient boundary",
        "Fishermen whisper of lights beneath the waves on moonless nights",
        "Salt-crusted ruins of a lighthouse jut from eroding cliffs",
        "Tide pools shimmer with bioluminescent algae; alchemists pay well for samples",
        "A half-sunken ship's mast is visible at low tide — cargo unknown",
        "Coastal caves flood at high tide; smugglers use them at low",
        "Seabirds nest in impossible numbers on one particular cliff face",
        "An old sea-wall runs into the water — built by hands larger than human",
        "Driftwood carvings wash up here, seemingly from no mortal workshop",
    ],
    "frostspire": [
        "Aurora pillars dance here year-round; the Ice Sovereign claims it as divine proof",
        "Frost-locked cairns from a forgotten army line the ridge",
        "Ice caves echo with voices that speak in no living tongue",
        "Permafrost preserves pre-Sundering corpses — scholars and looters both want them",
        "Wind-carved ice formations resemble kneeling figures",
        "A thermal vent melts a perfect circle in the snow; warmth draws beasts",
        "Frozen waterfalls contain trapped air bubbles that glow faintly blue",
        "Yeti tracks (or something larger) cross here regularly",
        "A collapsed observatory dome protrudes from a snowbank",
        "The Winter Court posted boundary markers — carved ice pillars that never melt",
    ],
    "skyreach": [
        "Lightning-struck glass formations litter the peak — valued by enchanters",
        "Monastery bells echo from somewhere above, but no path leads there",
        "Sky serpent nesting season turns this area lethal in spring",
        "Stone steps carved into the cliff face lead nowhere — or everywhere, depending on the wind",
        "Dusk bat swarms roost in the overhangs; their guano is prized fertilizer",
        "Wind howls through natural rock pipes creating eerie music",
        "A hermit monk tends a single garden on an impossible ledge",
        "Rope bridges sway between spires — some old, some freshly cut",
        "Storm clouds gather here unnaturally; sailors use it as a weather marker",
        "Petrified tree stumps suggest this was once a forest canopy, now elevated by tectonic shift",
    ],
    "whispering_marches": [
        "The trees lean in as if listening; locals say they report to the Verdant Vale",
        "An old waystone hums faintly at dawn — veil bleed or mechanical?",
        "Thornwolf pack territory markers: fresh claw gouges on white birch",
        "Silverlake mist rolls in every evening, carrying half-heard whispers",
        "A druid circle of standing stones, untouched by moss despite the damp",
        "Bioluminescent fungi light the forest floor on cloudy nights",
        "A stream runs uphill for thirty yards before vanishing underground",
        "Woodcutter's hut, long abandoned; tools still sharp, fire still warm",
        "Ether-touched deer glow faintly; hunting them is said to bring misfortune",
        "The path forks around a tree that was not there yesterday",
    ],
    "heartlands": [
        "A millstone marks where three farms meet — neutral ground for trade",
        "King's Road mile markers count down to Breley; travelers rest at even numbers",
        "Old Ash Century fortification walls repurposed as sheep pens",
        "A traveling tinker's wagon burned here; coins scattered but untouched by locals",
        "Ward-chalk boundaries visible on fence posts — monster deterrent or superstition?",
        "A well with water that tastes of copper; dwarven pipes suspected below",
        "Harvest festivals leave painted ribbons on field markers each autumn",
        "An iron cage hangs from a dead tree — Registry punishment for claim-jumpers",
        "Cart ruts suggest heavy traffic despite the road being 'minor' on maps",
        "A shrine to Aven sits at the crossroads; fresh flowers despite no nearby village",
    ],
    "transition": [
        "Bandit camp remnants: cold fire pits, broken bottles, drag marks into brush",
        "An unlicensed delver's cache hidden in a hollow log — picked clean",
        "Registry mile markers end abruptly; beyond is 'unmapped' per official charts",
        "Mixed tree line — heartland oak gives way to whispering birch",
        "A collapsed bridge over a ravine; someone rigged a rope crossing",
        "Iron Pact markers (three vertical slashes) appear on trees heading east",
        "Fog thickens unnaturally past this point; compass needles drift",
        "A hermit's warning carved in rock: 'TURN BACK — NOTHING PAST HERE WORTH DYING FOR'",
        "Abandoned prospector's dig — empty, but the tools are still good",
        "Wolf howls at dusk come from multiple directions simultaneously",
    ],
    "shadowfen": [
        "Mist never fully lifts; visibility beyond fifty yards is rare",
        "Causeway pylons emerge from the water — the only safe path, if you trust it",
        "Mireling burrows pit the ground; stepping wrong means sinking",
        "A pre-Sundering column rises from the marsh, covered in illegible glyphs",
        "The water here glows faintly green at night — ether contamination or algae?",
        "Dead trees stand like skeletal sentinels; their roots hide firm ground",
        "A Registry warning post: 'ESCORT REQUIRED — ADVISORY LEVEL 3'",
        "Bones of a large creature protrude from the peat — species unknown",
        "The air smells of sulfur near certain pools; breath catches in the throat",
        "Fireflies (or ether motes?) drift in patterns too regular to be random",
    ],
    "eastern_wastes": [
        "Bleached bones of unknown megafauna scatter across cracked earth",
        "A perfect stone circle — too geometrically precise to be natural",
        "Dust devils form and dissolve in minutes; locals say they carry whispers",
        "Centaur hoofprints cross here — a nomad trail still in use",
        "Orc war-totems mark contested territory; dried blood on the stakes",
        "A glass-smooth crater suggests ancient magical detonation",
        "Scrub brush hides deep sinkholes; test every step",
        "An abandoned watchtower, style matching no known civilization",
        "The sky takes on a bruised purple hue near the horizon — always eastward",
        "Carrion birds circle one spot perpetually; nothing visible below",
    ],
    "northern_highlands": [
        "Mountain goat trails wind between boulders; nimble or fall",
        "A frozen stream bed contains glittering mineral deposits",
        "Wind erosion carved faces into the cliff — or someone carved them long ago",
        "A collapsed mine entrance; timber supports rotted but ore veins visible",
        "Highland heather blooms purple in summer; medicinal if dried correctly",
        "A stone shelter built by shepherds; roof mostly intact",
        "Eagle nesting grounds; the birds are territorial and enormous",
        "Geothermal pools steam in winter; surrounded by mineral deposits",
        "A narrow pass between peaks — the only way through for miles",
        "Dwarf trade-road cobbles visible beneath centuries of soil",
    ],
    "central_plains": [
        "Grasslands stretch flat in every direction; navigation requires landmarks",
        "A lone oak tree serves as a meeting point for travelers",
        "Prairie dog warrens honeycomb the ground; horses beware",
        "Wild herds graze in the distance — aurochs, too large to hunt alone",
        "A merchant's waystation: water well, hitching post, fire ring",
        "Stone foundations of a long-gone village; only the well survives",
        "Wind carries smoke from a distant settlement",
        "Flocks of starlings form dark clouds at dusk; mesmerizing and disorienting",
        "A surveyor's stake with a Registry number — mapping in progress",
        "The road splits; one path well-worn, the other overgrown but shorter",
    ],
}


def weighted_choice(weights: dict) -> str:
    """Pick a key from a {key: weight} dict."""
    keys = list(weights.keys())
    vals = [weights[k] for k in keys]
    return random.choices(keys, weights=vals, k=1)[0]


def row_ord(r: str) -> int:
    return ord(r) - ord("A")


def in_bounds(col: int, row: str, bounds: dict) -> bool:
    return (
        bounds["colMin"] <= col <= bounds["colMax"]
        and row_ord(bounds["rowMin"]) <= row_ord(row) <= row_ord(bounds["rowMax"])
    )


def assign_region(col: int, row: str) -> str:
    for reg in REGION_PRIORITY:
        if in_bounds(col, row, {"colMin": reg["colMin"], "colMax": reg["colMax"],
                                "rowMin": reg["rowMin"], "rowMax": reg["rowMax"]}):
            return reg["key"]
    return "central_plains"


def get_trade_route(col: int, row: str) -> str | None:
    for route_name, waypoints in TRADE_ROUTES.items():
        if (col, row) in waypoints:
            return route_name
    return None


def cell_id(col: int, row: str) -> str:
    return f"{col}-{row}"


def generate_cell(col: int, row: str, region: str, rng: random.Random) -> dict:
    """Generate a complete cell seed for a surface cell."""
    region_key = region

    terrain = weighted_choice(TERRAIN_WEIGHTS.get(region_key, TERRAIN_WEIGHTS["central_plains"]))
    population = weighted_choice(POP_WEIGHTS.get(region_key, POP_WEIGHTS["central_plains"]))
    danger = weighted_choice(DANGER_WEIGHTS.get(region_key, DANGER_WEIGHTS["central_plains"]))
    scene_count = SCENE_COUNTS.get(terrain, 3)

    trade_route = get_trade_route(col, row)
    if trade_route:
        if terrain not in ("settlement", "road"):
            terrain = "road" if rng.random() < 0.4 else terrain

    # Override: settlements always have population >= village
    if terrain == "settlement" and population == "uninhabited":
        population = "village"

    # Build lore hooks
    hooks_pool = LORE_HOOKS.get(region_key, LORE_HOOKS["central_plains"])
    num_hooks = rng.randint(1, 2)
    hooks = rng.sample(hooks_pool, min(num_hooks, len(hooks_pool)))

    # Build tags
    tags = []
    if terrain in ("forest", "marsh", "mountains", "cliff", "tundra", "steppe", "desert"):
        tags.append("wilderness")
    if terrain in ("settlement",):
        tags.append("settlement")
    if terrain == "road":
        tags.append("road")
    if terrain == "ruins":
        tags.append("ruins")
    if trade_route:
        tags.append("trade")
    if danger in ("elite", "boss"):
        tags.append("dangerous")

    # Region biome
    biome_map = {
        "silversea_coast": "CO",
        "frostspire": "FR",
        "skyreach": "SK",
        "whispering_marches": "WM",
        "heartlands": "HL",
        "transition": "WM",
        "shadowfen": "SF",
        "eastern_wastes": "EW",
        "northern_highlands": "SK",
        "central_plains": "HL",
    }
    biome = biome_map.get(region_key, "HL")

    cid = cell_id(col, row)
    return {
        "id": cid,
        "column": col,
        "row": row,
        "surfaceRoot": cid,
        "parent": None,
        "layerStack": [],
        "biomes": [biome],
        "region": region_key,
        "terrain": terrain,
        "population": population,
        "sceneCount": scene_count,
        "loreHooks": hooks,
        "tradeRoute": trade_route,
        "dangerRating": danger,
        "registry": {"public": True, "stamped": danger is not None},
        "tags": tags,
        "childAddresses": [],
    }


def generate_display_name(cell: dict, rng: random.Random) -> str:
    """Generate a short display name from terrain/region/position."""
    terrain = cell["terrain"]
    region = cell["region"]

    region_names = {
        "silversea_coast": "Silversea",
        "frostspire": "Frostspire",
        "skyreach": "Skyreach",
        "whispering_marches": "Marches",
        "heartlands": "Heartland",
        "transition": "Wilds",
        "shadowfen": "Fen",
        "eastern_wastes": "Eastern",
        "northern_highlands": "Highlands",
        "central_plains": "Plains",
    }

    terrain_labels = {
        "forest": ["wood", "thicket", "grove", "timber"],
        "marsh": ["bog", "mire", "wetland", "fen"],
        "farmland": ["fields", "pastures", "tillage", "commons"],
        "road": ["crossroads", "waypoint", "mile post", "road bend"],
        "cliff": ["escarpment", "bluffs", "ledges", "crags"],
        "tundra": ["frost plain", "ice flat", "snowfield", "permafrost"],
        "coast": ["shore", "tideline", "cove", "beach"],
        "ruins": ["ruins", "rubble", "old walls", "fallen keep"],
        "settlement": ["hamlet", "outpost", "waystation", "homestead"],
        "plains": ["grassland", "open ground", "flatland", "steppe"],
        "hills": ["hillside", "ridgeline", "knolls", "slopes"],
        "mountains": ["peaks", "summit", "mountain pass", "crags"],
        "cavern-mouth": ["cave mouth", "sink", "grotto entrance", "pit"],
        "lake": ["lakeshore", "mere", "pool", "tarn"],
        "river": ["river crossing", "ford", "rapids", "stream"],
        "desert": ["wastes", "dust flat", "barrens", "dry bed"],
        "steppe": ["steppe", "windswept plain", "dry grass", "open waste"],
    }

    region_name = region_names.get(region, "Unknown")
    terrain_opts = terrain_labels.get(terrain, ["area"])
    terrain_label = rng.choice(terrain_opts)

    return f"{region_name} {terrain_label}"


def main():
    parser = argparse.ArgumentParser(description="Populate AV-GRID with all surface cells")
    parser.add_argument("--write", action="store_true", help="Write expanded av-grid.json")
    parser.add_argument("--validate", action="store_true", help="Write + run validation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    with open(GRID_PATH, "r", encoding="utf-8") as f:
        grid_data = json.load(f)

    addresses = grid_data["addresses"]
    existing_surface_ids = set()
    for addr_id, addr in addresses.items():
        if not addr.get("parent"):
            existing_surface_ids.add(addr_id)

    generated = 0
    skipped = 0

    for col in COLS:
        for row in ROWS:
            cid = cell_id(col, row)
            if cid in existing_surface_ids:
                skipped += 1
                continue

            region = assign_region(col, row)
            cell = generate_cell(col, row, region, rng)
            cell["displayName"] = generate_display_name(cell, rng)

            # Generate a short summary
            terrain_desc = cell["terrain"].replace("-", " ")
            pop = cell["population"]
            if pop == "uninhabited":
                pop_desc = "uninhabited"
            else:
                pop_desc = f"{pop} density"
            cell["summary"] = f"{terrain_desc.capitalize()}; {pop_desc}."

            addresses[cid] = cell
            generated += 1

    total_surface = len(COLS) * len(ROWS)
    print(f"Grid: {len(COLS)} cols x {len(ROWS)} rows = {total_surface} surface cells")
    print(f"Existing authored: {skipped}")
    print(f"Generated: {generated}")
    print(f"Total addresses (inc. layers): {len(addresses)}")

    # Stats by region
    region_counts: dict[str, int] = {}
    for addr in addresses.values():
        if not addr.get("parent"):
            r = addr.get("region", "unknown")
            region_counts[r] = region_counts.get(r, 0) + 1
    print("\nBy region:")
    for r, c in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"  {r}: {c}")

    if args.write or args.validate:
        # Sort addresses by id for consistent output
        sorted_addresses = dict(sorted(addresses.items(), key=lambda x: (x[1]["column"], x[1]["row"])))
        grid_data["addresses"] = sorted_addresses
        grid_data["version"] = "2.0.0"

        with open(GRID_PATH, "w", encoding="utf-8") as f:
            json.dump(grid_data, f, indent=2, ensure_ascii=False)
        print(f"\nWritten to {GRID_PATH}")

        if args.validate:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "build" / "tools" / "av_grid.py"), "validate"],
                capture_output=True, text=True, cwd=str(REPO_ROOT)
            )
            print(result.stdout)
            if result.returncode != 0:
                print(result.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
