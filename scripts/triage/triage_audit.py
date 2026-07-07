#!/usr/bin/env python3
"""
triage_audit.py — Triage Evidence Engine CLI
===============================================
The read-only mechanical layer behind `/triage`'s Trigger Matrix
completeness check (Phase 2), and direct pass-throughs of the existing
`scripts/focus/phase_status.py` (task/phase state, Phase 0b) and
`scripts/receipt/coverage.py` (receipt state, Phase 0c) engines — reused
directly, not duplicated. Emits a structured JSON evidence report the agent
reasons over; never judges trigger-evaluation rigor or priority assignment.
See scripts/triage/__init__.py for the full contract.

Usage:
    python triage_audit.py --workspace /abs/path [options]

Optional:
    --triage-md PATH       Path to triage.md itself (default: this repo's
                            claude-commands/triage.md, resolved relative to
                            this script's location).
    --report-file PATH     Path to an emitted Triage Report's text, for the
                            completeness check.
    --report-text TEXT     Inline report text, alternative to --report-file.
    --tasks-md PATH        Explicit tasks.md path override (phase state).
    --output-json          Emit JSON to stdout.
    --quiet                Suppress human-readable output.

Origin: implementation-plan.md Phase 4.4-4.5 (Sovereign Scaling Cluster),
docs/compression-staging/triage-honest-design.md Section 4.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from focus.phase_status import build_phase_status_report
from receipt.coverage import compute_coverage
from triage.matrix_completeness import check_report_completeness, extract_matrix_workflows
from triage.reporter import TriageEvidenceReporter

_DEFAULT_TRIAGE_MD = _HERE.parent.parent / "claude-commands" / "triage.md"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="triage_audit.py",
        description="Triage Evidence Engine — Trigger Matrix completeness, task/phase "
                    "state, and receipt coverage for /triage. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the target workspace root.")
    p.add_argument("--triage-md", type=str, default=None,
                   help="Path to triage.md (default: this repo's claude-commands/triage.md).")
    p.add_argument("--report-file", type=str, default=None,
                   help="Path to an emitted Triage Report's text.")
    p.add_argument("--report-text", type=str, default=None,
                   help="Inline report text, alternative to --report-file.")
    p.add_argument("--tasks-md", type=str, default=None,
                   help="Explicit tasks.md path override.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1

    completeness = None
    report_text = None
    if args.report_text is not None:
        report_text = args.report_text
    elif args.report_file is not None:
        report_text = Path(args.report_file).read_text(encoding="utf-8")

    if report_text is not None:
        triage_md_path = Path(args.triage_md) if args.triage_md else _DEFAULT_TRIAGE_MD
        matrix_workflows = extract_matrix_workflows(str(triage_md_path))
        completeness = check_report_completeness(matrix_workflows, report_text).as_dict()

    tasks_md_path = Path(args.tasks_md).resolve() if args.tasks_md else None
    phase_status = build_phase_status_report(workspace, tasks_md_path=tasks_md_path).as_dict()

    receipt_coverage = compute_coverage(workspace)

    report = {
        "completeness": completeness,
        "phase_status": phase_status,
        "receipt_coverage": receipt_coverage,
    }
    TriageEvidenceReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
