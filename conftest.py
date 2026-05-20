"""Pytest: resolve `tools` package from build/tools/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
PLAY_DIR = ROOT / "play"
APP_DIR = ROOT / "app"
for path in (BUILD_DIR, PLAY_DIR, APP_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
