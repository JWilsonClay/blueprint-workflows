"""
reporter.py — Plan Populator Reporter
========================================
Renders the PlanPopulator report as either structured JSON (for /sentinel to
consume) or a compact human-readable summary (for direct CLI use). Mirrors
the focus/doorway reporter contract: --output-json wins, --quiet suppresses
human output.
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
