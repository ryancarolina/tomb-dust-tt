"""Parse GM chat prose into ordered speak lines for multi-voice TTS."""

from __future__ import annotations

import re
from typing import Any

_QUOTE_RE = re.compile(r'[""]([^""]+)[""]|"([^"]+)"')
_AV_GRID_RE = re.compile(r"\b\d{1,2}-[A-Z](?:-(?:UG-\d+|EP|BV|SK))*\b")
_SKIP_LINE = re.compile(
    r"^(?:"
    r"\s*\{|\s*\"ok\":|\s*\[P\d+\]|\s*\[OOC\]|\s*\[PARTY\]|\s*\[GM\]"
    r"|Session state\b|Beat recorded\b|Awaiting\b"
    r"|Phase\s*$|Location\s*$|Cade\b.*HP\b"
    r"|^\|"
    r"|^---+\s*$"
    r"|^\*\*Campaign:"
    r"|Use \[OOC\]"
    r")",
    re.I,
)
_SPEAKER_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"marshal\s+garrick\s+holt|garrick\s+holt|\bholt(?:'s|\s+turns|\s+points|\s+leans|\s+looks|\s+slides|\s+tap|\s+tightens|\s+expression|\s+hand)\b", re.I), "marshal-garrick-holt"),
    (re.compile(r"\bsergeant\b|\bbreley\s+blue\b", re.I), "breley-sergeant"),
    (re.compile(r"\bpostern\s+clerk\b|\bclerk\b|\bledger\b|\bquill\b", re.I), "postern-clerk"),
]


def _normalize_quotes(text: str) -> str:
    return text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")


def _is_ui_metadata(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if _SKIP_LINE.match(stripped):
        return True
    if re.match(r"^\d{1,2}-[A-Z]\b", stripped) and "HP" not in stripped:
        return True
    if stripped.lower() in {
        "preparation",
        "delve",
        "combat",
        "extraction",
        "surface",
        "underground",
        "player_actions",
    }:
        return True
    return False


def _drop_leading_session_block(text: str) -> str:
    if not re.match(r"^\s*Session state\b", text, re.I):
        return text
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not re.match(r"^\s*Session state\b", lines[i], re.I):
        i += 1
    if i >= len(lines):
        return text
    i += 1
    while i < len(lines):
        line = lines[i].strip()
        if _is_ui_metadata(line) or line.startswith("|"):
            i += 1
            continue
        break
    return "\n".join(lines[i:]).strip()


def _strip_ui(text: str) -> str:
    text = _drop_leading_session_block(text)
    text = re.split(r"\nSession state\b", text, maxsplit=1, flags=re.I)[0]
    text = re.split(r"\n\*\*Campaign:", text, maxsplit=1, flags=re.I)[0]
    text = re.split(r"\n\[P\d+\]", text, maxsplit=1, flags=re.I)[0]
    lines: list[str] = []
    in_table = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            in_table = False
            continue
        if _is_ui_metadata(line):
            in_table = line.startswith("|")
            continue
        if line.startswith("|") or (in_table and line.count("|") >= 2):
            in_table = True
            continue
        if line.startswith("Term") and "Detail" in line:
            in_table = True
            continue
        if _AV_GRID_RE.search(line) and line.count("\t") >= 1:
            continue
        in_table = False
        lines.append(line)
    return "\n".join(lines).strip()


def _infer_voice(context: str, local: str = "") -> str:
    for pattern, voice_id in _SPEAKER_RULES:
        if local and pattern.search(local):
            return voice_id
    window = context[-400:]
    for pattern, voice_id in _SPEAKER_RULES:
        if pattern.search(window):
            return voice_id
    return "npc"


def _split_paragraph(
    para: str,
    context: str,
    current_speaker: str | None = None,
) -> tuple[list[dict[str, str]], str, str | None]:
    lines: list[dict[str, str]] = []
    cursor = 0
    for match in _QUOTE_RE.finditer(para):
        start, end = match.span()
        narration = para[cursor:start].strip(" \t-—")
        if narration:
            lines.append({"text": narration, "voice": "narrator"})
            context = f"{context}\n{narration}"
            speaker = _infer_voice("", narration)
            if speaker != "npc":
                current_speaker = speaker
        quote = match.group(1) or match.group(2) or ""
        quote = quote.strip()
        if quote:
            voice = _infer_voice(context, narration)
            if voice == "npc" and current_speaker:
                voice = current_speaker
            lines.append({"text": quote, "voice": voice})
            if voice != "narrator" and voice != "npc":
                current_speaker = voice
            context = f"{context}\n{para[:end]}"
        cursor = end
    tail = para[cursor:].strip(" \t-—")
    if tail:
        lines.append({"text": tail, "voice": "narrator"})
        context = f"{context}\n{tail}"
        speaker = _infer_voice("", tail)
        if speaker != "npc":
            current_speaker = speaker
    return lines, context, current_speaker


def _strip_brackets(text: str) -> str:
    """Remove all [bracketed] content — status lines, state summaries, etc."""
    return re.sub(r"\[[^\]]*\]", "", text)


def parse_scene(text: str) -> list[dict[str, str]]:
    """Turn GM narration prose into ordered speak lines."""
    cleaned = _strip_ui(_normalize_quotes(text))
    cleaned = _strip_brackets(cleaned)
    if not cleaned:
        return []

    context = ""
    current_speaker: str | None = None
    out: list[dict[str, str]] = []
    for para in re.split(r"\n\s*\n", cleaned):
        para = para.strip()
        if not para:
            continue
        if para.startswith("Roll:") or "→" in para and "natural" in para.lower():
            continue
        chunk, context, current_speaker = _split_paragraph(para, context, current_speaker)
        out.extend(chunk)
    return _merge_adjacent(out)


def _merge_adjacent(lines: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    for line in lines:
        text = line["text"].strip()
        if not text:
            continue
        if merged and merged[-1]["voice"] == line["voice"]:
            merged[-1]["text"] = f"{merged[-1]['text']} {text}"
        else:
            merged.append({"text": text, "voice": line["voice"]})
    return merged


def filter_for_mode(lines: list[dict[str, str]], mode: str) -> list[dict[str, str]]:
    if mode == "text_only":
        return []
    if mode != "speak_dialogue":
        return lines
    last_dialogue_idx = -1
    for i, line in enumerate(lines):
        if line["voice"] != "narrator":
            last_dialogue_idx = i

    filtered: list[dict[str, str]] = []
    opener_done = False
    for i, line in enumerate(lines):
        if line["voice"] != "narrator":
            filtered.append(line)
        elif not opener_done:
            filtered.append(line)
            opener_done = True
        elif i > last_dialogue_idx:
            filtered.append(line)
    return filtered


def lines_from_payload(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        voice = str(item.get("voice") or "narrator")
        out.append({"text": text, "voice": voice})
    return out
