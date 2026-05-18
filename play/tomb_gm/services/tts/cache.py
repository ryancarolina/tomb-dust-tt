from __future__ import annotations

import hashlib
from pathlib import Path


def cache_key(text: str, voice: str, rate: str) -> str:
    payload = f"{voice}|{rate}|{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


def cache_path(cache_dir: Path, key: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{key}.mp3"
