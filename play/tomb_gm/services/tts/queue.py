from __future__ import annotations

import tempfile
from pathlib import Path

from tomb_gm.services.tts.player import play_file_blocking, stop_playback
from tomb_gm.services.tts.scene import filter_for_mode, lines_from_payload, parse_scene
from tomb_gm.services.tts.synth import synthesize_to_file
from tomb_gm.services.tts.voices import resolve_voice

_STOP_REQUESTED = False


def request_stop() -> None:
    global _STOP_REQUESTED
    _STOP_REQUESTED = True
    stop_playback()


def speak_scene(
    text: str,
    *,
    tts: dict,
    cache_dir: Path,
    mode: str | None = None,
    lines: list[dict[str, str]] | None = None,
) -> dict:
    global _STOP_REQUESTED
    _STOP_REQUESTED = False

    speak_mode = mode or str(tts.get("mode", "speak_dialogue"))
    if speak_mode == "text_only":
        return {"ok": True, "skipped": True, "reason": "text_only"}

    ordered = lines_from_payload(lines) if lines else parse_scene(text)
    ordered = filter_for_mode(ordered, speak_mode)
    if not ordered:
        return {"ok": False, "error": "no speakable lines after filtering"}

    rate = str(tts.get("rate", "+0%"))
    played: list[dict[str, str]] = []
    temp_paths: list[Path] = []

    narrator_voice = str(tts.get("voice", "en-US-GuyNeural"))

    try:
        for line in ordered:
            if _STOP_REQUESTED:
                return {"ok": True, "stopped": True, "played": played, "line_count": len(played)}
            voice_key = line.get("voice", "narrator")
            voice = resolve_voice(voice_key, tts)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                out = Path(tmp.name)
            temp_paths.append(out)
            try:
                synthesize_to_file(line["text"], out, voice=voice, rate=rate, cache_dir=cache_dir)
            except Exception:
                if voice != narrator_voice:
                    synthesize_to_file(line["text"], out, voice=narrator_voice, rate=rate, cache_dir=cache_dir)
                    voice = narrator_voice
                else:
                    raise
            result = play_file_blocking(out)
            if not result.get("ok"):
                return {"ok": False, "error": result.get("error", "playback failed"), "played": played}
            played.append({"text": line["text"][:120], "voice": voice_key, "edge_voice": voice})
        return {"ok": True, "played": played, "line_count": len(played), "mode": speak_mode}
    except ImportError:
        return {"ok": False, "error": "edge_tts not installed; pip install edge-tts"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "played": played}
    finally:
        for path in temp_paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
