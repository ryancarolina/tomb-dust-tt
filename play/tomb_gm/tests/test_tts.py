from __future__ import annotations

from pathlib import Path

import pytest

from tomb_gm.services.tts.cache import cache_key, cache_path


def test_cache_key_stable():
    a = cache_key("hello", "en-US-GuyNeural", "+0%")
    b = cache_key("hello", "en-US-GuyNeural", "+0%")
    c = cache_key("other", "en-US-GuyNeural", "+0%")
    assert a == b
    assert a != c


def test_cache_path_writes(tmp_path: Path):
    key = cache_key("test", "v", "+0%")
    p = cache_path(tmp_path, key)
    p.write_bytes(b"\x00")
    assert p.is_file()


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("edge_tts") is None,
    reason="edge-tts not installed",
)
def test_synthesize_creates_file(tmp_path: Path):
    from tomb_gm.services.tts.synth import synthesize_to_file

    out = tmp_path / "out.mp3"
    synthesize_to_file("Test.", out, cache_dir=tmp_path / "cache")
    assert out.stat().st_size > 100
