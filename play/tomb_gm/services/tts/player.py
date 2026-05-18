from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_PLAYER_PROC: subprocess.Popen | None = None


def _player_cmd(path: Path) -> list[str]:
    for name in ("mpv", "ffplay", "start"):
        if name == "start" and sys.platform == "win32":
            return ["cmd", "/c", "start", "/min", "", str(path)]
        if shutil.which(name):
            if name == "ffplay":
                return [name, "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
            if name == "mpv":
                return [name, "--really-quiet", str(path)]
    if sys.platform == "win32":
        return ["powershell", "-c", f'(New-Object Media.SoundPlayer "{path}").PlaySync()']
    return ["xdg-open", str(path)]


def play_file(path: Path) -> dict:
    global _PLAYER_PROC
    stop_playback()
    cmd = _player_cmd(path)
    try:
        _PLAYER_PROC = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"ok": True, "played": str(path), "command": cmd[0]}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def stop_playback() -> None:
    global _PLAYER_PROC
    if _PLAYER_PROC is not None and _PLAYER_PROC.poll() is None:
        _PLAYER_PROC.terminate()
    _PLAYER_PROC = None
