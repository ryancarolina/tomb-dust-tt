from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

_PLAYER_PROC: subprocess.Popen | None = None
_MCI_PLAYING = False


def _mci_play_blocking(path: Path) -> dict:
    """Play MP3 on Windows using mciSendString (winmm.dll). No extra deps needed."""
    global _MCI_PLAYING
    import ctypes

    winmm = ctypes.windll.winmm
    mci = winmm.mciSendStringW
    buf = ctypes.create_unicode_buffer(256)

    abs_path = str(path.resolve()).replace("\\", "/")
    alias = "tombgm_tts"

    mci(f'close {alias}', None, 0, 0)
    err = mci(f'open "{abs_path}" type mpegvideo alias {alias}', None, 0, 0)
    if err:
        mci(f'close {alias}', None, 0, 0)
        return {"ok": False, "error": f"mciSendString open failed (code {err})"}

    err = mci(f'play {alias}', None, 0, 0)
    if err:
        mci(f'close {alias}', None, 0, 0)
        return {"ok": False, "error": f"mciSendString play failed (code {err})"}

    _MCI_PLAYING = True
    while _MCI_PLAYING:
        mci(f'status {alias} mode', buf, 255, 0)
        mode = buf.value.strip().lower()
        if mode != "playing":
            break
        time.sleep(0.1)

    mci(f'close {alias}', None, 0, 0)
    _MCI_PLAYING = False
    return {"ok": True, "played": str(path), "command": "mciSendString"}


def _mci_stop() -> None:
    """Stop any MCI playback."""
    global _MCI_PLAYING
    _MCI_PLAYING = False
    if sys.platform == "win32":
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            winmm.mciSendStringW('stop tombgm_tts', None, 0, 0)
            winmm.mciSendStringW('close tombgm_tts', None, 0, 0)
        except Exception:
            pass


def _blocking_player_cmd(path: Path) -> list[str] | None:
    for name in ("mpv", "ffplay"):
        if shutil.which(name):
            if name == "ffplay":
                return [name, "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
            return [name, "--really-quiet", str(path)]
    return None


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
        return ["cmd", "/c", "start", "/min", "", str(path)]
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


def play_file_blocking(path: Path) -> dict:
    global _PLAYER_PROC
    stop_playback()

    if sys.platform == "win32":
        cmd = _blocking_player_cmd(path)
        if cmd is None:
            return _mci_play_blocking(path)
    else:
        cmd = _blocking_player_cmd(path)
        if cmd is None:
            return {"ok": False, "error": "no audio player found (install mpv or ffplay)"}

    try:
        _PLAYER_PROC = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _PLAYER_PROC.wait()
        code = _PLAYER_PROC.returncode
        _PLAYER_PROC = None
        if code not in (0, None):
            return {"ok": False, "error": f"player exited {code}", "command": cmd[0]}
        return {"ok": True, "played": str(path), "command": cmd[0]}
    except OSError as exc:
        _PLAYER_PROC = None
        return {"ok": False, "error": str(exc)}


def stop_playback() -> None:
    global _PLAYER_PROC
    _mci_stop()
    if _PLAYER_PROC is not None and _PLAYER_PROC.poll() is None:
        _PLAYER_PROC.terminate()
    _PLAYER_PROC = None
