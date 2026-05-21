# QA PASS: plan

**Task:** app-024-block-site-fiction  
**backlog_ticket:** APP-024  
**ticket_path:** [tmp/backlog/app-024-block-site-fiction-without-enter-tool.md](../../app-024-block-site-fiction-without-enter-tool.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (spec QA round 2 confirmed `registry_gap: false`)

**Verdict:** PASS

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Ticket valid (`in_progress`) | PASS | `tmp/backlog/app-024-block-site-fiction-without-enter-tool.md` |
| Ticket domain spec matches plan | PASS | `tmp/app-exploration-delve-spec.md` § Site-entry fiction gate; run `spec.md` E1–E9 |
| Acceptance criteria testable | PASS | Seven pytest cases + three commands; AC ↔ § Requirements map |
| Code traces match repo | PASS | Independent read `orchestrator.py` — see audit table |
| AGENTS.md / drift policy | PASS | Behavior in domain spec; plan §7 spec sync on close |
| Tests/commands listed | PASS | §6 test matrix + regression slice |
| Plan impl files ⊆ Expected files | PASS | `orchestrator.py`, `test_exploration_site_entry_gate.py` only for code |
| qa-spec-pass remediation carried forward | PASS | E1 sticky flag, refusal pin, mode snapshot |

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` (E1–E6, compose wiring) | Yes |
| `app/tests/test_exploration_site_entry_gate.py` (new) | Yes |
| `tmp/app-exploration-delve-spec.md` (refusal copy, checklist, changelog) | Spec sync on close (ticket § Spec sync) — not impl Expected files |

No edits to `bridge.py`, `system_prompt.py`, `creation.py`, `logger.py` (E7 deferred).

## Code trace audit (adversarial)

| Claim | Repo check | Result |
|-------|------------|--------|
| Exploration branch: `_llm_loop` → `_emit_narration` with no compose | `orchestrator.py:779–814` | Match |
| No-tool leak: text-only return | `orchestrator.py:1959–1960` | Match — plan Flow B; caller compose |
| Primary leak: `all_failed and content` | `orchestrator.py:1999–2006` | Match — plan Flow C in-loop compose |
| `_last_tool_results` overwrite per tool name | `orchestrator.py:1978` | Match — E1 sticky flag rationale valid |
| Dual entry tools in dispatch | `orchestrator.py:2050–2051`, `2086–2090` | Match |
| `_emit_narration` creation drift only | `orchestrator.py:317–319` | Match — exploration gate is new |
| `_llm_loop` single exploration caller | Grep `app/` | Only `process_turn:813` — post-loop compose satisfies E5 |
| `Orchestrator.__init__` state slot ~L108 | `orchestrator.py:104–111` | Match — plan adds fields after existing attrs |
| Creation compose precedent | `creation.py:sanitize_premature_completion_flavor` | Pattern valid for module-level sanitizer |

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| Block site-entry fiction unless turn chain includes successful `enter_dungeon` / `site_enter` | §1 E1, §2 E4, §3 compose, §4 wiring | `test_surface_no_tool_*`, `test_surface_failed_*`, unit sanitizer |
| Entry commit not revoked by later failed retry | §1.3 sticky flag; Flow D | `test_success_then_failed_enter_dungeon_retains_fiction` |
| (implicit) in-dungeon interior narration unchanged | §1.4 E3 bypass | `test_site_entry_gate_bypass_when_in_dungeon` |
| Spec sync on close | §7 domain spec | Changelog + refusal line pin |

## Spec E1–E9 → plan map

| ID | Plan section | Verified |
|----|--------------|----------|
| E1 | §1 sticky `entry_committed_this_turn` | Yes — forbids dict-only inference |
| E2 | §1.4 `_exploration_gate_active` + §4.1 | Yes — surface + not committed |
| E3 | §1.4 bypass dungeon/site + E1 | Yes |
| E4 | §2 `sanitize_premature_site_entry_flavor` | Yes — marker intent + unit test |
| E5 | §4.1 post-loop + §4.2 `all_failed` | Yes — both leak paths |
| E6 | §2 refusal constant + §3 compose fallback | Yes — pinned string (qa-spec NOTE-002) |
| E7 | §5 optional defer | Yes — non-blocking |
| E8 | §1.3 both tool names | Yes — `test_successful_site_enter_*` |
| E9 | § Flow E, §3 APP-077 extension point | Yes — strip before future footer |

## qa-spec-pass notes — plan resolution

| Note | Plan handling |
|------|---------------|
| NOTE-002 refusal copy | §2 `_SITE_ENTRY_REFUSAL_LINE` exact string |
| NOTE-003 mode snapshot | Flow D — `party.mode` at depth 0; not `party.phase`; hub = `surface` |
| NOTE-001 orchestrator spec cross-link | Deferred to ticket close — acceptable |
| Sanitizer regex fixtures | §6.2 unit test + impl-defined markers |

## Scope boundary (re-check)

| Topic | Plan handling |
|-------|---------------|
| APP-022 failure hints | Non-goal |
| APP-028 combat narration leak | Non-goal — Flow F |
| APP-077 footer / status strip | Extension point only; no dependency |
| Travel fiction without `world_travel` | Non-goal |
| Engine / bridge entry logic | Non-goal |
| `system_prompt.py` prompt-only fix | Non-goal |

## Notes (non-blocking; implementation QA)

1. **Double compose:** `all_failed` path composes inside `_llm_loop`; `process_turn` composes again on the banner+body string. Sanitizer must be idempotent on clean prose and must not strip the `[Mechanics failed — …]` banner line.
2. **Test harness:** `_surface_exploration_orchestrator` is a stub — impl should use `conftest.orchestrator` + `monkeypatch` on `bridge.status()` / `_execute_tool` (same pattern as `test_creation_flavor_sanitize.py`); prefer `create_client` stub over raw `chat_completion` patch for consistency with existing tests.
3. **Depth limit / `_last_content`:** Not named in flow tables; post-loop compose still covers returns at `orchestrator.py:1927–1932` and `1959–1960` when `_last_content` carries entry prose.
4. **Refusal vs markers:** Impl must verify `_SITE_ENTRY_REFUSAL_LINE` survives second sanitizer pass (contains "threshold" but not listed crossing verbs).
5. **Session claim:** Implementer must `focus APP-024` / active batch before `app/` edits (hooks).

## Summary

Plan traces both documented leak paths (`no tool_calls` and `all_failed and content`), implements qa-spec round 2 E1 sticky commit tracking (not `_last_tool_results` final slot), pins refusal copy, wires dual compose entry points, maps all seven spec tests, and stays within ticket Expected files for code. Ready for Stage 4 (workstreams + implementation).

## Re-review focus

_None required unless Dev revises gate predicate (mode table), E1 signal, or refusal copy._
