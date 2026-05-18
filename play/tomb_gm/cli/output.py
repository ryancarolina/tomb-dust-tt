from __future__ import annotations

import json
import sys
from typing import Any


def emit(data: dict[str, Any], *, ok: bool | None = None) -> int:
    if ok is not None and "ok" not in data:
        data = {**data, "ok": ok}
    print(json.dumps(data, indent=2))
    return 0 if data.get("ok") else 1


def fail(message: str, **extra: Any) -> int:
    payload: dict[str, Any] = {"ok": False, "error": message, **extra}
    print(json.dumps(payload, indent=2), file=sys.stderr)
    return 1
