# Implementation Plan: APP-076-swap-default-llm-to-haiku-4-5

**Status:** draft  
**backlog_ticket:** APP-076  
**ticket_path:** tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md  
**domain_spec:** tmp/app-shell-config-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Config-only chore: change the shipped default `llm.model` string in `app/config.yaml` from `google/gemini-3.1-flash-lite` to `anthropic/claude-haiku-4.5`. Sync `tmp/app-shell-config-spec.md` shipped-default table and changelog so spec ↔ config agree. No Python edits — `main.load_config()` → `Orchestrator.self.model` → OpenRouter + JSONL + UI status bar already flow the config value unchanged.

**Preserve:** `llm.provider`, `max_tokens`, `temperature`, TTS/UI sections, and code fallback `anthropic/claude-sonnet-4` when `model` key omitted (`orchestrator.py` L90).

---

## Exact file edits

### 1. `app/config.yaml` — line 3 only

**Before (L3):**

```yaml
  model: google/gemini-3.1-flash-lite
```

**After (L3):**

```yaml
  model: anthropic/claude-haiku-4.5
```

**Unchanged lines (do not touch):**

| Line | Content |
|------|---------|
| 1–2 | `llm:` / `provider: openrouter` |
| 4–5 | `max_tokens: 2048` / `temperature: 0.8` |
| 7–35 | `tts:` and `ui:` blocks |

---

### 2. `tmp/app-shell-config-spec.md` — table row + changelog

#### 2a. Shipped default table — line 23

**Before (L23):**

```markdown
| `llm` | `model` | string | `google/gemini-3.1-flash-lite` | `Orchestrator.model`, UI model label |
```

**After (L23):**

```markdown
| `llm` | `model` | string | `anthropic/claude-haiku-4.5` | `Orchestrator.model`, UI model label |
```

**Do not edit** L37 code-fallback paragraph (`anthropic/claude-sonnet-4` when key omitted).

#### 2b. Changelog — append row after L78

**After existing APP-046 row, add:**

```markdown
| 2026-05-20 | **APP-076 done:** default `llm.model` → `anthropic/claude-haiku-4.5` (OpenRouter; Haiku 4.5 for tool-call reliability vs Flash Lite) |
```

**Optional (not required by AC):** leave APP-046 changelog row as historical record of the Flash Lite default — do not rewrite L78.

---

## Code-path traces (read-only — no edits)

| Layer | File | Line | Behavior after impl |
|-------|------|------|------------------------|
| Load | `app/main.py` | `load_config()` | Reads `config.yaml` |
| GM | `app/gm/orchestrator.py` | L90 | `self.model = llm_cfg.get("model", "anthropic/claude-sonnet-4")` → Haiku from config |
| API | `app/gm/openrouter.py` | — | Passes `model=` to OpenRouter |
| Log | `app/gm/logger.py` | `log_llm_request` | JSONL `data.model` = config string |
| UI | `app/ui/app.py` | L246–247 | Status bar `Model: anthropic/claude-haiku-4.5` |

---

## Verification (impl + close)

### Automated (no API key)

```powershell
cd app
python -c "import main"
Select-String -Path config.yaml -Pattern '^\s+model:'
# Expected: anthropic/claude-haiku-4.5
```

### Manual smoke (requires `OPENROUTER_API_KEY` in `app/.env`)

1. `cd app && python main.py` — window opens, no traceback.
2. **New game** → one creation step with tool call (e.g. name or race).
3. One post-creation exploration GM turn.
4. Status bar shows `Model: anthropic/claude-haiku-4.5`.
5. Grep latest session log:

```powershell
Select-String -Path logs\session-*.jsonl -Pattern '"model"' | Select-Object -Last 5
# Expected: "model": "anthropic/claude-haiku-4.5"
```

### Ticket close

1. Check ticket AC boxes in `tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md`.
2. `python tmp/backlog/claim_ticket.py release APP-076 --done`
3. **Do not** edit `tmp/app-master-spec.md` (shipped default only; no registry/cross-domain change per qa-spec-pass).

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/config.yaml` | L3: `llm.model` → `anthropic/claude-haiku-4.5` |
| `tmp/app-shell-config-spec.md` | L23 table row; changelog row APP-076 |

**Out of scope (explicit):**

- `app/gm/orchestrator.py` — Sonnet fallback unchanged
- `max_tokens` / `temperature` tuning
- Per-mode model routing
- `app/tests/*` — no new pytest (import smoke only)
- `tmp/app-master-spec.md` — not required
- APP-031/032 transcript fixes — escalate only if smoke fails

---

## Risk / escalation

| Risk | Mitigation |
|------|------------|
| Invalid OpenRouter model id | Smoke/API error surfaces at manual test; revert or fix id |
| Transcript 400 during creation tools | Note for APP-031/032; not in scope unless smoke cannot complete |
| Smoke blocked (no API key) | Document in run `status.md`; impl agent cannot close JSONL AC without key |

---

## AC mapping

| Ticket AC | Plan step |
|-----------|-----------|
| `config.yaml` Haiku default | §1 L3 |
| Spec table + changelog, no drift | §2a L23, §2b |
| Manual smoke | § Verification manual |
| JSONL `model` id | § Verification grep |
