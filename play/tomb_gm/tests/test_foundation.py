from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PLAY = REPO / "play"
WORKSPACE = PLAY / "workspace"


def _run(*args: str) -> dict:
    import os

    proc = subprocess.run(
        [sys.executable, "-m", "tomb_gm", "--workspace", str(WORKSPACE), *args],
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=os.environ,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(proc.stdout)


def test_init_status_check_suggest():
    active_path = WORKSPACE / ".local" / "active.json"
    if active_path.exists():
        active_path.unlink()
    out = _run("init")
    assert out["ok"] is True
    assert out["schema_version"] >= 1
    st = _run("status")
    assert st["ok"] is True
    assert st["awaiting"] == "SETUP"
    chk = _run("check")
    assert "blocked" in chk
    sug = _run("suggest")
    assert sug["ok"] is True
