from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from tomb_gm.cli.cmd_narrate import LATEST_NARRATION
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module


def register(sub: argparse._SubParsersAction) -> None:
    speak = sub.add_parser("speak", help="Speak narration via edgeTTS")
    speak.add_argument("--text", default=None, help="Speak a single narrator line")
    speak.add_argument("--scene", default=None, help="Parse GM prose into narrator + NPC voices")
    speak.add_argument("--file", default=None, dest="scene_file", help="Read scene prose from a file")
    speak.add_argument(
        "--last",
        action="store_true",
        help="Speak play/workspace/.local/latest-narration.txt from narrate push",
    )
    speak.add_argument(
        "--lines",
        default=None,
        help="JSON array of {text, voice} lines (overrides scene parsing)",
    )
    speak.add_argument("--beat-id", default=None, dest="beat_id", help="Speak a prior beat")
    speak.add_argument(
        "--mode",
        default=None,
        choices=("speak_all", "speak_dialogue", "text_only"),
        help="Override config tts.mode",
    )
    speak.add_argument("--stop", action="store_true", help="Stop playback")
    speak.set_defaults(handler=handle_speak)


def _tts_settings(cfg_path: Path) -> dict:
    if not cfg_path.is_file():
        return {}
    with cfg_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("tts") or {}


def _read_scene_input(args: argparse.Namespace, ctx: CommandContext | None = None) -> str | None:
    if args.scene_file:
        return Path(args.scene_file).read_text(encoding="utf-8")
    if getattr(args, "last", False):
        if ctx is None:
            return None
        latest = ctx.config.local_dir / LATEST_NARRATION
        if not latest.is_file():
            raise FileNotFoundError(f"missing {latest}; run narrate push first")
        return latest.read_text(encoding="utf-8")
    if args.scene:
        return args.scene
    if args.scene is None and args.text is None and args.beat_id is None and not args.stop:
        if not sys.stdin.isatty():
            return sys.stdin.read()
    return None


def _parse_lines_arg(raw: str | None) -> list[dict[str, str]] | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("--lines must be a JSON array")
    return [{"text": str(item.get("text", "")), "voice": str(item.get("voice", "narrator"))} for item in data]


def handle_speak(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    if args.stop:
        from tomb_gm.services.tts import request_stop, stop_playback

        request_stop()
        stop_playback()
        return {"ok": True, "stopped": True}

    ctx = _ctx(args)
    tts = _tts_settings(ctx.config.workspace / "config.yaml")
    cache_dir = ctx.config.local_dir / "tts-cache"
    mode = args.mode or tts.get("mode", "speak_dialogue")

    try:
        lines = _parse_lines_arg(args.lines)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}

    try:
        scene_text = _read_scene_input(args, ctx)
    except FileNotFoundError as exc:
        return {"ok": False, "error": str(exc)}

    if scene_text or lines:
        from tomb_gm.services.tts import speak_scene

        return speak_scene(
            scene_text or "",
            tts=tts,
            cache_dir=cache_dir,
            mode=mode,
            lines=lines,
        )

    if args.beat_id:
        row = ctx.conn.execute(
            "SELECT payload_json FROM events WHERE type = 'beat' ORDER BY id DESC"
        ).fetchall()
        brief = ""
        beat_lines: list[dict[str, str]] | None = None
        for r in row:
            payload = json.loads(r["payload_json"])
            if payload.get("beat_id") == args.beat_id:
                brief = payload.get("narration_brief") or ""
                beat_lines = payload.get("speak_lines")
                break
        if not brief and not beat_lines:
            return {"ok": False, "error": f"beat not found: {args.beat_id}"}
        from tomb_gm.services.tts import speak_scene

        return speak_scene(
            brief,
            tts=tts,
            cache_dir=cache_dir,
            mode=mode,
            lines=beat_lines,
        )

    if args.text:
        from tomb_gm.services.tts import speak_scene

        return speak_scene(
            args.text,
            tts=tts,
            cache_dir=cache_dir,
            mode=mode,
            lines=[{"text": args.text, "voice": "narrator"}],
        )

    return {
        "ok": False,
        "error": "Provide --scene, --file, --last, --text, --lines, --beat-id, stdin prose, or --stop",
    }


add_command_module(register)
