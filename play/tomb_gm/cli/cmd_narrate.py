from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from tomb_gm.cli.cmd_core import _ctx
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module

LATEST_NARRATION = "latest-narration.txt"


def register(sub: argparse._SubParsersAction) -> None:
    narrate = sub.add_parser("narrate", help="Save GM narration and speak via edgeTTS")
    narrate_sub = narrate.add_subparsers(dest="narrate_command", required=True)

    push = narrate_sub.add_parser(
        "push",
        help="Write latest narration and play narrator + NPC voices",
    )
    push.add_argument("--text", default=None, help="Narration prose to speak")
    push.add_argument("--file", default=None, help="Read narration prose from a file")
    push.add_argument(
        "--mode",
        default=None,
        choices=("speak_all", "speak_dialogue", "text_only"),
        help="Override config tts.mode",
    )
    push.set_defaults(handler=handle_push)


def _tts_settings(cfg_path: Path) -> dict:
    if not cfg_path.is_file():
        return {}
    with cfg_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("tts") or {}


def _read_narration(args: argparse.Namespace) -> str | None:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def handle_push(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    text = _read_narration(args)
    if not text or not text.strip():
        return {"ok": False, "error": "Provide --text, --file, or pipe narration on stdin"}

    latest = ctx.config.local_dir / LATEST_NARRATION
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(text, encoding="utf-8")

    tts = _tts_settings(ctx.config.workspace / "config.yaml")
    mode = args.mode or tts.get("mode", "speak_dialogue")
    if mode == "text_only":
        return {
            "ok": True,
            "skipped": True,
            "reason": "text_only",
            "saved_to": str(latest),
        }

    from tomb_gm.services.tts import speak_scene

    result = speak_scene(
        text,
        tts=tts,
        cache_dir=ctx.config.local_dir / "tts-cache",
        mode=mode,
    )
    result["saved_to"] = str(latest)
    return result


add_command_module(register)
