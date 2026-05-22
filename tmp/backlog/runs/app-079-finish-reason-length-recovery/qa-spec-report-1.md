# QA Report: spec — round 1

**Task:** app-079-finish-reason-length-recovery  
**backlog_ticket:** APP-079  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` § R2 (L172) vs § Recovery matrix (L86) and § Architecture `body_pending` (L53)
- **Issue:** R2 requires every `_auto_present_*` path with **non-empty code `body`** to pass `body_pending=True`. `_auto_present_name` always composes with a non-empty `body` (`"What name shall I put on the Registry ledger?"` — `orchestrator.py` L1123–1124) while the matrix classifies NAME as `body_pending=false`, `flavor_only=true`.
- **Implementation gap:** Dev following R2 will **discard** NAME flavor on `length` and ship only the static question line — no length retry/static fallback per R3. Dev following the matrix will retry/fallback — R2 and tests disagree.
- **Suggested fix:** Add a normative definition, e.g. `body_pending=True` only when an authoritative **code table or mechanical block** (`format_*_table()`, roll-stats table, class list) is composed after flavor — **not** prompt-only strings or error prefixes. Rewrite R2 to list gated steps (RACE, CLASS, SKILLS, SPELL_SCHOOLS, SPELLS, EQUIPMENT_GOLD, ROLL_STATS, FINALIZE→WORLD_INTRO handoff) explicitly; exclude NAME. Mirror in `tmp/app-llm-orchestrator-spec.md` § Recovery matrix.

### SPEC-002 — blocker

- **Location:** `spec.md` § Recovery matrix (L86) — “WORLD_INTRO banter” under `flavor_only=true`
- **Issue:** Post-registration WORLD_INTRO presentation (`_auto_finalize` after successful `character_create`, `orchestrator.py` L1486–1501) calls `_narrate_flavor` then composes **code-owned** `body` (HP/MP/Fortune/GP/skills/kit) plus a **code footer** (`RECEPTION_CHOICE`). This is not flavor-only banter; truncated flavor above authoritative mechanical summary should follow **discard**, not retry.
- **Implementation gap:** Classifying this path as `flavor_only=true` allows a length retry while the player still needs the mechanical summary block; retry does not fix truncated tables in flavor because the harm is duplicate/partial prose above code body.
- **Suggested fix:** Remove WORLD_INTRO from the flavor-only row; add a matrix row: “Creation FINALIZE / WORLD_INTRO handoff — code summary body + footer” → `body_pending=true`, `discard_flavor`, no length retry. Add test or extend `test_creation_length_discards_flavor_when_body_pending` to cover finalize handoff if in scope.

### SPEC-003 — blocker

- **Location:** `spec.md` § Architecture (helper params); `tmp/app-llm-orchestrator-spec.md` § `finish_reason: length` recovery (matrix only)
- **Issue:** `body_pending` and `flavor_only` are never defined beyond the matrix. Call-site note “Set `body_pending` from caller context” (L101) is insufficient for Dev to wire `_auto_present_class` (inline stats + table), NAME (prompt body), and finalize handoff (summary body) consistently.
- **Implementation gap:** Ambiguous callers → wrong policy branch; APP-083 verify may run on discarded text or skip discard on table steps.
- **Suggested fix:** Add § **Semantics** with decision table: step → `body_pending`, `flavor_only`, `mode`. Include `_auto_finalize` WORLD_INTRO block and `_creation_table_flavor` (error skip, no LLM). State invariant: `body_pending` implies `flavor_only=false`.

### SPEC-004 — major (non-blocking alone)

- **Location:** `spec.md` § Recovery matrix mid-chain row (L89); test `test_mid_chain_length_strips_tables_continues` (L224)
- **Issue:** “Strip markdown table blocks” has no normative detector (pipe-row heuristic, fenced blocks, min rows). Tests cannot assert pass/fail without inventing behavior.
- **Suggested fix:** Specify strip rule (e.g. drop consecutive lines matching `^\|.*\|$` with ≥2 such lines, or reuse a shared helper name if APP-078 will own it). Reference in test AC.

### TICKET-001 — major

- **Location:** `tmp/backlog/app-079-finish-reason-length-recovery-policy.md` § Code AC (L36) vs `spec.md` § R1 / domain spec helper signature
- **Issue:** Ticket AC names `handle_finish_reason_length(...) -> str | None`; run spec and domain spec require `LengthRecoveryResult` with `action` / `retry_hint`. Ticket “discard-and-fallback” wording does not match structured result contract.
- **Suggested fix:** Update ticket Code AC to match `LengthRecoveryResult` and list actions (`pass`, `discard_flavor`, `retry`, `fallback_last_content`, `fallback_static`).

### SPEC-005 — minor

- **Location:** Ticket § Exploration AC (L31) vs `spec.md` § R4 / domain spec
- **Issue:** Ticket says “reduced `max_tokens` target” on retry; spec says prompt hint “complete in ≤3 sentences” without token change.
- **Suggested fix:** Align ticket to spec (prompt-only retry) or document explicit `max_tokens` override in spec if cost control requires it.

## Verified (partial credit)

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-llm-orchestrator-spec.md`
- [x] `registry_gap: false` — orchestrator spec updated with § `finish_reason: length` recovery, APP-083 pipeline order, shared budget
- [x] Code traces largely accurate (`_CREATION_FLAVOR_MAX_TOKENS=120`, no `length` branch today, combat final `chat_completion` ~1966 without `finish_reason` handling, `_last_content` not length-aware)
- [x] Test file and pytest commands listed; `conftest` / `_patch_llm_content` pattern exists
- [x] APP-083 coordination (discard before verify when `body_pending`, shared `NARRATION_LLM_MAX_ATTEMPTS`) is coherent **once `body_pending` is defined**
- [x] Expected files in `spec.md` match ticket + logging spec on close
- [ ] Creation spec cross-link — deferred per ticket close (acceptable if blockers fixed first)

## Summary

Run spec and orchestrator domain § are strong on goals, helper shape, APP-083 ordering, observability, and test mapping, but **normative creation wiring is internally inconsistent**: R2 contradicts the NAME matrix row, and WORLD_INTRO post-finalize is mis-tagged as flavor-only despite code body + footer. Without a explicit `body_pending` definition, implementation will ship wrong player-visible behavior on two high-traffic creation paths.

**Blocker count:** 3 (SPEC-001, SPEC-002, SPEC-003)

## Re-review focus

- Revised § **Semantics** for `body_pending` / `flavor_only` with per-step table including NAME vs gated steps vs FINALIZE handoff
- R2 rewritten to match matrix (no “any non-empty body” rule)
- WORLD_INTRO row removed from flavor-only or split into two contexts (pre-active `process_turn` vs post-finalize compose)
- Optional: mid-chain strip algorithm; ticket AC aligned to `LengthRecoveryResult`
