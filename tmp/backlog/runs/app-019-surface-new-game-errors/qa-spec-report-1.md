# QA Report: spec — round 1

**Task:** APP-019-surface-new-game-errors
**backlog_ticket:** APP-019
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` R1 (emit pattern) vs R3 (death failure); `app/gm/orchestrator.py` `_handle_player_death` (~404–433) and combat callers (~1586–1591, ~1680–1684)
- **Issue:** R1 requires `_emit_recovery_narration` on **all** setup-failure contexts and forbids `_emit_narration` (drift risk on `[Awaiting: new game]` footers). Context B is implemented today as: `_handle_player_death` **returns** a string → caller always calls `_emit_narration(death_narration)` at **two** combat sites. The spec does not say whether:
  1. `_handle_player_death` must emit recovery JSONL internally and return without caller re-emit, or
  2. both combat callers must branch (recovery emit on setup failure, `_emit_narration` only on success), or
  3. failure returns a sentinel / tuple so callers skip `_emit_narration`.
- **Implementation gap:** Naive impl inside `_handle_player_death` only (log + `_emit_recovery_narration` + return) **double-logs** `gm_narration` because callers still invoke `_emit_narration`. Using caller `_emit_narration` on failure copy violates R1 and likely breaks T-019e (creation.active is true after C1–C2 even when L4/L5 fail — drift scope active).
- **Suggested fix:** Add explicit **Context B emit contract** to `spec.md` and domain § New game failure (APP-019), e.g.:
  - `_handle_player_death` on setup failure: `log_error` → build R3 copy → `_emit_recovery_narration` → return message; **callers MUST NOT** call `_emit_narration` when `setup_new_game` failed (document flag, separate helper, or inline branch at both call sites).
  - Success path unchanged: return success copy; callers keep `_emit_narration`.
  - Extend T-019c to assert **single** `log_gm_narration` call and no `creation_drift` / `awaiting_mismatch` when mocking failure.

### SPEC-002 — major (non-blocking)

- **Location:** `spec.md` Test plan T-019c, T-019d
- **Issue:** R1 AC requires dual JSONL (`error` + `gm_narration`) for contexts B and C; T-019a covers this for context A only. T-019c says “combat turn resolving death” but no pytest today exercises combat death (`rg` over `app/tests` — zero `_handle_player_death` / death combat tests). Plan is feasible via direct `_handle_player_death` mock + monkeypatch, but spec should state that explicitly to avoid brittle full combat integration.
- **Suggested fix:** T-019c: “monkeypatch `extract_death_from_mechanical` / call `_handle_player_death` with fixture mechanical”; assert `log_error("setup_new_game", …)` + one `log_gm_narration`. T-019d: same dual-log asserts as T-019a.

### SPEC-003 — minor (non-blocking)

- **Location:** `spec.md` line 185 (“extend ticket Expected files before impl”); run vs domain cause-line wording
- **Issue:** Ticket Expected files already include `orchestrator.py` and `test_setup_new_game_failure.py` — stale note. Domain § cause table wording differs slightly from run spec R5 (e.g. “Save campaign…” vs “The save campaign…”).
- **Suggested fix:** Remove stale “extend Expected files” note; align cause-line strings between run `spec.md` and domain spec (either direction).

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-019 `in_progress`; domain spec linked; Expected files align with Affected paths |
| registry_gap | **PASS** | false — session persistence owns behavior; domain § APP-019 added |
| AC testability | **PASS** | Ticket AC maps to R2–R5 copy + retry; blocked only by SPEC-001 emit contract |
| Code traces | **PASS** | Command failure `orchestrator.py:535–539`; silent death `424`; silent run_ended `558–564`; `_emit_recovery_narration` `309–311`; UI `clear_narration` on new game `283–284` |
| Domain spec sync | **PASS** | Run spec ↔ domain § New game failure — contexts, mapping, tests aligned except minor copy wording |
| AGENTS.md | **PASS** | App-only; no canon drift; no new domain spec |
| Tests/commands | **PARTIAL** | T-019a–f listed; B/C JSONL asserts thin (SPEC-002) |

## Acceptance criteria mapping

| Ticket AC | Spec | Testable | QA |
|-----------|------|----------|-----|
| Show clear error with cause + retry hint when new game fails | R0–R5, contexts A/B/C | T-019a–d, manual TC-A–C | **FAIL** until SPEC-001 resolved (context B emit) |

## Summary

Spec quality is strong overall: three failure contexts, APP-071 parity, cause mapping, ticket Expected files fixed, domain spec updated. **One blocker:** death-restart failure path does not reconcile R1’s `_emit_recovery_narration` mandate with the existing combat caller pattern that always uses `_emit_narration`. PM must document the caller contract before Dev plan.

## Re-review focus

- Context B emit ownership (helper vs both combat call sites) and drift silence (T-019e on death failure).
- T-019c/d dual JSONL assertions.
- Optional: pin R6 sentinel string if UI status boost is kept optional.
