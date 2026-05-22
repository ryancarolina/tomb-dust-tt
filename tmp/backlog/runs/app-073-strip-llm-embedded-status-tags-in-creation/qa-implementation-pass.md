# QA PASS: implementation — round 1

**Task:** app-073-strip-llm-embedded-status-tags-in-creation  
**backlog_ticket:** APP-073  
**ticket_path:** [tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md](../../app-073-strip-llm-embedded-status-tags-in-creation.md)  
**Round:** 1  
**domain_spec_creation:** draft present (`tmp/app-character-creation-spec.md` § Flavor sanitization pipeline APP-073); dated “APP-073 done” changelog pending at `release --done`

## Verdict

**PASS** — APP-073 acceptance criteria and run `spec.md` S1–S8 are satisfied in code and automated tests.

## Automated tests

```text
python -m pytest app/tests/test_creation_flavor_sanitize.py -q
....                                                                     [100%]
4 passed in 0.62s

python -m pytest app/tests/test_creation_tables.py app/tests/test_creation_flow.py -q
.......                                                                  [100%]
7 passed in 1.34s
```

| Module | Tests | Result |
|--------|-------|--------|
| `test_creation_flavor_sanitize.py` | 4 (APP-073 unit + compose + integration) | ✓ |
| `test_creation_tables.py` | 2 (APP-072 regression) | ✓ |
| `test_creation_flow.py` | 5 (golden path + APP-069/070 spies) | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| `strip_llm_status_tags()` removes bracket Location/Phase anywhere | `_LLM_STATUS_TAG_RE` unchanged bracket alternates; `test_strip_llm_status_tags_inline_awaiting` bracket fixture | ✓ |
| Remove **any** `Awaiting:` in flavor (not whole-line only) | `_LLM_STATUS_TAG_RE` L83: `Awaiting:\s*[A-Z0-9_]+` (removed `^\s*…$` anchor); inline + whole-line unit cases | ✓ |
| `_compose_creation_narration` sole composer; flavor prose-only after sanitizers | L638–664: flavor pipeline only; body + `format_creation_status` appended after; compose test | ✓ |
| Prompts do not teach non-canonical labels | `rg` on `orchestrator.py`: no `SKILL_INPUT`, `MAGIC_SCHOOLS_*`, `EQUIPMENT_CONFIRMATION`; `_creation_flavor_messages` forbids status/tables; `_auto_roll_stats` clerk-only rewrite L1113–1118 | ✓ |
| Add `strip_flavor_stats_table()` mirroring APP-072 | `creation.py` L574–604: heading, `\| Attr \|`, compact `\| STR \| AGI \|`, `` `roll_attributes( `` fingerprints | ✓ |
| Wire stats strip after race strip, flavor only | `orchestrator.py` L639–640; body never passed through stripper | ✓ |
| ROLL_STATS → CLASS: one attribute breakdown; numbers match engine | `_auto_roll_stats` L1105–1124; `test_roll_stats_narration_single_stats_table`: `count("\| Attr \| Base \|") == 1`; `FIXED_ROLL` finals in narration; wrong `\| 14 \|` absent from flavor region | ✓ |
| Tests: bad status + stat table → clean compose | `test_compose_flavor_sanitize_status_and_stats` + integration test | ✓ |

## Spec S1–S8 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **S1** | Harden `strip_llm_status_tags` | `_LLM_STATUS_TAG_RE` + unit test | ✓ |
| **S2** | `strip_flavor_stats_table` block-scoped strip | `creation.py` L574–604 + unit test | ✓ |
| **S3** | Compose hook after race, before `_sanitize_creation_flavor` | `orchestrator.py` L638–641 | ✓ |
| **S4** | Single compose choke point; C5 re-strip unchanged | L651–652 status-only re-strip when premature mutates | ✓ |
| **S5** | `_auto_roll_stats` clerk-only flavor prompt | L1113–1118 | ✓ |
| **S6** | Global flavor messages + no bad labels in step prompts | L690–706 `_creation_flavor_messages`; grep clean | ✓ |
| **S7** | ROLL_STATS single authoritative table | Integration test + `roll_attributes` monkeypatch | ✓ |
| **S8** | Bad-flavor compose fixture | `test_compose_flavor_sanitize_status_and_stats` + `_flavor_region` helper | ✓ |

## Independent code traces

| Flow | Path | Result |
|------|------|--------|
| Inline wrong `Awaiting:` in flavor | `strip_llm_status_tags` → compose | Stripped; single canonical footer from `format_creation_status` |
| LLM stat table + code body | `strip_flavor_stats_table` on flavor → append `format_roll_stats_table` body | One `\| Attr \| Base \|` block |
| ROLL_STATS turn (NAME→RACE→ROLL_STATS) | `_auto_roll_stats` → `_compose_creation_narration` | Integration drives `"Spluffy"` / `"undead"` with `BAD_STAT_FLAVOR` stub |
| Body/footer trust model | `_compose_creation_narration` | Sanitizers never applied to `body` or `footer` |

**Compose order (flavor):** `strip_llm_status_tags` → `strip_flavor_race_table` (APP-072) → **`strip_flavor_stats_table` (APP-073)** → `_sanitize_creation_flavor` (APP-069) → `sanitize_premature_completion_flavor` (APP-070) → C5 status re-strip → append body + footer.

## Plan QA notes — resolution

| Plan note | Impl resolution |
|-----------|-----------------|
| Patch `orchestrator.client` after stub | `_patch_llm_content` sets both `create_client` monkeypatch **and** `orchestrator.client`; integration asserts `"Test narration." not in narration` |
| Compose test needs `creation.step` for footer | `test_compose_flavor_sanitize_status_and_stats` sets `step = "CLASS"` |
| Trailing punctuation after `Awaiting:` token | Not covered by unit fixture; regex may leave `.` after stripped token — low risk, non-blocking |
| Heading-only leak with inline wrong numbers | Heading + table path covered; prose-only wrong numbers after heading stripped but not table — acceptable per plan |

## Scope notes (non-blocking for APP-073 PASS)

| Item | Note |
|------|------|
| **Release / drift** | Ticket still `in_progress`; domain spec has APP-073 draft § + checklist item marked complete for APP-007; dated “APP-073 done” changelog row required at `release --done` |
| **Human playtest** | Not run this round (Stage 7: RACE→ROLL_STATS undead replay, drift log `awaiting_mismatch` check) |
| **APP-065 chips** | Out of scope; narration clean before chip hardening per batch board |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-073 --done` (ticket AC checkboxes, Closed date, spec changelog).  
**Human playtest:** After race pick, one attribute table; no `### Your Attributes` or wrong `Awaiting: SKILL_INPUT` in flavor region; `app/logs/session-*.jsonl` — no `awaiting_mismatch` on clean play.
