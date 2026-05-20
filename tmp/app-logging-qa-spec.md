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
| `creation_drift` | Narration `[Phase:` / `[Awaiting:` disagrees with engine during creation (`Orchestrator._check_creation_drift`) |
| `creation_step` | `{creation.step, roster_len, awaiting, creation.active}` each creation turn (`Orchestrator._creation_turn` finally) |

### QA suite

- `app/tests/` — orchestrator, creation flow, bridge smoke, mock LLM golden path.
- CI / local gate: pytest app + tomb_gm + validate_content.

---

## Task checklist

- [x] JSONL logger with core event types

**Open work:** [APP-004](backlog/app-004-log-advancedto-on-creation-choice.md)–[APP-005](backlog/app-005-log-engine-status-after-finalize.md), [APP-049](backlog/app-049-create-app-tests-package.md)–[APP-051](backlog/app-051-golden-path-fixture-with-mock-llm.md) in [`tmp/backlog/README.md`](backlog/README.md).

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
| 2026-05-20 | APP-002: `creation_drift` JSONL via `log_creation_drift` + orchestrator drift check |
| 2026-05-20 | APP-003: `creation_step` JSONL via `log_creation_step` + `_creation_turn` finally snapshot |
