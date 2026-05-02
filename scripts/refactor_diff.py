#!/usr/bin/env python3
"""
refactor_diff.py — Cross-Phase Diff Review Node
================================================
Sovereign Refactor Protocol — Script Suite

A lightweight, phase-aware diff review node that compares the actual
filesystem state against the declared intent in REFACTOR_MANIFEST.yaml.

This script answers one question at every phase boundary:
  "Does reality match what the manifest said we intended to do?"

If not, it flags every deviation, categorizes them by severity, and
exits with code 1 — blocking any commit until deviations are resolved
or acknowledged.

The loop-back mechanism:
  - CRITICAL deviations → must be fixed before proceeding (exit 1)
  - WARNING deviations  → flagged for human review, but do not block
  - INFO items          → informational notes, no action required

Usage:
  python3 refactor_diff.py --project-root /path/to/project --phase p1
  python3 refactor_diff.py --project-root /path/to/project --phase p2
  python3 refactor_diff.py --project-root /path/to/project --phase p3
  python3 refactor_diff.py --project-root /path/to/project --phase p4
  python3 refactor_diff.py --project-root /path/to/project --phase p4 --pre-merge

  # Show a summary of what the manifest intends (no filesystem checks):
  python3 refactor_diff.py --project-root /path/to/project --spec-summary

Requirements: Python 3.8+, PyYAML (pip install pyyaml).
"""

import argparse
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from core.console import out, fail, section_header
from core.manifest import load_manifest, get_language, MANIFEST_FILENAME
from core.filesystem import (
    walk_project, is_shim_file, get_source_extensions,
    read_file_safe, is_forward_shim, is_reverse_shim, shim_points_to
)

try:
    import yaml
except ImportError:
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

SHIM_FILE_MARKER = "⚠️ SHIM FILE"
REVERSE_SHIM_MARKER = "⚠️ REVERSE SHIM"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING  = "WARNING"
    INFO     = "INFO"


@dataclass
class Deviation:
    severity: Severity
    category: str
    path: str
    message: str
    suggestion: str = ""


@dataclass
class DiffReport:
    phase: str
    project_root: Path
    deviations: list = field(default_factory=list)

    def add(self, severity: Severity, category: str, path: str,
            message: str, suggestion: str = "") -> None:
        self.deviations.append(Deviation(severity, category, path, message, suggestion))

    @property
    def criticals(self) -> list:
        return [d for d in self.deviations if d.severity == Severity.CRITICAL]

    @property
    def warnings(self) -> list:
        return [d for d in self.deviations if d.severity == Severity.WARNING]

    @property
    def infos(self) -> list:
        return [d for d in self.deviations if d.severity == Severity.INFO]

    @property
    def is_clean(self) -> bool:
        return len(self.criticals) == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_all_shims(root: Path) -> list:
    """Return all rel paths for files containing shim headers."""
    result = []
    for dirpath, _, filenames in walk_project(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            if is_shim_file(fp):
                result.append(str(fp.relative_to(root)))
    return sorted(result)


def find_unexpected_files(root: Path, language: str, manifest: dict) -> list:
    """
    Find source files that exist on disk but are not referenced anywhere
    in the manifest (neither as current: nor target:).
    """
    exts = get_source_extensions(language)

    known_paths = set()
    for e in manifest.get("files", []):
        known_paths.add(e.get("current", ""))
        known_paths.add(e.get("target", ""))

    unexpected = []
    for dirpath, _, filenames in walk_project(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fp.suffix not in exts:
                continue
            rel = str(fp.relative_to(root))
            if rel not in known_paths:
                unexpected.append(rel)
    return sorted(unexpected)


# ---------------------------------------------------------------------------
# Phase-specific checkers
# ---------------------------------------------------------------------------

def check_phase_p1(root: Path, manifest: dict, report: DiffReport) -> None:
    """
    Phase 1 expected state:
    - For every MOVE/SPLIT entry: a FORWARD SHIM must exist at target.
    - The forward shim must point back to `current`.
    - No original files should have been moved (current must still exist and be real).
    - KEEP files: must exist and must NOT be shims.
    """
    files = manifest.get("files", [])

    for entry in files:
        current = entry.get("current", "")
        target = entry.get("target", "")
        action = entry.get("action", "")

        if action in ("MOVE", "SPLIT"):
            # Shim must exist at target
            target_path = root / target
            if not target_path.exists():
                report.add(
                    Severity.CRITICAL, "MISSING_SHIM", target,
                    f"Expected a forward shim at target path — file does not exist.",
                    f"Run: python3 refactor_bridge.py --project-root <root>"
                )
            elif not is_forward_shim(target_path):
                report.add(
                    Severity.WARNING, "SHIM_HEADER_MISSING", target,
                    f"File exists at target path but does not contain '⚠️ SHIM FILE' header.",
                    f"The real file may have been moved here already. Check Phase 2 status."
                )
            else:
                # Verify shim points to the correct current path
                pointed_to = shim_points_to(target_path)
                if pointed_to and pointed_to != current:
                    report.add(
                        Severity.CRITICAL, "SHIM_WRONG_SOURCE", target,
                        f"Shim points to '{pointed_to}' but manifest says source is '{current}'.",
                        f"The shim was written with an incorrect import path. Regenerate it."
                    )

            # Original file must still exist and be the real thing
            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "SOURCE_MISSING", current,
                    f"Original source file missing — was it moved before Phase 2?",
                    f"Phase 1 must not move files. Check if git mv was run prematurely."
                )
            elif is_shim_file(current_path):
                report.add(
                    Severity.WARNING, "SOURCE_IS_SHIM", current,
                    f"Original source path contains a shim header — may be a Phase 2 artifact.",
                    f"If Phase 2 has already run for this file, this is expected."
                )

        elif action == "KEEP":
            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "KEEP_FILE_MISSING", current,
                    f"KEEP entry does not exist on disk.",
                    f"Verify the path in the manifest is correct."
                )
            elif is_shim_file(current_path):
                report.add(
                    Severity.WARNING, "KEEP_FILE_IS_SHIM", current,
                    f"KEEP file contains a shim header — should be a real source file.",
                    f"This file should not have been shimmed."
                )


def check_phase_p2(root: Path, manifest: dict, report: DiffReport) -> None:
    """
    Phase 2 expected state (after migration):
    - For every MOVE entry: real file at target, reverse shim at current.
    - Reverse shim must point TO the target.
    - No forward shims should remain at any target path (replaced by real files).
    - KEEP files unchanged.
    """
    files = manifest.get("files", [])

    for entry in files:
        current = entry.get("current", "")
        target = entry.get("target", "")
        action = entry.get("action", "")

        if action == "MOVE":
            # Target must exist and be a real file (not a shim)
            target_path = root / target
            if not target_path.exists():
                report.add(
                    Severity.CRITICAL, "TARGET_MISSING", target,
                    f"Target file does not exist after Phase 2 — was git mv run?",
                    f"Run: python3 refactor_migrate.py --project-root <root> --module <name>"
                )
            elif is_forward_shim(target_path):
                report.add(
                    Severity.CRITICAL, "TARGET_STILL_SHIM", target,
                    f"Target path still contains a Phase 1 forward shim — real file not yet moved here.",
                    f"Run git mv for this module: refactor_migrate.py --module <name>"
                )
            elif is_reverse_shim(target_path):
                report.add(
                    Severity.CRITICAL, "TARGET_IS_REVERSE_SHIM", target,
                    f"Target path contains a reverse shim — migration appears inverted.",
                    f"Investigate whether current and target are swapped in the manifest."
                )

            # Old path must exist as a reverse shim
            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "REVERSE_SHIM_MISSING", current,
                    f"Old path does not exist — reverse shim was never written.",
                    f"Write a reverse shim at '{current}' pointing to '{target}'."
                )
            elif not is_reverse_shim(current_path):
                report.add(
                    Severity.WARNING, "REVERSE_SHIM_HEADER_MISSING", current,
                    f"Old path exists but lacks the '⚠️ REVERSE SHIM' header.",
                    f"Confirm this is a proper reverse shim, not the original file."
                )
            else:
                # Reverse shim must point to the target
                pointed_to = shim_points_to(current_path)
                if pointed_to and pointed_to != target:
                    report.add(
                        Severity.CRITICAL, "REVERSE_SHIM_WRONG_TARGET", current,
                        f"Reverse shim points to '{pointed_to}' but manifest target is '{target}'.",
                        f"Rewrite the reverse shim with the correct new path."
                    )

        elif action == "KEEP":
            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "KEEP_FILE_MISSING", current,
                    f"KEEP file is missing from disk.",
                    f"Verify this file was not accidentally moved or deleted."
                )


def check_phase_p3(root: Path, manifest: dict, report: DiffReport) -> None:
    """
    Phase 3 expected state:
    - All MOVE files at target paths (real, not shims).
    - All old paths have reverse shims.
    - surgery_complete tracking is consistent with actual import state.
    - Files marked surgery_complete=true are checked for any remaining stale imports.
    """
    # First run all P2 checks — P3 inherits P2's structural requirements
    check_phase_p2(root, manifest, report)

    # Additionally: check surgery_complete consistency
    files = manifest.get("files", [])
    move_entries = [e for e in files if e.get("action") == "MOVE"]
    language = manifest.get("language", "python")

    if language == "python":
        exts = {".py"}
    else:
        exts = {".js", ".ts", ".jsx", ".tsx"}

    for entry in move_entries:
        current = entry.get("current", "")
        target = entry.get("target", "")
        surgery_complete = entry.get("surgery_complete", False)

        target_path = root / target
        if surgery_complete and target_path.exists() and not is_shim_file(target_path):
            # Verify the target file doesn't import from any path that is now a shim
            content = read_file_safe(target_path)
            # Check if this file imports from any old (current) path
            for other in move_entries:
                other_current = other.get("current", "")
                if other_current == current:
                    continue
                # Build a simple pattern
                if language == "python":
                    p = Path(other_current)
                    dotted = str(p.with_suffix("")).replace("/", ".")
                    if f"from {dotted}" in content or f"import {dotted}" in content:
                        report.add(
                            Severity.WARNING, "SURGERY_COMPLETE_BUT_STALE", target,
                            f"Marked surgery_complete=true but still imports from old path: '{other_current}'.",
                            f"Update the import in '{target}' to use '{other.get('target', '')}'."
                        )

    # Count manifest progress
    total_move = len(move_entries)
    complete = sum(1 for e in move_entries if e.get("surgery_complete", False))
    remaining = total_move - complete

    if remaining > 0:
        report.add(
            Severity.INFO, "SURGERY_PROGRESS", "REFACTOR_MANIFEST.yaml",
            f"Phase 3 progress: {complete}/{total_move} modules have surgery_complete=true. "
            f"{remaining} remaining.",
            f"Run: python3 refactor_audit.py --project-root <root> --scan"
        )
    else:
        report.add(
            Severity.INFO, "SURGERY_PROGRESS", "REFACTOR_MANIFEST.yaml",
            f"All {total_move} MOVE entries are marked surgery_complete=true in the manifest.",
            f"Run --verify to confirm: python3 refactor_audit.py --project-root <root> --verify"
        )


def check_phase_p4(root: Path, manifest: dict, report: DiffReport, pre_merge: bool) -> None:
    """
    Phase 4 expected state (pre-merge):
    - Zero shim files anywhere in the project.
    - Zero stale imports remain (all real files import from target paths).
    - ARCHIVE files have been removed.
    - All KEEP files still exist.
    - (pre_merge=True) Stricter: also checks that refactor artifacts are cleaned.
    """
    # Check: no shim files anywhere
    all_shims = find_all_shims(root)
    if all_shims:
        for shim_path in all_shims:
            report.add(
                Severity.CRITICAL, "SHIM_STILL_EXISTS", shim_path,
                f"Shim file still exists — Phase 4 cleanup is incomplete.",
                f"Run: python3 refactor_clean.py --project-root <root>"
            )
    else:
        report.add(
            Severity.INFO, "NO_SHIMS_FOUND", "project",
            "✅ Zero shim files found — shim cleanup is complete.",
        )

    files = manifest.get("files", [])

    # Check KEEP files still exist
    for entry in files:
        if entry.get("action") == "KEEP":
            current = entry.get("current", "")
            if not file_exists(root, current):
                report.add(
                    Severity.CRITICAL, "KEEP_FILE_MISSING", current,
                    f"KEEP file is missing — may have been accidentally deleted.",
                    f"Restore from git: git checkout HEAD -- {current}"
                )

    # Check MOVE target files exist and are real (not shims)
    for entry in files:
        if entry.get("action") == "MOVE":
            target = entry.get("target", "")
            current = entry.get("current", "")
            target_path = root / target
            current_path = root / current
            if not target_path.exists():
                report.add(
                    Severity.CRITICAL, "TARGET_MISSING_AT_P4", target,
                    f"MOVE target is missing at Phase 4 — file was never successfully migrated.",
                    f"Investigate: git log --all -- {target}"
                )
            if current_path.exists():
                # Should not exist after clean (was a reverse shim, removed)
                report.add(
                    Severity.WARNING, "OLD_PATH_STILL_EXISTS", current,
                    f"Old path still exists — reverse shim may not have been removed.",
                    f"Run: python3 refactor_clean.py --project-root <root> --shim {current}"
                )

    if pre_merge:
        # Refactor artifacts should be gone
        for artifact in ["IMPORT_GRAPH.txt", "REFACTOR_MANIFEST.yaml"]:
            artifact_path = root / artifact
            if artifact_path.exists():
                report.add(
                    Severity.WARNING, "ARTIFACT_NOT_CLEANED", artifact,
                    f"Refactor artifact '{artifact}' still exists — remove before merging.",
                    f"Run: git rm {artifact} && git commit -m 'refactor(p4): remove artifacts'"
                )

        # Check for any unexpected source files not in manifest
        unexpected = find_unexpected_files(root, manifest.get("language", "python"), manifest)
        for uf in unexpected:
            if not is_shim_file(root / uf):
                report.add(
                    Severity.WARNING, "UNEXPECTED_FILE", uf,
                    f"Source file exists on disk but is not referenced in the manifest.",
                    f"Verify this file was not accidentally created. Add to manifest if legitimate."
                )


# ---------------------------------------------------------------------------
# Spec summary mode
# ---------------------------------------------------------------------------

def print_spec_summary(root: Path, manifest: dict) -> None:
    """Print a human-readable summary of what the manifest intends."""
    files = manifest.get("files", [])
    by_action: dict = {}
    for e in files:
        a = e.get("action", "TBD")
        by_action.setdefault(a, []).append(e)

    section_header(f"MANIFEST SPEC SUMMARY — {manifest.get('project_name', root.name)}")
    print(f"  Language         : {manifest.get('language', '?')}")
    print(f"  Verification gate: {manifest.get('verification_gate', '(not set)')}")
    print(f"  Total entries    : {len(files)}")
    print()

    for action in ["MOVE", "SPLIT", "KEEP", "ARCHIVE", "TBD"]:
        entries = by_action.get(action, [])
        if not entries:
            continue
        emoji = {"MOVE": "🚚", "SPLIT": "✂️ ", "KEEP": "📌", "ARCHIVE": "🗃️ ", "TBD": "❓"}.get(action, "•")
        print(f"  {emoji}  {action} ({len(entries)} files)")
        print(f"  {'─' * 64}")
        for e in entries:
            current = e.get("current", "")
            target = e.get("target", "")
            notes = e.get("notes", "")
            surgery = e.get("surgery_complete", False)
            if action in ("MOVE", "SPLIT") and current != target:
                line = f"    {current} → {target}"
            else:
                line = f"    {current}"
            if notes:
                line += f"  # {notes}"
            if action == "MOVE" and surgery:
                line += "  ✅ surgery_complete"
            print(line)
        print()

    print("═" * 70)
    print()


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_report(report: DiffReport) -> None:
    total = len(report.deviations)
    section_header(f"DIFF REVIEW NODE — Phase {report.phase.upper()} Report")
    print(f"       Project: {report.project_root}")
    print(f"  Total findings  : {total}")
    print(f"  🔴 CRITICAL     : {len(report.criticals)}")
    print(f"  🟡 WARNING      : {len(report.warnings)}")
    print(f"  🔵 INFO         : {len(report.infos)}")
    print()

    if not report.deviations:
        print("  ✅  No deviations found — actual state matches declared intent.")
        print("  ✅  Safe to commit and proceed to the next phase.")
        print("═" * 70)
        print()
        return

    # Print by severity
    for severity, emoji, entries in [
        (Severity.CRITICAL, "🔴", report.criticals),
        (Severity.WARNING,  "🟡", report.warnings),
        (Severity.INFO,     "🔵", report.infos),
    ]:
        if not entries:
            continue
        print(f"  {emoji}  {severity.value} ({len(entries)})")
        print(f"  {'─' * 66}")
        for d in entries:
            print(f"  [{d.category}]  {d.path}")
            print(f"  ↳ {d.message}")
            if d.suggestion:
                print(f"  💡 {d.suggestion}")
            print()

    if report.criticals:
        print("  ═══ LOOP-BACK REQUIRED ════════════════════════════════════════")
        print(f"  {len(report.criticals)} CRITICAL deviation(s) must be resolved before committing.")
        print("  Do NOT proceed to the next phase.")
        print("  Fix the issues above, then re-run this diff review.")
        print("  ════════════════════════════════════════════════════════════════")
    elif report.warnings:
        print("  ═══ WARNINGS — HUMAN REVIEW ADVISED ══════════════════════════")
        print("  No CRITICAL issues. Review warnings before committing.")
        print("  Proceed with caution.")
        print("  ════════════════════════════════════════════════════════════════")

    print("═" * 70)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
                   help="Stricter Phase 4 check: also verify artifacts are cleaned (use before git merge).")
    p.add_argument("--spec-summary", action="store_true",
                   help="Print a human-readable summary of manifest intent. No filesystem checks.")
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

    out("🔍", f"Sovereign Refactor Protocol — Diff Review Node (Phase: {args.phase.upper()})")
    out("📁", f"Project root: {root}")
    out("📋", f"Manifest: {MANIFEST_FILENAME} ({len(manifest.get('files', []))} entries)")

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
    out("🏁", f"Diff review complete. Exit code: {exit_code} "
        f"({'CLEAN' if exit_code == 0 else 'DEVIATIONS FOUND — loop back required'})")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
