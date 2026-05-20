from __future__ import annotations


_MALE_HINTS = {
    "he", "him", "his", "man", "boy", "sir", "lord", "king", "prince",
    "marshal", "sergeant", "guard", "soldier", "knight", "brother",
    "father", "clerk", "barkeep", "blacksmith", "merchant",
}
_FEMALE_HINTS = {
    "she", "her", "woman", "girl", "lady", "queen", "princess",
    "priestess", "mother", "sister", "witch", "maiden", "barmaid",
}


def resolve_voice(voice_key: str, tts: dict) -> str:
    narrator = str(tts.get("voice", "en-US-GuyNeural"))
    if voice_key in ("narrator", "gm"):
        return narrator
    npc_voices = tts.get("npc_voices") or {}
    if voice_key in npc_voices:
        return str(npc_voices[voice_key])

    gender = _infer_gender(voice_key)
    if gender == "female":
        return str(tts.get("npc_voice_default_female", tts.get("npc_voice_default", "en-US-JennyNeural")))
    return str(tts.get("npc_voice_default_male", tts.get("npc_voice_default", "en-US-AndrewNeural")))


def _infer_gender(voice_key: str) -> str:
    """Guess gender from the voice key string."""
    lower = voice_key.lower().replace("-", " ")
    words = set(lower.split())
    if words & _FEMALE_HINTS:
        return "female"
    if words & _MALE_HINTS:
        return "male"
    if "female" in lower or "woman" in lower or "she" in lower:
        return "female"
    return "male"
