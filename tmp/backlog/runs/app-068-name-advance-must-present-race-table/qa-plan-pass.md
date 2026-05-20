# QA PASS: plan

**Task:** APP-068-name-advance-must-present-race-table  
**backlog_ticket:** APP-068  
**ticket_path:** tmp/backlog/app-068-name-advance-must-present-race-table.md  
**Round:** 1  
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress` (`tmp/backlog/app-068-name-advance-must-present-race-table.md`)
- [x] Ticket domain spec matches spec/plan updates (`tmp/app-character-creation-spec.md` — § NAME→RACE same-turn presentation APP-068, § Tests APP-068)
- [x] Acceptance criteria testable (plan tasks 1–3 map to run `spec.md` R1–R3 and ticket AC; task 4 = changelog on close)
- [x] Code traces match repo (independent traces below)
- [x] AGENTS.md / canon compliance (orchestrator creation path + tests only; no `build/` changes)
- [x] Tests/commands listed (`cd app && python -m pytest tests/test_creation_flow.py -q`; focused test names in plan §3)
- [x] Plan files ⊆ ticket Expected files (exact three paths; no out-of-scope edits)
- [x] registry_gap N/A at plan stage (spec `registry_gap: false` confirmed in qa-spec-pass)

## Independent code traces (plan accuracy)

| Plan claim | Verified location | Result |
|------------|-------------------|--------|
| NAME success returns chain with empty `prior` | `orchestrator.py` L721–724 | Confirmed — `_execute_creation_choice("NAME", …)` then `return self._chain_after_creation_choice("")` |
| Chain RACE branch → `_auto_present_race` | `orchestrator.py` L843–845 | Confirmed |
| Chain default → `"The clerk waits."` | `orchestrator.py` L867 | Confirmed — `return prior or "The clerk waits."` (only source when `prior == ""`) |
| `_auto_present_race` sets flag + code table + compose footer | `orchestrator.py` L681–691 | Confirmed — `races_table_shown = True`; `format_races_table()` body; `_compose_creation_narration` adds `format_creation_status` |
| Footer `Awaiting: RACE_INPUT` | `creation.py` L69–71, L538–541; `orchestrator.py` L521 | Confirmed — `CREATION_STATUS_LABELS["RACE"]` → `RACE_INPUT` |
| Table strings for test assertions | `creation.py` L544–555 | Confirmed — `Pick **one race**`, `\| Race \| Adjustments \| Description \|` |
| `advance()` resets `races_table_shown` on RACE entry | `creation.py` L215–220 | Confirmed — flag False until `_auto_present_race` |
| RACE commit requires `races_table_shown` | `orchestrator.py` L1199–1201 | Confirmed — plan Flow B turn-2 routing preserves guard |
| `_creation_turn_body` RACE auto-present gating | `orchestrator.py` L590–596 | Confirmed — `not races_table_shown` branch; after fix turn 1 sets flag True |
| Integration test gap (step only, no narration) | `test_creation_flow.py` L35–47 | Confirmed — `"Dumpy"` turn asserts `step == RACE` only; no table/footer checks today |
| Mock flavor stub | `conftest.py` L54 | Confirmed — `"Test narration."` prepended; code table strings still assertable |

## Spec / ticket / plan alignment

| Ticket AC | Plan task | Spec R |
|-----------|-----------|--------|
| NAME success same turn returns `_auto_present_race()` body (table + footer) | §1 | R1 |
| Never bare `"The clerk waits."` when `step == RACE` and race unset | §1 + §2 | R2 |
| Integration test: name → race header + `Awaiting: RACE_INPUT` | §3a + §3b | R3 |

Flows A–D in `plan.md` match live orchestrator routing and domain spec § NAME→RACE / § Tests APP-068. Task 1 (direct `_auto_present_race` after NAME commit) removes chain as single point of failure for the observed session bug regardless of unproven `step` mismatch inside `_chain_after_creation_choice`.

## Scope gate

Plan **Files touched** ⊆ ticket **Expected files**:

| Path | In plan | In ticket |
|------|---------|-----------|
| `app/gm/orchestrator.py` | ✓ | ✓ |
| `app/tests/test_creation_flow.py` | ✓ | ✓ |
| `tmp/app-character-creation-spec.md` | ✓ (close only) | ✓ |

No APP-059/066, duplicate-table recovery, debug logging, or new domain spec — matches run `spec.md` non-goals.

## Notes (non-blocking)

- **Root cause unproven:** Session log shows `advanced_to: RACE` while chain fallthrough narrates clerk-waits with no `llm_request`; plan correctly treats Task 1 as the fix that does not depend on reproducing `self.creation.step` inside chain. Task 2 is defensive for R2 wording; given current `_chain_after_creation_choice` structure, the pre-fallthrough RACE guard is **unreachable** when `step == "RACE"` at function entry (existing L843–845 already returns). It does not hurt AC; impl may collapse to Task 1 only if Dev verifies no double `_auto_present_race`.
- **Flavor system string:** Plan uses `"[SYSTEM: Step auto-advanced from name. Continue.]"` vs chain `"[SYSTEM: Step auto-advanced. Continue.]"` — affects thin flavor context only, not table/footer AC.
- **Plan line refs:** Slightly off on `_execute_creation_choice` NAME block (plan cites ~1193–1197; name assignment L1193–1197, `advance()` + log L1280–1285) — non-blocking; symbols and order are correct.
- **pytest not run** at plan stage (expected); impl QA must run commands in plan § Test commands.
