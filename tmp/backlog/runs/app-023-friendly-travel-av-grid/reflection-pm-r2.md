# Reflection: PM — APP-023 friendly travel (r2)

**Agent:** PM  
**Round:** 2 (QA spec revision)  
**Trigger:** `qa-spec-report-1.md` — SPEC-001, TICKET-001, SPEC-002 blockers; SPEC-003 major; SPEC-004 minor  
**Deliverables:** `spec.md`, `tmp/app-exploration-delve-spec.md`, ticket Expected files, `reflection-pm-r2.md`

## Blockers addressed

| ID | Fix |
|----|-----|
| **SPEC-001** | Chose **apostrophe folding** (strip `'`/`'` before substring + slug) — no `av-grid.json` change. Pinned scoring proof: `kings road` @ `32-C` → `33-C` at score **70** (slug) / **60** (substring); current cell excluded; exit `33-C` needs no `tradeRoute`. |
| **TICKET-001** | Expected files now include `beat.py`, `test_world.py`, `test_beat.py`, optional `tools.py`; aligned with run spec Affected paths. |
| **SPEC-002** | Added domain § **Layered fallback**: pass 1 surface-only; pass 2 scores non-surface `legal_exits` with same table; single layered match → `USE_ENTER_DUNGEON`. T5 pinned to **`USE_ENTER_DUNGEON`** for `undercrypt` → `32-C-UG-1`. |
| **SPEC-003** | Wiring row documents beat maps resolver **`UNKNOWN_ADDRESS` → `NO_DESTINATION`**; `AMBIGUOUS_ADDRESS` / `USE_ENTER_DUNGEON` pass through. Added T7 / domain beat error-map test row. |
| **SPEC-004** | Run spec Non-goals + R1 naming note: engine **`resolve_surface_address`** ≠ `av_grid.py:resolve_surface`. |

## Design choices

- **Apostrophe folding over JSON `tradeRoute` on exits:** avoids canon grid edits and duplicate-name risk; generalizes beyond King's Road. Exit-level `tradeRoute` score 80 retained when present on candidates.
- **Two-pass resolution:** keeps surface travel strict; layered intent is explicit outcome, not ad hoc `resolve_site_address` in travel path.
- **Beat error enum split preserved:** resolver uses `UNKNOWN_ADDRESS`; beat keeps existing `NO_DESTINATION` for LLM/beat consumers — mapping documented, not unified enum rename (out of scope).

## Self-critique

- Apostrophe folding covers common English possessives but not all Unicode apostrophe variants — Dev may extend fold set if playtest finds gaps.
- Layered pass 2 ambiguity (two UG exits tie) specified as `AMBIGUOUS_ADDRESS` — rare for Breley fixture; acceptable.
- Did not add `status.md` update — QA re-review is spec-only gate; Dev plan stage can bump status on PASS.

## Handoff

**Ready for:** QA spec re-review (round 2)

**Re-review focus:** King's Road proof table; ticket Expected files ⊆ spec scope; T5 = `USE_ENTER_DUNGEON` only; beat `NO_DESTINATION` mapping; layered fallback algorithm completeness
