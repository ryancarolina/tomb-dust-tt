from __future__ import annotations

import argparse
import sys

from tomb_gm.cli.output import emit, fail
from tomb_gm.cli.parser import build_parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if not handler:
        fail("No command handler")
        return 1
    try:
        result = handler(args, None)
        return emit(result)
    except Exception as exc:  # noqa: BLE001 — CLI top-level
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
