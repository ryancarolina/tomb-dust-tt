# QA PASS: plan

**Task:** APP-070-block-premature-pre-delve  
**backlog_ticket:** APP-070  
**ticket_path:** tmp/backlog/app-070-block-premature-pre-delve-narration.md  
**Round:** 1  
**domain_spec_creation:** not_needed (spec QA round 1 confirmed `registry_gap: false`)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-character-creation-spec.md` § Block premature completion copy APP-070)
- [x] Acceptance criteria testable (C1–C5 compose, D1–D2 drift, T1 regression)
- [x] Code traces match repo (symbols and call order spot-checked; line refs ~accurate)
- [x] AGENTS.md / canon compliance (app-only; flavor-layer only; no engine canon drift)
- [x] Tests/commands listed (`test_creation_flow.py` T1 + full file + `test_creation_gating.py`)
- [x] Plan files ⊆ ticket Expected files (strict equality)
- [x] registry_gap matches reality (N/A at plan gate — `false` per qa-spec-pass)
- [x] Single enforcement path: compose sanitizer (P0) → drift telemetry (P0) → T1; D2 optional

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/creation.py` (`sanitize_premature_completion_flavor`) | Yes |
| `app/gm/orchestrator.py` (`_compose_creation_narration`, `_check_creation_drift`, `_PRE_DELVE_PHASES`) | Yes |
| `app/tests/test_creation_flow.py` (`test_skills_turn_rejects_premature_completion_flavor`) | Yes |
| `tmp/app-character-creation-spec.md` (changelog on close) | Yes |

No edits to `logger.py`, `tools.py`, `conftest.py`, or APP-069/072/073 scopes.

## Code trace audit (adversarial)

| Claim | Repo check | Result |
|-------|------------|--------|
| `_compose_creation_narration` at 520–537; flavor-only compose path | `orchestrator.py:520–537` | Match |
| All `_auto_present_*` + finalize success use compose | Grep call sites 692–1055 | Match |
| `_check_creation_drift` scope + early parse exit 196–197 | `orchestrator.py:180–234` | Match; D1 inserts before `if not reasons: return` |
| `_PREMATURE_EXPLORE_PHASES` at :65 | Present | Match |
| `_auto_finalize` roster gate 1018–1026; `footer=` 1054–1055 | Present | Match; C2 guard valid |
| `strip_llm_status_tags` bracket-only; unbracketed `Phase:` survives | `creation.py:532–535`, `_LLM_STATUS_TAG_RE` | Match — sanitizer required for T1 BAD_FLAVOR |
| SKILLS commit → `_chain_after_creation_choice` → `_auto_present_schools` | `768–794`, `854–866`, `894–908` | Match — T1 inject on schools `_narrate_flavor` |
| `CREATION_STATUS_LABELS` / post-SKILLS footer `SPELL_SCHOOLS_INPUT` | `creation.py:69–80`, `538–541` | Match — `RECEPTION_CHOICE not in last` assert is meaningful |
| `INPUTS` turn 5 = skills input → `SPELL_SCHOOLS` | `test_creation_flow.py:26–35` | Match (indices 0–4 then turn 5) |
| Golden path turn 8 `RECEPTION_CHOICE` + `Phase: preparation` allowed | `test_creation_flow.py:92–94` | Regression guard in plan |

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| No `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” until finalize + non-empty roster | §1 C1–C5 sanitizer in `_compose_creation_narration` | T1 substring asserts + existing turn-8 guard |
| `_check_creation_drift` → `premature_exploration_phase` when `roster_len == 0` | §2 D1a–D1c (`_PRE_DELVE_PHASES`, gated `len(roster)==0`) | Optional drift capture in T1; not required if sanitizer total |
| Regression: mock bad LLM at SKILLS; FSM/roster unchanged | §3 T1; patch `_narrate_flavor` before turn 5 only | `creation.step == SPELL_SCHOOLS`, `roster` empty, forbidden strings absent |

## Scope boundary (re-check)

| Topic | Plan handling |
|-------|---------------|
| APP-009 `_auto_finalize` roster gate | Do not modify — regression table |
| APP-069 flavor FSM alignment | Non-goal |
| APP-072 duplicate tables | Non-goal |
| APP-073 bracket tag strip | Non-goal; C5 re-strip after sanitizer only |
| `_creation_llm_loop` / non-compose narration | Out of scope; creation desk uses compose path |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket / Expected files | **PASS** | Four-file touch list equals ticket |
| Trace topology | **PASS** | Flow A + compose/drift traces independently verified |
| AC testability | **PASS** | T1 turn index and assertions align domain § Tests APP-070 |
| Regression | **PASS** | Legitimate `footer=` path explicitly excluded from sanitizer |
| APP-009 non-regression | **PASS** | Empty-roster finalize return string bypasses compose — unchanged |

## Notes (non-blocking; implementation QA)

1. **Drift vs sanitizer:** If C3 blanks flavor and footer is code-only `Awaiting: *_INPUT`, `parse_narration_status_line` may not see `PRE_DELVE`/`RECEPTION_CHOICE` — D1 is belt-and-suspenders; T1 does not require drift events.
2. **D1a without `creation.active`:** Plan gates on `roster_len == 0` only for D1a — matches domain spec table; correct for `CHARACTER_CREATION` + empty roster edge.
3. **Helper naming:** Plan exports `sanitize_premature_completion_flavor` (public); domain spec allows `_sanitize_*` — cosmetic only.
4. **D2 optional:** Ship D1-only acceptable per spec; impl may skip `premature_completion_copy` if compose is total.
5. **Claim session:** Implementer must `focus APP-070` / active batch before `app/` edits (hooks).

**Verdict:** PASS — ready for Stage 4 (workstreams + implementation).
