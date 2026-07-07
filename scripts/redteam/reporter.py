"""
reporter.py — Static Evidence Scan report rendering (human + JSON)
"""

import json


class RedteamReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  REDTEAM STATIC EVIDENCE SCANNER")

        mocks = report.get("mocks")
        if mocks is None:
            print("  Mock Enumeration: SKIPPED (no --scan-paths given)")
        else:
            print(f"  Mock Enumeration: {len(mocks)} call-site(s) found")
            for m in mocks:
                print(f"    {m['file']}:{m['line']} [{m['construct']}] {m['snippet']}")

        secrets = report.get("secrets")
        if secrets is None:
            print("  Secret Scan: SKIPPED (no --scan-paths given)")
        elif not secrets:
            print("  Secret Scan: 0 hits found")
        else:
            print(f"  Secret Scan: {len(secrets)} hit(s) found (values redacted)")
            for s in secrets:
                print(f"    {s['file']}:{s['line']} [{s['pattern_matched']}] <REDACTED>")

        coverage = report.get("coverage_gaps")
        if coverage is None:
            print("  Coverage Gaps: SKIPPED (no --coverage-json given)")
        else:
            below = [c for c in coverage if c["below_threshold"]]
            print(f"  Coverage Gaps: {len(below)}/{len(coverage)} file(s) below threshold")
            for c in below:
                print(f"    {c['file']}: {c['percent_covered']}% (threshold {c['threshold_applied']}%)")

        print("  ADVISORY: this engine reports facts only — mock call-site locations (never a "
              "tautology verdict), secret-pattern matches (values always redacted, never the "
              "match's actual content), and coverage percentages from an already-produced report. "
              "It never judges mock realism, secret severity, or whether a coverage gap matters.")
        print("=" * 60)
