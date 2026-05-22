# QA PASS: plan — round 1

**Task:** app-031-transcript-sanitize-orphan-tool-messages  
**backlog_ticket:** APP-031  
**ticket_path:** [tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md](../../app-031-transcript-sanitize-orphan-tool-messages.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`; domain § Transcript sanitize APP-031)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-llm-orchestrator-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (impl: `orchestrator.py`, `test_transcript_sanitize.py`; domain spec changelog on close is process-only, not impl scope creep)
- [x] Acceptance criteria testable — ticket AC + spec R1–R6 mapped in plan architecture, sanitizer design, test matrix, and task breakdown
- [x] Code traces match repo — six `chat_completion(` sites at L1046, L1673, L1700, L2047, L2132, L2212; APP-028 system-before-tool append at ~L2091–2098 (combat) and ~L2276–2287 (exploration)
- [x] AGENTS.md / canon compliance — orchestrator-only scope; no `build/` drift; no `openrouter.py` signature change
- [x] Tests/commands listed — ten pytest rows (T1–T10) + full `cd app && python -m pytest tests/ -q` regression
- [x] Spec R1–R6 coverage in plan (helper contract, invariants, APP-028 reorder, six wire points, R5 defer, APP-032 boundary)
- [x] `qa-spec-pass.md` round 2 requirements carried into plan (non-mutating helper, safe-prefix fallback, Holt fixture naming, APP-032 pairing)
- [x] Monkeypatch compatibility — wrapper delegates to module-level `chat_completion` symbol (existing tests unchanged)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` — helpers + `_chat_completion` + six site swaps | Yes |
| `app/tests/test_transcript_sanitize.py` (new) | Yes |
| `tmp/app-llm-orchestrator-spec.md` — checklist + changelog on close | Process (Spec sync on close); not impl gate |

**Out of scope (explicit):** `app/gm/openrouter.py`, APP-032 retry, APP-034 `transcript_sanitized` JSONL — aligned with spec non-goals.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 `sanitize_transcript_messages` + safe-prefix fallback | § `sanitize_transcript_messages()` design; `_safe_prefix_fallback` | T9 (non-mutating), T10 (safe-prefix cases) |
| R2 validity / orphan drop / round-trip | Pass 1 + Pass 2 walk; `_is_valid_tool_call` | T1–T5, T7, `assert_transcript_invariants` |
| R3 APP-028 reorder (TOOL FAILED after tools) | § APP-028 reorder; Pass 2 step 2 deferred segment | T6 |
| R4 wire all six call sites via wrapper | § Architecture; § Deep code-path traces; task 2–3 | T8 (`_llm_loop` integration mock) |
| R5 observability (optional) | § Open questions Q3 — defer APP-034 | Not blocking |
| R6 APP-032 boundary (no 400 retry; shared primitive) | Summary pairing; § Open questions Q2 export `_safe_prefix_fallback` | Unit tests only; no retry in scope |
| Ticket AC: no orphan tools without preceding `tool_calls` | Full sanitizer + wrapper always-on | T1–T8 + invariant helper |
| Ticket AC: land tests | § Test matrix T1–T10; task 4–5 | `test_transcript_sanitize.py` |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-031 `in_progress`, P1 |
| Plan ⊆ Expected files | **PASS** | No unauthorized paths in impl scope |
| Spec R1–R6 in plan | **PASS** | Algorithm detail sufficient for impl |
| Code traces | **PASS** | Line refs spot-checked against live `orchestrator.py` |
| Test plan vs `qa-spec-pass` / run `spec.md` | **PASS** | All ten named cases + T10 pinned rows |
| APP-032 / APP-028 boundaries | **PASS** | Reorder at send boundary; no loop append changes |
| TurnTruth / narration gate conflict | **PASS** | API transcript layer only |

## Notes (non-blocking — implementation QA)

1. **Wrapper `tool_choice` pseudocode** — Plan shows `tool_choice if tools else "auto"`. `openrouter.chat_completion` only sends `tool_choice` when `tools` is truthy; site 3’s `"none"` at depth ≥2 is API-no-op today. Impl should still forward per-site `tool_choice` kwargs for fidelity.
2. **T2 fixture** — Pin assistant `content` in test setup so assertion matches spec “content-only assistant” vs empty-shell drop + safe-prefix path.
3. **T7 Holt fixture** — Plan correctly encodes structural invalidity (empty `tool_calls`, missing `function.name`), not arg corruption (APP-080); matches `qa-spec-pass` adversarial note.
4. **Plan draft commentary** — § Site 4 inline “Wait, let me re-read…” notes are dev scratch; harmless for gate; clean during impl if desired.
5. **Safe-prefix excludes trailing assistant** — Explicit non-goal documented; APP-032 may extend later (`qa-spec-pass` r2 note).

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
