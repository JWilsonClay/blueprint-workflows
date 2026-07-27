"""
reporter.py — Plan package reporters
========================================
Renders this package's reports as either structured JSON (for a consuming
workflow) or a compact human-readable summary (for direct CLI use). Mirrors
the focus/doorway reporter contract: --output-json wins, --quiet suppresses
human output.

  PlanReporter    — Plan & Tasks Format Check (ensure_plan_templates.py)
  LedgerReporter  — Findings Ledger (remediation_ledger.py)
"""

import json


class PlanReporter:
    """Renders a plan-populator report dict to stdout."""

    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        mode = "DRY-RUN" if report.get("dry_run") else "LIVE"
        print(f"\n=== {report.get('workspace', 'workspace')} — Plan & Tasks Format Check ({mode}) ===")
        for action in report.get("actions", []):
            print(f"  {action['file']}: {action['action']} — {action['reason']}")

        summary = report.get("summary", {})
        print(
            f"\nSummary: {summary.get('populated', 0)} populated, "
            f"{summary.get('would_populate', 0)} would-populate, "
            f"{summary.get('skipped', 0)} skipped, "
            f"{summary.get('errors', 0)} errors"
        )


class LedgerReporter:
    """Renders a Findings Ledger report dict to stdout."""

    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print(f"\n=== Findings Ledger — {report.get('audit_name', 'audit')} ===")

        status = report.get("status")
        if status == "unreadable":
            print("  STATUS: UNREADABLE — the audit report could not be read.")
            self._render_errors(report)
            return
        if status == "no_findings_section":
            print("  STATUS: NO FINDINGS SECTION — parse failure, NOT a zero-findings result.")
            self._render_errors(report)
            return

        summary = report.get("summary", {})
        findings = report.get("findings", [])

        if not findings:
            print("  No findings reported (findings section located and genuinely empty).")
        for finding in findings:
            citations = ", ".join(finding.get("citations") or []) or "(no citations)"
            deduction = finding.get("deduction")
            deduction_text = f"-{deduction} pts" if deduction is not None else "-- pts"
            print(f"  {finding['id']} [{deduction_text}] {finding['claim']}")
            print(f"      cites: {citations}")

        print(
            f"\nSummary: {summary.get('critical', 0)} critical, "
            f"{summary.get('medium', 0)} medium, "
            f"{summary.get('total', 0)} total"
            + (
                f" ({summary.get('total_deduction')} pts deducted)"
                if summary.get("total_deduction") is not None else ""
            )
        )
        print(f"ID source: {report.get('id_source', 'none')}")
        self._render_errors(report)

    @staticmethod
    def _render_errors(report: dict) -> None:
        for err in report.get("errors", []):
            print(f"  [!] {err}")
