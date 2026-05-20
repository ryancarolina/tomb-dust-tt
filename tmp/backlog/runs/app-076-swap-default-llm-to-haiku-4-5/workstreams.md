# Workstreams: APP-076-swap-default-llm-to-haiku-4-5

**backlog_ticket:** APP-076  
**plan:** [plan.md](plan.md) · **spec:** [spec.md](spec.md) · **domain spec:** [tmp/app-shell-config-spec.md](../../../app-shell-config-spec.md)

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Default LLM model swap + spec sync | — | `app/config.yaml`, `tmp/app-shell-config-spec.md` | L3 Haiku default; spec table L23 + APP-076 changelog; import smoke green |

**Stream count:** 1 — config-only chore; no Python edits.

**Out of workstreams (ticket release):** Manual smoke + JSONL grep (requires `OPENROUTER_API_KEY`); ticket AC checkboxes; `claim_ticket.py release APP-076 --done`.

---

## WS1 — Default LLM model swap + spec sync

**Scope:** Plan §1–2 — change shipped `llm.model` in `app/config.yaml` from `google/gemini-3.1-flash-lite` to `anthropic/claude-haiku-4.5`; sync `tmp/app-shell-config-spec.md` shipped-default table row and append APP-076 changelog entry dated 2026-05-20.

**Requirements covered:** spec R1 (config default), R2 (spec table + changelog, no drift).

### Implementation order (within stream)

| # | Task | File | Plan ref |
|---|------|------|----------|
| 1 | Change `llm.model` value | `app/config.yaml` L3 | §1 |
| 2 | Update shipped-default table row | `tmp/app-shell-config-spec.md` L23 | §2a |
| 3 | Append APP-076 changelog row | `tmp/app-shell-config-spec.md` after L78 | §2b |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Line scope | **Only** `config.yaml` L3 — do not touch `provider`, `max_tokens`, `temperature`, `tts`, or `ui` |
| Code unchanged | No edits to `orchestrator.py`, `openrouter.py`, `main.py`, `app/ui/app.py`, or tests |
| Fallback preserved | Spec L37 code fallback `anthropic/claude-sonnet-4` when key omitted — do not edit |
| History preserved | APP-046 changelog row stays as historical record — append only |
| No master-spec | Do not edit `tmp/app-master-spec.md` |

### Test gates (WS1 done when)

```powershell
cd app
python -c "import main"
Select-String -Path config.yaml -Pattern '^\s+model:'
# Expected: anthropic/claude-haiku-4.5
```

**Expected:** import succeeds; config and spec table both show `anthropic/claude-haiku-4.5`.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-076
ticket: tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md
run-folder: tmp/backlog/runs/app-076-swap-default-llm-to-haiku-4-5/
spec: spec.md | plan: plan.md §1–2 | domain spec: tmp/app-shell-config-spec.md
workstreams: workstreams.md § WS1

Implement WS1 only — config.yaml L3 + app-shell-config-spec.md table L23 + changelog APP-076.
No Python edits; no orchestrator/tests changes.
Run import smoke: cd app && python -c "import main"
Write reflection-dev-impl-ws1.md before return.
```

---

## AC mapping (quick reference)

| AC / spec | WS | Verification |
|-----------|-----|--------------|
| R1 — `config.yaml` Haiku default | WS1 | `Select-String` on L3 |
| R2 — spec table + changelog | WS1 | File diff |
| R3 — manual smoke (creation + exploration) | Release | Human with API key |
| R4 — JSONL `model` id | Release | Post-smoke grep on session logs |
