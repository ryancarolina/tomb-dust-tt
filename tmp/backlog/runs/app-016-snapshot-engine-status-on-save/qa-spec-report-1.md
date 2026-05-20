# QA Report: spec — round 1

**Task:** APP-016-snapshot-engine-status-on-save
**backlog_ticket:** APP-016
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) — cross-refs at checklist L58, batch table L152, changelog L319; run [`spec.md`](spec.md) L86
- **Issue:** PM changelog and run spec claim a full **§ Engine status snapshot on save (APP-016)** with **S5 write rules**, but that section **does not exist** in the domain spec. Content jumps from § New game — creation block clear (APP-015) to § Tests; only **Tests APP-016** (T4a–d) and file-map/changelog lines mention `engine_status`.
- **Implementation gap:** Dev has no authoritative domain behavior for write shape, failure semantics (`null` vs omitted), single-`get_status()` optimization, or schema examples. Run `spec.md` R1–R3 are not mirrored in the domain spec source of truth.
- **Suggested fix:** Add `## Engine status snapshot on save (APP-016)` before § Tests with: field name `engine_status`; payload = full `get_status()` / `handle_status` dict; write triggers (S5); failure handling; backward compatibility; batch notes (APP-014/015/017/018). Update top § Spec persist bullet to include `engine_status`. Align changelog with actual content.

### SPEC-002 — blocker

- **Location:** Run [`spec.md`](spec.md) R3 vs domain § New game — creation block clear (APP-015) C2 / C4
- **Issue:** **Batch boundary conflict.** APP-016 R3 requires APP-015 to **clear or replace `engine_status` on new game** so stale `awaiting` cannot survive. Domain APP-015 C2 **preferred** path says surgical `creation_state` write must leave **`engine_status` unchanged** when present. APP-015 run spec lists APP-016 as a **non-goal**.
- **Implementation gap:** Parallel batch impl could leave post-wipe disk with fresh `creation_state` (NAME) and pre-wipe `engine_status.awaiting` / `roster` after engine empty — undermining the stated purpose of save-time snapshots for reconcile.
- **Suggested fix:** Pick one owner and document in **both** domain sections: (A) APP-015 extends C2 to null/remove `engine_status` on every `setup_new_game` entry (update APP-015 run spec + T-015 tests), or (B) APP-016 owns clear via whole-file delete on new-game success only and APP-015 must **omit** `engine_status` on surgical write (explicit in C2). Remove contradictory R3 wording once resolved.

### SPEC-003 — blocker

- **Location:** Run [`spec.md`](spec.md) R3 AC; domain spec (missing § APP-016)
- **Issue:** R3 requires documenting that **APP-017 / APP-018 consume `engine_status` on load**. No such consumer note exists in the domain spec (and APP-017/018 tickets have no `engine_status` AC yet).
- **Implementation gap:** Downstream tickets may implement reconcile without referencing the snapshot field PM positioned as prerequisite.
- **Suggested fix:** In new § APP-016, add a short **Consumers** subsection: write-only in APP-016; APP-017/018 read/reconcile (out of scope); no load-path changes in APP-016. Optional one-line forward pointer in APP-017 ticket Notes (not required for APP-016 PASS if domain spec is complete).

### TICKET-001 — blocker

- **Location:** [`tmp/backlog/app-016-snapshot-engine-status-on-save.md`](../../app-016-snapshot-engine-status-on-save.md) **Expected files**
- **Issue:** `app/save/load code` is not a valid repo path (research-brief and PM reflection already flag this). Plan QA **plan files ⊆ Expected files** will fail Dev unless ticket is corrected.
- **Suggested fix:** Set Expected files to at least `app/ui/app.py`, `app/tests/` (new/extended save tests), `tmp/app-session-persistence-spec.md`. Add `app/gm/orchestrator.py` only if batch resolution assigns `engine_status` clear on new game to orchestrator.

## Summary

Run-local `spec.md` is structurally sound (problem, R1–R2, T4, code traces, registry_gap false, APP-017/018 correctly out of read scope) and matches current `_save_session()` behavior in `app/ui/app.py`. **FAIL** because the **domain spec lacks the promised APP-016 behavior section**, the **top-level persist list omits `engine_status`**, **APP-015 vs APP-016 batch rules contradict**, and the **ticket Expected files** block plan/impl gates.

## Re-review focus

- Confirm `## Engine status snapshot on save (APP-016)` exists with S5 write rules and matches run `spec.md` R1–R3.
- Resolved APP-015 / APP-016 ownership for `engine_status` on **new game** (surgical clear vs omit vs full delete).
- Ticket Expected files list real paths ⊆ implementation plan.
- § Spec persist bullet includes `engine_status`.
- Optional: canonical `engine_status` shape on `get_status()` failure (`null` vs key omitted).
