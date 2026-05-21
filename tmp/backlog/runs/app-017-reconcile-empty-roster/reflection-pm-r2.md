# Reflection: PM — APP-017 reconcile-empty-roster

**Agent:** PM
**Round:** 2
**Deliverables:** `spec.md` (r2), `tmp/app-session-persistence-spec.md` § APP-017, `tmp/backlog/app-017-reconcile-empty-roster-on-load.md` (Expected files + AC), `reflection-pm-r2.md`

## Completed

- **SPEC-001:** Removed run spec “017 before 018” sentence. R4 merge order now matches domain § Merge order and [APP-018 run spec](../app-018-continue-creation-state/spec.md): **018 restore → 017 force-active if still inactive → `_sync_creation_from_status`**.
- **SPEC-002:** R1 AC rewritten as domain R1 table row (inactive + empty **`roster`** + **`CHARACTER_CREATION`** live or saved). Removed standalone “empty roster only” bullet; non–`CHARACTER_CREATION` **`awaiting`** explicitly no-op.
- **TICKET-001:** Expanded Expected files: `app/tests/test_reconcile_empty_roster_on_load.py` (T-017a–f, T-017c2). Ticket AC tightened to include **`CHARACTER_CREATION`** gate.
- **SPEC-003:** New run spec **R3 — Empty roster definition (`roster` vs `characters`)**; domain **R1b** table; **T-017f** (`ROSTER_SETUP` no-op); **T-017c2** stale-snapshot case (live empty wins over saved non-empty roster).

## Self-critique

- Renumbered run spec R3/R4/R5 (was R3 boundary + R4 locus) — Dev plan should reference R4 merge order and R5 locus, not old R3/R4 numbers.
- **`ROSTER_SETUP` no-op** is explicit but has no product owner ticket — acceptable deferral; QA or Dev may file follow-up if orphan-row recovery is needed in play.
- Domain spec changelog only; no duplicate merge-order edit in APP-018 section (already canonical from APP-018 PM r1).

## Did I miss anything?

- [x] QA SPEC-001 merge order
- [x] QA SPEC-002 R1/R2 guard unified
- [x] QA TICKET-001 Expected files for tests
- [x] QA SPEC-003 roster vs characters + ROSTER_SETUP
- [x] T-017c2 stale snapshot per re-review focus
- [ ] APP-018 ticket Expected files for its tests — out of APP-017 scope; 018 run spec already lists tests

## Handoff

**Ready for:** QA spec review round 2 (adversarial PASS/FAIL on updated `spec.md` + domain § APP-017)

**Escalate human if:** Product wants APP-017 to force-active on **`ROSTER_SETUP`** (orphan unslotted rows) — would need new AC and likely conflict with APP-018 gate
