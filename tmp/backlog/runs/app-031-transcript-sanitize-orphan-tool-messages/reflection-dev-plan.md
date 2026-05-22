# Reflection: Dev plan — APP-031

**Role:** Dev (plan phase)  
**backlog_ticket:** APP-031  
**Artifact:** [plan.md](./plan.md)

## Completed

- Re-read all six `chat_completion` sites in live `orchestrator.py` (L1046, L1673, L1700, L2047, L2132, L2212) — line numbers match research-brief and qa-spec-pass.
- Traced upstream callers: exploration (`process_turn` → `_llm_loop`), combat (`_combat_turn` → `_combat_llm_loop` → inner + narrate pass), creation flavor (`narrate_with_verification` → `_call_narration_llm`), combat code-owned narrate (`_narrate_text` → `_narrate_only`).
- Confirmed `_creation_llm_loop` has **zero callers** but remains a wired site per R4/domain spec (same as APP-080 symmetry).
- Designed two-pass sanitizer: normalize assistant `tool_calls`, then segment-based tool round assembly with APP-028 deferral of interstitial `system`/`user`.
- Pinned `_safe_prefix_fallback` and empty-assistant drop rule to satisfy `test_tail_invalid_returns_safe_prefix` / PM r2.
- Mapped all ten pytest rows to concrete fixtures and T8 integration via existing monkeypatch patterns.

## Self-critique

- **Combat depth:** Re-read confirms `_combat_llm_loop_inner` does not recurse like `_llm_loop`; primary APP-028 risk is SITE 4 → SITE 5 handoff, not multi-depth combat. Plan states this explicitly — research-brief “recurse” wording applies to exploration/creation loops only.
- **Look-ahead boundary:** Pass 2 stops at next assistant-with-tool_calls; if a content-only assistant appears mid-segment, plan treats it as deferred — rare in current loops but could affect future transcripts. Acceptable for v1; QA should flag if integration tests show edge cases.
- **Valid Holt post-APP-080:** If model returns structurally **valid** `tool_calls` with corrupted argument *strings*, sanitizer may not strip calls — 400 would not occur from orphan pattern. T7 fixture must use **structurally** invalid calls (empty array / missing name), not markup in arguments alone.

## Decisions locked for implementation

1. **Single `Orchestrator._chat_completion` wrapper** — all six sites; no `openrouter.py` change.
2. **Module-level `sanitize_transcript_messages`** — public enough for APP-032; non-mutating shallow copies.
3. **APP-028 fix at sanitize boundary only** — do not reorder orchestrator append loops in APP-031.
4. **Safe-prefix excludes trailing assistant** — per PM r2 / QA adversarial note; document in helper docstring.
5. **R5 observability deferred** — not blocking close.

## Risks to watch during impl

- Shallow copy vs nested `tool_calls` mutation: filter into new list on assistant copy, never edit input nested lists.
- `_call_narration_llm` passes `max_tokens=_CREATION_FLAVOR_MAX_TOKENS` — wrapper must forward explicit `max_tokens` (plan signature includes override).
- T8 integration: patch `chat_completion` not `_chat_completion` so existing test modules keep working; assert on second invocation messages only.
- Double-sanitize: wrapper sanitizes once per call — loops must not pre-sanitize (avoid duplicate work / reorder bugs).

## Open for QA plan review

- Whether T7 should also assert **reordered** system line content substring `TOOL FAILED` still present after sanitize (plan assumes yes — worth one explicit assert in qa-plan).
- Whether `assert_transcript_invariants` belongs in orchestrator as `__all__` export or test-only (plan: test-only helper).
- Combat SITE 5: confirm human-test-plan includes successful PC action after prior tool failure in same turn (partial ok/fail) — reorder regression.

## Estimate

Single dev stream: ~120–180 LOC helper + wrapper + test file. No workstream split. APP-032 should follow immediately to reuse helper without forking repair logic.
