# Spec: APP-001-fix-site-passage-edge-types

**Status:** approved
**backlog_ticket:** APP-001
**ticket_path:** tmp/backlog/app-001-fix-site-passage-edge-types.md
**domain_spec:** tmp/app-exploration-delve-spec.md
**registry_gap:** false

## Problem

Site JSON uses non-canonical edge types (`passage`, `gap`). `validate_content` and `tomb_gm check` fail, blocking engine QA.

## Scope

**In:** Remap invalid edge types in `boydon-undercroft.json` and `shadowfen-vaults.json`; update exploration domain spec blocker section + changelog; record canon decision (remap, not new type).

**Out:** Adding `passage` to `SITE_EDGE_TYPES` (APP-013 alternative — rejected for this implementation); `app/` changes; new site nodes.

## Acceptance criteria (ticket)

- [x] Remap `passage` → `archway` in both site files (all occurrences)
- [x] Remap `gap` → `archway` in shadowfen (required for validate exit 0)
- [x] `python build/tools/validate_content.py` exits 0
- [x] `python -m tomb_gm --workspace play/workspace check` — no site edge blocker
- [x] Domain spec: decision recorded, blocker cleared, changelog entry

## Canon decision (for APP-013)

**Chosen:** Remap legacy `passage` and `gap` to **`archway`** in site JSON. Canonical set remains `door | archway | stairs | secret | hatch | collapse`.

## Test commands

```bash
python build/tools/validate_content.py
python -m tomb_gm --workspace play/workspace check
python -m pytest play/tomb_gm/tests/test_site.py -q
```

## Affected paths

- `build/data/sites/boydon-undercroft.json`
- `build/data/sites/shadowfen-vaults.json`
- `tmp/app-exploration-delve-spec.md`

**Note:** `play/tomb_gm/world/sites.py` in ticket does not exist — no engine code change required.
