from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

STAMP_COST_BY_DANGER: dict[str, int] = {
    "hazard": 20,
    "skirmisher": 45,
    "elite": 120,
    "boss": 250,
}


@dataclass(frozen=True)
class RegistryStamp:
    primary: str
    surface_entry: str | None
    danger: str
    cost_gp: int
    valid_days: int
    issued_at: str

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> RegistryStamp | None:
        if not data:
            return None
        return cls(
            primary=str(data["primary"]),
            surface_entry=data.get("surfaceEntry") or data.get("surface_entry"),
            danger=str(data.get("danger", "skirmisher")),
            cost_gp=int(data.get("costGp", data.get("cost_gp", 0))),
            valid_days=int(data.get("validDays", data.get("valid_days", 30))),
            issued_at=str(data["issuedAt"]),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "surfaceEntry": self.surface_entry,
            "danger": self.danger,
            "costGp": self.cost_gp,
            "validDays": self.valid_days,
            "issuedAt": self.issued_at,
        }

    def is_valid(self, *, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        issued = datetime.fromisoformat(self.issued_at.replace("Z", "+00:00"))
        if issued.tzinfo is None:
            issued = issued.replace(tzinfo=timezone.utc)
        expires = issued + timedelta(days=self.valid_days)
        return now <= expires

    def covers_address(self, address: str) -> bool:
        return address == self.primary or (
            self.surface_entry is not None and address == self.surface_entry
        )


def stamp_matches_site(stamp: RegistryStamp | None, site_primary: str, party_address: str) -> bool:
    if stamp is None or not stamp.is_valid():
        return False
    if stamp.primary != site_primary:
        return False
    return stamp.covers_address(party_address) or party_address == site_primary


def build_stamp(*, address: str, danger: str = "skirmisher", surface_entry: str | None = None) -> dict[str, Any]:
    cost = STAMP_COST_BY_DANGER.get(danger.lower(), STAMP_COST_BY_DANGER["skirmisher"])
    issued = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    surface = surface_entry
    if surface is None and "-" in address:
        parts = address.split("-")
        if len(parts) >= 2:
            surface = f"{parts[0]}-{parts[1]}"
    return {
        "primary": address,
        "surfaceEntry": surface,
        "danger": danger,
        "costGp": cost,
        "validDays": 30,
        "issuedAt": issued,
    }
