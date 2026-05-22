"""Core image generation service with cache and moderation retry."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from threading import Thread
from typing import Any, Callable

from gm.image_cache import ImageCache
from gm.image_prompt_builder import ENTITY_TYPES, ImagePromptBuilder
from gm.logger import log_entry
from gm.openrouter import create_client
from gm.openrouter_images import ImageModerationError, generate_image

DEFAULT_IMAGE_MODEL = "black-forest-labs/flux.2-klein-4b"


class ImageService:
    def __init__(
        self,
        *,
        workspace: Path,
        content_root: Path,
        client_factory: Callable[[], Any] = create_client,
        image_generator: Callable[..., bytes] = generate_image,
        async_generation: bool = False,
    ) -> None:
        self._workspace = workspace
        self._content_root = content_root
        self._cache = ImageCache(workspace)
        self._builder = ImagePromptBuilder(content_root)
        self._client_factory = client_factory
        self._image_generator = image_generator
        self._client: Any | None = None
        self._generations_this_session = 0
        self._async_generation = async_generation

    def resolve(
        self,
        campaign_slug: str,
        entity_type: str,
        entity_id: str,
        *,
        images_enabled: bool,
        config: dict[str, Any],
    ) -> str | None:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unsupported image entity type: {entity_type}")

        images_cfg = config.get("images") or {}
        model = str(images_cfg.get("model") or DEFAULT_IMAGE_MODEL)
        prompt = self._builder.build_prompt(entity_type, entity_id)
        prompt_hash = self._prompt_hash(prompt)

        cached_path, sidecar = self._cache.load(campaign_slug, entity_type, entity_id)
        if cached_path and self._is_cache_valid(sidecar, prompt_hash, model):
            log_entry(
                "image_gen_cache_hit",
                {
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "path": str(cached_path),
                },
            )
            return str(cached_path)

        bundled = self._lookup_bundled_image(entity_type, entity_id)
        if bundled and bundled.is_file():
            seeded = self._cache.save(
                campaign_slug,
                entity_type,
                entity_id,
                image_bytes=bundled.read_bytes(),
                sidecar=self._build_sidecar(
                    campaign_slug,
                    entity_type,
                    entity_id,
                    prompt,
                    prompt_hash,
                    model,
                ),
            )
            log_entry(
                "image_gen_bundled_seed",
                {
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "source": str(bundled),
                    "path": str(seeded),
                },
            )
            return str(seeded)

        if not (bool(images_cfg.get("enabled", False)) and images_enabled):
            log_entry(
                "image_gen_skipped",
                {
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "reason": "disabled",
                },
            )
            return None

        max_per_session = int(images_cfg.get("max_generations_per_session", 30))
        if self._generations_this_session >= max_per_session:
            log_entry(
                "image_gen_skipped",
                {
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "reason": "session_cap",
                    "max": max_per_session,
                },
            )
            return None

        if self._async_generation:
            thread = Thread(
                target=self._generate_and_cache,
                kwargs={
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "prompt": prompt,
                    "prompt_hash": prompt_hash,
                    "model": model,
                    "aspect_ratio": self._aspect_ratio(entity_type, images_cfg),
                },
                daemon=True,
            )
            thread.start()
            return None

        return self._generate_and_cache(
            campaign_slug=campaign_slug,
            entity_type=entity_type,
            entity_id=entity_id,
            prompt=prompt,
            prompt_hash=prompt_hash,
            model=model,
            aspect_ratio=self._aspect_ratio(entity_type, images_cfg),
        )

    def _generate_and_cache(
        self,
        *,
        campaign_slug: str,
        entity_type: str,
        entity_id: str,
        prompt: str,
        prompt_hash: str,
        model: str,
        aspect_ratio: str,
    ) -> str | None:
        self._generations_this_session += 1
        log_entry(
            "image_gen_start",
            {
                "campaign_slug": campaign_slug,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "model": model,
                "aspect_ratio": aspect_ratio,
            },
        )

        try:
            image_bytes = self._call_provider(model=model, prompt=prompt, aspect_ratio=aspect_ratio)
        except Exception as exc:
            log_entry(
                "image_gen_fail",
                {
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "error": str(exc),
                },
            )
            return None

        path = self._cache.save(
            campaign_slug,
            entity_type,
            entity_id,
            image_bytes=image_bytes,
            sidecar=self._build_sidecar(
                campaign_slug,
                entity_type,
                entity_id,
                prompt,
                prompt_hash,
                model,
            ),
        )
        log_entry(
            "image_gen_pass",
            {
                "campaign_slug": campaign_slug,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "path": str(path),
            },
        )
        return str(path)

    def _call_provider(self, *, model: str, prompt: str, aspect_ratio: str) -> bytes:
        client = self._client
        if client is None:
            client = self._client_factory()
            self._client = client
        try:
            return self._image_generator(
                client,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except ImageModerationError:
            sanitized = self._builder.sanitize_prompt(prompt)
            log_entry(
                "image_gen_moderated",
                {
                    "retry": True,
                    "sanitized_changed": sanitized != prompt,
                },
            )
            return self._image_generator(
                client,
                model=model,
                prompt=sanitized,
                aspect_ratio=aspect_ratio,
            )

    @staticmethod
    def _prompt_hash(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    @staticmethod
    def _aspect_ratio(entity_type: str, images_cfg: dict[str, Any]) -> str:
        if entity_type in {"npc", "monster", "item"}:
            return str(images_cfg.get("portrait_aspect_ratio") or "1:1")
        return str(images_cfg.get("scene_aspect_ratio") or "4:3")

    @staticmethod
    def _is_cache_valid(sidecar: dict[str, Any] | None, prompt_hash: str, model: str) -> bool:
        if not sidecar:
            return True
        return (
            str(sidecar.get("prompt_hash") or "") == prompt_hash
            and str(sidecar.get("model") or "") == model
        )

    @staticmethod
    def _build_sidecar(
        campaign_slug: str,
        entity_type: str,
        entity_id: str,
        prompt: str,
        prompt_hash: str,
        model: str,
    ) -> dict[str, Any]:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "campaign_slug": campaign_slug,
            "prompt_hash": prompt_hash,
            "model": model,
            "created_at": datetime.now(UTC).isoformat(),
            "prompt": prompt,
        }

    def _lookup_bundled_image(self, entity_type: str, entity_id: str) -> Path | None:
        path = self._content_root / "data" / "portraits" / f"{entity_id}.png"
        if path.is_file():
            return path
        return None
