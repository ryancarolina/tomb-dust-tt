from __future__ import annotations

import json
from typing import Any

from tomb_gm.services.content import ContentService


def _format_surface_id(column: int, row: str) -> str:
    return f"{column}-{row}"


def _adjacent_surface_ids(content: ContentService, address: str) -> list[str]:
    entry = content.get_cell(address)
    if not entry or entry.get("layerStack"):
        return []
    col = int(entry["column"])
    row = str(entry["row"])
    row_ord = ord(row)
    candidates = [
        _format_surface_id(col - 1, row),
        _format_surface_id(col + 1, row),
    ]
    if row_ord > ord("A"):
        candidates.append(_format_surface_id(col, chr(row_ord - 1)))
    if row_ord < ord("Z"):
        candidates.append(_format_surface_id(col, chr(row_ord + 1)))
    addresses = content.load_av_grid()["addresses"]
    out: list[str] = []
    for cid in candidates:
        cell = addresses.get(cid)
        if cell and not cell.get("layerStack"):
            out.append(cid)
    return sorted(out)


class WorldService:
    def __init__(self, content: ContentService) -> None:
        self.content = content

    def unknown_address_error(self, address: str) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "UNKNOWN_ADDRESS",
            "address": address,
            "message": f"Unknown AV-GRID address: {address}",
        }

    def legal_exits(self, address: str) -> list[str] | None:
        entry = self.content.get_cell(address)
        if not entry:
            return None
        targets: set[str] = set()
        parent = entry.get("parent")
        if parent:
            targets.add(parent)
        for child in entry.get("childAddresses", []):
            targets.add(child)
        if not entry.get("layerStack"):
            targets.update(_adjacent_surface_ids(self.content, address))
        return sorted(targets)

    def can_travel(self, from_address: str, to_address: str) -> tuple[bool, str | None]:
        if not self.content.get_cell(from_address):
            return False, "UNKNOWN_FROM_ADDRESS"
        if not self.content.get_cell(to_address):
            return False, "UNKNOWN_ADDRESS"
        if from_address == to_address:
            return True, None
        exits = self.legal_exits(from_address)
        if exits is None:
            return False, "UNKNOWN_FROM_ADDRESS"
        if to_address not in exits:
            return False, "INVALID_TRAVEL"
        return True, None

    def stamp_validity(
        self, address: str, stamp_json: str | None
    ) -> dict[str, Any]:
        entry = self.content.get_cell(address)
        if not entry:
            return {"valid": False, "reason": "unknown_address"}
        registry = entry.get("registry") or {}
        stamped_site = bool(registry.get("stamped"))
        party_stamp = json.loads(stamp_json) if stamp_json else None
        if not stamped_site:
            return {
                "valid": True,
                "required": False,
                "registryStamped": False,
                "partyStamp": party_stamp,
            }
        if party_stamp and party_stamp.get("address") == address:
            return {
                "valid": True,
                "required": True,
                "registryStamped": True,
                "partyStamp": party_stamp,
            }
        return {
            "valid": False,
            "required": True,
            "registryStamped": True,
            "partyStamp": party_stamp,
            "reason": "stamp_required_for_stamped_site",
        }

    def where_payload(
        self, address: str, *, mode: str, stamp_json: str | None
    ) -> dict[str, Any] | None:
        cell = self.content.cell_payload(address)
        if not cell:
            return None
        return {
            "address": address,
            "mode": mode,
            "cell": cell,
            "stamp": self.stamp_validity(address, stamp_json),
        }

    def wilderness_travel_needed(self, to_address: str, stamp_json: str | None) -> bool:
        entry = self.content.get_cell(to_address)
        if not entry:
            return False
        registry = entry.get("registry") or {}
        if registry.get("stamped"):
            validity = self.stamp_validity(to_address, stamp_json)
            return not validity.get("valid", True)
        return True
