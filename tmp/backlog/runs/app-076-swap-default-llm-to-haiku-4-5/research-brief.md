# Research Brief: APP-076-swap-default-llm-to-haiku-4-5

**Date:** 2026-05-20
**Question:** Where is the default LLM defined, how does it flow to API/UI/logs, and what must change to swap Gemini 3.1 Flash Lite → Claude Haiku 4.5?

**backlog_ticket:** APP-076
**ticket_path:** tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md
**domain_spec:** tmp/app-shell-config-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket links **Shell & config** domain spec (`tmp/app-shell-config-spec.md`), which owns `app/config.yaml`, `main.py`, and documents `llm.model` shipped defaults. No new domain spec required.

## Summary

The shipped default OpenRouter model lives in `app/config.yaml` (`llm.model`). `main.load_config()` loads it at startup; `Orchestrator` sets `self.model` and passes it to every `chat_completion()` call. Session JSONL logs record that string via `log_llm_request`. The PyGame status bar shows the same config value. Swapping to `anthropic/claude-haiku-4.5` requires editing `config.yaml` and syncing `tmp/app-shell-config-spec.md`. No orchestrator/UI/logger code changes needed. Code fallback if `model` is omitted remains `anthropic/claude-sonnet-4` (out of scope).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Config file | `app/config.yaml` | **Change:** `llm.model` line 3 |
| Config load | `app/main.py` | `yaml.safe_load`; no defaults in code |
| Model consumer | `app/gm/orchestrator.py` | `self.model = llm_cfg.get("model", "anthropic/claude-sonnet-4")` |
| OpenRouter client | `app/gm/openrouter.py` | Model param only |
| UI label | `app/ui/app.py` | `Model: {config["llm"]["model"]}` |
| Logging | `app/gm/logger.py` | JSONL `llm_request` → `data.model` |
| Spec | `tmp/app-shell-config-spec.md` | Shipped default table + changelog |

## Acceptance criteria mapping

| AC | Implementation locus | Verification |
|----|----------------------|--------------|
| `config.yaml` → Haiku 4.5 | `app/config.yaml` | File diff |
| Spec sync | `tmp/app-shell-config-spec.md` | Table + changelog |
| Manual smoke | PyGame | Human playtest |
| JSONL model id | `app/logs/session-*.jsonl` | Grep after smoke |

## Risks

- Tool/transcript issues may persist (APP-031/032).
- Haiku costs more than Flash Lite but less than Sonnet.
- Omitted `model` key still falls back to Sonnet 4 in code.
