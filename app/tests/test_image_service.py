from __future__ import annotations

import hashlib
from pathlib import Path

from gm.image_cache import ImageCache
from gm.image_prompt_builder import ImagePromptBuilder
from gm.image_service import ImageService
from gm.openrouter_images import ImageModerationError

_PNG_BYTES = b"\x89PNG\r\n\x1a\nmock-image"


def _config(*, enabled: bool = True, max_per_session: int = 30) -> dict:
    return {
        "images": {
            "enabled": enabled,
            "model": "black-forest-labs/flux.2-klein-4b",
            "portrait_aspect_ratio": "1:1",
            "scene_aspect_ratio": "4:3",
            "max_generations_per_session": max_per_session,
        }
    }


def _service(isolated_workspace: Path, **kwargs) -> ImageService:
    root = Path(__file__).resolve().parents[2]
    return ImageService(
        workspace=isolated_workspace,
        content_root=root / "build",
        **kwargs,
    )


def test_resolve_returns_cache_hit_without_provider_call(isolated_workspace, monkeypatch):
    calls = {"count": 0}

    def _generator(*args, **kwargs):
        calls["count"] += 1
        return _PNG_BYTES

    service = _service(isolated_workspace, image_generator=_generator, client_factory=lambda: object())
    builder = ImagePromptBuilder(Path(__file__).resolve().parents[2] / "build")
    prompt = builder.build_prompt("monster", "grave-ghoul")
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    cache = ImageCache(isolated_workspace)
    cache_path = cache.save(
        "camp-a",
        "monster",
        "grave-ghoul",
        image_bytes=_PNG_BYTES,
        sidecar={
            "entity_type": "monster",
            "entity_id": "grave-ghoul",
            "campaign_slug": "camp-a",
            "prompt_hash": prompt_hash,
            "model": "black-forest-labs/flux.2-klein-4b",
            "prompt": prompt,
            "created_at": "2026-05-22T00:00:00Z",
        },
    )

    resolved = service.resolve(
        "camp-a",
        "monster",
        "grave-ghoul",
        images_enabled=True,
        config=_config(),
    )
    assert resolved == str(cache_path)
    assert calls["count"] == 0


def test_resolve_skips_when_images_disabled(isolated_workspace):
    service = _service(
        isolated_workspace,
        image_generator=lambda *args, **kwargs: _PNG_BYTES,
        client_factory=lambda: object(),
    )
    resolved = service.resolve(
        "camp-a",
        "monster",
        "grave-ghoul",
        images_enabled=False,
        config=_config(enabled=True),
    )
    assert resolved is None


def test_resolve_generates_and_writes_sidecar(isolated_workspace):
    service = _service(
        isolated_workspace,
        image_generator=lambda *args, **kwargs: _PNG_BYTES,
        client_factory=lambda: object(),
    )
    resolved = service.resolve(
        "camp-a",
        "monster",
        "grave-ghoul",
        images_enabled=True,
        config=_config(),
    )
    assert resolved is not None
    out = Path(resolved)
    assert out.is_file()
    sidecar = out.with_suffix(".json")
    assert sidecar.is_file()
    data = sidecar.read_text(encoding="utf-8")
    assert '"entity_type": "monster"' in data
    assert '"entity_id": "grave-ghoul"' in data


def test_resolve_enforces_session_cap(isolated_workspace):
    service = _service(
        isolated_workspace,
        image_generator=lambda *args, **kwargs: _PNG_BYTES,
        client_factory=lambda: object(),
    )
    first = service.resolve(
        "camp-a",
        "monster",
        "grave-ghoul",
        images_enabled=True,
        config=_config(max_per_session=1),
    )
    second = service.resolve(
        "camp-a",
        "monster",
        "thornwolf",
        images_enabled=True,
        config=_config(max_per_session=1),
    )
    assert first is not None
    assert second is None


def test_resolve_retries_once_after_moderation(isolated_workspace, monkeypatch):
    events: list[str] = []
    monkeypatch.setattr("gm.image_service.log_entry", lambda event, data: events.append(event))

    calls = {"count": 0}

    def _generator(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ImageModerationError("Content Moderated")
        return _PNG_BYTES

    service = _service(isolated_workspace, image_generator=_generator, client_factory=lambda: object())
    resolved = service.resolve(
        "camp-a",
        "monster",
        "thornwolf",
        images_enabled=True,
        config=_config(),
    )
    assert resolved is not None
    assert calls["count"] == 2
    assert "image_gen_moderated" in events


def test_resolve_seeds_bundled_holt_without_api(isolated_workspace, monkeypatch):
    events: list[str] = []
    monkeypatch.setattr("gm.image_service.log_entry", lambda event, data: events.append(event))

    calls = {"count": 0}

    def _generator(*args, **kwargs):
        calls["count"] += 1
        return _PNG_BYTES

    service = _service(
        isolated_workspace,
        image_generator=_generator,
        client_factory=lambda: object(),
    )
    resolved = service.resolve(
        "salt-road",
        "npc",
        "marshal-garrick-holt",
        images_enabled=False,
        config=_config(enabled=True),
    )
    assert resolved is not None
    assert Path(resolved).is_file()
    assert calls["count"] == 0
    assert "image_gen_bundled_seed" in events

    second = service.resolve(
        "salt-road",
        "npc",
        "marshal-garrick-holt",
        images_enabled=False,
        config=_config(enabled=True),
    )
    assert second == resolved
    assert calls["count"] == 0
    assert "image_gen_cache_hit" in events
