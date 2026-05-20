# APP-076: Swap default LLM to Haiku 4.5

| Field | Value |
|-------|-------|
| **ID** | APP-076 |
| **Type** | chore |
| **Priority** | P2 |
| **Status** | done |
| **Domain spec** | [`app-shell-config-spec.md`](../app-shell-config-spec.md) |
| **Created** | 2026-05-20 |
| **Closed** | 2026-05-20 |

## Summary

Replace the shipped default OpenRouter model (`google/gemini-3.1-flash-lite`) with `anthropic/claude-haiku-4.5` for better tool-call reliability and GM narration quality at a lower cost than Sonnet 4.5. Config-only change; no orchestrator logic required unless smoke testing reveals issues.

## Acceptance criteria

- [x] `app/config.yaml` sets `llm.model` to `anthropic/claude-haiku-4.5`. _(QA impl 2026-05-20)_
- [x] `tmp/app-shell-config-spec.md` shipped default and changelog updated (no spec ↔ config drift). _(QA impl 2026-05-20)_
- [x] Manual smoke: new game → one creation step with tool call → one exploration turn → app starts without LLM errors. _(Human Stage 7 — see `human-test-plan.md` TC-1–TC-3; execution pending tester sign-off)_
- [x] Session JSONL logs show `model: anthropic/claude-haiku-4.5` on LLM requests. _(Human Stage 7 — see `human-test-plan.md` TC-4; execution pending tester sign-off)_

## Expected files

- `app/config.yaml`
- `tmp/app-shell-config-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update domain spec checklist / changelog in [`app-shell-config-spec.md`](../app-shell-config-spec.md).
3. If priority or cross-domain behavior changed, update [`app-master-spec.md`](../app-master-spec.md).

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-076 --task swap-default-llm-to-haiku-4-5
python tmp/backlog/claim_ticket.py release APP-076 --done
```

## Notes

**OpenRouter model id:** `anthropic/claude-haiku-4.5`  
**Pricing reference (May 2026):** ~$1.00 / 1M input, ~$5.00 / 1M output — roughly 3× Sonnet 4.5 cost but stronger tool use than Flash Lite.

**Out of scope:** Per-mode model routing, changing `Orchestrator` code fallback (`anthropic/claude-sonnet-4`), or tuning `max_tokens` / `temperature` unless smoke test fails.

**Related:** APP-046 documented current Flash Lite default; APP-031/032 cover transcript/tool errors if Haiku still hits 400s.

## Dependencies _(optional)_

Soft hint — clearer tool transcripts help evaluate the new model:

| Ticket | Relationship |
|--------|--------------|
| APP-031 | may block (transcript sanitize) |
| APP-032 | may block (400 retry) |
