# Dev Plan: APP-001-fix-site-passage-edge-types

**backlog_ticket:** APP-001

## Steps

1. **boydon-undercroft.json** — change edge `old-crypt` → `veil-crack`: `"type": "passage"` → `"archway"`.

2. **shadowfen-vaults.json** — remap all `"passage"` → `"archway"` (4 edges):
   - flooded-anteroom → fungal-grotto
   - collapsed-archive → ashret-camp
   - cult-chamber → ward-seal (both directions)

3. **shadowfen-vaults.json** — remap `"gap"` → `"archway"` on glyph-corridor → collapsed-archive; keep `"hazard": "squeeze-check DC 12 AGI"`.

4. **tmp/app-exploration-delve-spec.md** — mark blocker resolved; document remap decision; changelog APP-001; remove APP-001 from open-work list.

5. **Verify**
   ```bash
   python build/tools/validate_content.py
   python -m tomb_gm --workspace play/workspace check
   python -m pytest play/tomb_gm/tests/test_site.py -q
   ```

## Risks

- None — data-only; edge semantics unchanged for engine (type string passed through).

## Files (⊆ ticket Expected files, minus missing sites.py)

| File | Change |
|------|--------|
| `build/data/sites/boydon-undercroft.json` | 1 edge type |
| `build/data/sites/shadowfen-vaults.json` | 5 edge types |
| `tmp/app-exploration-delve-spec.md` | spec sync |
