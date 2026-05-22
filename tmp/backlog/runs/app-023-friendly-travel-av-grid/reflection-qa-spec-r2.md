# Reflection: QA spec — APP-023 friendly-travel-av-grid (r2)

**Agent:** QA (adversarial)
**Round:** 2
**Trigger:** PM r2 revision after `qa-spec-report-1.md`
**Deliverables:** `qa-spec-pass.md`, `reflection-qa-spec-r2.md`

## Completed

- Re-read round 1 FAIL report (SPEC-001 through SPEC-004, TICKET-001).
- Verified PM fixes in `spec.md`, `tmp/app-exploration-delve-spec.md` § APP-023, and ticket Expected files.
- Ran scoring proof script for apostrophe folding: `kings road` → `33-C` score **70**; `undercrypt` → `32-C-UG-1` score **70**; confirmed pre-fold score **0** for King's Road (reproduces round 1 blocker root cause).
- Cross-checked live JSON (`32-C`, `33-C`, `32-C-UG-1`) and `world.legal_exits` / `site_resolve._match_score` template.
- Wrote **PASS** for round 2.

## Self-critique

- Did not enumerate a concrete T4 ambiguity grid cell — acceptable deferral to plan phase but Dev may need PM/Dev to pick one before impl tests land.
- Did not trace whether `bridge.world_travel` today preserves `from`/`to` on resolver errors — spec requires it; plan QA should assert shape.
- Temporary scoring script deleted after verification; not committed (run-folder hygiene only).

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001 fixed
- [x] Domain spec / registry_gap — PASS
- [x] Research risks — layered pass + scoring proof now pinned
- [x] AC testability — King's Road + undercrypt provable
- [x] Beat error mapping — T7 + wiring row
- [x] Naming collision `resolve_surface` vs `resolve_surface_address` — Non-goals note
- [ ] Live PyGame repro — not run (spec stage)

## Handoff

**Verdict:** PASS (round 2)
**Report:** [qa-spec-pass.md](./qa-spec-pass.md)
**Ready for:** Dev plan + QA plan gates
**Escalate human if:** Product rejects apostrophe folding and requires JSON `tradeRoute` on road exits instead (would reopen SPEC-001)
