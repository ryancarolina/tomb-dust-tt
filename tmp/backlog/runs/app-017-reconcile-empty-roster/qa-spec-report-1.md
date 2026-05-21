# QA Report: spec — round 1

**Task:** APP-017-reconcile-empty-roster
**backlog_ticket:** APP-017
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` § R3 (lines 57–58) vs `tmp/app-session-persistence-spec.md` § Reconcile empty roster on load (APP-017) **Merge order** (line 384) and § Engine status snapshot **Consumers** (line 332)
- **Issue:** Run spec says parallel batch merge so **APP-017 runs before or as first phase of APP-018** (“018 may assume `active == true` after 017”). Domain spec (canonical per run spec § Domain spec) says **APP-018 field restore runs first**; **APP-017 force-active runs only if roster empty and `creation.active` still false after 018**. APP-016 Consumers table also states 017 forces active **after** APP-018.
- **Implementation gap:** Two implementers following different artifacts will wire opposite hook order in `orchestrator.py`, breaking batch coordination and step-restore guarantees (017 must not clobber 018’s imported step).
- **Suggested fix:** Delete the “017 before 018” sentence in run `spec.md` R3; align verbatim with domain § Merge order (018 restore → 017 force-active if still inactive). Cross-link APP-018 run spec the same way.

### SPEC-002 — blocker

- **Location:** `spec.md` § R1 acceptance criteria (lines 36–37) vs § R2 (lines 48–49) and domain § R1 table (line 365)
- **Issue:** R1 AC requires force-active whenever **`creation.active` is false and roster is empty**, with no `awaiting` guard. R2 and domain R1 require **additionally** `awaiting == CHARACTER_CREATION` (live or saved). An implementer satisfying R1 alone could force creation on empty roster + inactive when live/saved `awaiting` is `SETUP` or other non–desk states (post–`new game` / stale disk edge).
- **Implementation gap:** Over-activation risk; ticket AC mapping in domain spec is correct but run spec R1 bullets are not aligned.
- **Suggested fix:** Fold mid-creation guard into R1 AC (single row matching domain R1 table). Remove contradictory standalone “empty roster only” bullet or mark it as subordinate to R2.

### TICKET-001 — blocker

- **Location:** `spec.md` § Affected paths (lines 97–98) vs ticket **Expected files** (`app/gm/orchestrator.py` only)
- **Issue:** Run spec lists **`app/tests/`** for T-017a–e and pytest commands, but ticket Expected files do not include `app/tests/**`. Plan/impl gates require files ⊆ ticket Expected files; Dev cannot land tests without ticket expansion.
- **Suggested fix:** Add `app/tests/test_*` path(s) to ticket Expected files before Dev plan, or narrow spec to “tests added in APP-054 follow-up” with explicit ticket reference (not acceptable for this ticket’s AC).

### SPEC-003 — blocker

- **Location:** `spec.md` § R2 / T-017c (lines 48, 78) vs `research-brief.md` risk #2; current `orchestrator.py` `_sync_creation_from_status` (lines 186–191)
- **Issue:** Spec and tests use **empty `roster`** for mid-creation detection; existing reconcile uses **`not status.get("characters")`** for activation. Spec does not state whether unslotted campaign rows (`characters` non-empty, `roster` empty, `awaiting: ROSTER_SETUP`) should force `creation.active` or defer to another path — ambiguous vs ticket symptom (empty roster + inactive).
- **Implementation gap:** Dev may keep `characters` check and fail T-017a/b, or switch to `roster` and change behavior for orphan-character saves without an AC.
- **Suggested fix:** Add one AC row: reconcile empty check uses **`roster` only** (not `characters`); document `ROSTER_SETUP` + empty roster as no-op for APP-017 (or explicit owner ticket).

## Summary

Registry gate **PASS** (`registry_gap: false`, domain spec owns APP-017). Ticket valid (`in_progress`, correct domain spec). Code traces in research-brief match repo (`_load_session` → `_sync_creation_from_status`, no `engine_status` read today).

**FAIL** until: (1) merge order matches domain spec (018 then 017), (2) R1/R2 awaiting guard unified, (3) ticket Expected files include tests, (4) `roster` vs `characters` rule explicit.

## Re-review focus

- R3 merge order identical to domain § Merge order and APP-016 Consumers
- R1 AC = domain R1 table row (inactive + empty roster + `CHARACTER_CREATION`)
- Ticket Expected files lists orchestrator + test module(s)
- T-017c states live `roster` empty when saved snapshot non-empty (stale snapshot case)
