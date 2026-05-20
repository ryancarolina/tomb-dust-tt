# QA PASS: plan

**Task:** APP-066-sync-engine-awaiting-with-creation-step  
**backlog_ticket:** APP-066  
**ticket_path:** tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md  
**Round:** 1  
**domain_spec_creation:** not_needed

**Verdict:** PASS

**Verified:**

- [x] Backlog ticket valid; status `in_progress`; domain spec + logging spec drafted for APP-066
- [x] Run `spec.md` R1–R6 and ticket AC mapped in plan § Acceptance criteria mapping
- [x] `qa-spec-pass.md` contract (label compare, no engine/bridge edits) carried through plan unchanged
- [x] Code traces match repo (independent traces below)
- [x] Plan files ⊆ ticket Expected files (orchestrator + domain specs; optional test gated)
- [x] Tests/commands listed (`test_creation_flow.py`, `test_campaign_session.py`, JSONL grep)
- [x] Non-goals respected — no `bridge.py`, `play/tomb_gm/`, or `creation.py` body edits

## Independent code traces (plan accuracy)

| Plan claim | Verified location | Result |
|------------|-------------------|--------|
| Bug: `narrated_awaiting != engine_awaiting` every creation turn | `orchestrator.py` L202–203 | Confirmed — compares granular footer to coarse `CHARACTER_CREATION` |
| `_check_creation_drift` entry + payload | `orchestrator.py` L184–221 | Confirmed — scope, parse early return, reasons, `log_creation_drift` |
| `_creation_drift_scope` unchanged (R4) | `orchestrator.py` L172–182 | Confirmed — `creation.active` OR engine `CHARACTER_CREATION` + empty roster |
| `_emit_narration` → drift after every narration | `orchestrator.py` L247–249 | Confirmed |
| Footer from `format_creation_status` / label map | `creation.py` L69–80, L538–541 | Confirmed — `CREATION_STATUS_LABELS.get(step, f"{step}_INPUT")` |
| `_compose_creation_narration` default footer | `orchestrator.py` L507–524 | Confirmed — L521 `format_creation_status(self.creation)` |
| Creation turn emits narration | `orchestrator.py` L647 | Confirmed — `_emit_narration(narration)` in `_creation_turn_body` |
| Engine coarse awaiting | `bridge.py` L36–37 → `cmd_core.py` L178–180 | Confirmed — empty roster → `CHARACTER_CREATION` |
| Parse narration status | `logger.py` L65–77 | Confirmed — `parse_narration_status_line` |
| Phase drift guards (Trace C) | `orchestrator.py` L204–207, L63 | Confirmed — `phase_mismatch` requires `narrated_phase`; `_PREMATURE_EXPLORE_PHASES` at L63 |
| Post-finalize: `active=False` before footer emit | `orchestrator.py` L1032–1033, L1057–1058, L647 | Confirmed — `_auto_finalize` clears `active` then returns custom footer; caller `_emit_narration` |
| Post-finalize scope off (non-empty roster) | `orchestrator.py` L179–181 | Confirmed — scope false when roster populated |
| Label reference table | `creation.py` L69–80 | Confirmed — matches plan § Label reference |
| Golden-path test exists (optional drift assert) | `test_creation_flow.py` L35–62 | Confirmed — no drift collector yet; plan Task 7 optional |

## Spec / ticket / plan alignment

| Ticket AC | Plan task | Spec R |
|-----------|-----------|--------|
| Engine awaiting reflects step **or** label-based drift compare | §3 (label compare; engine unchanged) | R1, R2 |
| No `creation_drift` every healthy creation turn | §3 removes false `awaiting_mismatch` | R2, R3 |
| Domain spec documents engine vs narration contract | §5 changelog; § already in domain spec L150–163 | R1 |
| Optional golden-path drift assert | §7 (gated Expected files update) | R6 |

## Plan logic review

- **Fix site:** Single comparator rewrite in `_check_creation_drift` + import `CREATION_STATUS_LABELS` — matches research-brief minimal fix and qa-spec-pass “single change site.”
- **Expected label:** `CREATION_STATUS_LABELS.get(step, f"{step}_INPUT").upper()` mirrors `format_creation_status()` L540 — correct source of truth.
- **Resume edge (R4):** Skip awaiting compare when `not creation.active` and scope true — plan Trace E matches spec; avoids stale/missing step false positives.
- **Phase (R3):** Plan correctly notes desk footers omit `Phase:`; existing L204 guard already suppresses `phase_mismatch` on omission — no change required for golden path.
- **Post-finalize (Trace D):** `creation.active=False` + non-empty roster → scope false before RECEPTION_CHOICE footer — no false drift spam.

## Notes (non-blocking)

1. **`engine_awaiting` local** may become unused after §3 — Dev should drop or retain only if needed for debug; payload still uses `status.get("awaiting")`.
2. **Optional test (§7):** Add `app/tests/test_creation_flow.py` to ticket Expected files before edit (per qa-spec-pass; plan §7 gate documented).
3. **`expected_awaiting` payload (R5):** optional — plan §4 recommends; not required for PASS.
4. **§3 prose “Replace L201–207”** — phase/premature branches (L204–207) stay logically unchanged; only awaiting branch (L202–203) rewrites.
5. **LLM `Phase:` leaks** during desk creation may still log `phase_mismatch` or `premature_exploration_phase` — intentional per spec; not addressed by awaiting fix.

## Re-review focus

_N/A — PASS round 1._
