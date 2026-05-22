# Reflection: QA spec — round 1 (APP-032)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `qa-spec-pass.md`, `reflection-qa-spec.md`

## Completed

- Adversarial review of run `spec.md`, `research-brief.md`, ticket APP-032 AC, and `tmp/app-llm-orchestrator-spec.md` § Reactive 400 retry (APP-032).
- Verified ticket Expected files include `app/tests/test_transcript_400_retry.py` (contrast APP-031 round-1 TICKET-001 blocker).
- Independent code trace: `_chat_completion` L1174–1192 (sanitize only, no try/except); six call sites; `_llm_loop` GM-falters path L2343–2347; no retry helper yet.
- Mapped ticket AC → R1–R5 → domain detection/retry/tests; confirmed APP-031 pairing and non-goals.
- Confirmed `registry_gap: false` against `app-master-spec.md` LLM orchestrator row.
- Issued **PASS** (round 1).

## Self-critique

- Did not mock `openai.BadRequestError` locally to validate SDK exception shape — research cites SDK 2.37.0; spec types are sufficient for plan stage.
- Session JSONL Holt evidence gitignored — relied on research-brief + APP-031 human TC-6 cross-link.
- “Caller messages not repaired” risk noted as non-blocking; could have been escalated if run spec were silent — spec explicitly scopes non-mutating v1.

## Did I miss anything?

- [x] Ticket scope / Expected files — **PASS** (test file present)
- [x] Domain spec / registry_gap / AGENTS.md
- [x] Code paths traced (single intercept + six sites + exploration fallback)
- [x] Tests or AC mapped
- [x] APP-031 boundary clarity — **confirmed PASS**
- [x] TurnTruth / narration gate conflict — none (transcript transport only)
- [ ] Live provider 400 string corpus — deferred to Dev fixtures + APP-034 logs

## Handoff

**Proceed to Dev plan + QA plan** — spec gate PASS round 1.

**Dev plan should pin:** exception mock fixtures for Google malformed string + negative 400 cases; confirm retry uses caller **original** `messages` for truncate (not post-sanitize `clean`).
