"""APP-104: table-driven image pipeline logging tests P01–P11."""

from __future__ import annotations

import base64
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame
import pytest

from gm.image_service import ImageService, _emit_resolve_result
from gm.openrouter_images import generate_image

_PNG_BYTES = b"\x89PNG\r\n\x1a\nmock-image"
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _init_pygame() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((1, 1))


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
    return ImageService(
        workspace=isolated_workspace,
        content_root=_REPO_ROOT / "build",
        **kwargs,
    )


@pytest.fixture
def captured_logs(monkeypatch):
    entries: list[tuple[str, dict]] = []

    def _capture(entry_type, data):
        entries.append((entry_type, data if isinstance(data, dict) else {"raw": data}))

    monkeypatch.setattr("gm.logger.log_entry", _capture)
    return entries


@pytest.fixture
def ui_logs(monkeypatch):
    entries: list[tuple[str, dict]] = []

    def _capture(entry_type, data):
        entries.append((entry_type, data if isinstance(data, dict) else {"raw": data}))

    monkeypatch.setattr("ui.app.log_entry", _capture)
    return entries


@pytest.fixture
def service_logs(monkeypatch):
    entries: list[tuple[str, dict]] = []

    def _capture(entry_type, data):
        entries.append((entry_type, data if isinstance(data, dict) else {"raw": data}))

    monkeypatch.setattr("gm.image_service.log_entry", _capture)
    return entries


@pytest.fixture
def panel_logs(monkeypatch):
    entries: list[tuple[str, dict]] = []

    def _capture(entry_type, data):
        entries.append((entry_type, data if isinstance(data, dict) else {"raw": data}))

    monkeypatch.setattr("ui.panels.illustration.log_entry", _capture)
    return entries


@pytest.fixture
def provider_logs(monkeypatch):
    entries: list[tuple[str, dict]] = []

    def _capture(entry_type, data):
        entries.append((entry_type, data if isinstance(data, dict) else {"raw": data}))

    monkeypatch.setattr("gm.openrouter_images.log_entry", _capture)
    return entries


def _make_app(app_config, ui_logs):
    from ui.app import App

    app = App(app_config)
    app._layout(900, 600)
    return app


# ─── P01 image_bootstrap ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "source",
    ["init_orchestrator", "load_session"],
    ids=["init_orchestrator", "load_session"],
)
def test_p01_image_bootstrap(app_config, ui_logs, source):
    _init_pygame()
    try:
        app = _make_app(app_config, ui_logs)
        status = {
            "active": {"campaign_slug": "camp-a"},
            "party": {"phase": "combat", "site_id": "undercrypt"},
            "combat": {"combatants": [{"monsterId": "grave-ghoul"}]},
        }
        app._log_image_bootstrap(source, status)

        bootstrap = [(t, d) for t, d in ui_logs if t == "image_bootstrap"]
        assert len(bootstrap) == 1
        _, data = bootstrap[0]
        assert data["source"] == source
        assert data["retroactive_request"] is False
        assert data["campaign_slug"] == "camp-a"
        assert data["status_hint"]["phase"] == "combat"
        assert data["status_hint"]["monster_id"] == "grave-ghoul"
        assert data["status_hint"]["site_id"] == "undercrypt"
    finally:
        pygame.quit()


# ─── P02 image_trigger_detect ────────────────────────────────────────────────


def test_p02_image_trigger_detect_null_winner(app_config, ui_logs):
    _init_pygame()
    try:
        app = _make_app(app_config, ui_logs)
        stable_status = {"party": {"mode": "surface", "address": "23-A"}}
        app._orchestrator = MagicMock()
        app._orchestrator.get_status.return_value = stable_status
        app._current_turn_id = 7
        app._prev_engine_status = dict(stable_status)

        app._queue_turn_status(7)

        detect = [(t, d) for t, d in ui_logs if t == "image_trigger_detect"]
        assert len(detect) == 1
        _, data = detect[0]
        assert data["candidates"] == []
        assert data["winner"] is None
        assert data["item_selected"] is False
        assert data["turn_id"] == 7
        assert not any(t == "image_request" for t, _ in ui_logs)
    finally:
        pygame.quit()


# ─── P03 image_request ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "trigger_source",
    ["narration_npc", "status_delta", "character_panel"],
)
def test_p03_image_request_trigger_sources(app_config, ui_logs, trigger_source, monkeypatch):
    _init_pygame()
    try:
        app = _make_app(app_config, ui_logs)
        mock_orch = MagicMock()
        mock_orch.get_status.return_value = {"active": {"campaign_slug": "camp-a"}}
        app._orchestrator = mock_orch
        app._images_enabled = True
        app._illustration_trigger_source = trigger_source

        mock_service = MagicMock()
        mock_service.resolve.return_value = None
        app._image_service = mock_service

        class _SyncThread:
            def __init__(self, target=None, kwargs=None, daemon=None):
                self._target = target
                self._kwargs = kwargs or {}

            def start(self):
                if self._target:
                    self._target(**self._kwargs)

        monkeypatch.setattr("ui.app.threading.Thread", _SyncThread)

        app._request_illustration("npc", "isla-brack", "Isla Brack")

        requests = [(t, d) for t, d in ui_logs if t == "image_request"]
        assert len(requests) == 1
        _, data = requests[0]
        assert data["entity_type"] == "npc"
        assert data["entity_id"] == "isla-brack"
        assert data["trigger_source"] == trigger_source
        assert data["campaign_slug"] == "camp-a"
        assert data["runtime_enabled"] is True
        assert data["async"] is True
    finally:
        pygame.quit()


# ─── P04 image_resolve_result ────────────────────────────────────────────────


def test_p04_image_resolve_result(service_logs):
    _emit_resolve_result(
        campaign_slug="camp-a",
        entity_type="monster",
        entity_id="grave-ghoul",
        path="/cache/grave-ghoul.png",
        source="cache",
        prompt_hash="abc123",
    )

    resolve = [(t, d) for t, d in service_logs if t == "image_resolve_result"]
    assert len(resolve) == 1
    _, data = resolve[0]
    assert data["campaign_slug"] == "camp-a"
    assert data["entity_type"] == "monster"
    assert data["entity_id"] == "grave-ghoul"
    assert data["path"] == "/cache/grave-ghoul.png"
    assert data["source"] == "cache"
    assert data["prompt_hash"] == "abc123"


# ─── P05 image_ui_queue ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "queue_msg,expected_action,extra",
    [
        (
            ("illustration", {"entity_type": "monster", "entity_id": "grave-ghoul", "title": "Ghoul", "loading": True}),
            "loading",
            {"loading": True, "path": None},
        ),
        (
            (
                "illustration",
                {
                    "entity_type": "monster",
                    "entity_id": "grave-ghoul",
                    "title": "Ghoul",
                    "path": "/tmp/ghoul.png",
                    "loading": False,
                },
            ),
            "set",
            {"loading": False, "path": "/tmp/ghoul.png"},
        ),
    ],
    ids=["loading", "set"],
)
def test_p05_image_ui_queue_actions(app_config, ui_logs, queue_msg, expected_action, extra):
    _init_pygame()
    try:
        app = _make_app(app_config, ui_logs)
        app._ui_queue.put(queue_msg)
        app._process_ui_queue()

        ui_queue = [(t, d) for t, d in ui_logs if t == "image_ui_queue"]
        assert len(ui_queue) == 1
        _, data = ui_queue[0]
        assert data["action"] == expected_action
        assert data["entity_type"] == "monster"
        assert data["entity_id"] == "grave-ghoul"
        assert data["loading"] == extra["loading"]
        assert data["path"] == extra["path"]
    finally:
        pygame.quit()


def test_p05_image_ui_queue_clear(app_config, ui_logs):
    _init_pygame()
    try:
        app = _make_app(app_config, ui_logs)
        app._last_illustration_entity_type = "npc"
        app._last_illustration_entity_id = "isla-brack"
        app._ui_queue.put(("illustration_clear", None))
        app._process_ui_queue()

        ui_queue = [(t, d) for t, d in ui_logs if t == "image_ui_queue"]
        assert len(ui_queue) == 1
        _, data = ui_queue[0]
        assert data["action"] == "clear"
        assert data["entity_type"] == "npc"
        assert data["entity_id"] == "isla-brack"
        assert data["path"] is None
        assert data["loading"] is False
    finally:
        pygame.quit()


# ─── P06 image_panel_load ────────────────────────────────────────────────────


def test_p06_image_panel_load_missing_path(tmp_path: Path, panel_logs):
    _init_pygame()
    try:
        from ui.panels.illustration import IllustrationPanel

        default_path = tmp_path / "default.png"
        surf = pygame.Surface((120, 120))
        surf.fill((40, 40, 40))
        pygame.image.save(surf, str(default_path))

        panel = IllustrationPanel(
            pygame.Rect(0, 0, 420, 240),
            default_image_path=default_path,
        )
        missing = tmp_path / "missing.png"
        panel.set_illustration(path=str(missing), title="Missing", loading=False)

        loads = [(t, d) for t, d in panel_logs if t == "image_panel_load"]
        assert len(loads) == 1
        _, data = loads[0]
        assert data["path"] == str(missing)
        assert data["ok"] is False
        assert data["error"]
        assert data["showing_default"] is True
        assert panel._showing_default is True
    finally:
        pygame.quit()


# ─── P07 image_toggle ────────────────────────────────────────────────────────


def test_p07_image_toggle(app_config, ui_logs):
    _init_pygame()
    try:
        app = _make_app(app_config, ui_logs)
        app._images_enabled = True
        app.illustration.set_images_enabled(True)
        app._image_service = MagicMock()

        app._toggle_images_enabled()

        toggles = [(t, d) for t, d in ui_logs if t == "image_toggle"]
        assert len(toggles) == 1
        _, data = toggles[0]
        assert data["enabled"] is False
        assert data["cancelled_in_flight"] is True
        app._image_service.cancel_generation.assert_called_once()
    finally:
        pygame.quit()


# ─── P08 image_gen_cancel ────────────────────────────────────────────────────


def test_p08_image_gen_cancel(isolated_workspace, service_logs):
    service = _service(isolated_workspace)
    assert service._generation_epoch == 0

    service.cancel_generation()

    cancel = [(t, d) for t, d in service_logs if t == "image_gen_cancel"]
    assert len(cancel) == 1
    _, data = cancel[0]
    assert data["generation_epoch"] == 1
    assert service._generation_epoch == 1


# ─── P09 image_gen_stale_callback ────────────────────────────────────────────


def test_p09_image_gen_stale_callback(isolated_workspace, service_logs):
    gate = threading.Event()

    def slow_gen(*args, **kwargs):
        gate.wait(timeout=1.0)
        return _PNG_BYTES

    service = _service(
        isolated_workspace,
        image_generator=slow_gen,
        client_factory=lambda: object(),
        async_generation=True,
    )

    callbacks: list[str | None] = []
    service.resolve(
        "camp-a",
        "monster",
        "grave-ghoul",
        images_enabled=True,
        config=_config(),
        on_complete=callbacks.append,
    )

    service.cancel_generation()
    gate.set()

    deadline = time.time() + 2.0
    while time.time() < deadline:
        if any(t == "image_gen_stale_callback" for t, _ in service_logs):
            break
        time.sleep(0.02)

    stale = [(t, d) for t, d in service_logs if t == "image_gen_stale_callback"]
    assert len(stale) == 1
    _, data = stale[0]
    assert data["expected_epoch"] == 0
    assert data["generation_epoch"] == 1
    assert data["entity_type"] == "monster"
    assert data["entity_id"] == "grave-ghoul"
    assert not any(t == "image_resolve_result" for t, _ in service_logs)
    assert callbacks == []


# ─── P10 image_gen_skipped ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "config_enabled,runtime_enabled,expected_reason",
    [
        (False, True, "config_off"),
        (True, False, "runtime_off"),
        (False, False, "both_off"),
    ],
)
def test_p10_image_gen_skipped_gate_reasons(
    isolated_workspace,
    service_logs,
    config_enabled,
    runtime_enabled,
    expected_reason,
):
    service = _service(
        isolated_workspace,
        image_generator=lambda *args, **kwargs: _PNG_BYTES,
        client_factory=lambda: object(),
    )
    service.resolve(
        "camp-a",
        "monster",
        "grave-ghoul",
        images_enabled=runtime_enabled,
        config=_config(enabled=config_enabled),
    )

    skipped = [(t, d) for t, d in service_logs if t == "image_gen_skipped"]
    assert len(skipped) == 1
    assert skipped[0][1]["reason"] == expected_reason

    resolve = [(t, d) for t, d in service_logs if t == "image_resolve_result"]
    assert len(resolve) == 1
    assert resolve[0][1]["source"] == "skipped"
    assert resolve[0][1]["skip_reason"] == expected_reason
    assert resolve[0][1]["path"] is None


def test_p10_image_gen_skipped_session_cap(isolated_workspace, service_logs):
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

    skipped = [(t, d) for t, d in service_logs if t == "image_gen_skipped"]
    assert len(skipped) == 1
    assert skipped[0][1]["reason"] == "session_cap"

    resolve_skipped = [
        (t, d)
        for t, d in service_logs
        if t == "image_resolve_result" and d.get("skip_reason") == "session_cap"
    ]
    assert len(resolve_skipped) == 1


# ─── P11 image_provider_request ────────────────────────────────────────────


def _mock_client_success():
    data_url = "data:image/png;base64," + base64.b64encode(_PNG_BYTES).decode("ascii")
    message = SimpleNamespace(
        images=[SimpleNamespace(image_url=SimpleNamespace(url=data_url))]
    )
    response = SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class _Completions:
        @staticmethod
        def create(**kwargs):
            return response

    return SimpleNamespace(chat=SimpleNamespace(completions=_Completions()))


def test_p11_image_provider_request_success(provider_logs):
    client = _mock_client_success()
    result = generate_image(
        client,
        model="black-forest-labs/flux.2-klein-4b",
        prompt="A grave ghoul in torchlight.",
        aspect_ratio="1:1",
    )
    assert result == _PNG_BYTES

    provider = [(t, d) for t, d in provider_logs if t == "image_provider_request"]
    assert len(provider) == 1
    _, data = provider[0]
    assert data["model"] == "black-forest-labs/flux.2-klein-4b"
    assert data["aspect_ratio"] == "1:1"
    assert isinstance(data["latency_ms"], int)
    assert data["bytes"] == len(_PNG_BYTES)
    assert "error" not in data


def test_p11_image_provider_request_failure(provider_logs):
    class _Completions:
        @staticmethod
        def create(**kwargs):
            raise RuntimeError("provider timeout")

    client = SimpleNamespace(chat=SimpleNamespace(completions=_Completions()))

    with pytest.raises(RuntimeError, match="provider timeout"):
        generate_image(
            client,
            model="black-forest-labs/flux.2-klein-4b",
            prompt="A grave ghoul in torchlight.",
            aspect_ratio="1:1",
        )

    provider = [(t, d) for t, d in provider_logs if t == "image_provider_request"]
    assert len(provider) == 1
    _, data = provider[0]
    assert data["model"] == "black-forest-labs/flux.2-klein-4b"
    assert data["aspect_ratio"] == "1:1"
    assert isinstance(data["latency_ms"], int)
    assert data["error"] == "provider timeout"
    assert "bytes" not in data
