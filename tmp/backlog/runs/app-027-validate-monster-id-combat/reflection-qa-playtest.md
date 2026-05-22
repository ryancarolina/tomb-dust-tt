# Reflection: QA human playtest plan — APP-027

**Role:** QA (Stage 7 — human playtest plan)  
**backlog_ticket:** APP-027  
**Deliverable:** `human-test-plan.md`

## Completed

- Read ticket APP-027, run `spec.md`, `plan.md`, `qa-implementation-pass.md`, domain spec § Monster id validation at combat start (APP-027), and `app/tests/test_combat_monster_validation.py` (V1–V8 contracts).
- Authored `human-test-plan.md` with seven test cases: pytest gate (TC-1), undercrypt setup (TC-2), **exploration unknown-id `start_combat`** (TC-3), **beat-trigger failure with dev file-hide** (TC-4), explicit **no combat HUD** sidebar checklist (TC-5), optional valid grave-ghoul smoke (TC-6), optional empty-spec note deferring to V5 (TC-7).
- Mapped ticket AC and spec R1–R6 to manual steps; global pass/fail signals include required error substrings (`monster JSON not found:`, `monster_specs required`, `invalid monster spec`) and banned combat-fiction substrings aligned with V8 / APP-028.
- Documented dual-channel beat path (`process_beat` ok:true + player failure-only text) and canonical `[Mechanics failed — combat start: …]` / `Combat could not begin.` shape from V7.

## Self-critique

- **Did not run manual playtest** — plan only; human tester must execute in PyGame with live LLM.
- **Did not re-run pytest** in this gate (impl QA already reported 12 passed, 1 skipped); TC-1 delegates to tester.
- **Commit hash** left as `pending` — Stage 7 commit for APP-027 not on `HEAD` at authoring time (`792c663` is APP-023); tester should use the commit containing APP-027 validation changes.
- **TC-4 requires temporary monster file rename** because canon `grave-ghoul.json` exists — same repro pattern as APP-028 TC-5; without hide, beat path only validates success (TC-6 optional smoke).
- **TC-3 LLM flakiness:** Model may not call `start_combat` on first phrasing — plan documents explicit retry wording; structural empty-list case (R3) is pytest-authoritative (TC-7).
- **“No combat HUD”** interpreted as phase badge **`DELVE` not `COMBAT`**, unchanged HP, exploration input still works — PyGame has no dedicated combat panel beyond phase pill and orchestrator routing (per `stats.py` / APP-035).

## Not verified (explicit)

- [ ] Live PyGame session for any TC
- [ ] TC-3 with live LLM calling `start_combat` on bogus id
- [ ] TC-4 with `grave-ghoul.json` hidden end-to-end
- [ ] TC-6 successful combat start after restore
- [ ] TTS reads failure prefix aloud (APP-041 scope — not APP-027 AC)
- [ ] Invalid format string (`not a spec`) via natural player speech — pytest V2/V9 authoritative
- [ ] Mixed-tool batch failure + success same turn (APP-027 non-goal)

## Handoff

**Orchestrator:** Stage 7 — human executes `human-test-plan.md`, fills sign-off, commit APP-027 if not done; update `status.md` Stage 7 ✅ with commit hash.

**If TC-3 fails but TC-1 passes:** Check R2 bridge pre-check and APP-028 `_llm_loop` all-failed strip — player may see raw engine traceback or appended fiction after prefix.

**If TC-4 fails:** Beat short-circuit regression — compare `_handle_combat_trigger` return vs second `chat_completion`; ensure R2 runs inside `start_combat_from_trigger`.

**If TC-5 fails (HUD shows COMBAT):** Validation passed incorrectly or orchestrator `_sync_combat_from_status` drift — file bug against R5 (`status.combat` null on fail).

**If TC-6 fails after TC-4 restore:** `grave-ghoul.json` not restored or content_root mismatch — restore file before blaming validation.

**Blockers from this gate:** None (plan artifact only).
