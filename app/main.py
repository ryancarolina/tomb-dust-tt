"""Tomb Dust — PyGame standalone application."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "play"))
sys.path.insert(0, str(ROOT / "build" / "tools"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import yaml

def load_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.yaml"
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _log_startup_health(config: dict) -> None:
    """Emit JSONL startup row before pygame/orchestrator init (APP-044)."""
    from gm.logger import log_entry
    from tomb_gm.config import resolve_workspace, load_config as load_workspace_config

    ws = resolve_workspace(None)
    ws_cfg = load_workspace_config(ws)
    payload: dict = {
        "workspace": str(ws_cfg.workspace.resolve()),
        "content_root": str(ws_cfg.content_root.resolve()),
        "model": (config.get("llm") or {}).get("model"),
    }
    try:
        from tomb_gm.domain.campaign import build_content_pin

        payload["content_pin"] = build_content_pin(ws_cfg.content_root)
    except Exception:
        pass
    log_entry("startup", payload)


def main():
    config = load_config()
    _log_startup_health(config)
    from ui.app import App

    app = App(config)
    app.run()


if __name__ == "__main__":
    main()
