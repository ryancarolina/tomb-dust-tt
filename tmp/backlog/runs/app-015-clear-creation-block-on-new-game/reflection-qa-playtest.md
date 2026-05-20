# Reflection: QA — APP-015 human playtest plan

**Agent:** QA  
**Round:** 1 (Stage 7)  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket AC (single item), run `spec.md` § Human playtest hints, domain spec § **New game — creation block clear (APP-015)** (C1–C3, T-015a–d), `qa-implementation-pass.md`, and `templates.md` § human-test-plan.
- Wrote **TC-0** pytest gate (`test_creation_block_on_new_game.py` + `-k` filter) before manual work.
- Wrote **TC-1** primary path: live creation through **SKILLS** (`Flupps` / `human` / `apprentice` aligned with pytest seed), inspect `app/session_state.json`, **`new game`**, assert disk `NAME` + empty `name` / no stale roll/skills.
- Wrote **TC-2** `load game` variant B checks (no SKILLS / old name in copy; `[Awaiting: NAME_INPUT]`) — maps T-015c / APP-071.
- Wrote **TC-3** `engine_status` absent/null after `new game`, optional manual seed for T-015d.
- Wrote **TC-4** clean-boot non-regression; **TC-5** optional failure path deferring to T-015b pytest when not reproducible.
- AC / T-015 mapping table and adjacent-ticket notes (APP-014/016/018/019).

## Self-critique

- TC-1 step 5 depends on LLM following creation FSM (`apprentice` → SKILLS); if GM drifts, use Dev seed shortcut in plan § TC-1 optional block.
- TC-3 fake `engine_status` seed is adversarial — normal autosave may already satisfy T-015d; step 2 marked optional.
- Commit hash left `pending` — APP-015 impl may be local/uncommitted per impl QA (`??` test file); human should pin rev when Stage 7 lands.
- Did not run pytest in this QA pass (impl QA already reported 5/5 green); human TC-0 should re-run before playtest.

## Did I miss anything?

- [x] Ticket scope / Expected files (orchestrator + tests; no UI edit required)
- [x] Domain spec C1–C3 + T-015a–d + batch note vs APP-016
- [x] Spec human hints: SKILLS inspect → new game → disk; failure reload; happy NAME desk
- [x] Pytest commands from repo root
- [x] Manual `cd app && python main.py` stale SKILLS → **new game** → NAME
- [x] Pass/fail checkboxes + sign-off + templates structure
- [ ] Human executed TC-1–TC-4 — plan only; tester runs post-commit

## Handoff

**Ready for:** Stage 7 commit + human sign-off on TC-0–TC-4  
**Escalate human if:** TC-1 step 10 shows `SKILLS` or old `name` after `new game`, or TC-2 cites prior step/name — indicates C1–C2 not running at `setup_new_game` entry or UI undoing orchestrator clear.
