"""
reporter.py — Quality Audit Reporter
======================================
Renders the QualityAuditor report as JSON (for workflow consumption) or a compact
human-readable summary. Mirrors the doorway/focus reporter contract.
"""

import json


class QualityReporter:
    """Renders a quality-audit report dict to stdout."""

    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        summary = report.get("summary", {})
        print(f"\n=== {report.get('workspace', 'workspace')} — Quality Process Audit ===")
        print(f"  NOTE: {summary.get('advisory', '')}")

        led = report.get("ledger", {})
        if led.get("log_found"):
            print(
                f"\nLedger: {led['valid_entries']} valid / {len(led['malformed_lines'])} malformed | "
                f"{led['unreviewed_entries']} unreviewed (last reviewed: {led['last_reviewed']}) "
                f"→ audit_trigger={led['audit_trigger']}"
            )
            for ml in led["malformed_lines"][:5]:
                print(f"    [malformed L{ml['line_no']}] {ml['reason']}")
        else:
            print(f"\nLedger: no witness log at {led.get('log_path')}")

        scan = report.get("scan")
        if scan:
            print(f"\nScan: {scan['target_file']}")
            print(f"  Chain tag: {scan['chain_tag']['status']} ({scan['chain_tag']['count']} found)")
            if scan["smells"]["smell_total"]:
                print(f"  Mechanical smells ({scan['smells']['smell_total']}):")
                for s in scan["smells"]["smells"]:
                    print(f"    - {s['pattern']} ×{s['count']}")
            else:
                print("  Mechanical smells: none detected (NOT a quality verdict)")

        print(f"\nVerdict hint: {summary.get('verdict_hint', '?')} (advisory — process/smells only)")
