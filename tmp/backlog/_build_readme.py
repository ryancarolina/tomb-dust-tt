"""Build tmp/backlog/README.md from ticket files."""
from __future__ import annotations

import re
from pathlib import Path

BACKLOG = Path(__file__).parent


def parse_ticket(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    title_line = text.split("\n", 1)[0].removeprefix("# ").strip()
    fields = {}
    for key in ("ID", "Type", "Priority", "Status"):
        m = re.search(rf"\*\*{key}\*\* \| ([^|\n]+)", text)
        if m:
            fields[key] = m.group(1).strip()
    m_spec = re.search(r"Domain spec\*\* \| \[([^\]]+)\]\(\.\./([^)]+)\)", text)
    if not fields.get("ID"):
        return None
    short_title = title_line.split(": ", 1)[-1] if ": " in title_line else title_line
    return {
        "id": fields["ID"],
        "priority": fields.get("Priority", "?"),
        "type": fields.get("Type", "?"),
        "title": short_title,
        "status": fields.get("Status", "?"),
        "spec": m_spec.group(2) if m_spec else "?",
        "file": path.name,
    }


def main() -> None:
    rows = []
    for p in BACKLOG.glob("app-*.md"):
        row = parse_ticket(p)
        if row and row["id"] != "APP-000":
            rows.append(row)
    rows.sort(key=lambda r: int(r["id"].split("-")[1]))

    active = {s: 0 for s in ("open", "in_progress", "done", "cancelled")}
    for r in rows:
        if r["status"] in active:
            active[r["status"]] += 1

    p0_open = [
        r for r in rows if r["priority"] == "P0" and r["status"] in ("open", "in_progress")
    ]
    if p0_open:
        p0 = "\n".join(
            f"| [{r['id']}]({r['file']}) | {r['status']} | {r['title']} |" for r in p0_open
        )
        p0_header = "| Ticket | Status | Title |\n|--------|--------|-------|"
    else:
        p0 = "_All P0 tickets closed._"
        p0_header = ""

    p1_open = [
        r for r in rows if r["priority"] == "P1" and r["status"] in ("open", "in_progress")
    ]
    p1 = "\n".join(
        f"| [{r['id']}]({r['file']}) | {r['status']} | {r['title']} |" for r in p1_open
    )
    if not p1:
        p1 = "_No open P1 tickets._"
    index = "\n".join(
        f"| [{r['id']}]({r['file']}) | {r['priority']} | {r['type']} | {r['title']} | "
        f"[{r['spec']}](../{r['spec']}) | `{r['file']}` |"
        for r in rows
    )

    readme = f"""# App backlog (`tmp/backlog/`)

Work items for the **Tomb Dust pygame app** (`app/`). Every change under `app/` (and any path listed in a ticket) **must** have a backlog ticket before implementation.

## Workflow

1. **Pick or create a ticket** — copy [`TEMPLATE.md`](TEMPLATE.md); see [`APP-000-example-ticket.md`](APP-000-example-ticket.md).
2. **Set status** to `in_progress` when starting work.
3. **Implement** only files listed in the ticket (update the ticket first if scope grows).
4. **Close** — mark `done`, update domain spec + changelog, run tests from the ticket/spec.
5. **No ticket, no change** — enforced by [`.cursor/rules/tomb-dust-backlog.mdc`](../../.cursor/rules/tomb-dust-backlog.mdc).

## Priority snapshot (P0 — open / in progress)

{p0_header}
{p0}

## Priority snapshot (P1 — open / in progress)

| Ticket | Status | Title |
|--------|--------|-------|
{p1}

## Grooming stats

| Status | Count |
|--------|-------|
| open | {active['open']} |
| in_progress | {active['in_progress']} |
| done | {active['done']} |
| **Total** | **{len(rows)}** |

_Last README rebuild from ticket files — run `python tmp/backlog/_build_readme.py` after bulk status changes._

## Full index

| ID | Priority | Type | Title | Domain spec | File |
|----|----------|------|-------|-------------|------|
{index}
"""
    (BACKLOG / "README.md").write_text(readme, encoding="utf-8")
    print(f"README with {len(rows)} tickets")


if __name__ == "__main__":
    main()
