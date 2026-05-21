# QA PASS: implementation — round 1

**Task:** app-024-block-site-fiction  
**backlog_ticket:** APP-024  
**ticket_path:** [tmp/backlog/app-024-block-site-fiction-without-enter-tool.md](../../app-024-block-site-fiction-without-enter-tool.md)  
**Round:** 1  
**domain_spec_creation:** draft present (`tmp/app-exploration-delve-spec.md` § Site-entry fiction gate); checklist `[ ] APP-024` + dated changelog pending at `release --done`

## Verdict

**PASS** — APP-024 acceptance criteria and run `spec.md` E1–E6/E8–E9 are satisfied in code and automated tests.

## Automated tests

```text
python -m pytest app/tests/test_exploration_site_entry_gate.py -v
7 passed in 2.29s

python -m pytest app/tests/ -q -k "not exploration_site_entry"
93 passed, 7 deselected in 9.30s
```

| Module | Tests | Result |
|--------|-------|--------|
| `test_exploration_site_entry_gate.py` | 7 (unit + six integration paths) | ✓ |
| `app/tests/` regression slice | 93 (excludes APP-024 module) | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Block site-entry fiction unless current turn's tool chain includes successful (`ok: true`) `enter_dungeon` or `site_enter` | `_entry_committed_this_turn` set L2091–2092; `_exploration_gate_active` L376–381; `_compose_exploration_narration` L383–388; `process_turn` post-loop compose L882–885; `all_failed` in-loop compose L2133–2135 | ✓ |
| Entry commit not revoked by later failed retry / final `_last_tool_results` slot | Sticky flag never cleared within turn; `test_success_then_failed_enter_dungeon_retains_fiction` asserts `_entry_committed_this_turn is True` while `_last_tool_results["enter_dungeon"]["ok"] is False` | ✓ |
| (implicit) In-dungeon interior narration unchanged | `_exploration_gate_active` bypass when `pre_turn_mode in ("dungeon", "site")`; `test_site_entry_gate_bypass_when_in_dungeon` | ✓ |

## Spec E1–E9 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **E1** | Sticky `entry_committed_this_turn` at depth 0 | Reset L2030; set L2091–2092 on first successful entry tool | ✓ |
| **E2** | Gate active when surface + not committed | `_exploration_gate_active` L376–381; `process_turn` uses `pre_turn_mode` L882–884 | ✓ |
| **E3** | Bypass when `dungeon`/`site` or committed | L377–380; dungeon bypass test | ✓ |
| **E4** | `sanitize_premature_site_entry_flavor` | L119–131 + `_SITE_ENTRY_MARKER_RES` L98–116; unit test | ✓ |
| **E5** | Wire on final return **and** `all_failed and content` | Post-loop L885; in-loop L2133–2135 before banner append | ✓ |
| **E6** | Code-owned refusal when strip empties prose | `_SITE_ENTRY_REFUSAL_LINE` L93–96; compose fallback L386–387; asserted in strip tests | ✓ |
| **E7** | Optional drift telemetry | Deferred per plan — non-blocking | defer |
| **E8** | Dual entry tools (`enter_dungeon`, `site_enter`) | L2091; `test_successful_site_enter_allows_fiction` | ✓ |
| **E9** | APP-077 compose extension point | `_compose_exploration_narration` docstring L384; strip before future footer | ✓ |

## Orchestrator merge: combat vs exploration `all_failed` path

Shared block at `orchestrator.py` L2119–2135:

| Branch | Condition | Behavior | Verified |
|--------|-----------|----------|----------|
| **Combat (APP-028)** | `failed_names & _COMBAT_TOOL_NAMES` | **Prefix-only** — return `[Mechanics failed — …]` with no LLM `content` appended | `test_llm_loop_all_failed_strips_content` in `test_combat_failure_narration.py` |
| **Exploration (APP-024)** | Non-combat failures with `content` | **Sanitize path** — `_compose_exploration_narration(content, gate_active=…)` then `prefix + "\n\n" + safe` | `test_surface_failed_enter_dungeon_no_entry_fiction` |

Split is correct: combat success-fiction leak class stays prefix-only; exploration entry-fiction uses marker sanitizer + refusal fallback. No regression in combat tests (included in 93-pass regression slice).

## Independent code traces

| Flow | Path | Result |
|------|------|--------|
| No-tool entry hallucination on surface | `_llm_loop` text-only return → `process_turn` compose | Markers stripped; refusal emitted; engine stays `surface` |
| Failed `enter_dungeon` + entry `content` (`all_failed`) | In-loop compose before banner | Banner present; no entry markers in output |
| Successful entry then prose | Sticky flag → gate inactive → prose retained | Integration tests pass |
| Success then failed retry same tool | Flag stays `True`; gate off despite dict `ok: false` | Sticky regression test |
| Depth-0 mode snapshot for in-loop gate | `_exploration_pre_turn_mode` L2031–2035 matches `process_turn` pre-turn snapshot | Consistent |
| Double compose idempotency | `all_failed` composes in-loop; `process_turn` composes again | Refusal line has no marker hits; benign prose unchanged on second pass |
| Non-exploration returns through `process_turn` | API error / depth-limit `_last_content` | Still composed at L885 before emit |

## Plan QA notes — resolution

| Plan note | Impl resolution |
|-----------|-----------------|
| Double compose on `all_failed` path | Idempotent — refusal survives second pass; banner not fed through sanitizer |
| Test harness `chat_completion` patch vs `create_client` | Uses `chat_completion` monkeypatch — works; minor style deviation, non-blocking |
| Depth limit / `_last_content` leak | Covered by post-loop compose in `process_turn` |
| Refusal vs marker regex | "at the threshold" / "Crossing requires" do not match crossing patterns |
| E7 telemetry | Deferred — acceptable |

## Scope notes (non-blocking for APP-024 PASS)

| Item | Note |
|------|------|
| **Release / drift** | Ticket still `in_progress`; domain spec checklist item L120 unchecked; exact `_SITE_ENTRY_REFUSAL_LINE` copy not yet pinned in spec — required at `release --done` |
| **E7 drift telemetry** | `premature_site_entry` logging not implemented — optional per spec/plan |
| **`mode=site` bypass test** | Logic mirrors `dungeon` bypass in `_exploration_gate_active`; no dedicated test — low risk |
| **Human playtest** | Not run this round (Stage 7: surface wrong-tool / happy-path entry per `spec.md`) |
| **Engine slice** | `play/tomb_gm/tests/test_extraction_slice.py` not run — out of ticket Expected files; engine unchanged per plan |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-024 --done` (ticket AC checkboxes, Closed date, domain spec checklist + refusal copy pin + changelog).  
**Human playtest:** At Registry hub on surface, "I enter the crypt" without successful entry tool → no interior prose; failed `enter_dungeon` → banner only + refusal/safe surface text; successful entry → fiction allowed; in-dungeon room search → unchanged interior narration.
