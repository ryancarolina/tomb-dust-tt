from __future__ import annotations

from pathlib import Path

from tomb_gm.cli.cmd_narrate import LATEST_NARRATION, handle_push


def test_narrate_push_saves_latest(tmp_path: Path, monkeypatch):
    import argparse

    ws = tmp_path / "workspace"
    local = ws / ".local"
    local.mkdir(parents=True)
    (ws / "config.yaml").write_text("tts:\n  mode: text_only\n", encoding="utf-8")

    class FakeConfig:
        workspace = ws
        local_dir = local
        content_root = tmp_path / "build"

    class FakeCtx:
        config = FakeConfig()
        conn = None

    monkeypatch.setattr("tomb_gm.cli.cmd_narrate._ctx", lambda _args: FakeCtx())

    args = argparse.Namespace(
        workspace=str(ws),
        text="Garrick Holt turns from the window. \"Sign.\"",
        file=None,
        mode=None,
    )
    result = handle_push(args)
    assert result["ok"] is True
    assert result["skipped"] is True
    latest = local / LATEST_NARRATION
    assert latest.is_file()
    assert "Garrick Holt" in latest.read_text(encoding="utf-8")
