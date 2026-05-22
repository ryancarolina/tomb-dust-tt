# Reflection: QA — APP-073 playtest (Stage 7)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-073 AC, run `spec.md`, `qa-implementation-pass.md`, `qa-plan-pass.md`, domain spec § Flavor sanitization pipeline (APP-073), and APP-067/APP-074 human-test-plan templates for structure.
- Mapped five manual TCs to ticket AC (status tags + stat table leak), spec S1–S8, and Stage 7 human playtest hints from run spec.
- Centered **TC-2** on Undead roll replay (`Spluffy` / `undead`, optional `Tuffy`) — direct ticket evidence from `session-2026-05-20.jsonl`.
- Added flavor-region inspection guide mirroring `_flavor_region()` from `test_creation_flavor_sanitize.py` so testers can separate LLM prose from code body.
- Split **TC-3** (single Awaiting on roll + name/race steps) from **TC-4** (SKILLS / schools / equipment wrong-label smoke) per historical Supa/Bumpy drift cases.
- Included JSONL cross-check (TC-2 step 8–9, TC-5 `awaiting_mismatch`) and pytest gate TC-1 from impl QA commands.

## Self-critique

- Did not run PyGame playtest myself — plan only; human must execute after Stage 7 commit.
- Commit hash left `pending` because `status.md` shows Stage 7 git commit not yet landed; tester should update header after commit.
- TC-4 extended path depends on class pick (caster vs non-caster); steps note optional schools/equipment — tester may stop at SKILLS for minimum APP-073 scope.
- APP-065 chip stale-token behavior explicitly out of scope but noted — could confuse tester if chips disagree with clean footer.
- Did not add Human race TC variant — Undead was the ticket repro; optional repeat covers second evidence name only on same race.

## Did I miss anything?

- [x] Ticket scope / Expected files
- [x] Domain spec § APP-073 compose pipeline, ROLL_STATS flavor policy, canon labels
- [x] Ticket AC → TC mapping table
- [x] Play entry `cd app && python main.py`
- [x] Pass/fail checkboxes per step
- [x] Failure signals per TC
- [x] Undead roll single stat table (primary user request)
- [x] No duplicate Awaiting tags (primary user request)
- [ ] Live session execution — deferred to human tester
- [ ] Update `status.md` Stage 7 checkbox — orchestrator task

## Handoff

**Ready for:** Human tester after APP-073 commit; orchestrator updates `status.md` when playtest plan accepted.  
**Escalate human if:** TC-2 shows two `\| Attr \| Base \|` blocks or flavor-region Final values disagree with JSONL `roll_attributes` after commit (sanitizer or compose regression).  
**Minimum bar:** TC-1 + TC-2 + TC-3 pass before `release --done` batch sign-off with APP-065.
