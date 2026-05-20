# Spec: APP-076-swap-default-llm-to-haiku-4-5

**Status:** draft
**backlog_ticket:** APP-076
**ticket_path:** tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md
**domain_spec:** tmp/app-shell-config-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-shell-config-spec.md

## Problem

The shipped default OpenRouter model is `google/gemini-3.1-flash-lite` (documented in APP-046). Playtesting shows weaker tool-call reliability than desired for GM turns. We want a config-only swap to `anthropic/claude-haiku-4.5` — better tool use and narration quality at lower cost than Sonnet 4.5.

## Goals

- Change the **shipped default** `llm.model` string in `app/config.yaml` to `anthropic/claude-haiku-4.5`.
- Sync `tmp/app-shell-config-spec.md` so the keys table and changelog match config (no spec ↔ config drift).
- Verify via manual smoke that the app runs LLM turns without errors and logs the new model id.

## Non-goals

- Per-mode model routing (creation vs exploration vs combat).
- Changing `Orchestrator` code fallback when `model` is omitted (`anthropic/claude-sonnet-4` stays).
- Tuning `max_tokens` or `temperature` unless smoke test fails.
- OpenRouter client, UI, or logger code changes (model flows from config unchanged).

## Requirements

### R1: Shipped config default

**File:** `app/config.yaml`

Set `llm.model` to exactly:

```yaml
anthropic/claude-haiku-4.5
```

Leave `llm.provider`, `max_tokens`, and `temperature` unchanged.

**Acceptance criteria**

- [ ] `app/config.yaml` line `llm.model` is `anthropic/claude-haiku-4.5`.

### R2: Domain spec sync (Dev on close)

**File:** `tmp/app-shell-config-spec.md`

Update:

1. **Shipped default table** — `llm.model` row: change from `google/gemini-3.1-flash-lite` to `anthropic/claude-haiku-4.5`.
2. **Changelog** — dated entry: `APP-076 done: default llm.model → anthropic/claude-haiku-4.5`.

Do not alter code-fallback documentation (`anthropic/claude-sonnet-4` when key omitted).

**Acceptance criteria**

- [ ] Spec table and `config.yaml` agree on shipped default.
- [ ] Changelog entry references APP-076.

### R3: Runtime smoke (manual)

With valid `OPENROUTER_API_KEY` in `app/.env`:

1. Launch `cd app && python main.py` — window opens, no traceback.
2. Start **new game** → complete **one creation step** that triggers a tool call (e.g. name or race choice).
3. Complete **one exploration turn** after creation (or earliest post-creation GM turn available).
4. No LLM/API errors in UI or console.

**Acceptance criteria**

- [ ] Manual smoke passes per steps above.

### R4: JSONL model id

After smoke, inspect latest session log under `app/logs/session-*.jsonl`.

**Acceptance criteria**

- [ ] `llm_request` events include `"model": "anthropic/claude-haiku-4.5"` (via `log_llm_request` → `data.model`).

## Test plan

```bash
# Import smoke (no API key required)
cd app && python -c "import main"

# Config value check (after impl)
grep -E "^\s+model:" app/config.yaml
# Expected: anthropic/claude-haiku-4.5

# Manual (requires OPENROUTER_API_KEY)
cd app && python main.py
# → new game → one creation tool step → one exploration turn

# Log verification (after manual smoke)
grep '"model"' app/logs/session-*.jsonl | tail -5
# Expected: anthropic/claude-haiku-4.5
```

No new pytest required — behavior is config string only; existing import smoke suffices for CI.

## Human playtest hints (for Stage 7)

- Confirm status bar shows `Model: anthropic/claude-haiku-4.5` (reads `config["llm"]["model"]` in `app/ui/app.py`).
- Watch for transcript/400 errors during creation tool chain; if failures persist, note for APP-031/032 — not blockers for this ticket unless app cannot complete smoke steps.
- Compare one GM narration turn quality informally (optional; not AC).

## Affected paths

Must match ticket **Expected files**:

- `app/config.yaml` — change `llm.model` only
- `tmp/app-shell-config-spec.md` — table + changelog (Dev on ticket close)

**Read-only reference (no edits):**

| Path | Role |
|------|------|
| `app/main.py` | Loads config via `load_config()` |
| `app/gm/orchestrator.py` | `self.model` from config; fallback unchanged |
| `app/gm/openrouter.py` | Passes model to API |
| `app/ui/app.py` | Status bar model label |
| `app/gm/logger.py` | JSONL `llm_request.data.model` |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-076) |
