# Reflection: QA — playtest (APP-077)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-077 AC, run `spec.md` § Human playtest hints, domain spec § Code-owned status footer (APP-077), `qa-implementation-pass.md`, and `test_exploration_status_footer.py` (10 automated cases).
- Mapped manual cases to ticket AC (exploration/combat footer contract, wrong-GP strip, meta leak, APP-024 regression) and impl QA adversarial notes (IMPL-NOTE-004 prefix-only combat skip, F11 drift telemetry optional).
- Wrote TC-1 pytest gate (four regression commands from impl QA) plus nine PyGame TCs: setup at `32-C`, surface single-footer + GP authority, delve display address, multi-turn strip defense, combat `Turn:` segment, meta leak, APP-024 refusal+footer, optional mechanics-failed footer.
- Pinned footer shape strings, global pass/fail table, and stats-sidebar GP cross-check as primary human signal for wrong-GP bug (session `2026-05-22` repro class).
- Documented probabilistic LLM variance (TC-5 structural checks vs forced wrong GP), combat skip path, gold-in-transit footer format, and minimum manual bar (TC-1/2/3/5).

## Self-critique

- Did not run manual PyGame — plan derived from spec, domain spec, impl QA pass, test fixtures (`FOOTER_*` golden strings), and APP-023/024/065 playtest table patterns.
- **Wrong-GP repro is observational, not injectable** — human cannot reliably force LLM to emit `GP: 999`; TC-5 relies on counting bracket lines and sidebar ↔ footer parity across several turns (mirrors `test_compose_exploration_single_footer` / `test_combat_turn_compose_wrong_gp` intent without mocks).
- TC-6 combat depends on session content/encounters — marked skippable with TC-3/5 as minimum; did not pin a deterministic combat spawn command (engine content variance).
- TC-8 APP-024 refusal is **probabilistic** if LLM calls entry tool — aligned with APP-024 playtest pattern (pytest-primary fallback).
- Commit hash left **`pending`** — APP-077 may ship in batch with APP-025/030 per batch board.
- No dedicated JSONL assertion table for `exploration_drift` — F11 telemetry optional per ticket; TC-3 step 7 mentions optionally only.

## Did I miss anything?

| Check | Status |
|-------|--------|
| Ticket scope / Expected files | OK — manual play only; no new code claims |
| Domain spec § APP-077 footer contract | OK — field mapping, compose order, combat `Turn:` |
| Both ticket AC (exploration + combat footer) | OK — TC-3/4/5 + TC-6 |
| Wrong GP integration AC | OK — TC-3, TC-5, TC-6 (sidebar parity + single footer) |
| Meta leak strip (F5) | OK — TC-7 |
| Empty body / refusal footer (F7) | OK — TC-8 |
| APP-024 regression | OK — TC-8 + pytest gate TC-1 step 2 |
| APP-073 creation regression | OK — TC-1 step 3 |
| Mechanics failed + content footer | OK — TC-9 optional |
| IMPL-NOTE-004 combat prefix-only skip | OK — TC-6 out-of-scope note |
| Gold in transit format | OK — Notes section |
| APP-065/041/083 boundaries | OK — Notes section |

## Handoff

- **Ready for:** Stage 7 human execution after APP-077 commit; tick `status.md` human-test-plan checklist when executed.
- **Escalate human if:** TC-1 passes but TC-3/5 show duplicate `[Location:` lines or footer GP ≠ stats sidebar; TC-6 combat success path missing `Turn:`; TC-7 shows `Campaign Memory Updated`; TC-8 refusal turns are bracket-only; TC-4 loses footer after dungeon entry.
