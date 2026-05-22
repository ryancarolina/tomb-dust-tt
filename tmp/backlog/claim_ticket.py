#!/usr/bin/env python3
"""Claim, search, schedule, and manage backlog tickets (single or batch up to 3)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backlog_ticket_lib import (  # noqa: E402
    ACTIVE_STATUSES,
    CLOSED_STATUSES,
    MAX_BATCH_SIZE,
    PICKABLE_STATUSES,
    append_ticket_note,
    clear_active_ticket,
    compute_schedule,
    find_ticket_file,
    impl_stage_allowed,
    load_active_batch,
    load_active_ticket,
    parse_ticket_fields,
    remove_ticket_from_batch,
    run_dir_for,
    search_tickets,
    select_ticket_batch,
    set_batch_focus,
    set_ticket_status,
    ticket_record,
    write_active_batch,
    write_active_ticket,
)


def cmd_claim(ticket_id: str, task_name: str | None, create_run: bool) -> int:
    ticket_path = find_ticket_file(ticket_id)
    if not ticket_path:
        print(f"error: ticket not found: {ticket_id}", file=sys.stderr)
        return 1

    fields = parse_ticket_fields(ticket_path)
    status = fields.get("status", "")
    if status == "done":
        print(f"error: ticket {ticket_id} is already done", file=sys.stderr)
        return 1
    if status not in ACTIVE_STATUSES:
        print(f"error: ticket {ticket_id} has status `{status}`", file=sys.stderr)
        return 1

    if status == "open":
        set_ticket_status(ticket_path, "in_progress")

    run_dir = None
    if create_run:
        if not task_name:
            task_name = fields.get("title", ticket_id).lower().replace(" ", "-")
        run_dir = run_dir_for(ticket_id, task_name)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "status.md").touch(exist_ok=True)
        append_ticket_note(
            ticket_path,
            f"**Run folder:** `{run_dir.as_posix()}`",
        )

    payload = write_active_ticket(
        ticket_id.upper(),
        ticket_path,
        run_dir=run_dir,
        domain_spec=fields.get("domain_spec", ""),
    )
    print(json.dumps(payload, indent=2))
    return 0


def cmd_claim_batch(
    ticket_ids: list[str],
    task_names: dict[str, str],
    *,
    resume: bool = False,
) -> int:
    if len(ticket_ids) > MAX_BATCH_SIZE:
        print(
            f"error: at most {MAX_BATCH_SIZE} tickets per batch",
            file=sys.stderr,
        )
        return 1

    selected, errs = select_ticket_batch(ticket_ids)
    records: list[dict] = []
    for tid in selected:
        ticket_path = find_ticket_file(tid)
        if not ticket_path:
            print(f"error: ticket not found: {tid}", file=sys.stderr)
            return 1
        fields = parse_ticket_fields(ticket_path)
        status = fields.get("status", "")
        if status in CLOSED_STATUSES:
            print(f"error: ticket {tid} is closed (`{status}`)", file=sys.stderr)
            return 1
        if status == "in_progress" and not resume:
            print(
                f"error: ticket {tid} is already in_progress — omit from new batch "
                f"or pass --resume to continue that lane",
                file=sys.stderr,
            )
            return 1
        if status not in PICKABLE_STATUSES and not (resume and status == "in_progress"):
            print(f"error: ticket {tid} has status `{status}`", file=sys.stderr)
            return 1
        if status == "open":
            set_ticket_status(ticket_path, "in_progress")

        task_name = task_names.get(tid) or fields.get("title", tid).lower().replace(" ", "-")
        run_dir = run_dir_for(tid, task_name)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "status.md").touch(exist_ok=True)
        append_ticket_note(ticket_path, f"**Run folder:** `{run_dir.as_posix()}`")

        records.append(
            ticket_record(
                tid,
                ticket_path,
                run_dir=run_dir,
                domain_spec=fields.get("domain_spec", ""),
            )
        )

    schedule = compute_schedule(selected)
    batch = write_active_batch(records, schedule=schedule)
    if errs:
        batch["warnings"] = errs
    batch["batch_board_note"] = (
        f"Orchestrator: create {batch.get('batch_board', '')} from templates.md § batch-board"
    )
    print(json.dumps(batch, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    pickable = args.pickable_only or args.open_only
    rows = search_tickets(
        status=args.status,
        priority=args.priority,
        query=args.query,
        open_only=pickable,
        pickable_only=pickable,
    )
    print(json.dumps({"count": len(rows), "tickets": rows}, indent=2))
    return 0


def cmd_schedule(ticket_ids: list[str]) -> int:
    if len(ticket_ids) > MAX_BATCH_SIZE:
        print(
            json.dumps(
                {
                    "error": f"schedule preview supports at most {MAX_BATCH_SIZE} tickets",
                    "hint": "pass up to 3 IDs; use search first to pick candidates",
                },
                indent=2,
            )
        )
        return 1
    out = compute_schedule(ticket_ids)
    print(json.dumps(out, indent=2))
    return 0


def cmd_batch_status() -> int:
    batch = load_active_batch()
    if not batch:
        single = load_active_ticket()
        print(json.dumps({"batch": None, "legacy_single": single}, indent=2))
        return 0
    print(json.dumps(batch, indent=2))
    return 0


def cmd_focus(ticket_id: str) -> int:
    if not set_batch_focus(ticket_id):
        print(f"error: {ticket_id} not in active batch", file=sys.stderr)
        return 1
    print(json.dumps({"focus": ticket_id.upper()}, indent=2))
    return 0


def cmd_impl_check(ticket_id: str) -> int:
    ok, reason = impl_stage_allowed(ticket_id)
    print(json.dumps({"allowed": ok, "reason": reason}, indent=2))
    return 0 if ok else 1


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0].upper().startswith("APP-"):
        ticket_id = argv[0].upper()
        task_name = None
        create_run = True
        i = 1
        while i < len(argv):
            if argv[i] == "--task" and i + 1 < len(argv):
                task_name = argv[i + 1]
                i += 2
            elif argv[i] == "--no-run-dir":
                create_run = False
                i += 1
            else:
                i += 1
        return cmd_claim(ticket_id, task_name, create_run)

    parser = argparse.ArgumentParser(description="Manage backlog tickets (single or batch)")
    sub = parser.add_subparsers(dest="command", required=True)

    claim_p = sub.add_parser("claim")
    claim_p.add_argument("ticket_id")
    claim_p.add_argument("--task", dest="task_name")
    claim_p.add_argument("--no-run-dir", action="store_true")

    batch_p = sub.add_parser("claim-batch")
    batch_p.add_argument("ticket_ids", nargs="+", metavar="APP-XXX")
    batch_p.add_argument("--task", action="append", metavar="APP-XXX=kebab-name")
    batch_p.add_argument(
        "--resume",
        action="store_true",
        help="allow in_progress tickets (continue existing lane; not for new picks)",
    )

    search_p = sub.add_parser("search")
    search_p.add_argument("--status", choices=["open", "in_progress", "done", "cancelled"])
    search_p.add_argument("--priority", choices=["P0", "P1", "P2"])
    search_p.add_argument("--q", dest="query")
    search_p.add_argument(
        "--open-only",
        action="store_true",
        help="only status open (excludes in_progress, done, cancelled) — dev-team default",
    )
    search_p.add_argument(
        "--pickable-only",
        action="store_true",
        help="alias for --open-only",
    )

    sched_p = sub.add_parser("schedule")
    sched_p.add_argument("ticket_ids", nargs="+", metavar="APP-XXX")

    sub.add_parser("batch-status")
    sub.add_parser("clear")

    focus_p = sub.add_parser("focus")
    focus_p.add_argument("ticket_id")

    impl_p = sub.add_parser("impl-check")
    impl_p.add_argument("ticket_id")

    sub.add_parser("status")

    rel_p = sub.add_parser("release")
    rel_p.add_argument("ticket_id")
    rel_p.add_argument("--done", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "claim":
        return cmd_claim(args.ticket_id.upper(), args.task_name, not args.no_run_dir)
    if args.command == "claim-batch":
        task_map: dict[str, str] = {}
        for item in args.task or []:
            if "=" in item:
                tid, name = item.split("=", 1)
                task_map[tid.upper()] = name
        return cmd_claim_batch(
            [t.upper() for t in args.ticket_ids],
            task_map,
            resume=args.resume,
        )
    if args.command == "search":
        return cmd_search(args)
    if args.command == "schedule":
        return cmd_schedule([t.upper() for t in args.ticket_ids])
    if args.command == "batch-status":
        return cmd_batch_status()
    if args.command == "focus":
        return cmd_focus(args.ticket_id.upper())
    if args.command == "impl-check":
        return cmd_impl_check(args.ticket_id.upper())
    if args.command == "clear":
        clear_active_ticket()
        print("{}")
        return 0
    if args.command == "status":
        return cmd_batch_status()
    if args.command == "release":
        ticket_path = find_ticket_file(args.ticket_id.upper())
        if not ticket_path:
            print(f"error: ticket not found: {args.ticket_id}", file=sys.stderr)
            return 1
        if args.done:
            set_ticket_status(ticket_path, "done", closed=True)
        remove_ticket_from_batch(args.ticket_id.upper())
        print(json.dumps({"released": args.ticket_id.upper(), "done": args.done}, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
