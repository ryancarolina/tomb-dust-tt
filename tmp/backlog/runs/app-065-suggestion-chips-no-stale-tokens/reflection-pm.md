# Reflection: PM — APP-065 suggestion-chips

**Agent:** PM
**Round:** 1
**Deliverables:** `spec.md`, `tmp/app-pygame-ui-spec.md` (Suggestion chips section), `reflection-pm.md`

## Completed

- Wrote run-local `spec.md` with six requirements: always-clear, code-owned builder, `creation.step` map (not `Awaiting` labels), blocklist, click semantics, domain sync.
- Expanded domain spec **Suggestion chips** subsection: source-of-truth table, lookup order, v1 curated map, blocklist, always-refresh rule, batch note for APP-073.
- Confirmed `registry_gap: false` — no new `tmp/app-*-spec.md`; behavior lives in existing pygame-ui owner.
- Mapped ticket AC to R1–R6 and test/human-playtest hints; documented APP-073 impl preference without making chips depend on narration strip.

## Self-critique

- **WORLD_INTRO / RECEPTION_CHOICE:** Spec deliberately leaves `[]` chips at world intro; ticket mentioned exploration actions TBD — QA may ask whether reception should offer chips (e.g. “Enter the tomb”) in a follow-up ticket.
- **`app/ui/suggestions.py`:** Recommended in spec but not in ticket Expected files; Dev should add path to ticket before impl or colocate in `orchestrator.py` to avoid hook scope issues.
- **Test file path:** Proposed `app/tests/test_ui_suggestions.py` — not in Expected files; acceptable for pytest but Dev plan should cite it or extend an existing module.
- Did not re-read full `agents.md` PM checklist line-by-line after templates — relied on SKILL registry_gap table.

## Did I miss anything?

- [x] Ticket scope / Expected files — stayed within listed paths + proposed `ui/suggestions.py` under domain-owned `app/ui/**`
- [x] Domain spec / registry_gap / AGENTS.md — updated `app-pygame-ui-spec.md`; no orphan spec file
- [x] Code paths — echoed research traces (`_extract_suggestions`, `get_status` gap, `is_equipment_confirm`)
- [x] Tests or AC mapped — R1–R4 AC + pytest commands in spec
- [ ] **APP-075 batch mate** — no chip impact expected; no cross-spec edit
- [ ] **Display vs submit split** — deferred v1; flagged if QA wants labeled chips with different submit strings

## Handoff

**Ready for:** QA spec review (adversarial) — round 1

**Escalate human if:** Product wants reception/world-intro chips in v1 (not in ticket AC) or combat action chips beyond empty default.
