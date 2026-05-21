# Reflection: Dev — APP-019 workstreams

**Agent:** Dev (workstreams)  
**Round:** 1  
**Inputs:** `plan.md`, `spec.md`, `qa-plan-pass.md` (round 1), `reflection-dev-plan.md`, ticket APP-019  
**Deliverables:** `workstreams.md`, `reflection-dev-workstreams.md`

## Completed

- Read plan tasks §1–8, code-path traces A/B/C, acceptance mapping, and qa-plan PASS (round 1).
- Split into **WS1** (orchestrator helpers + contexts A/B/C + combat callers) and **WS2** (T-019a–f test module), matching APP-014/015 two-stream precedent.
- Mapped plan tasks §1–5 → WS1; plan task §7 → WS2; deferred plan task §6 (optional R6 UI) and §8 (domain spec sync) to release-only / human-escalate.
- Documented R5 cause table, R2–R4 copy variants, `PlayerDeathResult.already_emitted` contract, and both combat call sites (~1586, ~1680).
- Copied test matrix, mock patterns (APP-071), regression filters, and T-019c caller simulation notes from plan §7.
- Included prompt seeds, test gates, and critical constraints (`_emit_recovery_narration` vs `_emit_narration`, spec R1 `log_error` first) per stream.

## Stream decision

| Option | Verdict |
|--------|---------|
| **Single stream** | Viable — two files, one ticket; cohesive failure surfacing |
| **WS1 + WS2 (chosen)** | WS1 is independently smoke-testable via import; WS2 needs WS1 behavior for T-019a–f; matches APP-014/015/073 pattern |
| WS1 + WS2 + WS3 (optional UI) | Rejected — R6 deferred post-manual-smoke per plan and qa-plan; not parallel-safe until smoke proves need |
| Three streams (A/C vs B vs tests) | Rejected — context B shares helpers with A/C; combat callers depend on `PlayerDeathResult`; split adds handoff without parallel benefit |

Did **not** add a stream for `app/ui/app.py` — plan defers R6 until manual TC-A proves weak visibility; orchestrator + narration + chips should close ticket by default.

## Alignment checks

| Source | Check |
|--------|-------|
| qa-plan-pass R1 | SPEC-001 `already_emitted` + both combat sites in WS1 § Task 7 |
| qa-plan-pass R1 | Context A/C inline emit; context B in-handler emit in WS1 constraints |
| qa-plan-pass note #3 | WS1 Task 5/6: `log_error` before build + emit (spec order) |
| qa-plan-pass note #4 | R6 prefix sentinel documented in WS2 post-impl; flag only if brittle |
| qa-plan-pass note #5 | `PlayerDeathResult` dataclass in WS1; tuple acceptable if module convention prefers |
| Ticket Expected files | `orchestrator.py`, `test_setup_new_game_failure.py`, optional `app/ui/app.py` — workstreams match |
| APP-014 / APP-015 boundary | WS1 constraints: no lifecycle reorder; consume setup failures as-is |
| APP-071 mirror | `_emit_recovery_narration` reuse; regression filter in WS2 gates |

## Self-critique

- WS1 has only import smoke until WS2 — acceptable; ticket AC needs T-019a–f for close.
- Did not re-verify live `orchestrator.py` line numbers beyond plan/qa-plan anchors (~535, ~404, ~549, ~1586, ~1680); impl should confirm if files shifted.
- T-019c caller simulation is documented but not a shared repo helper yet — impl may add `_simulate_combat_death_emit` if asserts duplicate (per reflection-dev-plan).
- R4 run_ended lead-line assembly risk noted in WS1 Task 6 and WS2 constraints — T-019d should assert `{where}` + failure tail, not full prose lock against R3.
- Death/run_ended **success** paths have no new pytest (manual TC-D only) — acceptable per qa-plan note #2; WS2 regression filters guard T-019f command success only.

## Did I miss anything?

- [x] Plan tasks §1–5 → WS1; §7 → WS2; §6/§8 out-of-scope
- [x] Spec R0–R7 and R1a/R1b mapped to streams
- [x] Ticket AC + qa-plan acceptance mapping covered
- [x] Emit / double-JSONL / drift risks in WS1 constraints; T-019e in WS2
- [x] Test commands and APP-071/014/creation regression filters in WS2
- [x] Optional R6 escalation path documented
- [x] No code implemented (workstreams-only stage)

## Handoff

**Ready for:** Orchestrator dispatches **WS1** (required), then **WS2**  
**Order:** WS1 → WS2 (sequential; T-019a–f fail until failure branches land)  
**Escalate human if:** Manual smoke (TC-A) shows command failure copy invisible after `clear_narration` — then minimal R6 in `app/ui/app.py` (update ticket Expected files before dispatch)
