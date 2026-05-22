# APP-078: Generic creation table flavor stripper

| Field | Value |
|-------|-------|
| **ID** | APP-078 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | cancelled |
| **Superseded by** | [APP-083](app-083-creation-flavor-verification-gate.md) Phase 1 — `verify_narration` rejects `markdown_table` and off-catalog claims before publish |
| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |
| **Created** | 2026-05-20 |

## Summary

APP-072 and APP-073 added step-specific strippers for **race** and **stats** tables in LLM flavor. Session logs show the same failure mode on **SKILLS, SPELL_SCHOOLS, SPELLS, CLASS, and EQUIPMENT** steps: LLM embeds full or truncated markdown tables (e.g. `15:40:39` — 2338-char skills table; equipment kit prose). Code-owned `format_*_table()` / `format_equipment_summary()` bodies are authoritative; duplicate LLM tables waste panel space and confuse players.

Add a **generic markdown-table stripper** for creation flavor when the code body already supplies the step table — reducing per-step sanitizer sprawl and closing gaps APP-059 does not fully cover.

## Problem (observed)

- `_compose_creation_narration` runs `strip_flavor_race_table` + `strip_flavor_stats_table` only.
- SKILLS/SCHOOLS/SPELLS/CLASS steps have no table strippers; APP-075 skips LLM on error paths but not on success paths with embedded tables.
- Truncated tables (`finish_reason: length`) leave partial `\| … \|` blocks in flavor above the code body.
- Per-step strippers (APP-059 equipment GP strip) still needed for **non-table** prose leaks — this ticket handles **duplicate markdown tables** only.

## Acceptance criteria

### Decision (document in domain spec)

- [ ] When `body` contains a known step table header fingerprint, flavor must not contain any markdown table block with `\|…\|` rows.
- [ ] Step-specific strippers (race, stats, equipment GP) remain; generic stripper runs **before** or **after** them per documented order.

### Code

- [ ] `strip_flavor_markdown_tables(text: str, *, body: str = "") -> str` in `creation.py`:
  - If `body` empty → no-op (or strip all tables — document chosen behavior).
  - If `body` contains a table header → remove markdown table blocks from `text` (header row + optional separator + data rows), reusing `_MD_TABLE_SEPARATOR_RE` / `_MD_TABLE_ROW_RE` from APP-072.
  - Collapse blank lines; empty → `""`.
- [ ] Optional: `STEP_TABLE_HEADER_FINGERPRINTS: dict[str, str]` mapping `creation.step` → regex matched against `body` to decide strip aggressiveness.
- [ ] Wire into `_compose_creation_narration` after `strip_flavor_stats_table` (and before APP-059 `strip_flavor_equipment_claims` when that lands).
- [ ] Do **not** strip code `body` or explicit `footer=`.

### Tests

- [ ] Unit: flavor with embedded `\| Category \| Skill \|` + body containing same header → flavor prose retained, no `\|` rows in flavor output.
- [ ] Unit: truncated table (no separator row) stripped — mirror APP-072 race tests.
- [ ] Unit: flavor-only prose without tables unchanged.
- [ ] Integration: golden-path turn at SKILLS — at most one `\| Category \| Skill \|` block in full narration (from code body).

## Expected files

- `app/gm/creation.py`
- `app/gm/orchestrator.py`
- `app/tests/test_creation_flavor_sanitize.py`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Add § **`strip_flavor_markdown_tables`** to flavor sanitization pipeline in [`app-character-creation-spec.md`](../app-character-creation-spec.md); update compose order diagram.
3. Cross-reference from [APP-059](app-059-standardize-creation-table-outputs.md) notes.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-072 | template for block-scoped markdown strip |
| APP-073 | compose pipeline hook point |
| APP-059 | table catalog + equipment GP strip (orthogonal) |

Soft hint — implement **after** or **with** APP-059 equipment strip to avoid compose-order churn.

## Notes

- **Cancelled (2026-05-22)** — Primary enforcement is APP-083 `verify_narration` (`markdown_table`, catalog rules). Existing compose strippers (`strip_flavor_race_table`, `strip_flavor_stats_table`) remain defense-in-depth; no separate generic table stripper required unless verify gaps appear in logs.
- Do not implement this ticket unless post-083 monitoring shows duplicate tables still reaching players after verify exhaustion.

### Compose order (historical target — reference only)

```
strip_llm_status_tags
→ strip_flavor_race_table
→ strip_flavor_stats_table
→ strip_flavor_markdown_tables(flavor, body=body)   # APP-078
→ strip_flavor_equipment_claims                      # APP-059
→ _sanitize_creation_flavor
→ sanitize_premature_completion_flavor
→ body + footer
```

### Non-goals

- Changing `format_*_table()` column contracts (APP-059).
- Stripping exploration/combat narration tables (out of scope — exploration uses APP-077 footer pattern).
- Removing step-specific race/stats strippers in v1 (keep as fast-path fingerprints; generic strip is backstop).

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-078 --task generic-creation-table-flavor-stripper
python tmp/backlog/claim_ticket.py release APP-078 --done
```
