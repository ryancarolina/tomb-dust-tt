# QA PASS: plan — round 1

**Task:** app-028-combat-failure-narration  
**backlog_ticket:** APP-028  
**ticket_path:** [tmp/backlog/app-028-combat-tool-failure-narration.md](../../app-028-combat-tool-failure-narration.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (qa-spec-pass round 2 confirmed `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

**Blocker count:** 0

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-combat-play-spec.md`
- [x] Ticket domain spec matches plan (`tmp/app-combat-play-spec.md` § Combat tool failure narration APP-028)
- [x] Acceptance criteria testable (R1–R8 → locus + T1–T10 mapped; T11 optional for R8)
- [x] Code traces match repo (symbols and line refs spot-checked independently; exact match on `_handle_combat_trigger` L1906, `_combat_llm_loop_inner` L1848–1854, `_llm_loop` L1999–2006, `_execute_tool` process_beat L2040–2043)
- [x] AGENTS.md / canon compliance (orchestrator narration only; no engine/`build/` drift; Expected files respected)
- [x] Tests/commands listed (`test_combat_failure_narration.py` + engine regression pair)
- [x] Plan files ⊆ ticket Expected files (strict equality)
- [x] registry_gap matches reality (N/A at plan gate — spec QA confirmed `false`)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` — R1–R4, R8 | Yes |
| `app/tests/test_combat_failure_narration.py` (new T1–T11) | Yes |
| `tmp/app-combat-play-spec.md` — checklist + changelog on close | Yes |

Explicit out-of-scope: `app/gm/combat_fsm.py` / `pending_start` wiring (R7 optional), `bridge.py`, `app-llm-orchestrator-spec.md`, engine `process_beat` contract, APP-026/027/030 — no unauthorized paths.

## Code trace audit

Independent spot-check against live repo:

| Symbol / flow | File | Present | Plan ref |
|---------------|------|---------|----------|
| `_handle_combat_trigger` silent `-> None` on failed start | `orchestrator.py` L1906–1917 | Yes | Flow A / §1.1 |
| `_execute_tool` process_beat → trigger, no failure propagation | `orchestrator.py` L2040–2043 | Yes | §1.2 |
| `_llm_loop` `all_failed and content` appends `\n\n{content}` | `orchestrator.py` L1999–2006 | Yes | Flow B / §2 |
| `_llm_loop` per-tool `TOOL FAILED` injection | `orchestrator.py` L1986–1992 | Yes | R2 preserve |
| `_combat_llm_loop_inner` `all_failed` + content append | `orchestrator.py` L1848–1854 | Yes | Flow C / §3.2 |
| `_combat_llm_loop_inner` no `TOOL FAILED` injection | `orchestrator.py` L1831–1846 | Yes | R4 gap |
| `_combat_turn` `pending_start` canonical failure shape | `orchestrator.py` L1710–1717 | Yes | Flow D reference |
| Beat short-circuit **after** tool batch, **before** `all_failed and content` | plan Flow A step 5 | Planned | Critical ordering — explicit |

Planned R1 short-circuit ordering is correct: `process_beat` returns `ok: true` → `all_failed` is false, so beat failure must be handled by a dedicated flag check before the content-strip block.

## qa-spec-pass (round 2) → plan resolution

| Spec QA item | Plan handling |
|--------------|---------------|
| SPEC-001 R1 propagation | §1.1–1.3 + Flow A; T1 unit + T2 E2E (`chat_completion` count == 1) |
| SPEC-002 five exploration tools | T3–T7 parametrized; banned fiction per tool |
| SPEC-003 R4 partial failure | §3.1 TOOL FAILED before tool result; T10 message-order assertion |
| SPEC-004 dual-channel | Flow A note; T2 asserts player return not tool JSON |
| SPEC-005 R8 logging | §4 R8 table; T11 optional |
| TICKET-001 Expected files | § Files table; no scope creep |
| Same-batch tool order | Flow A / § Flow E — documented acceptable |

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| Enforce failure narration for **all** combat tools | R5 table; §2–3; Flow B/C | T3–T7 (exploration five) + T8–T9 (combat inner + wrong tool) |
| No success fiction on `ok: false` | R1–R6; Flow A–C | T1–T10 (prefix-only, banned substrings, beat short-circuit) |
| Spec sync on close | §5 domain spec on `release --done` | checklist + changelog |

### Requirement map

| ID | Plan locus | Test |
|----|------------|------|
| R1 | `_handle_combat_trigger`, `_execute_tool`, `_llm_loop` short-circuit | T1, T2 |
| R2 | `_llm_loop` strip | T3–T7 |
| R3 | `_combat_llm_loop_inner` strip | T8 |
| R4 | `_combat_llm_loop_inner` TOOL FAILED inject | T10 |
| R5 | exploration + combat tool inventory | T3–T9 |
| R6 | state truth (preconditions + T2 `status.combat` null) | T2; T3–T7 preconditions |
| R7 | optional `pending_start` | out of scope; Flow D regression guard |
| R8 | `log_error` on strip / short-circuit | T11 optional |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-028 `in_progress` |
| Plan ⊆ Expected files | **PASS** | Three files only |
| Code traces | **PASS** | Flows A–E verified independently |
| Spec R1–R8 coverage | **PASS** | All requirements mapped to locus + tests |
| AC testability | **PASS** | T1–T10 required; T11 optional |
| Regression commands | **PASS** | new module + engine combat pytest pair |
| qa-spec-pass alignment | **PASS** | Round 2 blockers addressed in plan |

## Notes (non-blocking — impl QA)

1. **LLM patch target:** Plan correctly requires patching `gm.orchestrator.chat_completion` for T2 call-count and loop tests; conftest `create_client` stub alone is insufficient (plan § Test plan, reflection-dev-plan).
2. **T2 message seed:** Minimal `[{"role":"user","content":"…"}]` is enough when `chat_completion` is fully mocked on first call — no full `process_turn` / roster required.
3. **T10 partial failure:** Assert `TOOL FAILED` index < matching `role: tool` on the accumulated `messages` list after `_combat_llm_loop_inner` completes; use `chat_completion` `side_effect` (two-tool response then narrate stub) if a single mock is awkward.
4. **R6 post-condition:** T2 asserts `status.combat` null; T3–T7 could optionally add the same post-assert — not required by plan but strengthens state-truth AC.
5. **R3 empty `failures` join:** Plan fallback `\n\nYour action did not resolve.` when join empty has no dedicated test; T9 wrong-tool path covers non-empty failure label — acceptable edge.
6. **Same-batch `process_beat` + other tools:** Documented acceptable; grave-ghoul path is beat-only.
7. **`_beat_combat_start_failure` depth==0 reset:** Optional hygiene in plan §1.4 — recommend impl clears at `_llm_loop` depth 0 alongside `_last_tool_results`.

**Verdict:** PASS — ready for workstreams + implementation.
