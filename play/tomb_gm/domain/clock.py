from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CLOCK_NAMES = frozenset({"ingress", "delve", "extract"})
DEFAULT_CLOCKS: dict[str, int] = {"ingress": 0, "delve": 0, "extract": 0, "max": 6}


@dataclass(frozen=True)
class ClockState:
    ingress: int
    delve: int
    extract: int
    max_segments: int = 6

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> ClockState:
        raw = data or {}
        return cls(
            ingress=int(raw.get("ingress", 0)),
            delve=int(raw.get("delve", 0)),
            extract=int(raw.get("extract", 0)),
            max_segments=int(raw.get("max", 6)),
        )

    def to_json(self) -> dict[str, int]:
        return {
            "ingress": self.ingress,
            "delve": self.delve,
            "extract": self.extract,
            "max": self.max_segments,
        }

    def get(self, clock: str) -> int:
        if clock not in CLOCK_NAMES:
            raise ValueError(f"Unknown clock: {clock}")
        return getattr(self, clock)

    def tick(self, clock: str, segments: int = 1) -> tuple[ClockState, dict[str, Any]]:
        if clock not in CLOCK_NAMES:
            raise ValueError(f"Unknown clock: {clock}")
        if segments < 1:
            raise ValueError("segments must be >= 1")
        current = self.get(clock)
        new_value = min(current + segments, self.max_segments)
        updated = ClockState(
            ingress=new_value if clock == "ingress" else self.ingress,
            delve=new_value if clock == "delve" else self.delve,
            extract=new_value if clock == "extract" else self.extract,
            max_segments=self.max_segments,
        )
        return updated, {
            "clock": clock,
            "before": current,
            "after": new_value,
            "segments": segments,
            "at_max": new_value >= self.max_segments,
        }
