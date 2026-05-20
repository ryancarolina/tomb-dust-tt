"""Ensure tests cannot wipe play/workspace."""

from __future__ import annotations

import pytest

from tomb_gm.config import DEFAULT_WORKSPACE, load_config
from tomb_gm.db.connection import connect
from tomb_gm.domain.session import start_session


def test_start_session_refuses_play_workspace_under_pytest():
    cfg = load_config(DEFAULT_WORKSPACE)
    conn = connect(cfg.db_path)
    try:
        with pytest.raises(RuntimeError, match="play/workspace"):
            start_session(conn, cfg, "salt-road")
    finally:
        conn.close()
