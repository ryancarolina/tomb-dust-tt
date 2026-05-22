# Reflection: QA playtest — APP-025

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-025 AC, run `spec.md` R1–R5 + T1–T5, domain spec § Registry hub loop integration test, `qa-implementation-pass.md`, `drift-check.md`, and dev-team `templates.md` § human-test-plan.
- Used APP-023 / APP-022 playtest plans as format references for Breley **`32-C`** setup, MAP/footer assertions, and optional JSONL checks.
- Ran `python -m pytest app/tests/test_registry_hub_loop.py -v` — **5 passed** (matches impl QA).
- Wrote `human-test-plan.md` with 7 TCs: **required pytest preflight (TC-1)**, optional PyGame loop TC-2–TC-5, full-session smoke TC-6, APP-022 regression TC-7.
- Mapped ticket AC and T1–T5 to manual cases; emphasized **TC-4 exit-vs-extract** as the highest-value manual check pytest cannot fully substitute (orchestrator tool choice + HUD).

## Self-critique

- Did not run live PyGame — plan derived from spec, bridge test assertions, impl QA pass, and related exploration playtest patterns; human still needed for LLM **`enter_dungeon` / `exit_dungeon` / `set_phase`** dispatch and narration quality.
- Correctly scoped manual play as **optional** — ticket is test-only; overstating manual TCs as required would misrepresent Stage 7 priority vs pytest.
- TC-3 entry prompts are probabilistic — listed multiple phrasings but cannot guarantee LLM picks **`enter_dungeon`** on first try; noted APP-024 failure signals.
- T3 **`events` `phase.set` audit** explicitly left pytest-owned — not reproducible in player UI without DB tooling.
- Commit hash left **pending** — Stage 7 commit not in `status.md` at plan write time.
- TC-6 save/resume overlaps APP-052 — marked optional/skip guidance to avoid duplicate release-smoke burden.

## Did I miss anything?

- [x] Ticket scope / Expected files — test module + domain spec; no prod changes
- [x] Domain spec § APP-025 — canonical loop table, path constraints, exit vs extract contract
- [x] Primary user scenario — Breley hub, undercrypt entry, surface return, extract declare
- [x] Tests or AC not mapped — sign-off table links T1–T5 + ticket AC; T3 pytest-only called out
- [x] Regression — APP-022 hint optional TC-7 at same repro site
- [x] Pytest as primary gate — TC-1 required; manual optional called out in scope note
- [ ] Live play verification — deferred to human tester (optional by design)
- [ ] Full `app/tests` suite — not re-run here; impl QA + focused module green

## Handoff

**Ready for:** Human tester **optionally** after Stage 7 APP-025 commit; orchestrator updates `status.md` Stage 7 checklist + commit hash in `human-test-plan.md`.  
**Escalate human if:** TC-1 fails; TC-4 shows **`Phase: extract`** immediately after **`exit_dungeon`**; TC-3 narrates entry but footer stays **`preparation`** (orchestrator/APP-024 wiring).
