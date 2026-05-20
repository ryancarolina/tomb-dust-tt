# Reflection: Dev — APP-057 workstreams

**Agent:** Dev (workstreams phase)  
**Inputs:** `plan.md`, PASS `spec.md`, `qa-plan-pass.md`, ticket, `reflection-dev-plan.md`  
**Deliverables:** `workstreams.md`, `reflection-dev-workstreams.md`

## Stream split decision

**Count: 2 (WS1 → WS2).**

Plan task breakdown (steps 1–5 vs 6) and plan “Workstream suggestion” align with a hard dependency: integration test (R1–R3) cannot pass until orchestrator/creation R6 fixes let the 8-input Apprentice caster path chain through RACE and CLASS without table re-present.

```text
WS1: creation.py + orchestrator.py (R6)
  ↓
WS2: test_creation_flow.py (R1–R3)
```

Considered but rejected:

| Candidate split | Why not |
|-----------------|---------|
| WS1 creation only / WS2 orchestrator only | Same ticket slice; chain edits span both files and must land together for any manual smoke |
| WS1 + WS2 parallel | WS2 pytest would fail until WS1 gates/chains exist |
| WS3 spec sync | Plan R5 is **release-only** (`release --done`) — not an impl workstream |
| WS3 conftest fixture | Plan R4 explicitly no-change; inline monkeypatch only |

## WS1 file list

| File | Role |
|------|------|
| `app/gm/creation.py` | `races_table_shown`, `classes_table_shown`, advance resets, serialization |
| `app/gm/orchestrator.py` | Gates, present flags, NAME→RACE + ROLL_STATS→CLASS chain, execute guards |

**WS1 test gate:** engine `test_creation_gating.py` + app smoke — no new test file yet.

## WS2 file list

| File | Role |
|------|------|
| `app/tests/test_creation_flow.py` | `test_full_creation_apprentice_caster` — 8 inputs, FIXED_ROLL, finalize assertions |

**Excluded from impl streams:** `app/tests/conftest.py` (default unchanged), domain spec (ticket close).

## Risks carried into impl

1. **ROLL_STATS nested chain** — class table appended in `_chain_after_creation_choice`, not inside `_auto_roll_stats`; if QA impl rejects, alternative is inlining `format_classes_table` in roll path (spec-valid; larger diff).
2. **Strict per-step assertions** — loop assumes Apprentice + Spellcasting path with no extra auto-skips; WS1 chain must match `INPUTS` expected steps exactly.
3. **Collection-time imports** — WS2 must not module-level import `Orchestrator` (APP-049 constraint).
4. **WS2 before WS1** — orchestrator will re-present race on turn 3; test appears “flaky” but is correct failure mode.

## Self-critique

- WS1 done criteria do not run `test_creation_flow.py` (file does not exist until WS2) — intentional; WS1 closure is regression-only.
- Optional mid-loop narration asserts (plan §3.4 nice-to-have) left out of WS2 AC table to keep impl focused on required post-finalize checks; impl agent may add if trivial.
- Did not re-read live `orchestrator.py` line numbers — plan line refs passed through; impl should verify anchors if file drifted since plan draft.

## Did I miss anything?

- [x] Ticket scope / Expected files — all four paths mapped; conftest explicitly excluded
- [x] Domain spec / AGENTS.md — no canon changes; spec sync deferred to release
- [x] Plan task order preserved in WS1 table (1–6) and WS2 table (1–4)
- [x] Dependency WS2 → WS1 documented in summary table, WS2 section, and prompt seeds
- [x] Test commands from plan § Tests copied per stream

## Handoff

**Ready for:** sequential Dev impl dispatches — WS1 then WS2 (not parallel)  
**Escalate human if:** WS1 regressions fail in `test_creation_gating.py` (may indicate overlap with APP-006–012 behavior — reconcile before WS2)  
**After WS2:** QA implementation gate → drift → `release APP-057 --done` + spec changelog
