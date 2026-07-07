"""
reporter.py — Structural Assessment report rendering (human + JSON)
"""

import json


class HardenWorkflowReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  HARDEN-WORKFLOW STRUCTURAL ASSESSMENT ENGINE")

        facts = report.get("facts")
        if facts is None:
            print("  Structural Facts: SKIPPED (file not found/unreadable)")
        else:
            print("  Structural Facts:")
            for key, value in facts.items():
                print(f"    {key}: {value}")

        grade = report.get("grade_hint")
        if grade is not None:
            print(f"  Grade Hint: {grade['grade_hint']} "
                  f"(missing: {grade['missing_criteria'] or 'none'})")
            if grade["structured_output_unknown"]:
                print("    NOTE: structured_output presence is UNKNOWN — verify manually.")

        degradation = report.get("degradation")
        if degradation is not None:
            status = "DEGRADED" if degradation["degraded"] else "CURRENT"
            print(f"  Degradation Check: certified={degradation['certified_version']} "
                  f"current={degradation['current_version']} — {status}")

        triage_gap = report.get("triage_gap")
        if triage_gap is not None:
            status = "REPRESENTED" if triage_gap["represented"] else "GAP — NOT in Trigger Matrix"
            print(f"  /triage Compatibility: {status}")

        print("  ADVISORY: this engine reports structural presence/absence and version facts "
              "only — grade_hint is one-directional and advisory, never a certified grade. "
              "Content-quality judgment (rule completeness, decision-branch coverage) stays "
              "entirely with the agent.")
        print("=" * 60)
