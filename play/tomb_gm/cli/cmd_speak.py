from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import yaml

from tomb_gm.cli.cmd_core import _ctx
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module


def register(sub: argparse._SubParsersAction) -> None:
    speak = sub.add_parser("speak", help="Speak narration via edgeTTS")
    speak.add_argument("--text", default=None, help="Speak this text")
    speak.add_argument("--beat-id", default=None, dest="beat_id", help="Speak a prior beat")
    speak.add_argument("--stop", action="store_true", help="Stop playback")
    speak.set_defaults(handler=handle_speak)


def _tts_settings(cfg_path: Path) -> dict:
    if not cfg_path.is_file():
        return {}
    with cfg_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("tts") or {}


def _speak_text(ctx: CommandContext, text: str) -> dict:
    from tomb_gm.services.tts import play_file, synthesize_to_file

    tts = _tts_settings(ctx.config.workspace / "config.yaml")
    mode = tts.get("mode", "speak_dialogue")
    if mode == "text_only":
        return {"ok": True, "skipped": True, "reason": "text_only"}

    voice = str(tts.get("voice", "en-US-GuyNeural"))
    rate = str(tts.get("rate", "+0%"))
    cache_dir = ctx.config.local_dir / "tts-cache"

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            out = Path(tmp.name)
        synthesize_to_file(text, out, voice=voice, rate=rate, cache_dir=cache_dir)
        play_result = play_file(out)
        return {"ok": play_result.get("ok", False), "text": text[:200], **play_result}
    except ImportError:
        return {"ok": False, "error": "edge_tts not installed; pip install edge-tts"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def handle_speak(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    if args.stop:
        from tomb_gm.services.tts import stop_playback

        stop_playback()
        return {"ok": True, "stopped": True}

    ctx = _ctx(args)
    if args.beat_id:
        row = ctx.conn.execute(
            "SELECT payload_json FROM events WHERE type = 'beat' ORDER BY id DESC"
        ).fetchall()
        brief = ""
        for r in row:
            payload = json.loads(r["payload_json"])
            if payload.get("beat_id") == args.beat_id:
                brief = payload.get("narration_brief") or ""
                break
        if not brief:
            return {"ok": False, "error": f"beat not found: {args.beat_id}"}
        return _speak_text(ctx, brief)

    if args.text:
        return _speak_text(ctx, args.text)

    return {"ok": False, "error": "Provide --text, --beat-id, or --stop"}


add_command_module(register)
