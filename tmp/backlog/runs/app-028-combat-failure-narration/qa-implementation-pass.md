# QA PASS: implementation

**Task:** APP-028-combat-failure-narration  
**backlog_ticket:** APP-028  
**ticket_path:** tmp/backlog/app-028-combat-tool-failure-narration.md  
**Round:** 1  
**domain_spec:** tmp/app-combat-play-spec.md (§ Combat tool failure narration — behavior matches code; checklist/changelog pending close)

## Verdict

**PASS** — R1–R4 and R8 implemented in `orchestrator.py`; `_COMBAT_TOOL_NAMES` gates exploration `all_failed` content strip; T1–T11 green; no success fiction on combat-tool total failure paths.

## Automated tests

```text
python -m pytest app/tests/test_combat_failure_narration.py -v
11 passed in 1.04s
```

| ID | Test | Result |
|----|------|--------|
| T1 | `test_handle_combat_trigger_returns_failure_string` | ✓ |
| T2 | `test_beat_trigger_e2e_llm_loop_short_circuits` | ✓ |
| T3–T7 | `test_llm_loop_all_failed_strips_content[*]` (5 exploration tools) | ✓ |
| T8 | `test_combat_inner_all_failed_strips_content` | ✓ |
| T9 | `test_combat_inner_wrong_tool_failure` | ✓ |
| T10 | `test_combat_inner_partial_failure_injects_tool_failed` | ✓ |
| T11 | `test_all_failed_or_beat_failure_logs` | ✓ |

**Engine regression (sanity):**

```text
python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py play/tomb_gm/tests/test_combat_attack.py -q
3 passed in 0.30s
```

## `_COMBAT_TOOL_NAMES` — exploration `all_failed` branch

**Definition** (`orchestrator.py` L84–91): frozenset of `start_combat`, `combat_attack`, `combat_end`, `cast_spell`, `fortune_spend`, `combat_action`.

**Branch** (`_llm_loop`, after beat short-circuit, L2119–2135):

1. When `all_failed and content`: build `failures` prefix and `failed_names` from `_last_tool_results`.
2. If `failed_names & _COMBAT_TOOL_NAMES` → **return prefix only** (R2 content strip).
3. Else → `_compose_exploration_narration(content, …)` and return `prefix\n\n{safe}` (preserves non-combat failure narration path).

| Check | Evidence | Result |
|-------|----------|--------|
| All five exploration combat tools in set | L84–90 | ✓ |
| Intersection triggers strip | L2131–2132 `return prefix` | ✓ |
| T3–T7 exercise each exploration tool | Parametrize hits branch via failing tool names | ✓ |
| Beat failure bypasses branch | R1 short-circuit L2113–2117 runs before `all_failed` block | ✓ |
| Combat inner loop strips without frozenset | `_combat_llm_loop_inner` L1934–1948 always returns prefix on `all_failed` | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Enforce failure narration for all combat tools | Tool table in spec; T3–T10 cover exploration + combat inner paths | ✓ |
| No success fiction when `ok: false` | R1 beat string; R2/R3 strip; banned-substring asserts in T3–T9 | ✓ |

## Spec requirements → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Beat-trigger returns canonical failure; same-turn short-circuit | `_handle_combat_trigger` L2000–2014; `_beat_combat_start_failure` L161, L2029, L2171–2173, L2113–2117; T1–T2 | ✓ |
| **R1** | No `run_combat_monster_turns()` on failed start | T1 `run_turns.assert_not_called()` | ✓ |
| **R2** | Exploration `all_failed` — prefix only for combat tools | `_COMBAT_TOOL_NAMES` branch L2127–2132; T3–T7 | ✓ |
| **R2** | Per-tool `TOOL FAILED` injection retained | L2100–2106 unchanged on partial failure | ✓ |
| **R3** | Combat inner `all_failed` strip | L1934–1948; T8–T9 | ✓ |
| **R4** | Combat inner partial failure injection | L1925–1931; T10 (system before tool result) | ✓ |
| **R5** | Five exploration combat tools | T3–T7 parametrized | ✓ |
| **R6** | State truth after failure | T2 asserts `status.combat` null | ✓ |
| **R8** | Logging on beat short-circuit / strip | `log_error` L2116, L2120, L1945; T11 beat path | ✓ |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/gm/orchestrator.py` | R1 flag + trigger return; R2 `_COMBAT_TOOL_NAMES` branch; R3/R4 combat inner | ✓ |
| `app/tests/test_combat_failure_narration.py` | New T1–T11 | ✓ |
| `tmp/app-combat-play-spec.md` | § APP-028 drafted; checklist item still `[ ]` | ✓ (close-stage sync) |

No unauthorized edits under `app/` outside Expected files.

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **T11 partial** | Covers beat short-circuit `log_error` only; optional `all_failed` strip log not asserted (spec marks T11 optional) |
| **Log copy** | Exploration strip path logs `"returning content"` even when combat branch returns prefix-only — cosmetic |
| **Mixed batch** | Same LLM turn with `process_beat` + other tools before R1 short-circuit — accepted per dev reflection |
| **Domain spec close** | Checklist `[ ] APP-028` + dated changelog on `release --done` |
| **Human playtest** | Stage 7 — not required for impl PASS |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-028 --done` + domain spec changelog/checklist.
