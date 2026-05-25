"""
report.py — Report formatting for the Sovereign Suite Linter
=============================================================
Extracted from lint_workflows.py during SoC decomposition.
"""

from suite.models import LintReport


def print_report(report):
    print()
    print("=" * 70)
    print(f"  SOVEREIGN SUITE LINT REPORT")
    print(f"  Workflows scanned: {report.workflows_scanned}")
    print(f"  Clean:             {report.workflows_clean}")
    print(f"  Findings:          {len(report.findings)}")
    print(f"    CRITICAL: {len(report.criticals)}")
    print(f"    WARNING:  {len(report.warnings)}")
    print(f"    INFO:     {len(report.infos)}")
    print("=" * 70)

    if report.criticals:
        print("\n  CRITICAL:")
        for f in report.criticals:
            print(f)

    if report.warnings:
        print("\n  WARNING:")
        for f in report.warnings:
            print(f)

    if report.infos:
        print("\n  INFO:")
        for f in report.infos:
            print(f)

    print()
    if not report.criticals and not report.warnings:
        print("  VERDICT: CLEAN — no critical or warning findings.")
    elif not report.criticals:
        print("  VERDICT: WARNINGS ONLY — review recommended.")
    else:
        print(f"  VERDICT: {len(report.criticals)} CRITICAL finding(s) require attention.")
    print("=" * 70)
    print()
