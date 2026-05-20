# Drift Check: APP-076-swap-default-llm-to-haiku-4-5

**backlog_ticket:** APP-076  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-shell-config-spec.md`](../../../app-shell-config-spec.md) § `config.yaml` keys | no | `llm.model` shipped default `anthropic/claude-haiku-4.5` (L23) matches `app/config.yaml` L3 |
| [`tmp/app-shell-config-spec.md`](../../../app-shell-config-spec.md) changelog | no | **APP-076 done** row dated 2026-05-20 (L79) documents Haiku 4.5 default; APP-046 Flash Lite history preserved (L78) |
| Run `spec.md` R1–R2 | no | Config + spec table + changelog aligned; code-fallback docs unchanged (`anthropic/claude-sonnet-4` when key omitted, L37) |
| Ticket [`app-076-swap-default-llm-to-haiku-4-5.md`](../../app-076-swap-default-llm-to-haiku-4-5.md) | no | All AC checked; status `done`; Closed 2026-05-20 |

## Config ↔ domain spec (`llm.model`)

| Field | `app/config.yaml` | Spec shipped default (L23) | Match |
|-------|-------------------|------------------------------|-------|
| `llm.provider` | `openrouter` | `openrouter` | yes |
| `llm.model` | `anthropic/claude-haiku-4.5` | `anthropic/claude-haiku-4.5` | yes |
| `llm.max_tokens` | `2048` | `2048` | yes |
| `llm.temperature` | `0.8` | `0.8` | yes |

**Out of scope (intentional, not drift):** `Orchestrator` code fallback when `model` key omitted remains `anthropic/claude-sonnet-4` per spec L37 and ticket Non-goals.

## Code paths (read-only trace — no Python edits in APP-076)

| Consumer | Path | Expected behavior | Match |
|----------|------|-------------------|-------|
| Config load | `main.load_config()` → `config["llm"]` | Reads `config.yaml` | yes (unchanged) |
| Orchestrator | `orchestrator.py` L91 `llm_cfg.get("model", …)` | Uses config value | yes |
| UI label | `ui/app.py` L246–247 `Model: {model_name}` | Displays config `llm.model` | yes |
| JSONL | `logger.py` L84–85 `log_llm_request(…, model, …)` | `"model"` in `llm_request` events | yes (unchanged) |

## Ticket AC ↔ evidence

| Acceptance criterion | Result |
|----------------------|--------|
| `app/config.yaml` sets `llm.model` to `anthropic/claude-haiku-4.5` | **PASS** — L3; verified at impl QA + drift re-read |
| `tmp/app-shell-config-spec.md` shipped default + changelog updated | **PASS** — table L23 + changelog L79 |
| Manual smoke: new game → creation tool step → exploration turn | **Human gate** — `human-test-plan.md` TC-1–TC-3; execution pending tester sign-off |
| Session JSONL shows `model: anthropic/claude-haiku-4.5` | **Human gate** — `human-test-plan.md` TC-4; execution pending tester sign-off |

## Tests run (drift stage)

```bash
cd app; python -c "import main"
# exit 0 (no output)
```

| Check | Result |
|-------|--------|
| Import smoke | ✓ |
| `git diff app/` scope | Only `app/config.yaml` (model line) — no orchestrator/UI/logger drift |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file (human ACs noted)
- [x] Domain spec changelog — **APP-076 done** row present
- [x] Spec ↔ config — no drift on `llm.model` shipped default
- [ ] `python tmp/backlog/claim_ticket.py release APP-076 --done` — **orchestrator** (QA drift: not run per subagent scope)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Historical references to `google/gemini-3.1-flash-lite` remain in APP-046 ticket/changelog rows and run artifacts (pre-impl snapshots) — not live config/spec drift.
- OpenRouter model-id availability at runtime not proven at drift QA time; human playtest is the runtime gate per R3/R4.
