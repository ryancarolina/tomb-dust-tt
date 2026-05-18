from __future__ import annotations

import asyncio
from pathlib import Path

from tomb_gm.services.tts.cache import cache_key, cache_path


async def _edge_save(text: str, voice: str, rate: str, out_path: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(out_path))


def synthesize_to_file(
    text: str,
    out_path: Path,
    *,
    voice: str = "en-US-GuyNeural",
    rate: str = "+0%",
    cache_dir: Path | None = None,
) -> Path:
    if not text.strip():
        raise ValueError("empty text for TTS")
    if cache_dir is not None:
        key = cache_key(text, voice, rate)
        cached = cache_path(cache_dir, key)
        if cached.is_file():
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(cached.read_bytes())
            return out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_edge_save(text, voice, rate, out_path))
    if cache_dir is not None:
        key = cache_key(text, voice, rate)
        cached = cache_path(cache_dir, key)
        cached.write_bytes(out_path.read_bytes())
    return out_path
