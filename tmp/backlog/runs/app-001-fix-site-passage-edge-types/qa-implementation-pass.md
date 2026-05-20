# QA Implementation Pass — APP-001

**backlog_ticket:** APP-001

## Ticket AC mapping

| AC | Evidence |
|----|----------|
| Remap passage → archway | `boydon-undercroft.json` edges[3]; `shadowfen-vaults.json` 4× passage → archway |
| validate_content exit 0 | `python build/tools/validate_content.py` → OK |
| tomb_gm check clean | `cd play && python -m tomb_gm --workspace workspace check` → `blocked: false` |
| gap edge (discovered) | shadowfen edges[3] `gap` → `archway`, hazard preserved |

## Tests run

```text
validate_content: OK
tomb_gm check: ok true, blockers []
pytest play/tomb_gm/tests/test_site.py -q: 4 passed
```

## Verdict

**PASS**
