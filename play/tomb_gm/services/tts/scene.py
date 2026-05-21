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
_FEMALE_PATTERNS = re.compile(
    r"\bshe\s+(?:says|whispers|hisses|murmurs|calls|replies|speaks|asks|snaps|growls)"
    r"|\bwoman\b|\bgirl\b|\blady\b|\bpriestess\b|\bmaiden\b|\bwitch\b|\bmother\b|\bsister\b"
    r"|\bher\s+(?:voice|eyes|lips|hand|face)\b",
    re.I,
)


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


def _infer_voice_from_rules(text: str) -> str | None:
    """Check if text matches any known speaker rule. Returns None if no match."""
    for pattern, voice_id in _SPEAKER_RULES:
        if pattern.search(text):
            return voice_id
    return None


def _infer_voice(context: str, local: str, current_speaker: str | None) -> str:
    """Determine who is speaking. Uses rules, then scene context, then current speaker."""
    if local:
        match = _infer_voice_from_rules(local)
        if match:
            return match
    window = context[-600:]
    match = _infer_voice_from_rules(window)
    if match:
        return match
    if current_speaker:
        return current_speaker
    combined = (local or "") + " " + window
    if _FEMALE_PATTERNS.search(combined):
        return "npc-female"
    return "npc-male"


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
            detected = _infer_voice_from_rules(narration)
            if detected:
                current_speaker = detected
        quote = match.group(1) or match.group(2) or ""
        quote = quote.strip()
        if quote:
            voice = _infer_voice(context, narration or "", current_speaker)
            lines.append({"text": quote, "voice": voice})
            if voice != "narrator":
                current_speaker = voice
            context = f"{context}\n{para[:end]}"
        cursor = end
    tail = para[cursor:].strip(" \t-—")
    if tail:
        lines.append({"text": tail, "voice": "narrator"})
        context = f"{context}\n{tail}"
        detected = _infer_voice_from_rules(tail)
        if detected:
            current_speaker = detected
    return lines, context, current_speaker


_STATUS_AWAITING_RE = re.compile(r"\bAwaiting:\s*\S+", re.IGNORECASE)
_STATUS_LOCATION_RE = re.compile(r"\bLocation:\s*[^\n|]+", re.IGNORECASE)
_STATUS_PHASE_RE = re.compile(r"\bPhase:\s*[^\n|]+", re.IGNORECASE)


def _strip_status_tags(text: str) -> str:
    """Remove inline status tokens before TTS (APP-041). Panel display uses raw text."""
    if not (text or "").strip():
        return ""
    cleaned = _STATUS_AWAITING_RE.sub("", text)
    cleaned = _STATUS_LOCATION_RE.sub("", cleaned)
    cleaned = _STATUS_PHASE_RE.sub("", cleaned)
    return re.sub(r"[ \t]{2,}", " ", cleaned).strip()


def _strip_brackets(text: str) -> str:
    """Remove all [bracketed] content — status lines, state summaries, etc."""
    return re.sub(r"\[[^\]]*\]", "", text)


def _strip_markup(text: str) -> str:
    """Remove markdown formatting characters (* _ # `) that should not be spoken."""
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"_+", " ", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    return text


def parse_scene(text: str) -> list[dict[str, str]]:
    """Turn GM narration prose into ordered speak lines."""
    cleaned = _strip_ui(_normalize_quotes(text))
    cleaned = _strip_status_tags(cleaned)
    cleaned = _strip_brackets(cleaned)
    cleaned = _strip_markup(cleaned)
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


_SHORT_NARRATOR_THRESHOLD = 12


def _merge_adjacent(lines: list[dict[str, str]]) -> list[dict[str, str]]:
    """Merge adjacent same-voice lines AND absorb short narrator fragments into NPC lines."""
    merged: list[dict[str, str]] = []
    for line in lines:
        text = line["text"].strip()
        if not text:
            continue
        if merged and merged[-1]["voice"] == line["voice"]:
            merged[-1]["text"] = f"{merged[-1]['text']} {text}"
        else:
            merged.append({"text": text, "voice": line["voice"]})

    return _absorb_short_fragments(merged)


def _absorb_short_fragments(lines: list[dict[str, str]]) -> list[dict[str, str]]:
    """Remove short narrator lines sandwiched between NPC dialogue.

    A narrator line under ~12 words that sits between two NPC lines (same voice)
    is a stage direction like "he says" or "He leans forward," — not worth
    voicing separately. Absorb it into the next NPC line as a pause.
    """
    if len(lines) < 3:
        return lines

    result: list[dict[str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            line["voice"] == "narrator"
            and len(line["text"].split()) <= _SHORT_NARRATOR_THRESHOLD
            and i > 0
            and i < len(lines) - 1
            and result
            and result[-1]["voice"] != "narrator"
            and lines[i + 1]["voice"] != "narrator"
        ):
            i += 1
            continue
        result.append(line)
        i += 1
    return result


_LONG_NARRATOR_THRESHOLD = 20


def filter_for_mode(lines: list[dict[str, str]], mode: str) -> list[dict[str, str]]:
    """Filter lines based on TTS mode.

    speak_all: everything
    speak_dialogue: opener narration + all NPC dialogue + significant narrator
                    lines (>20 words) between dialogue + closing narration
    text_only: nothing
    """
    if mode == "text_only":
        return []
    if mode != "speak_dialogue":
        return lines

    if not lines:
        return []

    first_dialogue_idx = -1
    last_dialogue_idx = -1
    for i, line in enumerate(lines):
        if line["voice"] != "narrator":
            if first_dialogue_idx == -1:
                first_dialogue_idx = i
            last_dialogue_idx = i

    filtered: list[dict[str, str]] = []
    for i, line in enumerate(lines):
        if line["voice"] != "narrator":
            filtered.append(line)
        elif i < first_dialogue_idx:
            filtered.append(line)
        elif i > last_dialogue_idx:
            filtered.append(line)
        elif len(line["text"].split()) >= _LONG_NARRATOR_THRESHOLD:
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
