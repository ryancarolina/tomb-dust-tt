"""Filesystem cache for generated campaign illustrations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ImageCache:
    def __init__(self, workspace: Path) -> None:
        self._root = workspace / ".local" / "image-cache"

    def image_path(self, campaign_slug: str, entity_type: str, entity_id: str) -> Path:
        return self._root / campaign_slug / entity_type / f"{entity_id}.png"

    def sidecar_path(self, campaign_slug: str, entity_type: str, entity_id: str) -> Path:
        return self._root / campaign_slug / entity_type / f"{entity_id}.json"

    def load(
        self,
        campaign_slug: str,
        entity_type: str,
        entity_id: str,
    ) -> tuple[Path | None, dict[str, Any] | None]:
        image = self.image_path(campaign_slug, entity_type, entity_id)
        sidecar = self.sidecar_path(campaign_slug, entity_type, entity_id)
        sidecar_data: dict[str, Any] | None = None
        if sidecar.is_file():
            try:
                sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
            except Exception:
                sidecar_data = None
        if image.is_file():
            return image, sidecar_data
        return None, sidecar_data

    def save(
        self,
        campaign_slug: str,
        entity_type: str,
        entity_id: str,
        *,
        image_bytes: bytes,
        sidecar: dict[str, Any],
    ) -> Path:
        image = self.image_path(campaign_slug, entity_type, entity_id)
        meta = self.sidecar_path(campaign_slug, entity_type, entity_id)
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(image_bytes)
        meta.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
        return image
