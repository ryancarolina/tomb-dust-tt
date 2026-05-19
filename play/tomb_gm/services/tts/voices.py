from __future__ import annotations


def resolve_voice(voice_key: str, tts: dict) -> str:
    narrator = str(tts.get("voice", "en-US-GuyNeural"))
    if voice_key in ("narrator", "gm"):
        return narrator
    npc_voices = tts.get("npc_voices") or {}
    if voice_key in npc_voices:
        return str(npc_voices[voice_key])
    default_npc = str(tts.get("npc_voice_default", "en-US-JennyNeural"))
    return default_npc
