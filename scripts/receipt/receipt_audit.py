#!/usr/bin/env python3
"""
receipt_audit.py — Receipt Coverage Engine CLI
=================================================
Cross-references tasks.md's completed phases against BUILD/VALIDATION/HARDEN
receipts, reports the Documented dimension's existence (not a per-phase
match — see coverage.py docstring for why), and wires the Quality-Process
dimension via a direct call to quality_audit.py. Emits a structured coverage
report + gap percentage. Read-only; writes nothing.

Usage:
    python receipt_audit.py --workspace /abs/path [--output-json] [--quiet]

Origin: Sovereign Verification-Spine Upgrade Campaign, QUEUE #11, resolving
helpdesk-tickets/CLOSED_20260704_hallucinated-success-recurrence_workflow.md.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from receipt.coverage import compute_coverage
from receipt.reporter import CoverageReporter


def _parse_args():
    p = argparse.ArgumentParser(
        prog="receipt_audit.py",
        description="Receipt Coverage Engine — cross-references tasks.md completed "
                    "phases against receipt files and computes a gap percentage.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the project workspace root.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main():
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1
    report = compute_coverage(workspace)
    CoverageReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
