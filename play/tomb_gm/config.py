from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_ROOT = REPO_ROOT / "build"
PLAY_ROOT = REPO_ROOT / "play"
DEFAULT_WORKSPACE = PLAY_ROOT / "workspace"


@dataclass(frozen=True)
class GameplayConfig:
    workspace: Path
    content_root: Path
    local_dir: Path
    max_players: int = 4

    @property
    def db_path(self) -> Path:
        return self.local_dir / "memory.db"

    @property
    def active_path(self) -> Path:
        return self.local_dir / "active.json"

    @property
    def campaigns_dir(self) -> Path:
        return self.workspace / "campaigns"


def resolve_workspace(workspace_arg: str | None) -> Path:
    if workspace_arg:
        return Path(workspace_arg).resolve()
    return DEFAULT_WORKSPACE.resolve()


def load_config(workspace: Path) -> GameplayConfig:
    workspace = workspace.resolve()
    config_path = workspace / "config.yaml"
    example_path = workspace / "config.example.yaml"
    if not config_path.exists() and example_path.exists():
        shutil.copy(example_path, config_path)
    data: dict = {}
    if config_path.exists():
        with config_path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    content_rel = data.get("content_root", "../../build")
    content_root = (workspace / content_rel).resolve()
    local_rel = data.get("local_dir", ".local")
    local_dir = (workspace / local_rel).resolve()
    local_dir.mkdir(parents=True, exist_ok=True)
    return GameplayConfig(
        workspace=workspace,
        content_root=content_root,
        local_dir=local_dir,
        max_players=int(data.get("max_players", 4)),
    )
