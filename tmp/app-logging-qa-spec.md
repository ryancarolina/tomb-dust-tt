# Spec — App Logging & QA

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/logger.py`, `app/logs/`, `app/tests/`

---

## Spec

### JSONL session logs (`app/logs/session-YYYY-MM-DD.jsonl`)

| Event type | When |
|------------|------|
| `player_input` | Every player line |
| `llm_request` / `llm_response` | Every API call |
| `tool_call` | Every tool name, args, result |
| `gm_narration` | Final text to UI |
| `error` | Exceptions, setup failures |
| `creation_drift` | **(planned)** narration `[Phase:` / `[Awaiting:` disagrees with engine |
| `creation_step` | **(planned)** `{creation.step, roster_len, awaiting}` each creation turn |

### QA suite

- `app/tests/` — orchestrator, creation flow, bridge smoke, mock LLM golden path.
- CI / local gate: pytest app + tomb_gm + validate_content.

---

## Task checklist

- [x] JSONL logger with core event types
- [ ] Log `{creation.step, roster_len, awaiting, creation.active}` after each creation turn
- [ ] Log `creation_drift` when narration phase ≠ engine step
- [ ] Log `advanced_to` on every successful `_execute_creation_choice`
- [ ] Log engine `status()` snapshot after `character_create` / finalize
- [ ] Create `app/tests/` package + conftest
- [ ] CI workflow or documented local gate (see Tests below)
- [ ] Golden path fixture: mock LLM creation → enter undercrypt → one beat

---

## Tests (this spec owns the gate commands)

```bash
python -m pytest app/tests -q
python -m pytest play/tomb_gm/tests -q
python build/tools/validate_content.py
python -m tomb_gm --workspace play/workspace check
```

**App smoke:** `cd app && python main.py` → `new game` → complete creation → one surface beat → save → resume.

**Done when:**

- CI fails if creation completes without roster or if `validate_content` errors.
- Golden path runs headless without OpenRouter key.

---

## Known issues (from log review)

| Session | Issue |
|---------|-------|
| 2026-05-20 Dumpy | PRE_DELVE UI, empty roster, no JSONL errors (LLM narrated only) |
| 2026-05-19 | Creation step order; delve/combat tool failures |
| 2026-05-18 | SQLite thread; Google 400 malformed transcript |

---

## File map

| Path | Role |
|------|------|
| `gm/logger.py` | Log writers |
| `logs/*.jsonl` | Session transcripts (local) |
| `tests/` | App test package (to create) |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged sync-logging + regression-suite content |
