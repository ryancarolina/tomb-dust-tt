"""Core image generation service with cache and moderation retry."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from threading import Thread
from typing import Any, Callable

from gm.image_cache import ImageCache
from gm.image_prompt_builder import ENTITY_TYPES, ImagePromptBuilder
from gm.logger import log_entry, redact_secrets
from gm.openrouter import create_client
from gm.openrouter_images import ImageModerationError, generate_image

DEFAULT_IMAGE_MODEL = "black-forest-labs/flux.2-klein-4b"


def _skip_reason(config_enabled: bool, runtime_enabled: bool) -> str:
    """Skip reason when runtime Images toggle is off (config is not a player gate)."""
    if not runtime_enabled:
        if not config_enabled:
            return "both_off"
        return "runtime_off"
    raise ValueError("skip reason requested while runtime Images is on")


def _emit_resolve_result(
    *,
    campaign_slug: str,
    entity_type: str,
    entity_id: str,
    path: str | None,
    source: str,
    skip_reason: str | None = None,
    prompt_hash: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "campaign_slug": campaign_slug,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "path": path,
        "source": source,
    }
    if skip_reason is not None:
        payload["skip_reason"] = skip_reason
    if prompt_hash is not None:
        payload["prompt_hash"] = prompt_hash
    log_entry("image_resolve_result", payload)


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
        self._generation_epoch = 0

    def resolve(
        self,
        campaign_slug: str,
        entity_type: str,
        entity_id: str,
        *,
        images_enabled: bool,
        config: dict[str, Any],
        on_complete: Callable[[str | None], None] | None = None,
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
            _emit_resolve_result(
                campaign_slug=campaign_slug,
                entity_type=entity_type,
                entity_id=entity_id,
                path=str(cached_path),
                source="cache",
                prompt_hash=prompt_hash,
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
            _emit_resolve_result(
                campaign_slug=campaign_slug,
                entity_type=entity_type,
                entity_id=entity_id,
                path=str(seeded),
                source="bundled",
                prompt_hash=prompt_hash,
            )
            return str(seeded)

        config_enabled = bool(images_cfg.get("enabled", False))
        if not images_enabled:
            skip_reason = _skip_reason(config_enabled, images_enabled)
            log_entry(
                "image_gen_skipped",
                {
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "reason": skip_reason,
                    "config_enabled": config_enabled,
                    "runtime_enabled": images_enabled,
                },
            )
            _emit_resolve_result(
                campaign_slug=campaign_slug,
                entity_type=entity_type,
                entity_id=entity_id,
                path=None,
                source="skipped",
                skip_reason=skip_reason,
                prompt_hash=prompt_hash,
            )
            if on_complete:
                on_complete(None)
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
            _emit_resolve_result(
                campaign_slug=campaign_slug,
                entity_type=entity_type,
                entity_id=entity_id,
                path=None,
                source="skipped",
                skip_reason="session_cap",
                prompt_hash=prompt_hash,
            )
            if on_complete:
                on_complete(None)
            return None

        if self._async_generation:
            epoch = self._generation_epoch
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
                    "on_complete": on_complete,
                    "generation_epoch": epoch,
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
            on_complete=on_complete,
            generation_epoch=self._generation_epoch,
        )

    def cancel_generation(self) -> None:
        """Invalidate async callbacks for generations started before now."""
        self._generation_epoch += 1
        log_entry("image_gen_cancel", {"generation_epoch": self._generation_epoch})

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
        on_complete: Callable[[str | None], None] | None = None,
        generation_epoch: int | None = None,
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
                "prompt_hash": prompt_hash,
            },
        )

        try:
            image_bytes = self._call_provider(
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        except Exception as exc:
            log_entry(
                "image_gen_fail",
                {
                    "campaign_slug": campaign_slug,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "error": redact_secrets(str(exc)),
                },
            )
            if self._should_run_callback(
                generation_epoch,
                entity_type=entity_type,
                entity_id=entity_id,
            ):
                _emit_resolve_result(
                    campaign_slug=campaign_slug,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    path=None,
                    source="skipped",
                    skip_reason="api_fail",
                    prompt_hash=prompt_hash,
                )
                if on_complete:
                    on_complete(None)
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
        resolved = str(path)
        if self._should_run_callback(
            generation_epoch,
            entity_type=entity_type,
            entity_id=entity_id,
        ):
            _emit_resolve_result(
                campaign_slug=campaign_slug,
                entity_type=entity_type,
                entity_id=entity_id,
                path=resolved,
                source="api",
                prompt_hash=prompt_hash,
            )
            if on_complete:
                on_complete(resolved)
        return resolved

    def _should_run_callback(
        self,
        generation_epoch: int | None,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> bool:
        if generation_epoch is None:
            return True
        if generation_epoch == self._generation_epoch:
            return True
        payload: dict[str, Any] = {
            "generation_epoch": self._generation_epoch,
            "expected_epoch": generation_epoch,
        }
        if entity_type is not None:
            payload["entity_type"] = entity_type
        if entity_id is not None:
            payload["entity_id"] = entity_id
        log_entry("image_gen_stale_callback", payload)
        return False

    def _call_provider(
        self,
        *,
        model: str,
        prompt: str,
        aspect_ratio: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> bytes:
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
            moderated_payload: dict[str, Any] = {
                "retry": True,
                "sanitized_changed": sanitized != prompt,
            }
            if entity_type is not None:
                moderated_payload["entity_type"] = entity_type
            if entity_id is not None:
                moderated_payload["entity_id"] = entity_id
            log_entry("image_gen_moderated", moderated_payload)
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
