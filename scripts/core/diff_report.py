"""
diff_report.py — Display and formatting for the Diff Review Node
================================================================
Extracted from refactor_diff.py during SoC decomposition.
"""

from pathlib import Path

from core.console import section_header
from core.diff_models import Severity, DiffReport


def print_spec_summary(root: Path, manifest: dict) -> None:
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
        emoji = {"MOVE": ">>", "SPLIT": "//", "KEEP": "==", "ARCHIVE": "[]", "TBD": "??"}.get(action, " *")
        print(f"  {emoji}  {action} ({len(entries)} files)")
        print(f"  {'─' * 64}")
        for e in entries:
            current = e.get("current", "")
            target = e.get("target", "")
            notes = e.get("notes", "")
            surgery = e.get("surgery_complete", False)
            if action in ("MOVE", "SPLIT") and current != target:
                line = f"    {current} -> {target}"
            else:
                line = f"    {current}"
            if notes:
                line += f"  # {notes}"
            if action == "MOVE" and surgery:
                line += "  [surgery_complete]"
            print(line)
        print()

    print("=" * 70)
    print()


def print_report(report: DiffReport) -> None:
    total = len(report.deviations)
    section_header(f"DIFF REVIEW NODE — Phase {report.phase.upper()} Report")
    print(f"       Project: {report.project_root}")
    print(f"  Total findings  : {total}")
    print(f"  CRITICAL        : {len(report.criticals)}")
    print(f"  WARNING         : {len(report.warnings)}")
    print(f"  INFO            : {len(report.infos)}")
    print()

    if not report.deviations:
        print("  No deviations found — actual state matches declared intent.")
        print("  Safe to commit and proceed to the next phase.")
        print("=" * 70)
        print()
        return

    for severity, label, entries in [
        (Severity.CRITICAL, "CRITICAL", report.criticals),
        (Severity.WARNING,  "WARNING",  report.warnings),
        (Severity.INFO,     "INFO",     report.infos),
    ]:
        if not entries:
            continue
        print(f"  {label} ({len(entries)})")
        print(f"  {'─' * 66}")
        for d in entries:
            print(f"  [{d.category}]  {d.path}")
            print(f"  -> {d.message}")
            if d.suggestion:
                print(f"  Suggestion: {d.suggestion}")
            print()

    if report.criticals:
        print("  === LOOP-BACK REQUIRED ===")
        print(f"  {len(report.criticals)} CRITICAL deviation(s) must be resolved before committing.")
        print("  Do NOT proceed to the next phase.")
        print("  Fix the issues above, then re-run this diff review.")
        print("  ===")
    elif report.warnings:
        print("  === WARNINGS — HUMAN REVIEW ADVISED ===")
        print("  No CRITICAL issues. Review warnings before committing.")
        print("  Proceed with caution.")
        print("  ===")

    print("=" * 70)
    print()
