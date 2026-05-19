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


def main():
    config = load_config()
    from ui.app import App

    app = App(config)
    app.run()


if __name__ == "__main__":
    main()
