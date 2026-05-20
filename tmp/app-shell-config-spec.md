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

---

## Task checklist

- [x] `main.py` entry: init bridge, orchestrator, UI app loop
- [x] `config.yaml` model + TTS + layout keys
- [ ] Startup health: log workspace path, model id, content_root pin
- [ ] Fail fast if `build/` or `play/tomb_gm` not importable
- [ ] Document all config keys in this spec when added

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
