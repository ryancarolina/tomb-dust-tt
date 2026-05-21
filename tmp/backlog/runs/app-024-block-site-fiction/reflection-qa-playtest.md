# Reflection: QA — playtest (APP-024)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `human-test-plan.md`, `reflection-qa-playtest.md`

## Completed

- Read ticket APP-024 AC, run `spec.md` § Human playtest hints, domain spec § Site-entry fiction gate, `qa-implementation-pass.md`, and `test_exploration_site_entry_gate.py` (7 automated cases).
- Mapped manual cases to ticket AC, spec E1–E6/E8, and impl QA handoff (surface wrong-tool, failed entry + banner, happy path, in-dungeon bypass, travel regression).
- Wrote TC-1 pytest gate plus seven PyGame TCs (setup at Breley `32-C`, block without commit, `all_failed` leak path, successful entry, in-dungeon bypass, travel regression, optional sticky-retry).
- Pinned exact `_SITE_ENTRY_REFUSAL_LINE` copy and marker failure signals from `orchestrator.py` for human observers.
- Documented LLM variance, APP-022/077/028 boundaries, and TC-8 as optional (pytest-primary for success-then-failed retry).

## Self-critique

- Did not run manual PyGame — plan derived from spec, domain spec, impl QA pass, orchestrator sanitizer markers, and APP-065/APP-017 playtest table patterns.
- TC-4 (`all_failed and content`) is **probabilistic** with live LLM — steps allow skip-to-TC-5 and retry; human may need multiple surface turns to trigger failure banner without success commit.
- Did not include dedicated **`site_enter`** manual path — engine/site mode mirrors `dungeon` bypass in code; happy path TC-5 focuses on Breley **`enter_dungeon` → `32-C-UG-1`** (domain spec manual verification).
- Commit hash left **`pending`** — APP-024 impl may ship in batch commit APP-024/APP-028/APP-080 per batch board.
- No JSONL drift assertions — E7 `premature_site_entry` telemetry deferred per impl QA.

## Did I miss anything?

| Check | Status |
|-------|--------|
| Ticket scope / Expected files | OK — manual play only; no engine/bridge change claims |
| Domain spec § Site-entry fiction gate | OK — refusal copy, gate conditions, manual verification hints |
| Both ticket AC (block; sticky commit) | OK — TC-3/4 + TC-1/8 |
| `all_failed and content` path | OK — TC-4 |
| In-dungeon bypass (E3) | OK — TC-6 |
| Dual tool `site_enter` | Partial — auto test only; noted in self-critique |
| Travel / false-positive regression | OK — TC-7 + notes |
| pytest before manual | OK — TC-1 |
| Combat APP-028 non-regression | OK — out of scope note (covered by regression slice at impl QA) |

## Handoff

- **Ready for:** Stage 7 human execution after APP-024 commit; tick `status.md` human-test-plan checklist.
- **Escalate human if:** TC-1 passes but TC-3/TC-4 show interior/entry prose on surface without tool commit; TC-6 strips legitimate in-dungeon room narration; TC-7 collapses non-entry travel to refusal; TC-5 succeeds mechanically but all entry prose stripped.
