# Research Brief: APP-001-fix-site-passage-edge-types

**Date:** 2026-05-20
**Question:** How do we unblock `validate_content` / `tomb_gm check` for invalid site edge type `passage`?

**backlog_ticket:** APP-001
**ticket_path:** tmp/backlog/app-001-fix-site-passage-edge-types.md
**domain_spec:** tmp/app-exploration-delve-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

`tmp/app-exploration-delve-spec.md` owns site edge validation blockers and links APP-001 / APP-013. `build/tools/validate_content.py` is canon enforcement. No new domain spec required.

## Summary

`validate_content.py` defines `SITE_EDGE_TYPES = {door, archway, stairs, secret, hatch, collapse}`. Two site JSON files use non-canonical types:

- **boydon-undercroft.json:** 1× `passage` (old-crypt → veil-crack)
- **shadowfen-vaults.json:** 4× `passage`, 1× `gap` (glyph-corridor → collapsed-archive)

Validator raises on the **first** invalid edge per file, so fixing only one `passage` per file is insufficient.

Ticket lists `play/tomb_gm/world/sites.py` — **file does not exist**. Engine loads edges via `play/tomb_gm/services/site.py` (default `type` fallback `"passage"` for missing keys only). Fix is **content JSON remap**; optional engine default change is out of ticket Expected files.

`python -m tomb_gm --workspace play/workspace check` shells out to `validate_content.py` (`play/tomb_gm/cli/cmd_core.py`).

**Decision (implements APP-001, documents for APP-013):** remap `passage` → `archway`; remap `gap` → `archway` (preserve `hazard` metadata). Do not add `passage` to `SITE_EDGE_TYPES`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Canon types | `build/tools/validate_content.py:39,402` | `SITE_EDGE_TYPES` |
| Site data | `build/data/sites/boydon-undercroft.json` | 1 invalid edge |
| Site data | `build/data/sites/shadowfen-vaults.json` | 5 invalid edges |
| Engine load | `play/tomb_gm/services/site.py:81` | `edge_type=str(raw.get("type", "passage"))` |
| Exits UI | `play/tomb_gm/services/exploration.py:569` | displays `edge.get("type")` |
| Check CLI | `play/tomb_gm/cli/cmd_core.py:239` | runs validate_content |

## Code-path traces

### validate_content site check

1. Entry: `validate_content.main()` → `validate_sites_dir()`
2. Per file: `validate_site()` iterates `edges[]`, `_err` if `type` ∉ `SITE_EDGE_TYPES`
3. Exit: non-zero if any file fails

### tomb_gm check

1. Entry: `handle_check` in `cmd_core.py`
2. Subprocess: `python build/tools/validate_content.py`
3. Exit: blocker if validate fails

## Existing specs & docs

- Domain spec § Blocker: content validation — lists files and canonical types
- APP-013 — decision ticket (open); APP-001 AC allows remap without waiting

## Tests & commands

```bash
python build/tools/validate_content.py
python -m tomb_gm --workspace play/workspace check
python -m pytest play/tomb_gm/tests/test_site.py -q
```

## Risks & unknowns

- **gap → archway:** prose says "narrow gap"; `archway` is closest open connector; `hazard` field retained on edge object (validator does not reject extra keys).
- **ward-seal ↔ cult-chamber:** bidirectional `passage` → `archway` (iron door flavor in node text; `door` would also fit — using `archway` per uniform remap rule).

## Raw notes

```
boydon-undercroft.json/edges[3]: passage
shadowfen-vaults.json: passage ×4, gap ×1 at edges[3]
```
