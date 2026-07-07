#!/usr/bin/env python3
"""
harden_workflow_audit.py — Structural Assessment Evidence Engine CLI
=======================================================================
The read-only mechanical layer behind `/harden-workflow`'s Phase 1
Assessment Card, Degradation Check, Phase 5b `/triage` Compatibility Audit,
and Phase 7a/7c Completeness Check. Reuses `scripts/suite/checks.py`'s
already-exported functions directly rather than re-parsing structural facts
a fourth time. See scripts/harden_workflow/__init__.py for the full
contract.

Usage:
    python harden_workflow_audit.py --workflow-name NAME --workspace /abs/path [options]

Required:
    --workflow-name NAME    Bare workflow name, e.g. "focus-plan" (no
                            leading slash, no .md extension).
    --workspace PATH        Absolute path to the target workspace root.

Optional:
    --triage-md PATH        Path to triage.md for the /triage gap check
                            (default: this repo's claude-commands/triage.md).
    --output-json           Emit JSON to stdout.
    --quiet                 Suppress human-readable output.

Origin: implementation-plan.md Phase 4.5 (Sovereign Scaling Cluster),
docs/compression-staging/harden-workflow-honest-design.md Section 4.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from harden_workflow.degradation_check import check_degradation, extract_standard_version
from harden_workflow.grade_hint import compute_grade_hint
from harden_workflow.reporter import HardenWorkflowReporter
from suite.checks import (
    check_symlinks,
    count_phases,
    count_strict_rules,
    extract_glossary_terms,
    has_changelog_section,
    has_glossary_section,
    has_how_to_begin_section,
    has_integration_section,
    has_strict_rules_section,
    parse_frontmatter,
)
from suite.models import LintReport
from triage.matrix_completeness import extract_matrix_workflows

_DEFAULT_TRIAGE_MD = _HERE.parent.parent / "claude-commands" / "triage.md"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="harden_workflow_audit.py",
        description="Structural Assessment Evidence Engine — presence facts, degradation "
                    "check, /triage gap check, and an advisory grade hint for "
                    "/harden-workflow. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workflow-name", required=True, type=str,
                   help="Bare workflow name, e.g. 'focus-plan'.")
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the target workspace root.")
    p.add_argument("--triage-md", type=str, default=None,
                   help="Path to triage.md (default: this repo's claude-commands/triage.md).")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1

    command_file = workspace / "claude-commands" / f"{args.workflow_name}.md"
    if not command_file.is_file():
        report = {"facts": None, "grade_hint": None, "degradation": None, "triage_gap": None}
        HardenWorkflowReporter().render(report, quiet=args.quiet, output_json=args.output_json)
        return 0

    content = command_file.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    frontmatter_present = bool(fm) and bool(fm.get("description")) if fm is not None else False
    glossary_present = has_glossary_section(body)
    how_to_begin_present = has_how_to_begin_section(body)
    strict_rules_present = has_strict_rules_section(body)
    integration_present = has_integration_section(body)
    changelog_present = has_changelog_section(body)
    strict_rules_count = count_strict_rules(body)
    phase_count = count_phases(body)
    glossary_terms = extract_glossary_terms(body)

    symlink_report = LintReport()
    check_symlinks(f"{args.workflow_name}.md", str(workspace), symlink_report)
    symlink_present = not any(f.check == "symlink" for f in symlink_report.findings)

    facts = {
        "command_file_exists": True,
        "command_file_correct": True,
        "symlink_present": symlink_present,
        "frontmatter_present": frontmatter_present,
        "glossary_present": glossary_present,
        "glossary_term_count": len(glossary_terms),
        "how_to_begin_present": how_to_begin_present,
        "strict_rules_present": strict_rules_present,
        "strict_rules_count": strict_rules_count,
        "integration_present": integration_present,
        "phase_count": phase_count,
        "changelog_present": changelog_present,
    }

    grade_hint = compute_grade_hint(
        command_file_correct=True,
        symlink_present=symlink_present,
        frontmatter_present=frontmatter_present,
        glossary_present=glossary_present,
        how_to_begin_present=how_to_begin_present,
        strict_rules_present=strict_rules_present,
        changelog_present=changelog_present,
        structured_output_present=None,
    ).as_dict()

    certified_version = extract_standard_version(content)
    degradation = check_degradation(certified_version).as_dict()

    triage_md_path = Path(args.triage_md) if args.triage_md else _DEFAULT_TRIAGE_MD
    matrix_workflows = extract_matrix_workflows(str(triage_md_path))
    bare_names = {w.split()[0] for w in matrix_workflows}
    represented = f"/{args.workflow_name}" in bare_names
    triage_gap = {"represented": represented, "workflow": f"/{args.workflow_name}"}

    report = {
        "facts": facts,
        "grade_hint": grade_hint,
        "degradation": degradation,
        "triage_gap": triage_gap,
    }
    HardenWorkflowReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
