# Workstreams: APP-066-sync-engine-awaiting-with-creation-step

**backlog_ticket:** APP-066

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Drift comparator fix | — | `app/gm/orchestrator.py` | `_check_creation_drift` compares `narrated_awaiting` to `CREATION_STATUS_LABELS[step]` when `creation.active`; resume edge skips awaiting compare; `pytest play/tomb_gm/tests/test_campaign_session.py -q` green |
| WS2 | Golden-path drift assert (optional) | WS1 | `app/tests/test_creation_flow.py`, `tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md` | Ticket Expected files includes test path; `drift_events == []` on full creation mock; `pytest app/tests/test_creation_flow.py -q` green |

**Stream count:** 2 — WS1 is the required fix (~25–40 lines); WS2 is optional regression lock (plan §7 / spec R6) and **must** update ticket Expected files before editing the test module.

**Out of workstreams (ticket release):** `tmp/app-character-creation-spec.md` + `tmp/app-logging-qa-spec.md` changelogs; `python tmp/backlog/claim_ticket.py release APP-066 --done` (plan tasks 5–6).

**Explicitly not in any stream:** `app/gm/bridge.py`, `app/gm/creation.py` (body), `play/tomb_gm/**`, `app/gm/logger.py`.

---

## WS1 — Drift comparator fix

**Scope:** Plan §1–4 — import `CREATION_STATUS_LABELS`; rewrite awaiting branch in `_check_creation_drift`; optional `_expected_creation_awaiting_label` helper; optional `expected_awaiting` in drift payload (R5).

**Requirements covered:** spec R2 (label compare), R3 (phase guards unchanged), R4 (scope + resume skip), ticket AC (no per-turn false `awaiting_mismatch`).

### Implementation order (within stream)

| # | Task | File:area | Plan ref |
|---|------|-----------|----------|
| 1 | Add `CREATION_STATUS_LABELS` to existing `from gm.creation import (...)` | `orchestrator.py` L16–42 | §1 |
| 2 | Add `_expected_creation_awaiting_label()` (or inline equivalent) | `orchestrator.py` ~L171 (before `_creation_drift_scope`) | §2 |
| 3 | Rewrite awaiting `reasons` branch | `orchestrator.py` L184–221 | §3 |
| 4 | Optional: `expected_awaiting` in `log_creation_drift` payload | `orchestrator.py` L212–221 | §4 |
| 5 | Remove unused `engine_awaiting` local if dead after §3 | `orchestrator.py` | qa-plan-pass note 1 |

### `_check_creation_drift` awaiting logic (plan §3)

| Branch | Condition | Action |
|--------|-----------|--------|
| Awaiting (active) | `creation.active` and `narrated_awaiting` | `expected = CREATION_STATUS_LABELS.get(step, f"{step}_INPUT").upper()`; if `narrated_awaiting != expected` → `awaiting_mismatch` |
| Awaiting (resume) | not `creation.active` and `narrated_awaiting` | **no** awaiting compare (R4) |
| Phase | `narrated_phase` and `engine_phase` and differ | `phase_mismatch` (unchanged) |
| Premature explore | `creation.active` and `narrated_phase in _PREMATURE_EXPLORE_PHASES` | `premature_exploration_phase` (unchanged) |

**Remove:** `narrated_awaiting != engine_awaiting` when `creation.active` (current L202–203).

**Do not edit:** `_creation_drift_scope` (L172–182); `parse_narration_status_line` / `logger.py`.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Label source | Must mirror `format_creation_status()` — `CREATION_STATUS_LABELS.get(step, f"{step}_INPUT").upper()` (`creation.py` L540) |
| Engine unchanged | `status.get("awaiting")` stays in payload as coarse engine value; do not change `bridge` / `cmd_core` |
| Scope unchanged | `_creation_drift_scope` logic untouched (Trace B / R4) |
| Real drift preserved | Wrong footer vs step still logs `awaiting_mismatch` (e.g. `SKILLS` step + `Awaiting: CLASS_INPUT`) |
| Post-finalize | Trace D — `creation.active=False` + roster → scope false; no new handling needed |
| Out of scope | `creation.py` body, `bridge.py`, `play/tomb_gm/**` |

### Test gates (WS1 done when)

```bash
python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
```

**Manual (plan § Test plan):** after WS1, golden-path creation should not emit `creation_drift` with `awaiting_mismatch` when footer matches step (JSONL grep — Stage 7).

**WS1 does not require** `test_creation_flow.py` green if file unchanged (optional WS2).

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-066
ticket: tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md
run-folder: tmp/backlog/runs/app-066-sync-engine-awaiting-with-creation-step/
spec: spec.md | plan: plan.md §1–4 | domain: tmp/app-character-creation-spec.md (read); tmp/app-logging-qa-spec.md (read)
workstreams: workstreams.md § WS1

Implement WS1 only — orchestrator _check_creation_drift awaiting compare per plan §3 and spec R2–R4.
AGENTS.md: claim APP-066 before app/ edits; only app/gm/orchestrator.py.
Do not edit bridge, creation.py body, play/tomb_gm, logger.py.
Run: python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Golden-path drift assert (optional)

**Scope:** Plan §7 — monkeypatch `log_creation_drift` in `test_full_creation_apprentice_caster`; optional unit probes for `_check_creation_drift`.

**Depends on:** WS1 — without label compare fix, golden path may still append drift events.

**Requirements covered:** spec R6; ticket AC optional “no drift on golden-path turns”.

### Pre-edit gate

Add `app/tests/test_creation_flow.py` to ticket **Expected files** (qa-plan-pass note 2) before any test edit.

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | Update ticket Expected files | `tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md` | §7 gate |
| 2 | Drift collector in integration test | `monkeypatch.setattr("gm.orchestrator.log_creation_drift", lambda data: drift_events.append(data))` | §7 |
| 3 | Assert after INPUTS loop | `assert drift_events == []` with helpful message | §7 |
| 4 | (Optional) `test_check_creation_drift_healthy_skills_step` | Match narration `Awaiting: SKILLS_INPUT` + step `SKILLS` → no log | §7 |
| 5 | (Optional) negative probe | step `SKILLS`, narration `Awaiting: CLASS_INPUT` → `awaiting_mismatch` in reasons | §7 |

### Test gates (WS2 done when)

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
```

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Ticket gate | Expected files line for test module **before** edit |
| Collection imports | No module-level `Orchestrator` import (APP-049) |
| WS2 only | Do not re-open orchestrator except if WS1 left a bug |
| Optional probes | Unit tests not required for ticket close if §2–3 land |

### Post-impl (not WS2 — ticket release)

- `tmp/app-character-creation-spec.md` changelog: APP-066 drift uses `CREATION_STATUS_LABELS` when `creation.active`
- `tmp/app-logging-qa-spec.md` changelog: `creation_drift` awaiting compare semantics
- `python tmp/backlog/claim_ticket.py release APP-066 --done`

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-066
ticket: tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md
run-folder: tmp/backlog/runs/app-066-sync-engine-awaiting-with-creation-step/
spec: spec.md | plan: plan.md §7 | workstreams: workstreams.md § WS2

Prerequisite: WS1 merged — label-based drift compare in orchestrator.py.
Implement WS2 only — test_creation_flow.py drift silence assert; update ticket Expected files first.
AGENTS.md: claim APP-066 if not active.
Run: python -m pytest app/tests/test_creation_flow.py -q && python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
Write reflection-dev-impl-WS2.md before return.
```
