# QA PASS: spec

**Task:** APP-074-remove-dead-step-prompt  
**backlog_ticket:** APP-074  
**ticket_path:** tmp/backlog/app-074-remove-dead-get-step-prompt.md  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; § Step content sources updated in existing domain spec)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-character-creation-spec.md` — § Step content sources (APP-074), § Removed patterns, file map, changelog draft)
- [x] Acceptance criteria testable (R1 delete + grep; R2 live-path regression via existing pytest suite; R3 domain spec + close changelog)
- [x] Code traces match repo (`creation.py` `get_step_prompt` 742–833, definition-only; `orchestrator.py` imports `format_*` only, no `get_step_prompt`)
- [x] AGENTS.md / canon compliance (app-only deletion chore; no `build/` mechanics drift)
- [x] Tests/commands listed (`test_creation_flow.py`, `test_creation_tables.py`, `test_creation_gating.py`; post-delete `rg "get_step_prompt" app/`)
- [x] registry_gap matches reality (`false` — Character creation row in `app-master-spec.md` owns `creation.py` + orchestrator creation branch)
- [x] If registry_gap true: N/A — no § Proposed domain spec in run `spec.md` (correct)

## Ticket AC coverage

| Ticket AC | Spec / domain mapping |
|-----------|------------------------|
| Remove `get_step_prompt()` (or move hint to docs only) | **R1** — delete-only path chosen; ~92 lines at `creation.py` 742–833 |
| Grep `app/` confirms no references | **R1** — `rg "get_step_prompt" app/` must return zero matches post-delete |
| Spec: prompts in `_auto_present_*` / `format_*_table` only | **R2 + R3** — domain § Step content sources maps body/flavor/footer/commit layers; explicitly negates `get_step_prompt`; contrasts live `get_combat_step_prompt` |

## Scope gate

Run `spec.md` **Expected files** ⊆ ticket **Expected files**:

- `app/gm/creation.py` ✓
- `tmp/app-character-creation-spec.md` ✓

Non-goals exclude `system_prompt.py`, `_creation_llm_loop`, APP-059 formatter change, optional negative grep test, APP-059 backlog prose update (deferred to **close**) — no scope creep.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-074 valid, `in_progress`, domain spec matches |
| registry_gap | **PASS** | false — existing `app-character-creation-spec.md` |
| Drift policy | **PASS** | Ticket AC ↔ run spec R1–R3 ↔ domain § Step content sources aligned |
| Testability — deletion regression | **PASS** | Existing creation suite + grep AC; no new test required (chore) |
| Testability — live path unchanged | **PASS** | R2 documents full router chain; smoke + Dumpy golden path in human hints |
| Scope vs APP-059 / system_prompt | **PASS** | Boundaries in `spec.md` Non-goals; APP-059 hygiene on close only |
| Code traces | **PASS** | Research-brief + live grep: single definition, zero callers under `app/` |
| Template completeness | **PASS** | Human playtest hints (NAME→RACE smoke, APP-057 full path) |
| AGENTS.md / canon | **PASS** | App-only |

## Notes (non-blocking — Dev / close)

- **Target-state domain spec:** § Step content sources and § Removed patterns use present/past tense (“has no”, “deleted APP-074”) while code still defines `get_step_prompt` — intentional PM draft per changelog “APP-074 spec draft”. Dev must not `release --done` until code matches; on close replace draft changelog with “removed legacy prompt builder” per **R3**.
- **Ticket Evidence line numbers:** Backlog ticket cites ~639–728; function is at **742–833** after APP-067/072 insertions — spec/research have correct range; optional ticket prose fix on close.
- **`system_prompt.py`:** Still instructs `set_creation_choice` + LLM tables — documented non-goal; lingering agent confusion risk; separate follow-up if desired.
- **APP-059 backlog:** `app-059-standardize-creation-table-outputs.md` still cites `get_step_prompt` as RACE problem source — update on APP-074 close (spec Non-goals).
- **Optional guard test:** Negative grep in `test_creation_tables.py` not in AC — correctly deferred.

**Verdict:** PASS — ready for Stage 3 (Dev plan + QA plan).
