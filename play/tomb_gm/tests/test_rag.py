from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from tomb_gm.cli.cmd_rules import handle_index, handle_search
from tomb_gm.config import BUILD_ROOT, GameplayConfig
from tomb_gm.db.connection import connect, run_migrations
from tomb_gm.services.rag.index import chunk_markdown, index_rules, is_indexed
from tomb_gm.services.rag.search import search_rules


def _temp_config() -> tuple[GameplayConfig, Path]:
    tmp = Path(tempfile.mkdtemp())
    local = tmp / ".local"
    local.mkdir()
    cfg = GameplayConfig(
        workspace=tmp,
        content_root=BUILD_ROOT.resolve(),
        local_dir=local,
    )
    (tmp / "config.yaml").write_text(
        f"content_root: {BUILD_ROOT.resolve().as_posix()}\nlocal_dir: .local\n",
        encoding="utf-8",
    )
    return cfg, cfg.db_path


def test_chunk_markdown_splits_on_h2():
    text = "# Title\n\nIntro.\n\n## Alpha\n\none\n\n## Beta\n\ntwo\n"
    chunks = chunk_markdown(text)
    assert len(chunks) == 3
    assert chunks[0] == ("", "# Title\n\nIntro.")
    assert chunks[1] == ("Alpha", "one")
    assert chunks[2] == ("Beta", "two")


def test_index_and_search_threat_clock_returns_paths():
    cfg, db_path = _temp_config()
    conn = connect(db_path)
    run_migrations(conn)
    stats = index_rules(conn, cfg.content_root)
    assert stats["chunks"] > 0
    assert is_indexed(conn)

    results = search_rules(conn, cfg.content_root, "threat clock", max_results=5)
    paths = [r["path"] for r in results]
    assert paths
    assert any("extraction.md" in p for p in paths)
    for row in results:
        assert row["excerpt"]
        assert "path" in row


def test_search_auto_indexes_on_empty_db():
    cfg, db_path = _temp_config()
    conn = connect(db_path)
    run_migrations(conn)
    assert not is_indexed(conn)

    results = search_rules(conn, cfg.content_root, "threat clock", max_results=3)
    assert is_indexed(conn)
    assert any("extraction.md" in r["path"] for r in results)


def test_rules_cli_handlers():
    cfg, db_path = _temp_config()
    run_migrations(connect(db_path))
    ns = argparse.Namespace(workspace=str(cfg.workspace), query="threat clock", max=5)

    index_out = handle_index(ns, None)
    assert index_out["ok"] is True
    assert index_out["chunks"] > 0

    search_out = handle_search(ns, None)
    assert search_out["ok"] is True
    paths = [r["path"] for r in search_out["results"]]
    assert any("extraction.md" in p for p in paths)

    payload = json.dumps(search_out)
    assert "threat clock" in payload
