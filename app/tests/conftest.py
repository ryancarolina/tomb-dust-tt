"""Shared pytest fixtures for app tests — never mutate play/workspace (player saves)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from helpers import APP, BUILD, PLAY, REPO, make_isolated_workspace

for _p in (APP, PLAY, BUILD / "tools"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)


@pytest.fixture
def isolated_workspace(tmp_path: Path) -> Path:
    return make_isolated_workspace(tmp_path)


@pytest.fixture
def bridge(isolated_workspace: Path):
    from gm.bridge import GameBridge

    _bridge = GameBridge(workspace=isolated_workspace)
    _bridge.init()
    yield _bridge
    _bridge.ctx.conn.close()


@pytest.fixture
def app_config() -> dict:
    with open(APP / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@pytest.fixture
def mock_openrouter_client(monkeypatch):
    class _StubCompletions:
        @staticmethod
        def create(**kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Test narration.",
                            tool_calls=None,
                        ),
                        finish_reason="stop",
                    )
                ]
            )

    stub_client = SimpleNamespace(
        chat=SimpleNamespace(completions=_StubCompletions())
    )

    def _stub_factory(*args, **kwargs):
        return stub_client

    monkeypatch.setattr("gm.orchestrator.create_client", _stub_factory)
    yield stub_client


@pytest.fixture
def orchestrator(app_config, isolated_workspace, mock_openrouter_client, monkeypatch):
    """Construct Orchestrator against isolated_workspace via GameBridge factory patch."""

    def _orchestrator_game_bridge(workspace=None):
        from gm.bridge import GameBridge

        return GameBridge(
            workspace=workspace if workspace is not None else isolated_workspace
        )

    monkeypatch.setattr("gm.orchestrator.GameBridge", _orchestrator_game_bridge)

    from gm.orchestrator import Orchestrator

    orch = Orchestrator(app_config)
    assert orch.bridge.ctx.config.workspace.resolve() == isolated_workspace.resolve()
    yield orch
    orch.bridge.ctx.conn.close()
