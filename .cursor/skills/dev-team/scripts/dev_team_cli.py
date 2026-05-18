#!/usr/bin/env python3
"""CLI for dev-team state machine. All workflow transitions MUST go through this tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dev_team.machine import DevTeamMachine, TransitionError  # noqa: E402
from dev_team.memory_store import MemoryStore  # noqa: E402
from dev_team.session import SessionStore  # noqa: E402


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2))


def _print_validation(result) -> None:
    if result.errors:
        print("ERRORS:", file=sys.stderr)
        for e in result.errors:
            print(f"  - {e}", file=sys.stderr)
    if result.warnings:
        print("WARNINGS:", file=sys.stderr)
        for w in result.warnings:
            print(f"  - {w}", file=sys.stderr)


def _log_cli(store: SessionStore, command: str, rc: int, detail: str = "") -> int:
    if store.work:
        store.log(
            "cli",
            command=command,
            ok=rc == 0,
            detail=detail or store.load().state,
        )
    return rc


def _handle(
    machine: DevTeamMachine,
    fn,
    *,
    command: str = "",
    success_msg: str | None = None,
) -> int:
    store = machine.store
    try:
        outcome = fn()
        status = machine.status()
        payload: dict = {"ok": True, "message": success_msg, "status": status}
        if isinstance(outcome, tuple):
            _session, validation = outcome
            payload["validation"] = {
                "ok": validation.ok,
                "errors": validation.errors,
                "warnings": validation.warnings,
            }
        _print_json(payload)
        return _log_cli(store, command, 0, status.get("state", ""))
    except TransitionError as exc:
        payload: dict = {"ok": False, "error": str(exc), "status": machine.status()}
        if exc.validation:
            payload["validation"] = {
                "ok": exc.validation.ok,
                "errors": exc.validation.errors,
                "warnings": exc.validation.warnings,
            }
            _print_validation(exc.validation)
        _print_json(payload)
        return _log_cli(store, command, 1, str(exc))


def _memory_to_json(store: MemoryStore, lessons) -> list[dict]:
    return [store.lesson_to_dict(l) for l in lessons]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Dev-team workflow state machine (code-enforced transitions).",
    )
    p.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Project root containing .dev-team/ (default: cwd)",
    )

    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show current session state (includes blocked/blockers)")
    sub.add_parser("check", help="Run defense-in-depth checks without transitioning")
    sub.add_parser("suggest", help="Show recommended next CLI commands for current state")
    assert_gate = sub.add_parser("assert-gate", help="Fail if human gate artifacts/checks not ready")
    assert_gate.add_argument("phase", choices=["research", "spec", "dev", "qa"])
    sub.add_parser("reset", help="Remove legacy root session.json/artifacts and clear active work")
    verify = sub.add_parser("verify-path", help="Check if a repo path may be edited in current state")
    verify.add_argument("path", help="Path relative to project root")

    scope_begin = sub.add_parser("scope", help="Task scoping with human (step 0)")
    scope_sub = scope_begin.add_subparsers(dest="scope_cmd", required=True)
    scope_begin_cmd = scope_sub.add_parser(
        "begin",
        help="Create work dir works/<name>-<datetime>/ and enter TASK_SCOPING",
    )
    scope_begin_cmd.add_argument(
        "--name",
        required=True,
        help="Short topic label (required), e.g. game-docs → game-docs-2026-05-18-143022",
    )
    scope_propose = scope_sub.add_parser("propose", help="Propose 1–2 sentence plain-English scope")
    scope_propose.add_argument("--text", required=True)
    scope_sub.add_parser("confirm", help="Lock scope after human confirms wording")

    start = sub.add_parser("start", help="Start dev-team (requires scope confirm)")
    start.add_argument("--task", default="", help="Must match confirmed scope if provided")
    start.add_argument(
        "--mode",
        choices=["full", "lite", "skip-research", "skip-to-dev"],
        default="full",
    )

    write = sub.add_parser("write", help="Write phase artifact (must match current state)")
    write.add_argument("phase", choices=["research", "spec", "dev", "qa"])
    src = write.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", type=Path)
    src.add_argument("--text")

    fb = sub.add_parser("write-qa-feedback", help="QA writes blocker feedback (qa-reject prerequisite)")
    fb.add_argument("target", choices=["spec", "dev"])
    fb_src = fb.add_mutually_exclusive_group(required=True)
    fb_src.add_argument("--file", type=Path)
    fb_src.add_argument("--text")

    sub.add_parser("validate", help="Validate current phase artifact without transitioning")

    submit = sub.add_parser("submit", help="Submit phase for QA review or human gate")
    submit.add_argument("phase", nargs="?", choices=["research", "spec", "dev", "qa"])

    qa_pass = sub.add_parser("qa-pass", help="QA approves spec standards or dev-vs-spec match")
    qa_pass.add_argument("target", choices=["spec", "dev"])

    qa_reject = sub.add_parser("qa-reject", help="QA sends work back to PM or Dev (max 3 loops)")
    qa_reject.add_argument("target", choices=["spec", "dev"])

    approve = sub.add_parser("approve", help="Human gate approval")
    approve.add_argument("phase", choices=["research", "spec", "dev", "qa"])

    revise = sub.add_parser("revise", help="Human gate: send back for revision")
    revise.add_argument("phase", choices=["research", "spec", "dev", "qa"])
    revise.add_argument("--feedback", default="")

    reject = sub.add_parser("reject", help="Human gate: reject to earlier phase")
    reject.add_argument("target", choices=["research", "spec", "dev"])

    sub.add_parser("abort", help="Cancel session")

    checks = sub.add_parser("record-checks", help="Record build/test/lint results (DEV only)")
    checks.add_argument("--note", required=True)

    # --- Memory (project-local SQLite) ---
    mem = sub.add_parser("memory", help="Lessons learned (ttTomb-Dust project scope)")
    mem_sub = mem.add_subparsers(dest="memory_cmd", required=True)

    mem_sub.add_parser("stats", help="Memory DB statistics")

    mem_recall = mem_sub.add_parser("recall", help="Recall lessons for current work (ranked by age/relevance)")
    mem_recall.add_argument("--phase", choices=["research", "spec", "dev", "qa", "general"])
    mem_recall.add_argument("--query", default="")
    mem_recall.add_argument("--tags", default="", help="Comma-separated tags")
    mem_recall.add_argument("--limit", type=int, default=5)
    mem_recall.add_argument(
        "--since",
        default="",
        help="ISO timestamp; only lessons created at or after this time",
    )

    mem_add = mem_sub.add_parser("add", help="Add or upsert a lesson")
    mem_add.add_argument("--kind", required=True, choices=["bug", "spec", "convention", "tooling", "process", "preference"])
    mem_add.add_argument("--phase", required=True, choices=["research", "spec", "dev", "qa", "general"])
    mem_add.add_argument("--title", required=True)
    mem_add.add_argument("--lesson", required=True)
    mem_add.add_argument("--context", default="")
    mem_add.add_argument("--source", default="orchestrator")
    mem_add.add_argument("--tags", default="")
    mem_add.add_argument("--status", default="active", choices=["draft", "active"])

    mem_draft = mem_sub.add_parser("draft-from-feedback", help="Draft lessons from QA feedback file")
    mem_draft.add_argument("target", choices=["spec", "dev"])
    mem_draft.add_argument("--file", type=Path)

    mem_promote = mem_sub.add_parser("promote", help="Promote draft lesson to active")
    mem_promote.add_argument("id", type=int)

    mem_dep = mem_sub.add_parser("deprecate", help="Retire a wrong or outdated lesson")
    mem_dep.add_argument("id", type=int)

    mem_list = mem_sub.add_parser("list", help="List lessons (newest first)")
    mem_list.add_argument("--status", choices=["draft", "active", "deprecated"])
    mem_list.add_argument("--kind")
    mem_list.add_argument("--limit", type=int, default=20)

    works = sub.add_parser("works", help="List dev-team work instances")
    works_sub = works.add_subparsers(dest="works_cmd", required=True)
    works_sub.add_parser("list", help="List all work directories under .dev-team/works/")
    works_show = works_sub.add_parser("show", help="Show active work or --slug")
    works_show.add_argument("--slug", default="")

    log_p = sub.add_parser("log", help="Work instance logs (debug)")
    log_sub = log_p.add_subparsers(dest="log_cmd", required=True)
    log_tail = log_sub.add_parser("tail", help="Tail JSONL events for active work")
    log_tail.add_argument("--lines", type=int, default=30)
    log_note = log_sub.add_parser("note", help="Orchestrator/agent note in active work log")
    log_note.add_argument("--role", default="orchestrator")
    log_note.add_argument("--message", required=True)
    log_sub.add_parser("clear", help="Delete audit.log and events.jsonl for active work")

    works_remove = works_sub.add_parser("remove", help="Delete a work directory (logs, artifacts, session)")
    works_remove.add_argument("--slug", required=True, help="Work slug to remove, e.g. game-docs-2026-05-18-164625")

    return p


def _command_label(args: argparse.Namespace) -> str:
    parts = [args.command]
    for key in ("scope_cmd", "memory_cmd", "works_cmd", "log_cmd", "phase", "target", "name"):
        val = getattr(args, key, None)
        if val:
            parts.append(str(val))
    return " ".join(parts)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = SessionStore(args.workspace)
    machine = DevTeamMachine(store)
    memory = MemoryStore(args.workspace)
    cmd_label = _command_label(args)

    cmd = args.command

    if cmd == "memory":
        mcmd = args.memory_cmd
        if mcmd == "stats":
            _print_json({"ok": True, "stats": memory.stats()})
            return _log_cli(store, cmd_label, 0)
        if mcmd == "recall":
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]
            lessons = memory.recall(
                phase=args.phase,
                query=args.query,
                tags=tags,
                limit=args.limit,
                since=args.since or None,
            )
            _print_json({"ok": True, "lessons": _memory_to_json(memory, lessons)})
            return 0
        if mcmd == "add":
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]
            lesson = memory.add(
                kind=args.kind,
                phase=args.phase,
                title=args.title,
                lesson=args.lesson,
                context=args.context,
                source=args.source,
                status=args.status,
                session_id=machine.session.session_id,
                work_slug=machine.session.work_slug,
                tags=tags,
            )
            _print_json({"ok": True, "lesson": memory.lesson_to_dict(lesson)})
            return 0
        if mcmd == "draft-from-feedback":
            path = args.file or (
                store.artifacts_dir
                / (
                    SessionStore.ARTIFACT_SPEC_FEEDBACK
                    if args.target == "spec"
                    else SessionStore.ARTIFACT_DEV_FEEDBACK
                )
            )
            content = path.read_text(encoding="utf-8")
            created = memory.draft_from_feedback(
                args.target,
                content,
                session_id=machine.session.session_id,
                work_slug=machine.session.work_slug,
            )
            _print_json(
                {
                    "ok": True,
                    "drafted": len(created),
                    "lessons": _memory_to_json(memory, created),
                }
            )
            return 0
        if mcmd == "promote":
            lesson = memory.promote(args.id)
            if not lesson:
                _print_json({"ok": False, "error": f"Lesson {args.id} not found"})
                return 1
            _print_json({"ok": True, "lesson": memory.lesson_to_dict(lesson)})
            return 0
        if mcmd == "deprecate":
            lesson = memory.deprecate(args.id)
            if not lesson:
                _print_json({"ok": False, "error": f"Lesson {args.id} not found"})
                return 1
            _print_json({"ok": True, "lesson": memory.lesson_to_dict(lesson)})
            return 0
        if mcmd == "list":
            lessons = memory.list_lessons(status=args.status, kind=args.kind, limit=args.limit)
            _print_json({"ok": True, "lessons": _memory_to_json(memory, lessons)})
            return 0
        return 1

    if cmd == "status":
        st = machine.status()
        payload = {"ok": not st.get("blocked", False), "status": st, "memory": memory.stats()}
        _print_json(payload)
        rc = 0 if payload["ok"] else 1
        return _log_cli(store, cmd_label, rc, st.get("state", ""))

    if cmd == "check":
        report = machine.check()
        _print_json({"ok": report["ok"], "check": report, "status": machine.status()})
        return 0 if report["ok"] else 1

    if cmd == "suggest":
        suggestion = machine.suggest()
        _print_json({"ok": True, "suggest": suggestion, "status": machine.status()})
        return 0

    if cmd == "assert-gate":
        try:
            machine.assert_gate(args.phase)
            _print_json({"ok": True, "message": f"Gate {args.phase} ready", "status": machine.status()})
            return _log_cli(store, cmd_label, 0)
        except TransitionError as exc:
            _print_json({"ok": False, "error": str(exc), "status": machine.status()})
            return _log_cli(store, cmd_label, 1, str(exc))

    if cmd == "reset":
        removed = machine.reset()
        _print_json({"ok": True, "removed": removed, "message": "Legacy dev-team state cleared"})
        return 0

    if cmd == "verify-path":
        result = machine.verify_path(args.path)
        _print_json({"ok": result["allowed"], **result})
        return 0 if result["allowed"] else 1

    if cmd == "works":
        if args.works_cmd == "list":
            _print_json({"ok": True, "works": store.registry.list_works()})
            return 0
        if args.works_cmd == "show":
            info = store.show_work(args.slug.strip() or None)
            if not info:
                _print_json({"ok": False, "error": "No work found"})
                return 1
            _print_json({"ok": True, "work": info})
            return 0
        if args.works_cmd == "remove":
            try:
                slug = store.remove_work(args.slug.strip())
                _print_json({"ok": True, "removed": slug, "message": f"Deleted work {slug}"})
                return 0
            except FileNotFoundError as exc:
                _print_json({"ok": False, "error": str(exc)})
                return 1
        return 1

    if cmd == "log":
        if not store.work:
            _print_json({"ok": False, "error": "No active work. Run scope begin --name <topic> first."})
            return 1
        if args.log_cmd == "tail":
            events = store.tail_log(args.lines)
            _print_json({"ok": True, "work_slug": store.work.slug, "events": events})
            return 0
        if args.log_cmd == "note":
            store.log("agent_note", role=args.role, detail=args.message)
            _print_json({"ok": True, "message": "logged"})
            return 0
        if args.log_cmd == "clear":
            try:
                store.clear_logs()
                _print_json(
                    {
                        "ok": True,
                        "message": f"Cleared logs for {store.work.slug}",
                        "work_slug": store.work.slug,
                    }
                )
                return 0
            except RuntimeError as exc:
                _print_json({"ok": False, "error": str(exc)})
                return 1
        return 1

    if cmd == "scope":
        if args.scope_cmd == "begin":
            return _handle(
                machine,
                lambda: machine.scope_begin(args.name.strip()),
                command=cmd_label,
                success_msg=f"Task scoping started in {machine.status().get('work_dir', '')}",
            )
        if args.scope_cmd == "propose":
            return _handle(
                machine,
                lambda: machine.scope_propose(args.text),
                command=cmd_label,
                success_msg="Task scope proposed; awaiting human confirmation",
            )
        if args.scope_cmd == "confirm":
            return _handle(
                machine,
                machine.scope_confirm,
                command=cmd_label,
                success_msg="Task scope confirmed; run start",
            )
        return 1

    if cmd == "start":
        def _start():
            session = machine.start(
                args.mode,
                task=args.task.strip() or None,
            )
            memory.recall(phase="general", query=session.task, limit=3)
            return session

        return _handle(
            machine,
            _start,
            command=cmd_label,
            success_msg=f"Session started in {machine.session.state}",
        )

    if cmd == "write":
        content = args.file.read_text(encoding="utf-8") if args.file else (args.text or "")
        return _handle(
            machine,
            lambda: machine.write_artifact(args.phase, content),
            success_msg=f"Wrote artifact for {args.phase}",
        )

    if cmd == "write-qa-feedback":
        content = args.file.read_text(encoding="utf-8") if args.file else (args.text or "")
        return _handle(
            machine,
            lambda: machine.write_qa_feedback(args.target, content),
            success_msg=f"Wrote QA feedback for {args.target}",
        )

    if cmd == "validate":
        try:
            result = machine.validate_current()
            _print_json(
                {
                    "ok": result.ok,
                    "validation": {
                        "ok": result.ok,
                        "errors": result.errors,
                        "warnings": result.warnings,
                    },
                    "status": machine.status(),
                }
            )
            return 0 if result.ok else 1
        except TransitionError as exc:
            _print_json({"ok": False, "error": str(exc), "status": machine.status()})
            return 1

    if cmd == "submit":
        msgs = {
            "research": "Research submitted → RESEARCH_GATE",
            "spec": "Spec submitted → QA_SPEC_REVIEW",
            "dev": "Dev submitted → QA_DEV_REVIEW",
            "qa": "QA report submitted → QA_GATE",
        }
        phase = args.phase or machine.session.state.lower()

        def _submit():
            outcome = machine.submit(args.phase)
            st = machine.session.state
            recall_phase = {
                "QA_SPEC_REVIEW": "spec",
                "QA_DEV_REVIEW": "dev",
            }.get(st)
            if recall_phase:
                memory.recall(phase=recall_phase, limit=5)
            return outcome

        return _handle(machine, _submit, success_msg=msgs.get(phase, "Phase submitted"))

    if cmd == "qa-pass":
        return _handle(
            machine,
            lambda: machine.qa_pass(args.target),
            success_msg=f"QA passed {args.target} → human gate",
        )

    if cmd == "qa-reject":

        def _reject():
            session = machine.qa_reject(args.target)
            fb_name = (
                SessionStore.ARTIFACT_SPEC_FEEDBACK
                if args.target == "spec"
                else SessionStore.ARTIFACT_DEV_FEEDBACK
            )
            fb = store.read_artifact(fb_name)
            if fb:
                memory.draft_from_feedback(
                    args.target,
                    fb,
                    session_id=session.session_id,
                    work_slug=session.work_slug,
                )
            return session

        return _handle(
            machine,
            _reject,
            success_msg=f"QA rejected {args.target}; draft lessons saved to memory",
        )

    if cmd == "approve":
        return _handle(
            machine,
            lambda: machine.approve(args.phase),
            success_msg=f"Human approved {args.phase}",
        )

    if cmd == "revise":
        def _revise():
            session = machine.revise(args.phase, args.feedback)
            if args.feedback:
                memory.add(
                    kind="preference",
                    phase=args.phase,
                    title=f"Human revise {args.phase}: {args.feedback[:50]}",
                    lesson=args.feedback,
                    source="human-revise",
                    session_id=session.session_id,
                    work_slug=session.work_slug,
                    status="active",
                    tags=["human", args.phase],
                )
            return session

        return _handle(
            machine,
            _revise,
            success_msg=f"Sent back to {args.phase} for revision",
        )

    if cmd == "reject":
        return _handle(
            machine,
            lambda: machine.reject(args.target),
            success_msg=f"Rejected to {args.target}",
        )

    if cmd == "abort":
        return _handle(machine, machine.abort, success_msg="Session aborted")

    if cmd == "record-checks":
        return _handle(
            machine,
            lambda: machine.record_checks(args.note),
            success_msg="Check recorded",
        )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
