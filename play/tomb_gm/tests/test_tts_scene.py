from __future__ import annotations

from tomb_gm.services.tts.scene import filter_for_mode, parse_scene
from tomb_gm.services.tts.voices import resolve_voice


HOLT_SCENE = """
The postern clerk doesn't look up from his ledger. "Marshal's hours are for licensed delvers. Fee's twenty-five gold. Next."

You hold the counter anyway — undercrypt, seal-ring, REG-1172. His quill stops.

A sergeant in Breley blue has been leaning on the doorframe. "Holt's word on the crypt is bring the ring or don't waste his time." He eyes your empty pouch, then your tools. "He'll see you. Don't make him regret it."

Marshal's office — maps, a rack of cold iron, one chair that's seen too many bad reports. Garrick Holt turns from the window. Burn-scarred left hand on the sill. He does not offer a seat.

"You want coin." Not a question. "My brother died in 32-C-UG-1. Hollow knights still walk it."
"""


def test_parse_scene_splits_voices():
    lines = parse_scene(HOLT_SCENE)
    voices = [line["voice"] for line in lines]
    assert "postern-clerk" in voices
    assert "breley-sergeant" in voices
    assert "marshal-garrick-holt" in voices
    assert "narrator" in voices
    holt_quotes = [line for line in lines if line["voice"] == "marshal-garrick-holt"]
    assert any("You want coin" in line["text"] for line in holt_quotes)


def test_parse_scene_skips_prompts_and_tables():
    text = """
Session state

Phase
preparation
Location
32-C Breley Keep (surface)

[P1] Sign the contract?

Garrick Holt turns from the window. "Sign."
"""
    lines = parse_scene(text)
    assert len(lines) == 2
    assert lines[-1]["voice"] == "marshal-garrick-holt"
    assert all("[P1]" not in line["text"] for line in lines)


def test_filter_speak_dialogue_keeps_opener_and_quotes():
    lines = parse_scene(HOLT_SCENE)
    filtered = filter_for_mode(lines, "speak_dialogue")
    assert filtered[0]["voice"] == "narrator"
    has_npc = any(line["voice"] != "narrator" for line in filtered)
    assert has_npc
    narrator_between = [
        line for i, line in enumerate(filtered)
        if line["voice"] == "narrator" and 0 < i < len(filtered) - 1
    ]
    for n in narrator_between:
        assert len(n["text"].split()) >= 20


def test_resolve_voice_uses_npc_map():
    tts = {
        "voice": "en-US-GuyNeural",
        "npc_voices": {"marshal-garrick-holt": "en-US-SteffanNeural"},
        "npc_voice_default": "en-US-JennyNeural",
    }
    assert resolve_voice("narrator", tts) == "en-US-GuyNeural"
    assert resolve_voice("marshal-garrick-holt", tts) == "en-US-SteffanNeural"
    assert resolve_voice("npc", tts) == "en-US-JennyNeural"


def test_parse_scene_strips_inline_status_tags_for_tts():
    text = (
        "The clerk stamps the form. Location: 32-C Breley Keep. "
        "Phase: preparation. Awaiting: EQUIPMENT_CONFIRM.\n"
        '"Sign here," she says.'
    )
    lines = parse_scene(text)
    combined = " ".join(line["text"] for line in lines)
    assert "Location:" not in combined
    assert "Phase:" not in combined
    assert "Awaiting:" not in combined
    assert "Sign here" in combined
