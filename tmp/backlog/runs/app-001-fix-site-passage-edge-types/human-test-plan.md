# Human Playtest Plan — APP-001

**Ticket:** APP-001 — Fix site passage edge types  
**Entry:** [`app/README.md`](../../../app/README.md) — `cd app && python main.py`  
**Note:** This ticket is **content/validation** only. Playtest confirms site navigation still works after edge type remap.

---

## TC-1 — Engine check (CLI)

- [ ] **Pass** / **Fail**
- **Steps:** From repo root:
  ```bash
  python build/tools/validate_content.py
  cd play && python -m tomb_gm --workspace workspace check
  ```
- **Expected:** `validate_content: OK`; check JSON `"blocked": false`, `"blockers": []`
- **Failure signal:** Any `invalid edge type` or non-zero exit

---

## TC-2 — Enter Boydon Undercroft and reach veil-crack edge

- [ ] **Pass** / **Fail**
- **Steps:** Continue or start campaign at Registry (`32-C`); enter Boydon site; navigate from cellar → cistern → old crypt → toward veil stabilizer root (edge was `passage`, now `archway`)
- **Expected:** GM/site tools allow move along graph; no “unknown edge” errors in narration or `app/logs/*.jsonl`
- **Failure signal:** Stuck at old-crypt with no exit; tool error on `site_move`

---

## TC-3 — Shadowfen vaults multi-edge site

- [ ] **Pass** / **Fail**
- **Steps:** Travel to `47-B-UG-3` / enter shadowfen vaults; use exits from flooded anteroom (fungal grotto archway), glyph corridor (collapsed archive with squeeze hazard text if GM references it), cult chamber ↔ ward seal
- **Expected:** Bidirectional cult/ward moves work; fungal grotto reachable
- **Failure signal:** Missing exits, broken back-edge from ward-seal

---

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | |
