from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from tomb_gm.config import GameplayConfig


@dataclass
class CommandContext:
    config: GameplayConfig
    conn: sqlite3.Connection
