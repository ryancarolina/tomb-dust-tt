"""Chat-recorded human gate approvals (via beforeSubmitPrompt hook)."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dev_team.session import Session, SessionStore

ACK_FILE = "gate-acks.jsonl"
SECRET_FILE = ".gate-secret"
ACK_MAX_AGE_SECONDS = 3600


@dataclass
class ParsedIntent:
    action: str  # approve | revise | reject | scope_confirm
    phase: str = ""
    target: str = ""
    feedback: str = ""
    raw: str = ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret_path(store: SessionStore) -> Path:
    return store.registry.root / SECRET_FILE


def _acks_path(store: SessionStore) -> Path | None:
    if not store.work:
        return None
    return store.work.path / ACK_FILE


def _load_secret(store: SessionStore) -> bytes:
    path = _secret_path(store)
    store.registry.root.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(secrets.token_bytes(32))
    return path.read_bytes()


def _sign(store: SessionStore, payload: dict[str, Any]) -> str:
    key = _load_secret(store)
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(key, body.encode("utf-8"), hashlib.sha256).hexdigest()


def _verify_sig(store: SessionStore, payload: dict[str, Any], sig: str) -> bool:
    expected = _sign(store, payload)
    return hmac.compare_digest(expected, sig)


def parse_user_prompt(text: str, session: Session) -> ParsedIntent | None:
    """Parse a user chat message into a gate action, if unambiguous."""
    raw = text.strip()
    if not raw:
        return None
    lower = raw.lower()

    m = re.search(r"\bapprove\s+(research|spec|dev|qa)\b", lower)
    if m:
        return ParsedIntent("approve", phase=m.group(1), raw=raw)

    m = re.search(r"\breject\s+to\s+(research|spec|dev)\b", lower)
    if m:
        return ParsedIntent("reject", target=m.group(1), raw=raw)

    m = re.search(r"\brevise\s+(research|spec|dev|qa)\s*:\s*(.+)", raw, re.IGNORECASE)
    if m:
        return ParsedIntent(
            "revise",
            phase=m.group(1).lower(),
            feedback=m.group(2).strip(),
            raw=raw,
        )

    if session.state == "TASK_SCOPING" and session.task_scope and not session.task_scope_confirmed:
        if re.search(r"\b(scope confirm|confirm scope)\b", lower):
            return ParsedIntent("scope_confirm", raw=raw)
        if re.fullmatch(
            r"(yes|yep|yeah|confirmed|confirm|lgtm|looks good|approved?|go ahead|start)\.?!?",
            lower,
        ):
            return ParsedIntent("scope_confirm", raw=raw)

    if session.pending_human_gate and re.search(
        r"\b(lgtm|looks good|approved?|ship( it)?|go ahead)\b",
        lower,
    ):
        return ParsedIntent("approve", phase=session.pending_human_gate, raw=raw)

    return None


def _intent_allowed(intent: ParsedIntent, session: Session) -> bool:
    st = session.state
    if intent.action == "scope_confirm":
        return st == "TASK_SCOPING" and bool(session.task_scope) and not session.task_scope_confirmed
    if intent.action == "approve":
        gate = f"{intent.phase.upper()}_GATE" if intent.phase else ""
        return st == gate and session.pending_human_gate == intent.phase
    if intent.action == "revise":
        gate = f"{intent.phase.upper()}_GATE"
        return st == gate
    if intent.action == "reject":
        mapping = {
            "research": "SPEC_GATE",
            "spec": "DEV_GATE",
            "dev": "QA_GATE",
        }
        return st == mapping.get(intent.target, "")
    return False


def record_intent(store: SessionStore, session: Session, intent: ParsedIntent) -> bool:
    """Record a signed ack from the user's chat message. Returns True if recorded."""
    if not _intent_allowed(intent, session):
        return False
    path = _acks_path(store)
    if path is None:
        return False

    payload: dict[str, Any] = {
        "at": _utc_now(),
        "action": intent.action,
        "phase": intent.phase,
        "target": intent.target,
        "feedback": intent.feedback,
        "state": session.state,
        "work_slug": session.work_slug,
        "prompt_excerpt": intent.raw[:200],
        "consumed": False,
    }
    row = {"payload": payload, "sig": _sign(store, payload)}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    store.log(
        "human_gate_ack",
        detail=f"{intent.action}:{intent.phase or intent.target}",
        extra={"state": session.state},
    )
    return True


def process_user_prompt(store: SessionStore, prompt_text: str) -> dict[str, Any]:
    session = store.load()
    intent = parse_user_prompt(prompt_text, session)
    if intent is None:
        return {"recorded": False, "reason": "no_matching_intent"}
    if not _intent_allowed(intent, session):
        return {
            "recorded": False,
            "reason": "intent_not_allowed_for_state",
            "state": session.state,
            "intent": intent.action,
        }
    ok = record_intent(store, session, intent)
    return {
        "recorded": ok,
        "action": intent.action,
        "phase": intent.phase,
        "target": intent.target,
        "state": session.state,
    }


def _load_acks(store: SessionStore) -> list[dict[str, Any]]:
    path = _acks_path(store)
    if path is None or not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _is_fresh(at: str) -> bool:
    try:
        ts = datetime.fromisoformat(at)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age <= ACK_MAX_AGE_SECONDS
    except ValueError:
        return False


def find_ack(
    store: SessionStore,
    *,
    action: str,
    phase: str = "",
    target: str = "",
) -> dict[str, Any] | None:
    for row in reversed(_load_acks(store)):
        payload = row.get("payload", {})
        sig = row.get("sig", "")
        if payload.get("consumed"):
            continue
        if not _verify_sig(store, payload, sig):
            continue
        if payload.get("action") != action:
            continue
        if not _is_fresh(payload.get("at", "")):
            continue
        if action == "approve" and payload.get("phase") != phase:
            continue
        if action == "revise" and payload.get("phase") != phase:
            continue
        if action == "reject" and payload.get("target") != target:
            continue
        return row
    return None


def consume_ack(store: SessionStore, row: dict[str, Any]) -> None:
    payload = row["payload"]
    payload["consumed"] = True
    payload["consumed_at"] = _utc_now()
    path = _acks_path(store)
    if path is None:
        return
    lines: list[str] = []
    target_sig = row.get("sig")
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        if data.get("sig") == target_sig:
            data["payload"] = payload
            data["sig"] = _sign(store, payload)
        lines.append(json.dumps(data, ensure_ascii=False))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


class HumanGateError(Exception):
    """Raised when a human-only command lacks a valid chat acknowledgment."""


def require_chat_ack(
    store: SessionStore,
    command: str,
    *,
    action: str,
    phase: str = "",
    target: str = "",
) -> None:
    """Raise HumanGateError if no valid chat ack exists for this command."""
    import os

    from dev_team.human_gate import HUMAN_ACK_ENV

    if os.environ.get(HUMAN_ACK_ENV) == "1":
        return

    row = find_ack(store, action=action, phase=phase, target=target)
    if row is None:
        phase_hint = phase or target or "…"
        raise HumanGateError(
            f"'{command}' requires your approval in chat first. "
            f"Reply with e.g. `approve {phase_hint}` or `lgtm` while at the gate, "
            "then the orchestrator can run the CLI approve command."
        )
    consume_ack(store, row)
