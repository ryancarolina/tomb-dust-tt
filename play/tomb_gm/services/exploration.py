"""
Exploration service: manages intra-cell scene movement, feature generation,
dungeon room navigation, and persistent world state.
"""
from __future__ import annotations

import json
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tomb_gm.services.content import ContentService

TEMPLATES_PATH = Path(__file__).resolve().parents[3] / "build" / "data" / "templates" / "cell-features.json"
EVENTS_PATH = Path(__file__).resolve().parents[3] / "build" / "data" / "templates" / "dynamic-events.json"
SITES_DIR = Path(__file__).resolve().parents[3] / "build" / "data" / "sites"

DIRECTION_OFFSETS = {
    "N": (0, -1),
    "S": (0, 1),
    "E": (1, 0),
    "W": (-1, 0),
}

DIRECTION_NAMES = {"N": "North", "S": "South", "E": "East", "W": "West"}
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_templates() -> dict:
    if TEMPLATES_PATH.exists():
        return json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
    return {}


def _load_events() -> dict:
    if EVENTS_PATH.exists():
        return json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    return {}


class ExplorationService:
    def __init__(self, conn: sqlite3.Connection, content: ContentService) -> None:
        self.conn = conn
        self.content = content
        self._templates: dict | None = None
        self._events: dict | None = None

    @property
    def templates(self) -> dict:
        if self._templates is None:
            self._templates = _load_templates()
        return self._templates

    @property
    def events_data(self) -> dict:
        if self._events is None:
            self._events = _load_events()
        return self._events

    # ------------------------------------------------------------------
    # Cell visit tracking
    # ------------------------------------------------------------------

    def is_cell_visited(self, cell_address: str, campaign_slug: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM cell_visits WHERE cell_address = ? AND campaign_slug = ?",
            (cell_address, campaign_slug),
        ).fetchone()
        return row is not None

    def mark_cell_visited(self, cell_address: str, campaign_slug: str) -> None:
        now = _now_iso()
        self.conn.execute(
            """INSERT INTO cell_visits (cell_address, campaign_slug, first_visited_at, last_visited_at, times_visited)
               VALUES (?, ?, ?, ?, 1)
               ON CONFLICT(cell_address, campaign_slug)
               DO UPDATE SET last_visited_at = ?, times_visited = times_visited + 1""",
            (cell_address, campaign_slug, now, now, now),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Feature generation (first visit)
    # ------------------------------------------------------------------

    def generate_cell_features(self, cell_address: str) -> list[dict]:
        """Generate persistent features for a cell on first visit. Returns the created features."""
        cell = self.content.get_cell(cell_address)
        if not cell:
            return []

        terrain = cell.get("terrain", "plains")
        scene_count = cell.get("sceneCount", 3)
        templates = self.templates

        terrain_pool = templates.get("featuresByTerrain", {}).get(terrain, {})
        count_config = templates.get("featureCountByTerrain", {}).get(terrain, {"min": 2, "max": 4})
        num_features = random.randint(count_config["min"], count_config["max"])

        all_options: list[tuple[str, dict]] = []
        for category, items in terrain_pool.items():
            for item in items:
                all_options.append((category, item))

        if not all_options:
            return []

        weights = [opt[1].get("weight", 1) for opt in all_options]
        chosen = random.choices(all_options, weights=weights, k=min(num_features, len(all_options)))

        # Deduplicate by name
        seen_names: set[str] = set()
        unique_chosen: list[tuple[str, dict]] = []
        for cat, item in chosen:
            if item["name"] not in seen_names:
                seen_names.add(item["name"])
                unique_chosen.append((cat, item))

        features: list[dict] = []
        now = _now_iso()
        for i, (category, item) in enumerate(unique_chosen):
            scene_pos = (i % scene_count) + 1
            feature_id = str(uuid.uuid4())[:8]
            feature = {
                "id": f"{cell_address}-{feature_id}",
                "cell_address": cell_address,
                "feature_type": category,
                "display_name": item["name"],
                "description": item.get("desc", ""),
                "scene_position": scene_pos,
                "discovered": 0,
                "state": "pristine",
                "data_json": "{}",
                "created_at": now,
            }
            self.conn.execute(
                """INSERT OR IGNORE INTO cell_features
                   (id, cell_address, feature_type, display_name, description, scene_position, discovered, state, data_json, created_at)
                   VALUES (:id, :cell_address, :feature_type, :display_name, :description, :scene_position, :discovered, :state, :data_json, :created_at)""",
                feature,
            )
            features.append(feature)

        self.conn.commit()
        return features

    def get_cell_features(self, cell_address: str) -> list[dict]:
        """Get all features for a cell (whether discovered or not)."""
        rows = self.conn.execute(
            "SELECT * FROM cell_features WHERE cell_address = ? ORDER BY scene_position",
            (cell_address,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_scene_features(self, cell_address: str, scene_index: int) -> list[dict]:
        """Get features at a specific scene position."""
        rows = self.conn.execute(
            "SELECT * FROM cell_features WHERE cell_address = ? AND scene_position = ?",
            (cell_address, scene_index),
        ).fetchall()
        return [dict(r) for r in rows]

    def discover_feature(self, feature_id: str) -> bool:
        """Mark a feature as discovered."""
        self.conn.execute(
            "UPDATE cell_features SET discovered = 1 WHERE id = ?", (feature_id,)
        )
        self.conn.commit()
        return True

    def update_feature_state(self, feature_id: str, new_state: str) -> bool:
        """Update a feature's state (pristine, looted, triggered, etc.)."""
        self.conn.execute(
            "UPDATE cell_features SET state = ? WHERE id = ?", (new_state, feature_id)
        )
        self.conn.commit()
        return True

    # ------------------------------------------------------------------
    # Scene movement (overworld)
    # ------------------------------------------------------------------

    def advance_scene(
        self, session_id: str, campaign_slug: str, direction: str | None = None
    ) -> dict[str, Any]:
        """Advance one scene in the current cell. Returns result with features revealed."""
        ps = self.conn.execute(
            "SELECT address, scene_index, scene_max, heading, mode FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not ps:
            return {"ok": False, "error": "NO_PARTY_STATE"}

        address = ps["address"]
        scene_index = ps["scene_index"]
        scene_max = ps["scene_max"]
        heading = direction or ps["heading"]
        mode = ps["mode"]

        if mode != "surface":
            return {"ok": False, "error": "NOT_ON_SURFACE", "message": "Use room navigation in dungeons"}

        new_scene = scene_index + 1

        if new_scene > scene_max:
            # Crossed cell boundary — need to move to adjacent cell
            col_off, row_off = DIRECTION_OFFSETS.get(heading, (0, 0))
            cell = self.content.get_cell(address)
            if not cell:
                return {"ok": False, "error": "UNKNOWN_CELL"}
            new_col = cell["column"] + col_off
            new_row_ord = ord(cell["row"]) + row_off
            new_row = chr(new_row_ord) if ord("A") <= new_row_ord <= ord("Z") else None
            if new_row is None or new_col < 1 or new_col > 60:
                return {"ok": False, "error": "EDGE_OF_WORLD", "message": "Cannot go further in that direction"}

            new_address = f"{new_col}-{new_row}"
            new_cell = self.content.get_cell(new_address)
            if not new_cell:
                return {"ok": False, "error": "NO_CELL_DATA", "address": new_address}

            new_scene_max = new_cell.get("sceneCount", 3)

            # Generate features if first visit
            if not self.is_cell_visited(new_address, campaign_slug):
                self.generate_cell_features(new_address)
            self.mark_cell_visited(new_address, campaign_slug)

            # Update party state
            self.conn.execute(
                """UPDATE party_state SET address = ?, scene_index = 1, scene_max = ?, heading = ?
                   WHERE session_id = ?""",
                (new_address, new_scene_max, heading, session_id),
            )
            self.conn.commit()

            features_here = self.get_scene_features(new_address, 1)
            self._auto_discover(features_here)

            event = self.roll_scene_event(new_address)

            return {
                "ok": True,
                "crossed_cell": True,
                "from_address": address,
                "to_address": new_address,
                "cell": self.content.cell_payload(new_address),
                "scene_index": 1,
                "scene_max": new_scene_max,
                "heading": heading,
                "features_revealed": [f for f in features_here],
                "direction_name": DIRECTION_NAMES.get(heading, heading),
                "dynamic_event": event,
            }
        else:
            # Stay in current cell, advance scene
            self.conn.execute(
                "UPDATE party_state SET scene_index = ?, heading = ? WHERE session_id = ?",
                (new_scene, heading, session_id),
            )
            self.conn.commit()

            features_here = self.get_scene_features(address, new_scene)
            self._auto_discover(features_here)

            event = self.roll_scene_event(address)

            return {
                "ok": True,
                "crossed_cell": False,
                "address": address,
                "scene_index": new_scene,
                "scene_max": scene_max,
                "heading": heading,
                "features_revealed": [f for f in features_here],
                "direction_name": DIRECTION_NAMES.get(heading, heading),
                "dynamic_event": event,
            }

    def _auto_discover(self, features: list[dict]) -> None:
        """Mark features as discovered when the player reaches their scene."""
        for f in features:
            if not f.get("discovered"):
                self.conn.execute(
                    "UPDATE cell_features SET discovered = 1 WHERE id = ?", (f["id"],)
                )
        self.conn.commit()

    def roll_scene_event(self, cell_address: str) -> dict | None:
        """Roll for a dynamic event at this scene. 1d6: 1=encounter, 2=NPC/event, 3-6=quiet."""
        roll = random.randint(1, 6)
        cell = self.content.get_cell(cell_address)
        if not cell:
            return None

        region = cell.get("region", "central_plains")
        events = self.events_data

        if roll == 1:
            pool = events.get("encountersByRegion", {}).get(region, [])
            if pool:
                return {"type": "encounter", "roll": roll, "event": random.choice(pool)}
        elif roll == 2:
            pool = events.get("npcEventsByRegion", {}).get(region, [])
            if pool:
                return {"type": "npc_event", "roll": roll, "event": random.choice(pool)}

        # 3-6: quiet, but mention weather occasionally
        if roll == 3:
            weather_pool = events.get("weatherByRegion", {}).get(region, [])
            if weather_pool:
                return {"type": "weather", "roll": roll, "event": random.choice(weather_pool)}

        return None

    # ------------------------------------------------------------------
    # Compass exits (for LLM context)
    # ------------------------------------------------------------------

    def compass_exits(self, address: str, campaign_slug: str) -> dict[str, Any]:
        """Return compass-labeled adjacent cells with terrain info."""
        cell = self.content.get_cell(address)
        if not cell or cell.get("layerStack"):
            return {}

        col = cell["column"]
        row = cell["row"]
        row_ord_val = ord(row)
        grid = self.content.load_av_grid()["addresses"]

        exits: dict[str, Any] = {}
        directions = {
            "N": (col, chr(row_ord_val - 1) if row_ord_val > ord("A") else None),
            "S": (col, chr(row_ord_val + 1) if row_ord_val < ord("Z") else None),
            "E": (col + 1, row),
            "W": (col - 1, row),
        }

        for dir_key, (c, r) in directions.items():
            if r is None or c < 1 or c > 60:
                continue
            adj_id = f"{c}-{r}"
            adj_cell = grid.get(adj_id)
            if adj_cell and not adj_cell.get("layerStack"):
                visited = self.is_cell_visited(adj_id, campaign_slug)
                exits[dir_key] = {
                    "address": adj_id,
                    "displayName": adj_cell.get("displayName", adj_id),
                    "terrain": adj_cell.get("terrain", "unknown"),
                    "population": adj_cell.get("population", "unknown"),
                    "dangerRating": adj_cell.get("dangerRating"),
                    "visited": visited,
                }

        # Also check for underground children
        children = cell.get("childAddresses", [])
        if children:
            exits["below"] = [
                {"address": cid, "displayName": grid[cid].get("displayName", cid)}
                for cid in children if cid in grid
            ]

        return exits

    # ------------------------------------------------------------------
    # Dungeon room navigation
    # ------------------------------------------------------------------

    def enter_site(self, session_id: str, site_address: str) -> dict[str, Any]:
        """Transition from surface to dungeon mode."""
        # Load or generate rooms for this site
        rooms = self._get_site_rooms(site_address)
        if not rooms:
            rooms = self._load_or_generate_site(site_address)
            if not rooms:
                return {"ok": False, "error": "NO_SITE_DATA", "address": site_address}

        entry_room = next((r for r in rooms if "entry" in (r.get("tags_json") or "[]")), rooms[0])
        room_id = entry_room["room_id"] if isinstance(entry_room, dict) else entry_room[2]

        # Mark room visited
        self.conn.execute(
            "UPDATE site_rooms SET visited = 1 WHERE site_address = ? AND room_id = ?",
            (site_address, room_id),
        )

        # Update party state to dungeon mode
        self.conn.execute(
            """UPDATE party_state SET mode = 'dungeon', site_id = ?, dungeon_room_id = ?
               WHERE session_id = ?""",
            (site_address, room_id, session_id),
        )
        self.conn.commit()

        room_data = self._get_room(site_address, room_id)
        room_features = self._get_room_features(site_address, room_id)

        return {
            "ok": True,
            "site_address": site_address,
            "room": room_data,
            "features": room_features,
            "message": f"Entered {room_data.get('display_name', site_address)}",
        }

    def move_room(self, session_id: str, direction: str) -> dict[str, Any]:
        """Move to an adjacent room in the current dungeon via an exit."""
        ps = self.conn.execute(
            "SELECT site_id, dungeon_room_id, mode FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not ps or ps["mode"] != "dungeon":
            return {"ok": False, "error": "NOT_IN_DUNGEON"}

        site_address = ps["site_id"]
        current_room_id = ps["dungeon_room_id"]

        room_data = self._get_room(site_address, current_room_id)
        if not room_data:
            return {"ok": False, "error": "ROOM_NOT_FOUND"}

        exits = json.loads(room_data.get("exits_json", "[]"))

        # Find matching exit
        target_exit = None
        direction_lower = direction.lower()
        for ex in exits:
            if (ex.get("direction", "").lower() == direction_lower or
                ex.get("target_room_id", "").lower() == direction_lower):
                target_exit = ex
                break

        if not target_exit:
            return {
                "ok": False,
                "error": "NO_SUCH_EXIT",
                "available_exits": [e.get("direction", e.get("target_room_id")) for e in exits],
            }

        if target_exit.get("locked") and target_exit.get("state") != "unlocked":
            return {"ok": False, "error": "EXIT_LOCKED", "exit": target_exit}

        new_room_id = target_exit["target_room_id"]

        # Mark new room visited
        self.conn.execute(
            "UPDATE site_rooms SET visited = 1 WHERE site_address = ? AND room_id = ?",
            (site_address, new_room_id),
        )

        # Update party state
        self.conn.execute(
            "UPDATE party_state SET dungeon_room_id = ? WHERE session_id = ?",
            (new_room_id, session_id),
        )
        self.conn.commit()

        new_room_data = self._get_room(site_address, new_room_id)
        room_features = self._get_room_features(site_address, new_room_id)

        return {
            "ok": True,
            "site_address": site_address,
            "room": new_room_data,
            "features": room_features,
            "from_room": current_room_id,
            "direction": direction,
        }

    def exit_site(self, session_id: str) -> dict[str, Any]:
        """Exit dungeon back to surface."""
        ps = self.conn.execute(
            "SELECT site_id, address, mode FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not ps or ps["mode"] != "dungeon":
            return {"ok": False, "error": "NOT_IN_DUNGEON"}

        # Return to surface
        self.conn.execute(
            """UPDATE party_state SET mode = 'surface', site_id = NULL, dungeon_room_id = NULL
               WHERE session_id = ?""",
            (session_id,),
        )
        self.conn.commit()

        return {"ok": True, "address": ps["address"], "message": "Returned to surface"}

    def current_room_info(self, session_id: str) -> dict[str, Any] | None:
        """Get current room info if in dungeon mode."""
        ps = self.conn.execute(
            "SELECT site_id, dungeon_room_id, mode FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not ps or ps["mode"] != "dungeon":
            return None

        room_data = self._get_room(ps["site_id"], ps["dungeon_room_id"])
        features = self._get_room_features(ps["site_id"], ps["dungeon_room_id"])
        return {"room": room_data, "features": features, "site_address": ps["site_id"]}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_site_rooms(self, site_address: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM site_rooms WHERE site_address = ?", (site_address,)
        ).fetchall()
        return [dict(r) for r in rows]

    def _get_room(self, site_address: str, room_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM site_rooms WHERE site_address = ? AND room_id = ?",
            (site_address, room_id),
        ).fetchone()
        return dict(row) if row else None

    def _get_room_features(self, site_address: str, room_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM room_features WHERE site_address = ? AND room_id = ?",
            (site_address, room_id),
        ).fetchall()
        features = [dict(r) for r in rows]
        from tomb_gm.services.death import corpses_as_features, get_corpses_for_room

        corpses = get_corpses_for_room(site_address, room_id, self.conn)
        features.extend(corpses_as_features(corpses))
        return features

    def _load_or_generate_site(self, site_address: str) -> list[dict]:
        """Load authored site or generate a simple one."""
        # Try loading from authored site files
        for site_file in SITES_DIR.glob("*.json"):
            site_data = json.loads(site_file.read_text(encoding="utf-8"))
            if site_data.get("primaryAddress") == site_address:
                return self._import_site_graph(site_address, site_data)

        # Generate a simple site from cell data
        cell = self.content.get_cell(site_address)
        if not cell:
            return []

        return self._generate_simple_site(site_address, cell)

    def _import_site_graph(self, site_address: str, site_data: dict) -> list[dict]:
        """Import an authored site graph into the database."""
        now = _now_iso()
        rooms: list[dict] = []

        nodes = site_data.get("nodes", [])
        edges = site_data.get("edges", [])

        # Build edge lookup for exits
        exits_by_node: dict[str, list[dict]] = {}
        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            if from_id not in exits_by_node:
                exits_by_node[from_id] = []
            exits_by_node[from_id].append({
                "direction": edge.get("type", "passage"),
                "target_room_id": to_id,
                "locked": edge.get("locked", False),
                "hidden": edge.get("secret", False) if edge.get("type") == "secret" else False,
                "state": "pristine",
            })
            # Add reverse exit unless one-way
            if to_id not in exits_by_node:
                exits_by_node[to_id] = []
            exits_by_node[to_id].append({
                "direction": f"back ({edge.get('type', 'passage')})",
                "target_room_id": from_id,
                "locked": False,
                "hidden": False,
                "state": "pristine",
            })

        for node in nodes:
            room_id = node["id"]
            tags = node.get("tags", [])
            room = {
                "id": f"{site_address}-{room_id}",
                "site_address": site_address,
                "room_id": room_id,
                "display_name": node.get("displayName", room_id),
                "description": node.get("summary", ""),
                "exits_json": json.dumps(exits_by_node.get(room_id, [])),
                "tags_json": json.dumps(tags),
                "visited": 0,
                "created_at": now,
            }
            self.conn.execute(
                """INSERT OR IGNORE INTO site_rooms
                   (id, site_address, room_id, display_name, description, exits_json, tags_json, visited, created_at)
                   VALUES (:id, :site_address, :room_id, :display_name, :description, :exits_json, :tags_json, :visited, :created_at)""",
                room,
            )
            rooms.append(room)

            # Create room features from encounters
            for enc in node.get("encounters", []):
                feat_id = str(uuid.uuid4())[:8]
                self.conn.execute(
                    """INSERT OR IGNORE INTO room_features
                       (id, site_address, room_id, feature_type, display_name, description, state, data_json, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"{site_address}-{room_id}-{feat_id}",
                        site_address, room_id, "enemy",
                        enc.get("monsterId", "unknown"),
                        f"Encounter: {enc.get('monsterId', 'unknown')}",
                        "pristine",
                        json.dumps(enc),
                        now,
                    ),
                )

        self.conn.commit()
        return rooms

    def _generate_simple_site(self, site_address: str, cell: dict) -> list[dict]:
        """Generate a small site (3-6 rooms) from cell data."""
        now = _now_iso()
        danger = cell.get("dangerRating", "hazard")
        room_count = {"hazard": 3, "skirmisher": 4, "elite": 5, "boss": 6}.get(danger, 4)

        room_names = [
            ("entry", "Entry passage", ["entry"]),
            ("chamber-1", "First chamber", []),
            ("chamber-2", "Inner chamber", []),
            ("chamber-3", "Deep chamber", []),
            ("vault", "Sealed vault", ["loot"]),
            ("sanctum", "Inner sanctum", ["boss-adjacent"]),
        ]

        rooms: list[dict] = []
        for i in range(min(room_count, len(room_names))):
            room_id, name, tags = room_names[i]
            # Build exits: linear chain
            exits = []
            if i > 0:
                exits.append({"direction": "back", "target_room_id": room_names[i-1][0], "locked": False, "hidden": False, "state": "pristine"})
            if i < room_count - 1:
                exits.append({"direction": "forward", "target_room_id": room_names[i+1][0], "locked": False, "hidden": False, "state": "pristine"})

            room = {
                "id": f"{site_address}-{room_id}",
                "site_address": site_address,
                "room_id": room_id,
                "display_name": name,
                "description": f"A {name.lower()} within {cell.get('displayName', site_address)}.",
                "exits_json": json.dumps(exits),
                "tags_json": json.dumps(tags),
                "visited": 0,
                "created_at": now,
            }
            self.conn.execute(
                """INSERT OR IGNORE INTO site_rooms
                   (id, site_address, room_id, display_name, description, exits_json, tags_json, visited, created_at)
                   VALUES (:id, :site_address, :room_id, :display_name, :description, :exits_json, :tags_json, :visited, :created_at)""",
                room,
            )
            rooms.append(room)

        self.conn.commit()
        return rooms

    # ------------------------------------------------------------------
    # Initialize cell on first arrival
    # ------------------------------------------------------------------

    def ensure_cell_initialized(self, cell_address: str, campaign_slug: str, session_id: str) -> None:
        """Call when party arrives at a cell. Generates features if first visit, updates scene_max."""
        if not self.is_cell_visited(cell_address, campaign_slug):
            self.generate_cell_features(cell_address)
            self.mark_cell_visited(cell_address, campaign_slug)

        cell = self.content.get_cell(cell_address)
        if cell:
            scene_max = cell.get("sceneCount", 3)
            self.conn.execute(
                "UPDATE party_state SET scene_max = ? WHERE session_id = ?",
                (scene_max, session_id),
            )
            self.conn.commit()
