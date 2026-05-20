# QA PASS: Implementation

**Task:** APP-076-swap-default-llm-to-haiku-4-5  
**backlog_ticket:** APP-076  
**ticket_path:** tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md  
**Round:** 1  
**domain_spec:** `tmp/app-shell-config-spec.md` (table + changelog synced)

## Verdict

**PASS** — config-only default model swap; spec table and changelog match `app/config.yaml`; no out-of-scope `app/` edits; import smoke green.

## Tests run

```text
cd app && python -c "import main"
# exit 0 (no output)
```

| Check | Command / trace | Result |
|-------|-----------------|--------|
| Import smoke | `python -c "import main"` from `app/` | ✓ |
| Config value | `app/config.yaml` L3 `model: anthropic/claude-haiku-4.5` | ✓ |
| Spec table | `llm.model` shipped default `anthropic/claude-haiku-4.5` (L23) | ✓ |
| Spec changelog | APP-076 entry dated 2026-05-20 (L79) | ✓ |
| Code fallback unchanged | Spec L37 still `anthropic/claude-sonnet-4` when key omitted | ✓ |

## Ticket AC → evidence

| Ticket AC | Evidence | QA result |
|-----------|----------|-----------|
| `app/config.yaml` sets `llm.model` to `anthropic/claude-haiku-4.5` | File L3; `git diff app/config.yaml` single-line model change | ✓ (code review) |
| `tmp/app-shell-config-spec.md` shipped default + changelog updated | Table L23 + changelog L79; diff matches config | ✓ (code review) |
| Manual smoke: new game → creation tool step → exploration turn | Requires `OPENROUTER_API_KEY` + live PyGame | ☐ deferred — human Stage 7 |
| Session JSONL shows `model: anthropic/claude-haiku-4.5` | Depends on manual smoke + `app/logs/session-*.jsonl` | ☐ deferred — human Stage 7 |

## Spec requirements (run spec)

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | `llm.model` exactly `anthropic/claude-haiku-4.5` | `config.yaml` L3; provider/max_tokens/temperature unchanged | ✓ |
| **R2** | Spec table + APP-076 changelog | Diff: table row + one changelog line only in spec file | ✓ |
| **R2** | Code fallback docs unchanged | Sonnet-4 fallback still documented L37 | ✓ |
| **R3** | Manual runtime smoke | Not run in QA impl review | ☐ human |
| **R4** | JSONL model id | Not run in QA impl review | ☐ human |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/config.yaml` | `llm.model` Flash Lite → Haiku 4.5 only | ✓ |
| `tmp/app-shell-config-spec.md` | Table default + APP-076 changelog row | ✓ |

**`app/` scope:** `git diff app/` touches **only** `app/config.yaml` — no orchestrator, bridge, UI, or logger edits.

**Repo working tree:** Other modified paths exist in the broader branch (backlog, `.cursor/`, unrelated specs) — **not** part of APP-076 impl; no scope violation for this ticket’s Expected files.

## Non-goals respected

- No `Orchestrator` / OpenRouter / UI / logger code changes.
- `max_tokens` (2048) and `temperature` (0.8) unchanged.
- Per-mode routing not introduced.

## Handoff

**Ready for:** Stage 6 drift check; human playtest for manual smoke + JSONL AC; then `release APP-076 --done`.

**Human gate:** TC from run `spec.md` R3/R4 — status bar model label, creation tool turn, exploration turn, grep `"model"` in latest `app/logs/session-*.jsonl`.
