"""Phase exit-criteria validators for dev-team artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass

from dev_team.allowlist import parse_implementation_allowlist


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]

    def merge(self, other: ValidationResult) -> ValidationResult:
        return ValidationResult(
            ok=self.ok and other.ok,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


def _fail(msg: str) -> ValidationResult:
    return ValidationResult(False, [msg], [])


def _ok(warnings: list[str] | None = None) -> ValidationResult:
    return ValidationResult(True, [], warnings or [])


def _section(text: str, heading: str) -> str | None:
    pattern = rf"(?im)^#{{1,3}}\s*{re.escape(heading)}\s*$"
    match = re.search(pattern, text)
    if not match:
        return None
    start = match.end()
    next_heading = re.search(r"(?m)^#{1,3}\s+\S", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _has_file_path_reference(text: str) -> bool:
    patterns = [
        r"`[^`]+\.[a-zA-Z0-9]+`",  # `file.ext`
        r"\b[\w./\\-]+\.(py|ts|tsx|js|jsx|md|json|go|rs|java|cs|cpp|h|yml|yaml|toml)\b",
        r"(?:src|lib|app|tests?)/[\w./\\-]+",
        r"\b[A-Za-z]:\\[\w\\.-]+",  # Windows paths
    ]
    return any(re.search(p, text) for p in patterns)


AC_PATTERN = re.compile(r"(?im)(?:^|\s)AC-\d+\s*[:)]", re.MULTILINE)
AC_ID_PATTERN = re.compile(r"AC-\d+", re.IGNORECASE)


def extract_ac_ids(text: str) -> list[str]:
    ids = AC_ID_PATTERN.findall(text)
    # Normalize to AC-N
    seen: list[str] = []
    for raw in ids:
        num = re.search(r"\d+", raw)
        if not num:
            continue
        normalized = f"AC-{num.group()}"
        if normalized not in seen:
            seen.append(normalized)
    return seen


def validate_task_scope(text: str) -> ValidationResult:
    """Task scope must be 1–2 plain-English sentences agreed with the human."""
    errors: list[str] = []
    warnings: list[str] = []

    cleaned = text.strip()
    if not cleaned:
        return _fail("Task scope is empty.")

    if re.search(r"(?m)^#+\s", cleaned) or re.search(r"(?m)^-\s", cleaned):
        errors.append("Task scope must be plain sentences, not markdown lists or headings.")

    if "```" in cleaned or "`" in cleaned:
        warnings.append("Avoid code fences or backticks in task scope; use plain English.")

    words = cleaned.split()
    if len(words) < 8:
        errors.append("Task scope is too short; use at least one full sentence (roughly 8+ words).")
    if len(words) > 80:
        errors.append("Task scope is too long; keep it to 1–2 concise sentences (≤80 words).")

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    if len(sentences) < 1:
        errors.append("Task scope must include at least one sentence ending with . ! or ?")
    if len(sentences) > 2:
        errors.append(
            f"Task scope has {len(sentences)} sentences; limit to 1–2 plain-English sentences."
        )

    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_research(content: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not content.strip():
        return _fail("Research brief is empty.")

    if not re.search(r"(?i)research\s+brief", content):
        errors.append("Missing '## Research brief' heading.")

    request = _section(content, "Request")
    if not request or len(request.split()) < 3:
        errors.append("### Request must restate the task in at least one complete sentence.")

    findings = _section(content, "Findings")
    if not findings:
        errors.append("Missing ### Findings section.")
    elif not _has_file_path_reference(findings):
        errors.append("Findings must cite at least one codebase file path.")

    risks = _section(content, "Risks & unknowns") or _section(content, "Risks and unknowns")
    if risks is None:
        errors.append("Missing ### Risks & unknowns section (use 'none identified' if applicable).")

    recommendation = _section(content, "Recommendation")
    if not recommendation:
        errors.append("Missing ### Recommendation section.")
    elif not re.search(r"(?i)\b(proceed|clarify|blocked)\b", recommendation):
        errors.append("Recommendation must state proceed, clarify, or blocked.")

    if re.search(r"(?i)##\s*product\s+spec", content):
        errors.append("Research brief must not contain a product spec.")

    if AC_PATTERN.search(content):
        errors.append("Research brief must not define acceptance criteria (AC-N); that belongs in the spec phase.")

    if re.search(r"(?i)acceptance\s+criteria", content) and re.search(r"-\s*\[\s*\]", content):
        errors.append("Research brief must not include acceptance-criteria checklists.")

    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_spec(content: str, *, research_approved: bool, mode: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not content.strip():
        return _fail("Product spec is empty.")

    if mode == "full" and not research_approved:
        errors.append("Research was not approved. Approve research at RESEARCH_GATE or restart with skip-research.")

    if not re.search(r"(?i)product\s+spec", content):
        errors.append("Missing '## Product spec' heading.")

    scope = _section(content, "Scope")
    if not scope:
        errors.append("Missing ### Scope section.")
    else:
        if not re.search(r"\*\*in:\*\*|\bin\s*:", scope, re.IGNORECASE):
            errors.append("Scope must define **In:** (in scope).")
        if not re.search(r"\*\*out:\*\*|\bout\s*:", scope, re.IGNORECASE):
            errors.append("Scope must define **Out:** (out of scope).")

    ac_section = _section(content, "Acceptance criteria")
    ac_ids = extract_ac_ids(content)
    if not ac_section or not ac_ids:
        errors.append("Spec must include at least one numbered acceptance criterion (AC-1, AC-2, …).")
    else:
        for ac in ac_ids:
            if len(ac_section.split(ac)) < 2:
                warnings.append(f"{ac} may not be documented under Acceptance criteria.")

    priority = _section(content, "Priority")
    if not priority:
        errors.append("Missing ### Priority section.")
    else:
        for label in ("Must", "Should", "Could"):
            if not re.search(rf"(?i)\b{label}\b", priority):
                errors.append(f"Priority must include **{label}:** level.")

    approach = _section(content, "Approach")
    if not approach or len(approach) < 10:
        errors.append("### Approach must describe the solution and key areas/files to touch.")

    if re.search(r"(?i)##\s*dev\s+handoff", content):
        errors.append("Product spec must not contain dev handoff content.")

    if not parse_implementation_allowlist(content):
        errors.append(
            "Missing ### Implementation allowlist with at least one path "
            "(e.g. - docs/** or - src/feature/**)."
        )

    vague = re.findall(r"(?i)\b(works well|fast enough|user friendly|robust)\b", content)
    if vague:
        warnings.append(f"Possibly vague terms in spec: {', '.join(set(vague))}. Prefer testable criteria.")

    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_spec_for_qa_review(content: str) -> ValidationResult:
    """QA spec review: all PM standards + rigor checks before qa-pass."""
    base = validate_spec(content, research_approved=True, mode="skip-research")
    errors = list(base.errors)
    warnings = list(base.warnings)

    ac_ids = extract_ac_ids(content)
    must_section = _section(content, "Priority") or ""
    for ac in ac_ids:
        line_pat = rf"(?im)^-\s*\[\s*\]\s*{re.escape(ac)}\s*:"
        if not re.search(line_pat, content):
            errors.append(f"{ac} must appear as a checkbox acceptance criterion (- [ ] {ac}: …).")

    for ac in ac_ids:
        if ac.upper() in must_section.upper() or "**must:**" in must_section.lower():
            continue
        warnings.append(f"{ac} is not listed under **Must:** in Priority.")

    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_qa_spec_feedback(content: str) -> ValidationResult:
    errors: list[str] = []
    if not content.strip():
        return _fail("QA spec feedback file is empty.")
    if not re.search(r"(?i)qa\s+spec\s+review", content):
        errors.append("Missing '## QA spec review' heading.")
    if not re.search(r"(?i)###\s*verdict", content):
        errors.append("Missing ### Verdict section.")
    if not re.search(r"(?i)\bfail\b", content):
        errors.append("Verdict must be Fail when rejecting spec (use qa-reject).")
    blockers = _section(content, "Blockers")
    if not blockers or not re.search(r"(?i)B-\d+", blockers):
        errors.append("### Blockers must list at least one item (B-1, B-2, …).")
    return ValidationResult(len(errors) == 0, errors, [])


def validate_qa_dev_feedback(content: str) -> ValidationResult:
    errors: list[str] = []
    if not content.strip():
        return _fail("QA dev feedback file is empty.")
    if not re.search(r"(?i)qa\s+dev\s+review", content):
        errors.append("Missing '## QA dev review' heading.")
    if not re.search(r"(?i)###\s*verdict", content):
        errors.append("Missing ### Verdict section.")
    if not re.search(r"(?i)\bfail\b", content):
        errors.append("Verdict must be Fail when rejecting dev work (use qa-reject).")
    blockers = _section(content, "Blockers")
    if not blockers or not re.search(r"(?i)B-\d+", blockers):
        errors.append("### Blockers must list at least one item (B-1, B-2, …).")
    mismatch = _section(content, "Spec mismatches") or _section(content, "Spec Mismatches")
    if not mismatch:
        errors.append("Missing ### Spec mismatches section referencing AC-N or spec clauses.")
    return ValidationResult(len(errors) == 0, errors, [])


def validate_dev_vs_spec(
    dev_content: str,
    spec_content: str | None,
) -> ValidationResult:
    """QA dev review: implementation must match approved spec."""
    errors: list[str] = []
    warnings: list[str] = []

    if not spec_content:
        return _fail("spec.md missing; cannot verify dev against spec.")

    ac_ids = extract_ac_ids(spec_content)
    if not ac_ids:
        errors.append("Spec has no AC-N IDs to verify against.")

    dev_upper = dev_content.upper()
    for ac in ac_ids:
        if ac.upper() not in dev_upper:
            errors.append(f"{ac} from spec is not addressed in dev handoff.")

    scope = _section(spec_content, "Scope") or ""
    out_match = re.search(r"(?i)\*\*out:\*\*\s*(.+)", scope)
    if out_match and out_match.group(1).strip() not in ("—", "-", "none", "n/a"):
        warnings.append("Confirm dev handoff does not implement **Out:** scope items.")

    approach = _section(spec_content, "Approach") or ""
    changes = _section(dev_content, "Changes") or ""
    if changes and approach:
        for path in re.findall(r"`([^`]+)`", changes):
            if path not in approach and not _has_file_path_reference(approach):
                warnings.append(f"Changed file `{path}` not mentioned in spec Approach.")

    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_dev_handoff(
    content: str,
    *,
    spec_approved: bool,
    spec_content: str | None,
    checks_run: list[str],
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not spec_approved:
        errors.append(
            "Product spec was not human-approved. Complete QA spec review, SPEC_GATE, and approve spec."
        )

    if not content.strip():
        return ValidationResult(False, errors + ["Dev handoff is empty."], warnings)

    if not re.search(r"(?i)dev\s+handoff", content):
        errors.append("Missing '## Dev handoff' heading.")

    changes = _section(content, "Changes")
    if not changes or not _has_file_path_reference(changes):
        errors.append("### Changes must list modified files with paths.")

    ac_ids_spec = extract_ac_ids(spec_content or "")
    ac_mapping = _section(content, "AC mapping")
    ac_ids_handoff = extract_ac_ids(content)

    if not ac_mapping:
        errors.append("Missing ### AC mapping section (table mapping each AC to implementation).")
    elif ac_ids_spec:
        content_upper = content.upper()
        missing = [ac for ac in ac_ids_spec if ac.upper() not in content_upper]
        if missing:
            errors.append(f"AC mapping missing entries for: {', '.join(missing)}.")

    verify = _section(content, "Verify")
    if not verify or len(verify) < 5:
        errors.append("### Verify must describe commands or steps to validate the change.")

    if not checks_run:
        warnings.append(
            "No checks recorded. Run: dev_team_cli.py record-checks --note 'pytest: pass' after build/test/lint."
        )

    return ValidationResult(len(errors) == 0, errors, warnings)


def validate_qa_report(
    content: str,
    *,
    dev_approved: bool,
    spec_content: str | None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not dev_approved:
        errors.append("Dev work was not approved. Approve at DEV_GATE before QA report.")

    if not content.strip():
        return ValidationResult(False, errors + ["QA report is empty."], warnings)

    if not re.search(r"(?i)qa\s+report", content):
        errors.append("Missing '## QA report' heading.")

    summary = _section(content, "Summary")
    if not summary or not re.search(r"(?i)\b(pass|fail)\b", summary):
        errors.append("### Summary must state Pass, Pass with notes, or Fail.")

    ac_ids_spec = extract_ac_ids(spec_content or "")
    if ac_ids_spec:
        for ac in ac_ids_spec:
            if ac.upper() not in content.upper():
                errors.append(f"QA report must include verification row/evidence for {ac}.")

    if not re.search(r"(?i)regression|edge", content):
        errors.append("QA report must document regression and/or edge-case checks.")

    # Critical issues block gate
    issues = _section(content, "Issues") or content
    critical_rows = re.findall(
        r"(?im)\|\s*critical\s*\|[^|\n]*\|[^|\n]*\|",
        issues,
    )
    if critical_rows:
        errors.append(
            f"QA report lists {len(critical_rows)} Critical issue(s). Resolve or get explicit user waiver before QA_GATE."
        )

    return ValidationResult(len(errors) == 0, errors, warnings)
