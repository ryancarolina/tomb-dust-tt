"""Implementation allowlist parsing from product spec."""

from __future__ import annotations

import re


def parse_implementation_allowlist(spec_content: str) -> list[str]:
    """Extract glob patterns from ### Implementation allowlist section."""
    patterns: list[str] = []
    in_section = False
    for line in spec_content.splitlines():
        if re.match(r"(?i)^#{1,3}\s*implementation\s+allowlist", line):
            in_section = True
            continue
        if in_section and re.match(r"^#{1,3}\s+", line):
            break
        if in_section:
            m = re.match(r"^\s*[-*]\s+`?([^`]+)`?\s*$", line)
            if m:
                patterns.append(m.group(1).strip())
            elif line.strip().startswith("- "):
                patterns.append(line.strip()[2:].strip())
    return patterns
