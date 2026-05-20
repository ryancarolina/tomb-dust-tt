# Spec — App Shell & Config

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress (baseline shipped)  
**Owns:** `app/main.py`, `app/config.yaml`, `app/requirements.txt`, `app/.env` (local only)

---

## Spec

- Launch PyGame client from `app/main.py` with `play/` and repo root on `sys.path`.
- Load `config.yaml`: LLM model, TTS mode, window layout, NPC voice map.
- Require `OPENROUTER_API_KEY` in `app/.env` for LLM turns (clear error if missing).
- Dependencies pinned in `requirements.txt` (pygame-ce, openai, edge-tts, python-dotenv, etc.).

### `config.yaml` keys (APP-046)

Loaded by `main.load_config()`; consumed by `Orchestrator` (`llm`) and `App` (`ui`, `tts`). Any OpenRouter model id is valid under `llm.model`.

| Section | Key | Type | Shipped default | Used by |
|---------|-----|------|-----------------|---------|
| `llm` | `provider` | string | `openrouter` | Documentation only today |
| `llm` | `model` | string | `anthropic/claude-haiku-4.5` | `Orchestrator.model`, UI model label |
| `llm` | `max_tokens` | int | `2048` | Main GM turns (`Orchestrator`) |
| `llm` | `temperature` | float | `0.8` | All LLM calls |
| `tts` | `mode` | string | `speak_dialogue` | `speak_all` \| `speak_dialogue` \| `text_only` |
| `tts` | `voice` | string | `en-US-GuyNeural` | Narrator / GM lines |
| `tts` | `rate` | string | `"+0%"` | edge-tts rate |
| `tts` | `npc_voice_default_male` | string | `en-US-AndrewNeural` | NPC fallback |
| `tts` | `npc_voice_default_female` | string | `en-US-JennyNeural` | NPC fallback |
| `tts` | `npc_voices` | map | see `config.yaml` | Per-NPC voice override |
| `ui` | `window_width` | int | `1280` | PyGame window |
| `ui` | `window_height` | int | `800` | PyGame window |
| `ui` | `font_size` | int | `16` | UI font |
| `ui` | `narration_width_ratio` | float | `0.7` | Layout split |

**Code fallbacks** (if a key is omitted): `Orchestrator` uses `model=anthropic/claude-sonnet-4`, `max_tokens=1024`, `temperature=0.8`; `App` uses `tts.mode=speak_dialogue`.

**Secrets:** `OPENROUTER_API_KEY` in `app/.env` (not in `config.yaml`).

---

## Task checklist

- [x] `main.py` entry: init bridge, orchestrator, UI app loop
- [x] `config.yaml` model + TTS + layout keys documented (APP-046)

**Open work:** [APP-044](backlog/app-044-startup-health-logging.md) in [`tmp/backlog/README.md`](backlog/README.md).

---

## Tests

```bash
cd app && python -c "import main"  # import smoke
cd app && python main.py           # manual: window opens
```

- Missing API key → user-visible error, no silent hang.

---

## File map

| File | Role |
|------|------|
| `main.py` | Entry, path setup, orchestrator + UI wiring |
| `config.yaml` | Runtime tuning |
| `requirements.txt` | Pip deps |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; baseline documents existing shell |
| 2026-05-20 | **APP-046 done:** Document all `config.yaml` keys; default `llm.model` → `google/gemini-3.1-flash-lite` (OpenRouter; ~same tier as 2.5 Flash, lower output $) |
| 2026-05-20 | **APP-076 done:** default `llm.model` → `anthropic/claude-haiku-4.5` (OpenRouter; Haiku 4.5 for tool-call reliability vs Flash Lite) |
