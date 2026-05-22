# QA PASS: plan — round 1

**Task:** app-073-strip-llm-embedded-status-tags-in-creation  
**backlog_ticket:** APP-073  
**ticket_path:** [tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md](../../app-073-strip-llm-embedded-status-tags-in-creation.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (spec QA confirmed `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches plan (`tmp/app-character-creation-spec.md` § Flavor sanitization pipeline APP-073)
- [x] Acceptance criteria testable (S1–S8 → locus + tests mapped below)
- [x] Code traces match repo (symbols and compose order spot-checked; line refs accurate ±0)
- [x] AGENTS.md / canon compliance (app-only sanitizers; no `build/` drift)
- [x] Tests/commands listed (`test_creation_flavor_sanitize.py` + APP-072/flow regressions)
- [x] Plan files ⊆ ticket Expected files (strict equality on impl set)
- [x] registry_gap matches reality (N/A at plan gate — spec QA confirmed `false`)
- [x] Single compose choke point (`_compose_creation_narration` only; footer/body never sanitized)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/creation.py` — hardened `strip_llm_status_tags`, `strip_flavor_stats_table` | Yes |
| `app/gm/orchestrator.py` — import, compose hook L638, `_auto_roll_stats` prompt | Yes |
| `app/tests/test_creation_flavor_sanitize.py` (new) | Yes |
| `tmp/app-character-creation-spec.md` (changelog + file map on close) | Yes |

Explicit out-of-scope: `app/ui/app.py` (APP-065), `app/gm/system_prompt.py`, `app/gm/logger.py`, `conftest.py`, cross-step skill/school/class table strip — no unauthorized paths.

## Code trace audit

Independent spot-check against live repo:

| Symbol / flow | File | Present | Plan ref |
|---------------|------|---------|----------|
| `_LLM_STATUS_TAG_RE` line-anchored `Awaiting:` only | `creation.py` L82–85 | Yes | S1 |
| `strip_llm_status_tags` | `creation.py` L537–540 | Yes | S1 |
| `strip_flavor_race_table` (APP-072 template) | `creation.py` L548–568 | Yes | S2 mirror |
| `_compose_creation_narration` flavor pipeline | `orchestrator.py` L628–662 | Yes | S3–S4 |
| C5 re-strip `strip_llm_status_tags` only when premature mutates | `orchestrator.py` L651–652 | Yes | S4 |
| `_auto_roll_stats` mixed-signal prompt (“Present attribute roll…”) | `orchestrator.py` L1111–1114 | Yes | S5 |
| `_auto_finalize` explicit `footer=` bypass | `orchestrator.py` L1222 | Yes | Flow D |
| `format_roll_stats_table` `\| Attr \| Base \|` fingerprint | `creation.py` L619–648 | Yes | S7 |
| `_creation_flavor_messages` global no status/tables | `orchestrator.py` L688–709 | Yes | S6 baseline |
| Eight `_compose_creation_narration` call sites | `orchestrator.py` | Yes | S3 inheritance |

Planned compose order matches domain spec and APP-069/070 ordering: status → race → **stats** → `_sanitize_creation_flavor` → premature → C5 status re-strip.

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| Bracket Location/Phase anywhere in flavor | S1 regex | `test_strip_llm_status_tags_inline_awaiting` |
| Remove any `Awaiting:` in flavor | S1 global alternation | unit + compose (`_flavor_region`) |
| `_compose_creation_narration` prose-only flavor; sole body/footer | S3–S4 single hook; Flow D footer | `test_compose_flavor_sanitize_status_and_stats` |
| Prompts do not teach non-canonical labels | S5 `_auto_roll_stats` rewrite + S6 grep | grep audit; integration |
| `strip_flavor_stats_table` + compose wiring | S2 + S3 L638 | unit + compose |
| ROLL_STATS single authoritative table | S5 + S7 | `test_roll_stats_narration_single_stats_table` |
| Tests: bad status + stat flavor → clean compose | S8 | compose + integration |
| Spec sync / APP-007 on close | §6 changelog checklist | release gate |

### Spec S1–S8 map

| ID | Plan locus | Test |
|----|------------|------|
| S1 | `creation.py` `_LLM_STATUS_TAG_RE` / `strip_llm_status_tags` | `test_strip_llm_status_tags_inline_awaiting` |
| S2 | `creation.py` `strip_flavor_stats_table` after race helper | `test_strip_flavor_stats_table_unit` |
| S3 | `orchestrator.py` compose hook after race strip | `test_compose_flavor_sanitize_status_and_stats` |
| S4 | C5 status-only re-strip; footer untouched | compose test asserts single footer |
| S5 | `_auto_roll_stats` instruction L1111–1114 | integration + grep |
| S6 | `_creation_flavor_messages` + grep audit | §4.2 `rg` command |
| S7 | compose + `roll_result` trust | `test_roll_stats_narration_single_stats_table` |
| S8 | bad-flavor fixture | compose test |

## qa-spec-pass adversarial notes — plan resolution

| Spec QA note | Plan handling |
|--------------|---------------|
| F2 “dice readout” vs APP-073 clerk-only flavor | §4.1 prompt rewrite; §6 spec sync on close |
| Prompt-hygiene AC without static test | §4.2 grep audit + S5 integration |
| Flavor-region slice undefined in domain | §5 `_flavor_region` helper before first `\| Attr \| Base \|` |
| File map / checklist premature | §6 on `release --done` only |
| Session log gitignored | human-test-plan Stage 7 (unchanged) |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-073 `in_progress`; domain spec aligned |
| Plan ⊆ Expected files | **PASS** | Four files; no scope creep |
| Code traces | **PASS** | Flows A–D verified independently |
| AC testability | **PASS** | S1–S8 + ticket AC mapped |
| Single enforcement path | **PASS** | Compose hook only; body/footer never stripped |
| Regression commands | **PASS** | new module + `test_creation_tables` + `test_creation_flow` |
| APP-065/059 boundaries | **PASS** | Non-goals explicit |

## Notes (non-blocking — impl QA)

1. **LLM stub target:** Plan §5 copies `_patch_llm_content` patching `gm.orchestrator.create_client`, but `orchestrator` fixture binds `self.client` at construct time. Integration test §5.4 requires `"Test narration." not in narration` — impl must patch `orchestrator.client`, `chat_completion`, or replace client after stub; copying APP-072 patch alone is insufficient for APP-073’s stronger proof.
2. **Compose unit test setup:** §5.3 should set `orchestrator.creation.step` (e.g. `CLASS`) and `creation.active` before calling `_compose_creation_narration` so `format_creation_status` footer matches `Awaiting: CLASS_INPUT` assertion.
3. **Heading-only leak:** `strip_flavor_stats_table` step 4 drops `### Your Attributes` when followed by prose but leaves inline wrong numbers — acceptable if rare; add unit case if ticket evidence shows heading + prose-only stats.
4. **Trailing punctuation on `Awaiting:` token:** Plan §1.1 defers `\b` / cleanup until test fails — impl should paste Supa/Bumpy-style fixtures if regex leaves `SKILL_INPUT.` residue.
5. **`_flavor_region` vs classes table:** Body is `format_roll_stats_table` then `format_classes_table`; first `\| Attr \| Base \|` marker is correct; do not slice on `\| Class \|`.
6. **Session claim:** Plan open question — confirm `tmp/.active-ticket.json` before `app/` edits (hooks).

**Verdict:** PASS — ready for workstreams + implementation.
