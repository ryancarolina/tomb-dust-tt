# QA PASS: plan — round 1

**Task:** app-019-surface-new-game-errors  
**backlog_ticket:** APP-019  
**ticket_path:** [tmp/backlog/app-019-surface-new-game-failure-errors.md](../../app-019-surface-new-game-failure-errors.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`; domain § New game failure APP-019)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-session-persistence-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (strict: `orchestrator.py`, optional `app/ui/app.py` R6, `test_setup_new_game_failure.py`; domain spec sync on close is release gate, not scope creep)
- [x] Acceptance criteria testable — ticket AC mapped in § Acceptance mapping; spec R0–R7 covered in tasks §1–7 + tests T-019a–f
- [x] Code traces match repo (`process_turn` 535–539 / 549–565; `_handle_player_death` 404–433; combat callers 1586–1591 / 1680–1684; `_emit_recovery_narration` 309–311)
- [x] AGENTS.md / canon compliance (app-only; no engine lifecycle reorder; mirrors APP-071 recovery pattern)
- [x] Tests/commands listed (new module T-019a–f; regression filters for APP-014/071/creation flow)
- [x] Spec R1a/R1b emit ownership resolved in plan (context B `PlayerDeathResult.already_emitted`; both combat sites skip `_emit_narration` when emitted)
- [x] Plan addresses qa-spec-pass round 2 notes (preserve `None` vs result at combat sites; R6 deferred)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` — helpers + contexts A/B/C + combat callers | Yes |
| `app/tests/test_setup_new_game_failure.py` (new) | Yes |
| `app/ui/app.py` — optional R6 `_set_turn_idle` | Yes (optional) |
| `tmp/app-session-persistence-spec.md` — checklist/changelog on close | Release gate (AGENTS.md); not impl scope |

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R0 three failure contexts | § Code-path traces A/B/C; tasks §2–4 | T-019a–d |
| R1 dual JSONL + drift-safe emit | Helpers reuse `_emit_recovery_narration`; forbid `_emit_narration` on failure | T-019a–d JSONL asserts; T-019e drift silence |
| R1b death caller contract | `PlayerDeathResult`; task §3 + §5 combat callers | T-019c + caller-branch simulation |
| R2 command copy + footer | `_setup_new_game_failure_message(context="command")`; task §2 | T-019a, T-019b |
| R3 death failure copy | task §3 | T-019c |
| R4 run_ended failure copy | task §4 | T-019d |
| R5 cause mapping | `_map_setup_new_game_cause`; table aligned with domain § Engine error → cause line | T-019a, T-019b |
| R6 optional UI | task §6 deferred post-manual-smoke | manual TC-A; ticket closes orchestrator-only |
| R7 success regression | task §2/§3/§4 success branches unchanged | T-019f; manual TC-D |
| Ticket AC: clear error + cause + retry | § Acceptance mapping | T-019a–d + `[Awaiting: new game]` |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-019 `in_progress` |
| Plan ⊆ Expected files | **PASS** | No unauthorized paths |
| Spec R0–R7 in plan | **PASS** | R1b SPEC-001 contract fully specified |
| Code traces | **PASS** | Line refs spot-checked against live `orchestrator.py` |
| Test plan vs `qa-spec-pass` | **PASS** | T-019a–f map to spec; APP-071 mock patterns cited |
| Emit / double-JSONL risk | **PASS** | Context B `already_emitted` + caller guards at both sites |
| Success-path non-regression | **PASS** | R7 explicit; T-019f + regression pytest filters |

## Notes (non-blocking — implementation QA)

1. **T-019 mock level:** Plan mocks `orchestrator.setup_new_game` for T-019a/b/c; spec prose mentions bridge L4/L5 — both valid; impl may add one bridge-level test if desired but not required for plan gate.
2. **Death / run_ended success automation:** No dedicated pytest for context B/C success (manual TC-D only) — acceptable per spec QA PASS; impl should not regress existing combat/death flows.
3. **Task §3 step order:** Build R3 before `log_error` in bullet list vs spec R1 `log_error` first — cosmetic; impl should follow spec order (`log_error` → build → emit).
4. **R6 sentinel:** Prefix match on “Could not start a fresh session” is documented; add orchestrator flag only if brittle during manual smoke.
5. **`PlayerDeathResult` vs tuple:** Plan allows tuple if module convention prefers — contract (`already_emitted`, `None` early exits) is what impl QA must enforce.

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
