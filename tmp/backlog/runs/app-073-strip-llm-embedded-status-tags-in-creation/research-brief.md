# Research Brief: APP-073-strip-llm-embedded-status-tags-in-creation

**Date:** 2026-05-20  
**Question:** Why do LLM-embedded status tags and duplicate stat tables still leak into creation narration after APP-007/APP-072, and where should sanitization and tests land?

**backlog_ticket:** APP-073  
**ticket_path:** tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) is the registered owner for `app/gm/creation.py` and the creation branch of `app/gm/orchestrator.py` ([`tmp/app-master-spec.md`](../../../app-master-spec.md) § Spec registry — Character creation). APP-073 expected files (`creation.py`, `orchestrator.py`, creation flavor tests, domain spec changelog) are a subset of that domain. No new domain spec row is required.

## Summary

APP-007 shipped `format_creation_status()` (code-owned footer) and `strip_llm_status_tags()`, but the stripper regex is **narrow**: it removes bracketed `[Location:…]` / `[Phase:…]` blocks and **whole-line** `Awaiting:` only (`creation.py` `_LLM_STATUS_TAG_RE`). Inline or mid-sentence `Awaiting: SKILL_INPUT` / `MAGIC_SCHOOLS_INPUT` / `EQUIPMENT_CONFIRMATION` survives in flavor, appears **before** the code footer in composed narration, and becomes the **first** match for `parse_narration_status_line()` — triggering `creation_drift` `awaiting_mismatch` and confusing APP-065 suggestion chips.

APP-072 added `strip_flavor_race_table()` for RACE duplicate tables; **no equivalent exists for ROLL_STATS**. `_auto_roll_stats()` rolls in code, appends `format_roll_stats_table()` + `format_classes_table()` in the body, but the thin LLM flavor call (`max_tokens=120`) still invents attribute markdown (`### Your Attributes`, compact `| STR | AGI | … |`, truncated `` `roll_attributes( ``) with **wrong numbers**. Model swap (Gemini 2.5 Flash → 3.1 Flash Lite) does not fix it (ticket session evidence).

`_compose_creation_narration` is the correct single choke point: flavor-only sanitizers, then code `body`, then one `format_creation_status()` footer. Fix = broaden `strip_llm_status_tags`, add `strip_flavor_stats_table()` mirroring APP-072 block-scoped strip, optionally tighten `_auto_roll_stats` flavor instruction (“clerk reaction only — no numbers/tables”), and add unit + compose tests with bad-flavor fixtures (default mock returns `"Test narration."` and cannot regress leaks).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Status strip (partial) | `app/gm/creation.py` | `strip_llm_status_tags`, `_LLM_STATUS_TAG_RE` L82–85, L537–540 |
| Race table strip (done) | `app/gm/creation.py` | `strip_flavor_race_table` L543–568 — template for stats strip |
| Stats table body | `app/gm/creation.py` | `format_roll_stats_table` L619–648 — authoritative `\| Attr \| Base \| … \|` |
| Status labels | `app/gm/creation.py` | `CREATION_STATUS_LABELS` L69–80 — canon awaiting tokens |
| Compose pipeline | `app/gm/orchestrator.py` | `_compose_creation_narration` L628–662 |
| ROLL_STATS path | `app/gm/orchestrator.py` | `_auto_roll_stats` L1101–1120 |
| Flavor LLM | `app/gm/orchestrator.py` | `_narrate_flavor` L721–738, `_CREATION_FLAVOR_MAX_TOKENS=120` |
| Flavor prompts | `app/gm/orchestrator.py` | `_creation_flavor_messages` L688–709; `_auto_roll_stats` uses `_narrate_creation_flavor` |
| Race-mismatch sanitizer | `app/gm/orchestrator.py` | `_sanitize_creation_flavor` L677–686 (APP-069) |
| Premature completion | `app/gm/creation.py` | `sanitize_premature_completion_flavor` L581–596 (APP-070) |
| Drift parse | `app/gm/logger.py` | `parse_narration_status_line` L65–77 — first `Awaiting:` in full narration |
| Drift check | `app/gm/orchestrator.py` | `_check_creation_drift` L202–238 — `awaiting_mismatch` vs `CREATION_STATUS_LABELS` |
| Exploration prompt bias | `app/gm/system_prompt.py` | Teaches `[Location: … \| Phase: … \| Awaiting: …]` state line — included in flavor messages via `SYSTEM_PROMPT` |
| Tests (gap) | `app/tests/test_creation_tables.py` | APP-072 race strip only; **no** status-tag or stats-table tests |
| Tests (stub) | `app/tests/test_creation_flow.py` | Golden path uses mock `"Test narration."`; APP-069 race-mismatch test; no duplicate-stats regression |
| Session evidence | `app/logs/session-2026-05-20.jsonl` | **gitignored**; cited in ticket, not in workspace |

## Code-path traces

### A — Compose (all creation narration)

1. **Entry:** Every `_auto_present_*`, `_auto_roll_stats`, `_auto_finalize` (partial) returns via `_compose_creation_narration(flavor, body[, footer])` (`orchestrator.py` L628+).
2. **Flavor sanitize (current order):**
   - `strip_llm_status_tags(flavor)` — bracket Location/Phase; whole-line Awaiting only
   - `strip_flavor_race_table(cleaned)` — APP-072
   - `_sanitize_creation_flavor(cleaned)` — blank flavor if wrong race title (APP-069)
   - `sanitize_premature_completion_flavor(...)` when `creation.active` or empty roster (APP-070)
   - Re-run `strip_llm_status_tags` if premature sanitizer mutated string (C5)
3. **Append:** cleaned flavor (if non-empty) + code `body` + `format_creation_status()` or explicit `footer`.
4. **Exit:** `_emit_narration` → history, UI, drift check on full string.

**Ticket target order:** after `strip_flavor_race_table`, insert **`strip_flavor_stats_table`** before `_sanitize_creation_flavor`.

### B — ROLL_STATS → CLASS (duplicate stat tables)

1. **Entry:** RACE commit → `_chain_after_creation_choice` / `_auto_roll_stats` (`orchestrator.py` L1101–1120).
2. **Code roll:** `bridge.roll_attributes(race)` → `creation.roll_result`; `advance()` to `CLASS`; `classes_table_shown = True`.
3. **Flavor:** `_narrate_creation_flavor` with instruction to “Present attribute roll results… ROLL_STATS results (dice readout)” — still allows model to emit numbers/tables despite global “Do NOT include markdown tables… mechanical numbers” (`L688–705`, `L1111–1116`).
4. **Body (authoritative):** `format_roll_stats_table(result) + format_classes_table(eligible)`.
5. **Compose:** flavor (possibly with LLM stat table) + body (code stat table) → **two** attribute presentations with conflicting Final values.

**Failure modes (ticket evidence):**

| Session | Model | LLM flavor leak | Code table | Notes |
|---------|-------|-----------------|------------|-------|
| Spluffy / undead @ 18:50 | gemini-2.5-flash | `### Your Attributes` (wrong STR/STA…) | `format_roll_stats_table` breakdown | `finish_reason: length` |
| Tuffy / undead @ 19:02 | gemini-3.1-flash-lite | compact `\| STR \| AGI \| … \|` + `` `roll_attributes( `` fragment | same code table | tool_call authoritative |

### C — Status tag leak (non-bracket / wrong label)

1. **Entry:** Any gated step `_narrate_flavor` during `creation.active`.
2. **LLM output:** May include inline `Awaiting: SKILL_INPUT` (canon: `SKILLS_INPUT`), `MAGIC_SCHOOLS_INPUT` (canon: `SPELL_SCHOOLS_INPUT`), `EQUIPMENT_CONFIRMATION` (canon: `EQUIPMENT_GOLD_CONFIRMATION`), or legacy full bracket blocks.
3. **Strip gap:** `_LLM_STATUS_TAG_RE` third branch is `^\s*Awaiting:\s*[A-Z0-9_]+\s*$` (MULTILINE) — **line-anchored only**. Inline `Clerk nods. Awaiting: SKILL_INPUT` is not removed.
4. **Downstream:** Composed narration = flavor (stale Awaiting) + body + code footer (correct Awaiting). `parse_narration_status_line` returns **first** `Awaiting:` → drift `awaiting_mismatch`; UI chips (APP-065) may parse stale token from flavor region.

**Bracket blocks:** `[Location: … | Phase: … | …]` starting with `[Location:` or `[Phase:` are stripped today. Standalone wrong labels inside prose survive unless whole-line.

### D — What already works

- Code footer always appended last via `format_creation_status(self.creation)` unless `_auto_finalize` passes explicit reception `footer` (WORLD_INTRO only, roster non-empty).
- APP-070 blanks flavor with `registered Delver`, `RECEPTION_CHOICE`, bracket `PRE_DELVE`, etc.; bracket Phase blocks stripped by APP-007 regex when present.
- APP-072 prevents duplicate `\| Race \|` headers in flavor region.
- `get_step_prompt()` removed (APP-074) — no runtime path teaches LLM to emit step tables via dead prompts.

## Existing specs & docs

- **Ticket:** `tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md` — AC for complete status strip, `strip_flavor_stats_table`, compose wiring, tests; notes APP-007 completion.
- **Domain spec:** `tmp/app-character-creation-spec.md` — compose pipeline § Flavor must reflect committed FSM (L70); APP-072 race strip (L127–149); ROLL_STATS orchestration (L175–189); APP-007 marked done in checklist (L203) but strip behavior incomplete per ticket.
- **Related closed:** APP-007 (partial strip), APP-072 (race table strip template), APP-069 (race mismatch), APP-070 (premature completion + C5 re-strip).
- **Related open:** APP-065 (chips parse `Awaiting:` — implement after APP-073 per batch board), APP-059 (table column standardization — out of scope).
- **AGENTS.md:** spec ↔ code drift policy; no ticket for run artifacts.

## Tests & commands

```bash
# Existing — does not cover status-tag or duplicate stat-table flavor leaks
python -m pytest app/tests/test_creation_tables.py -q
python -m pytest app/tests/test_creation_flow.py -q

# After impl (ticket)
python -m pytest app/tests/test_creation_flavor_sanitize.py -q   # new module per ticket
# or extended test_creation_tables.py
```

**Acceptance mapping (ticket → locus):**

| AC | Suggested locus |
|----|-----------------|
| Bracket Location/Phase anywhere in flavor | Broaden `_LLM_STATUS_TAG_RE` or multi-pass in `strip_llm_status_tags` |
| Remove **any** `Awaiting:` in flavor (not whole-line only) | Same helper — global replace or line+inline patterns; preserve code footer (never strip `body`/`footer`) |
| `strip_flavor_stats_table` | New function in `creation.py`; fingerprints: `### Your Attributes`, `\| Attr \| Base \|`, compact attr header row, `` `roll_attributes( `` |
| Wire in compose after race strip | `_compose_creation_narration` L637–638 |
| ROLL_STATS single authoritative table | Integration test: stub bad stat-table flavor on `"human"` / `"undead"` turn; assert one `\| Attr \| Base \|` block and Final values match `FIXED_ROLL` |
| Prompt hygiene | `_auto_roll_stats` instruction + verify `_creation_flavor_messages` / `SYSTEM_PROMPT` do not teach wrong labels |
| Spec sync | Domain spec compose pipeline + ROLL_STATS flavor policy + changelog; close APP-007 note |

## Risks & unknowns

- **Over-stripping `Awaiting:`:** Must apply only to **flavor** string before body append — never to composed narration or `_auto_finalize` reception footer (`Awaiting: RECEPTION_CHOICE` is legitimate post-finalize).
- **Over-stripping stats patterns:** Compact `\| STR \|` rows might appear in rare prose; prefer block-scoped strip (header fingerprint + separator + data rows) like APP-072, plus line fallback for `\| Attr \| Base \|` and `` `roll_attributes( `` fragments.
- **Scope creep:** Models may leak `\| Category \| Skill \|`, `\| School \|`, etc. in flavor on other steps — ticket is status tags + ROLL_STATS stats table; shared helper could be future ticket.
- **`SYSTEM_PROMPT` conflict:** Exploration state-line template in `system_prompt.py` (L213, L273) is still injected into creation flavor messages — may encourage status tags despite creation-specific negation; prompt-only fix insufficient (ticket: sanitizer is pass gate).
- **`finish_reason: length`:** Logged in `log_llm_response` but not acted on; truncated tables are stripped post-hoc, not retried.
- **Session log unverified:** `app/logs/session-2026-05-20.jsonl` gitignored; ticket timestamps (Spluffy 18:50, Tuffy 19:02, Supa/Bumpy status tags) taken on faith; human playtest should replay undead roll turn.
- **Alternative (ticket):** Skip LLM flavor entirely on ROLL_STATS — simpler but changes UX; if chosen, spec must document code-only intro line.
- **APP-065 dependency:** Batch board prefers APP-073 before APP-065 impl; clean narration reduces chip stale-token surface but APP-065 remains separate UI work.

## Raw notes

### Current `_LLM_STATUS_TAG_RE` (gap analysis)

```82:85:app/gm/creation.py
_LLM_STATUS_TAG_RE = re.compile(
    r"\[Location:[^\]]*\]|\[Phase:[^\]]*\]|^\s*Awaiting:\s*[A-Z0-9_]+\s*$",
    re.I | re.MULTILINE,
)
```

| Input pattern | Stripped today? |
|---------------|-----------------|
| `[Location: 32-C \| Phase: desk \| Awaiting: SKILL_INPUT]` | Yes (Location bracket) |
| Whole line `Awaiting: SKILL_INPUT` | Yes |
| Inline `Clerk speaks. Awaiting: SKILL_INPUT` | **No** (not line-anchored) |
| `MAGIC_SCHOOLS_INPUT` vs canon `SPELL_SCHOOLS_INPUT` | Wrong label survives until stripped |
| Unbracketed `Phase: preparation` in flavor | **No** (APP-070 blanks when active + step ≠ WORLD_INTRO) |

### Canon awaiting labels (`CREATION_STATUS_LABELS`)

| Step | Label |
|------|-------|
| SKILLS | `SKILLS_INPUT` (not `SKILL_INPUT`) |
| SPELL_SCHOOLS | `SPELL_SCHOOLS_INPUT` (not `MAGIC_SCHOOLS_*`) |
| EQUIPMENT_GOLD | `EQUIPMENT_GOLD_CONFIRMATION` (not `EQUIPMENT_CONFIRMATION`) |

### `_compose_creation_narration` (live)

```628:662:app/gm/orchestrator.py
    def _compose_creation_narration(
        self,
        flavor: str,
        body: str = "",
        *,
        footer: str | None = None,
    ) -> str:
        ...
        cleaned = strip_llm_status_tags(flavor)
        cleaned = strip_flavor_race_table(cleaned)
        cleaned = self._sanitize_creation_flavor(cleaned)
        ...
        if cleaned:
            parts.append(cleaned)
        if body.strip():
            parts.append(body.strip())
        status_line = footer if footer is not None else format_creation_status(self.creation)
```

No `strip_flavor_stats_table` call yet.

### `_auto_roll_stats` flavor instruction (encourages numbers)

```1111:1118:app/gm/orchestrator.py
        flavor = self._narrate_creation_flavor(
            f"Present attribute roll results for a delver whose lineage is **{race_title}**. "
            "Do not name or imply any other race. "
            "You are presenting ROLL_STATS results (dice readout) — not asking for class yet.",
            ...
        )
        body = format_roll_stats_table(result) + "\n\n" + format_classes_table(eligible)
```

Global flavor system text says “Do NOT include … mechanical numbers” (`L702–704`) but step instruction says “Present attribute roll results” — mixed signal.

### `format_roll_stats_table` header (dedup fingerprint)

```630:631:app/gm/creation.py
        "| Attr | Base | Genetic | Life Evt | Racial | Final |",
        "|:------|-----:|--------:|---------:|-------:|------:|",
```

### Drift: first `Awaiting:` wins

```74:76:app/gm/logger.py
    awaiting_m = re.search(r"Awaiting:\s*([^|\]]+)", narration, re.I)
    if awaiting_m:
        awaiting = awaiting_m.group(1).strip()
```

Flavor-region stale token poisons drift before footer is reached in search order (flavor precedes footer in composed string).

### Test gap

- `test_creation_flow.py` turn `"human"`: asserts code table + `"Test narration."` — no duplicate-table count.
- `test_roll_stats_flavor_reflects_committed_race`: APP-069 race mismatch only.
- `test_skills_turn_rejects_premature_completion_flavor`: APP-070; BAD_FLAVOR uses bracket block (stripped by APP-007) + prose (stripped by APP-070) — does not exercise inline wrong `Awaiting:`.

### APP-072 strip pattern (template for stats)

Block-scoped: detect header regex → skip optional separator → consume `\|…\|` rows → line fallback for stray header substring. Reuse `_MD_TABLE_SEPARATOR_RE` / `_MD_TABLE_ROW_RE` from `creation.py` L544–545.

### Session log (ticket, not verified locally)

| Time / character | Symptom |
|------------------|---------|
| ~14:06–14:10 Dumpy | Full bracket status every line (historical) |
| 16:13 Supa | `Awaiting: SKILL_INPUT` |
| Bumpy | `MAGIC_SCHOOLS_INPUT`, `EQUIPMENT_CONFIRMATION` |
| 18:50 Spluffy / undead | LLM `### Your Attributes` + code breakdown; `finish_reason: length` |
| 19:02 Tuffy / undead | LLM compact stat row + `` `roll_attributes( `` + code breakdown |
