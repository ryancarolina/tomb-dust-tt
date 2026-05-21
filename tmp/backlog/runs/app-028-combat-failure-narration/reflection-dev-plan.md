# Reflection: Dev plan — APP-028

**backlog_ticket:** APP-028  
**artifact:** [plan.md](./plan.md)  
**round:** 1

## What the plan covers

- **Root cause triad:** (1) silent `_handle_combat_trigger` on failed `start_combat_from_trigger`, (2) exploration `_llm_loop` `all_failed` appends pre-tool `content`, (3) combat inner loop lacks `TOOL FAILED` injection and repeats content append.
- **Fix layers:** R1 same-turn short-circuit via `_beat_combat_start_failure`; R2/R3 deterministic prefix-only returns; R4 parity system messages in `_combat_llm_loop_inner`.
- **Traces delivered:** Flow A (beat → trigger → `_llm_loop` exit), B (five exploration tools + strip), C (inner loop partial vs total failure), D (pending_start regression guard), E (instance flag lifecycle).

## Decisions locked in plan

| Decision | Rationale |
|----------|-----------|
| R1 via `_llm_loop` short-circuit, not engine `ok: false` on beat | QA SPEC-001/004; dual-channel explicit; engine contract unchanged |
| `_beat_combat_start_failure` on orchestrator | Spec-illustrative name; T2 asserts observable return, not field name |
| Strip `content` on `all_failed` only when `content` non-empty | Preserves `depth >= 2` retry when model emits tools-only failure turn |
| R4 inject before tool result in inner loop | Matches exploration L1986–1992 ordering for T10 |
| Patch `gm.orchestrator.chat_completion` in tests | `_llm_loop` / inner loop call wrapper directly; conftest `create_client` insufficient for T2 call-count |
| No `pending_start` wiring in APP-028 | R7 optional; inline R1 meets AC; avoids combat_fsm touch outside Expected files |
| Domain spec edit on close only | Expected files allow spec; avoid drift mid-impl |

## Risks called out for implementation

- **Same-batch tool order:** `process_beat` + another tool in one assistant message may run other tools before R1 return — documented acceptable; T2 uses beat-only batch.
- **`all_failed` vs beat short-circuit order:** Insert beat check **after** tool loop, **before** `all_failed and content` — plan explicit; wrong order would still leak ghoul fiction.
- **T10 flexibility:** Two-tool-call vs depth-retry — pass criteria are message ordering, not a single mock strategy.
- **Inner loop empty `failures` join:** Rare; plan uses fixed fallback line only when join empty — must not use model `content`.
- **Live line anchors:** `_handle_combat_trigger` ~1906, `_llm_loop` ~1999, `_combat_llm_loop_inner` ~1848 verified 2026-05-21; drift ±20 lines.

## QA-spec notes addressed

- TICKET-001: plan § Files ⊆ Expected files only.
- SPEC-001: R1 propagation table + T1/T2.
- SPEC-002: T3–T7 parametrized five exploration tools.
- SPEC-003: R4 + T10 partial-failure injection.
- SPEC-004: dual-channel called out in Flow A.
- SPEC-005: T11 optional logging.

## Out of scope (confirmed)

- APP-027 engine validation, APP-026 attack gating, APP-030 integration fixture, `app-llm-orchestrator-spec.md` edit, `pending_start = True` on trigger, changing `beat.process_beat` payload.

## Ready for

Stage 4 implementation: focus APP-028, implement plan §1–4, run `app/tests/test_combat_failure_narration.py` + engine regression, update `tmp/app-combat-play-spec.md` changelog, `release --done`.
