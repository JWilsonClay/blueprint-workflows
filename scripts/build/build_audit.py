#!/usr/bin/env python3
"""
build_audit.py — Build Evidence Engine CLI
=============================================
The read-only mechanical layer behind `/execute-build`'s Step 0b/0d/6 (Phase
Map + receipt status) and Step 5d/5f (Completeness Scan, Scope Diff). Emits a
structured JSON evidence report the agent reasons over — it never assesses
whether a phase is genuinely complete, a marker is justified, or a scope
deviation is warranted. See scripts/build/__init__.py for the full contract.

Usage:
    python build_audit.py --workspace /abs/path [options]

Optional:
    --tasks-md PATH           Explicit tasks.md path (overrides workspace/tasks.md).
    --phase-files PATH [...]  Files this phase created/modified — scanned for
                              Step 5d completeness markers. Omit to skip.
    --declared-scope PATH [...]  This phase's declared file scope — diffed
                              against `git status` for Step 5f. Omit to skip.
    --output-json             Emit the evidence report as JSON to stdout.
    --quiet                   Suppress human-readable output.

Origin: implementation-plan.md Phase 4.2 (Sovereign Scaling Cluster),
docs/compression-staging/execute-build-honest-design.md Section 3.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from build.evidence import compute_scope_diff, scan_completeness
from build.reporter import BuildEvidenceReporter
from focus.phase_status import build_phase_status_report


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="build_audit.py",
        description="Build Evidence Engine — Phase Map/receipt status, completeness "
                    "scan, and scope diff for /execute-build. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the target workspace root.")
    p.add_argument("--tasks-md", type=str, default=None,
                   help="Explicit tasks.md path (overrides workspace/tasks.md).")
    p.add_argument("--phase-files", nargs="*", default=None,
                   help="Files this phase created/modified (Step 5d completeness scan).")
    p.add_argument("--declared-scope", nargs="*", default=None,
                   help="This phase's declared file scope (Step 5f scope diff).")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1

    tasks_md_path = Path(args.tasks_md).resolve() if args.tasks_md else None
    phase_report = build_phase_status_report(workspace, tasks_md_path=tasks_md_path)

    completeness = None
    if args.phase_files is not None:
        completeness = [m.as_dict() for m in scan_completeness(args.phase_files, workspace=workspace)]

    scope_diff = None
    if args.declared_scope is not None:
        scope_diff = compute_scope_diff(workspace, args.declared_scope).as_dict()

    report = {
        "phase_status": phase_report.as_dict(),
        "completeness": completeness,
        "scope_diff": scope_diff,
    }
    BuildEvidenceReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
