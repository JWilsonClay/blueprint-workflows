"""
reporter.py — Harden Evidence Reporter
========================================
Renders the HardenAuditor report as JSON (for /harden to consume) or a compact
human-readable summary. Mirrors the doorway/focus/quality reporter contract:
--output-json wins, --quiet suppresses human output.
"""

import json


class HardenReporter:
    """Renders a harden-audit report dict to stdout."""

    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        summary = report.get("summary", {})
        print(f"\n=== {report.get('workspace', 'workspace')} — Hardening Evidence ===")
        print(f"  NOTE: {summary.get('advisory', '')}")

        totals = summary.get("severity_totals", {})
        print(
            f"\nScanned: {summary.get('files_scanned', 0)} scripts | "
            f"{summary.get('files_with_findings', 0)} with findings | "
            f"{summary.get('total_findings', 0)} findings "
            f"(CRIT {totals.get('CRITICAL', 0)} / HIGH {totals.get('HIGH', 0)} / "
            f"MED {totals.get('MEDIUM', 0)} / LOW {totals.get('LOW', 0)})"
        )
        print(f"Workspace lowest grade ceiling: {summary.get('lowest_ceiling', '?')}")

        for f in report.get("files", []):
            if not f.get("findings") and f.get("grade_ceiling") == "Diamond":
                continue  # nothing to show for a clean file
            print(f"\n  {f['path']}  [{f.get('threat_context', '?')}]  "
                  f"ceiling: {f.get('grade_ceiling', '?')}")
            print(f"    {f.get('ceiling_basis', '')}")
            for fd in f.get("findings", [])[:12]:
                tag = "advisory" if fd.get("advisory") else (
                    "confirm" if fd.get("requires_confirmation") else "firm")
                print(f"    - L{fd['line']} [{fd['severity']}/{tag}] "
                      f"{fd['cwe']} {fd['signature']}: {fd['excerpt']}")

        print(f"\nVerdict hint: {summary.get('verdict_hint', '?')} "
              f"(advisory — deterministic findings + grade ceiling only)")
