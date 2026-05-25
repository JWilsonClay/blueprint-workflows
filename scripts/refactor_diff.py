#!/usr/bin/env python3
"""
refactor_diff.py — Cross-Phase Diff Review Node
================================================
Sovereign Refactor Protocol — Script Suite

A lightweight, phase-aware diff review node that compares the actual
filesystem state against the declared intent in REFACTOR_MANIFEST.yaml.

This script answers one question at every phase boundary:
  "Does reality match what the manifest said we intended to do?"

Usage:
  python3 refactor_diff.py --project-root /path/to/project --phase p1
  python3 refactor_diff.py --project-root /path/to/project --phase p2
  python3 refactor_diff.py --project-root /path/to/project --phase p3
  python3 refactor_diff.py --project-root /path/to/project --phase p4
  python3 refactor_diff.py --project-root /path/to/project --phase p4 --pre-merge
  python3 refactor_diff.py --project-root /path/to/project --spec-summary

Requirements: Python 3.8+, PyYAML (pip install pyyaml).

SoC decomposition (2026-05-25):
  Data models    -> core/diff_models.py
  Phase checkers -> core/diff_checkers.py
  Report display -> core/diff_report.py
  CLI + main     -> this file
"""

import argparse
import sys
from pathlib import Path

from core.console import out, fail
from core.manifest import load_manifest, MANIFEST_FILENAME
from core.diff_models import DiffReport
from core.diff_checkers import (
    check_phase_p1, check_phase_p2, check_phase_p3, check_phase_p4
)
from core.diff_report import print_report, print_spec_summary

try:
    import yaml
except ImportError:
    print("FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="refactor_diff.py",
        description=(
            "Diff Review Node: compare actual filesystem state against manifest intent.\n"
            "Flags deviations and loops back if CRITICAL issues are found.\n\n"
            "Phases:\n"
            "  p1 — After refactor_bridge.py: shims at targets, originals untouched\n"
            "  p2 — After refactor_migrate.py: real files at targets, reverse shims at originals\n"
            "  p3 — During refactor surgery: structural P2 checks + surgery_complete consistency\n"
            "  p4 — After refactor_clean.py: zero shims, all targets present\n"
            "  p4 --pre-merge: stricter check before merging to main"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--project-root", required=True,
                   help="Path to the root of the project being refactored.")
    p.add_argument("--phase",
                   choices=["p1", "p2", "p3", "p4"],
                   help="Which phase to validate against.")
    p.add_argument("--pre-merge", action="store_true",
                   help="Stricter Phase 4 check: also verify artifacts are cleaned.")
    p.add_argument("--spec-summary", action="store_true",
                   help="Print a human-readable summary of manifest intent.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    if not root.exists():
        fail(f"Project root does not exist: {root}")

    manifest = load_manifest(root)

    if args.spec_summary:
        print_spec_summary(root, manifest)
        sys.exit(0)

    if not args.phase:
        fail("--phase is required unless --spec-summary is used.")

    out(">>", f"Sovereign Refactor Protocol — Diff Review Node (Phase: {args.phase.upper()})")
    out(">>", f"Project root: {root}")
    out(">>", f"Manifest: {MANIFEST_FILENAME} ({len(manifest.get('files', []))} entries)")

    report = DiffReport(phase=args.phase, project_root=root)

    if args.phase == "p1":
        check_phase_p1(root, manifest, report)
    elif args.phase == "p2":
        check_phase_p2(root, manifest, report)
    elif args.phase == "p3":
        check_phase_p3(root, manifest, report)
    elif args.phase == "p4":
        check_phase_p4(root, manifest, report, pre_merge=args.pre_merge)

    print_report(report)

    exit_code = 0 if report.is_clean else 1
    out(">>", f"Diff review complete. Exit code: {exit_code} "
        f"({'CLEAN' if exit_code == 0 else 'DEVIATIONS FOUND — loop back required'})")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
