# Reflection: QA human playtest plan — APP-026

**Role:** QA (Stage 7 — human playtest plan)  
**backlog_ticket:** APP-026  
**Deliverable:** `human-test-plan.md`

## Completed

- Read ticket APP-026, run `spec.md`, `plan.md`, `qa-implementation-pass.md`, domain spec § Combat attack gating (APP-026), and `app/tests/test_combat_attack_gating.py` (G1–G8 + G6b).
- Cross-read APP-028 `human-test-plan.md` TC-3 for narration strip expectations; updated canonical error to **`no active combat for session`** (gate before bridge, not engine `attacker not in combat`).
- Authored `human-test-plan.md` scoped to **attack gating outside combat**: pytest gate (TC-1), exploration setup (TC-2), primary outside-combat attack (TC-3), retry idempotence (TC-4), optional surface preparation (TC-5).
- Mapped ticket AC and spec R1/R2 to manual steps, global pass/fail signals, JSONL checks, and banned success-fiction substrings aligned with APP-028 pytest lists.
- Documented out-of-scope items (in-combat initiative G5/G8, happy path G6/G6b) as pytest-owned per user scope.

## Self-critique

- **Did not run manual playtest** — plan only; human tester must execute in PyGame with live LLM.
- **Did not re-run pytest** in this gate (impl QA already reported 20/20 green); TC-1 delegates to tester.
- **Commit hash** left **pending** — latest `HEAD` is unrelated (APP-060); tester must use commit containing APP-026 orchestrator changes when Stage 7 lands.
- TC-3 allows absurd targets (e.g. attacking clerk) to force `combat_attack` tool call — gate checks combat context, not target validity; may feel odd in play but isolates AC.
- Did not add manual TC for in-combat initiative gate (G5/G8) — intentional per task focus; pytest is authoritative for that path.

## Not verified (explicit)

- [ ] Live PyGame session for any TC
- [ ] JSONL `"error": "no active combat for session"` end-to-end with live LLM
- [ ] LLM reliably calls `combat_attack` on first player phrasing (may need retry)
- [ ] TTS reads failure prefix aloud (APP-041 scope — not APP-026 AC)
- [ ] Flow B: `combat_attack` blocked by combat-only tool guard during active combat (documented out of scope)

## Handoff

**Orchestrator:** Stage 7 — human executes `human-test-plan.md`, fills sign-off, then commit APP-026 if not already done; update `status.md` Stage 7 ✅ with commit hash.

**If TC-3 fails with `attacker not in combat` instead of `no active combat for session`:** Gate not wired on exploration path — bridge reached before `_gate_pc_attack` (regression to pre-APP-026).

**If TC-3 shows correct prefix but hit fiction appended:** APP-028 strip regression — check `_llm_loop` `all_failed` branch for `_COMBAT_TOOL_NAMES`, not gate logic.

**If TC-1 passes but TC-3 silent / no tool call:** LLM did not invoke `combat_attack` — retry phrasing from TC-4; not an APP-026 failure unless gate error never appears after explicit attack intent.

**Blockers from this gate:** None (plan artifact only).
