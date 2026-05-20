# Reflection: Dev — APP-076 WS1

**backlog_ticket:** APP-076  
**workstream:** WS1 — Default LLM model swap + spec sync  
**date:** 2026-05-20

## What shipped

- Changed `app/config.yaml` L3: `llm.model` from `google/gemini-3.1-flash-lite` to `anthropic/claude-haiku-4.5`.
- Updated `tmp/app-shell-config-spec.md` shipped-default table row (L23) to match config.
- Appended APP-076 changelog entry dated 2026-05-20; left APP-046 row intact as history.
- Wrote `workstreams.md` (single WS1 stream).

## Design choices

- **Config-only change** — no Python edits; existing `load_config()` → `Orchestrator.model` → OpenRouter/JSONL/UI path flows the new string unchanged.
- **Spec sync in same stream** — table + changelog updated together with config to close pre-impl drift (both previously Flash Lite).
- **Preserved** — `llm.provider`, `max_tokens`, `temperature`, TTS/UI blocks; code fallback `anthropic/claude-sonnet-4` in spec L37.

## Verification

```powershell
Set-Location app; python -c "import main"   # passed (exit 0)
Select-String -Path config.yaml -Pattern '^\s+model:'  # anthropic/claude-haiku-4.5
```

Manual smoke (new game → creation tool step → exploration turn) and JSONL `"model"` grep remain human-gated — require `OPENROUTER_API_KEY`.

## Handoff

- **QA impl:** Confirm config/spec diff matches plan §1–2; no stray file edits.
- **Release:** Manual smoke + JSONL AC; then ticket AC checkboxes and `release APP-076 --done`.
- **Escalate if:** OpenRouter returns model-not-found or persistent 400s during creation tools (APP-031/032).

## Risks / notes

- OpenRouter model id not catalog-verified at impl time; manual smoke is the gate per qa-plan-pass note 1.
- Import smoke alone cannot close R3/R4 AC.
