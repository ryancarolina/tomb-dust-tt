"""OpenRouter image generation helpers for APP-094."""

from __future__ import annotations

import base64
from typing import Any


class ImageModerationError(RuntimeError):
    """Raised when provider blocks a prompt for moderation."""


def is_moderation_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "content moderated" in message or "safety filter" in message


def _extract_image_data_url(message: Any) -> str:
    images = getattr(message, "images", None)
    if not images:
        model_extra = getattr(message, "model_extra", None)
        if isinstance(model_extra, dict):
            images = model_extra.get("images")
    if not images:
        raise RuntimeError(f"No image payload in response: {getattr(message, 'content', '')!r}")

    first = images[0]
    if hasattr(first, "image_url"):
        url = first.image_url.url
    elif isinstance(first, dict):
        url = str((first.get("image_url") or {}).get("url") or "")
    else:
        url = str(first)
    if not url.startswith("data:"):
        raise RuntimeError(f"Unexpected image URL format: {url[:80]!r}")
    return url


def _decode_image_data_url(data_url: str) -> bytes:
    try:
        _header, b64_data = data_url.split(",", 1)
    except ValueError as exc:
        raise RuntimeError("Malformed image data URL from provider") from exc
    try:
        return base64.b64decode(b64_data)
    except Exception as exc:
        raise RuntimeError("Unable to decode image payload from provider") from exc


def generate_image(
    client: Any,
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
) -> bytes:
    """Call OpenRouter image API and return PNG bytes."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={
                "modalities": ["image"],
                "image_config": {"aspect_ratio": aspect_ratio},
            },
        )
    except Exception as exc:
        if is_moderation_error(exc):
            raise ImageModerationError(str(exc)) from exc
        raise

    message = response.choices[0].message
    data_url = _extract_image_data_url(message)
    return _decode_image_data_url(data_url)
