#!/usr/bin/env python3
"""AV-GRID parser and validator. Source of truth: data/av-grid/av-grid.json"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "av-grid" / "av-grid.json"
SCHEMA_PATH = ROOT / "data" / "av-grid" / "schema.json"

SURFACE_RE = re.compile(r"^(\d{2})-([A-Z])$")
LAYER_UG_RE = re.compile(r"^UG-(\d+)$")
LAYER_DP_RE = re.compile(r"^DP-(\d+)$")
PLANE_LAYERS = frozenset({"EP", "BV", "SK"})


class AvGridError(Exception):
    pass


def load_data(path: Path | None = None) -> dict:
    path = path or DATA_PATH
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_address(address_id: str) -> dict:
    """Parse AV-GRID id into column, row, surfaceRoot, layerStack."""
    parts = address_id.split("-")
    if len(parts) < 2:
        raise AvGridError(f"Invalid address: {address_id}")
    col = int(parts[0])
    row = parts[1]
    if row < "A" or row > "Z":
        raise AvGridError(f"Invalid row in {address_id}")
    surface_root = f"{parts[0]}-{parts[1]}"
    layer_stack: list[dict] = []
    i = 2
    while i < len(parts):
        token = parts[i]
        if token == "UG" and i + 1 < len(parts) and parts[i + 1].isdigit():
            layer_stack.append({"type": "UG", "depth": int(parts[i + 1])})
            i += 2
            continue
        if token == "DP" and i + 1 < len(parts) and parts[i + 1].isdigit():
            layer_stack.append({"type": "DP", "depth": int(parts[i + 1])})
            i += 2
            continue
        if token in PLANE_LAYERS:
            layer_stack.append({"type": token})
            i += 1
            continue
        raise AvGridError(f"Unknown layer segment in {address_id} at '{token}'")
    return {
        "id": address_id,
        "column": col,
        "row": row,
        "surfaceRoot": surface_root,
        "layerStack": layer_stack,
    }


def validate_data(data: dict) -> list[str]:
    errors: list[str] = []
    grid = data["grid"]
    col_min, col_max = grid["columns"]["min"], grid["columns"]["max"]
    row_min, row_max = grid["rows"]["min"], grid["rows"]["max"]
    layer_types = set(data["layerTypes"])
    biomes = set(data["biomes"])
    regions = set(data["regions"])
    addresses: dict = data["addresses"]

    for addr_id, entry in addresses.items():
        if addr_id != entry.get("id"):
            errors.append(f"{addr_id}: id field mismatch ({entry.get('id')})")

        try:
            parsed = parse_address(addr_id)
        except AvGridError as e:
            errors.append(str(e))
            continue

        if entry["column"] != parsed["column"]:
            errors.append(f"{addr_id}: column {entry['column']} != parsed {parsed['column']}")
        if entry["row"] != parsed["row"]:
            errors.append(f"{addr_id}: row {entry['row']} != parsed {parsed['row']}")
        if entry["surfaceRoot"] != parsed["surfaceRoot"]:
            errors.append(f"{addr_id}: surfaceRoot mismatch")
        if entry["layerStack"] != parsed["layerStack"]:
            errors.append(f"{addr_id}: layerStack {entry['layerStack']} != parsed {parsed['layerStack']}")

        if not (col_min <= entry["column"] <= col_max):
            errors.append(f"{addr_id}: column out of grid bounds")
        if not (row_min <= entry["row"] <= row_max):
            errors.append(f"{addr_id}: row out of grid bounds")

        for layer in entry["layerStack"]:
            if layer["type"] not in layer_types:
                errors.append(f"{addr_id}: unknown layer type {layer['type']}")

        for b in entry["biomes"]:
            if b not in biomes:
                errors.append(f"{addr_id}: unknown biome {b}")
        if entry["region"] not in regions:
            errors.append(f"{addr_id}: unknown region {entry['region']}")

        parent = entry.get("parent")
        if parent is not None and parent not in addresses:
            errors.append(f"{addr_id}: missing parent {parent}")

        for child in entry.get("childAddresses", []):
            if child not in addresses:
                errors.append(f"{addr_id}: missing child {child}")
            elif addresses[child].get("parent") != addr_id:
                errors.append(
                    f"{child}: parent should be {addr_id}, got {addresses[child].get('parent')}"
                )

    return errors


def get_address(data: dict, address_id: str) -> dict | None:
    return data.get("addresses", {}).get(address_id)


def resolve_surface(data: dict, address_id: str) -> str:
    entry = get_address(data, address_id)
    if entry:
        return entry["surfaceRoot"]
    parsed = parse_address(address_id)
    return parsed["surfaceRoot"]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="AV-GRID tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="Validate av-grid.json")

    p_parse = sub.add_parser("parse", help="Parse an address id")
    p_parse.add_argument("address")

    p_get = sub.add_parser("get", help="Print address record as JSON")
    p_get.add_argument("address")

    p_children = sub.add_parser("children", help="List child addresses")
    p_children.add_argument("address")

    sub.add_parser("build-index", help="Write data/av-grid/index.json lookup file")

    args = parser.parse_args()
    data = load_data()

    if args.cmd == "validate":
        errors = validate_data(data)
        if errors:
            print(f"FAIL ({len(errors)} errors):", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1
        n = len(data["addresses"])
        print(f"OK: {n} addresses, version {data['version']}")
        return 0

    if args.cmd == "parse":
        print(json.dumps(parse_address(args.address), indent=2))
        return 0

    if args.cmd == "get":
        rec = get_address(data, args.address)
        if not rec:
            print(f"Not found: {args.address}", file=sys.stderr)
            return 1
        print(json.dumps(rec, indent=2))
        return 0

    if args.cmd == "children":
        rec = get_address(data, args.address)
        if not rec:
            print(f"Not found: {args.address}", file=sys.stderr)
            return 1
        for c in rec.get("childAddresses", []):
            print(c)
        return 0

    if args.cmd == "build-index":
        by_surface: dict[str, list[str]] = {}
        for addr_id, entry in data["addresses"].items():
            root = entry["surfaceRoot"]
            by_surface.setdefault(root, [])
            if addr_id != root:
                by_surface[root].append(addr_id)
        index = {
            "version": data["version"],
            "generatedBy": "tools/av_grid.py build-index",
            "addressIds": sorted(data["addresses"].keys()),
            "bySurface": {k: sorted(v) for k, v in sorted(by_surface.items())},
        }
        out = ROOT / "data" / "av-grid" / "index.json"
        out.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
