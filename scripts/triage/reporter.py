"""
reporter.py — Trigger Matrix Completeness report rendering (human + JSON)
"""

import json


class TriageEvidenceReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  TRIAGE EVIDENCE ENGINE")

        completeness = report.get("completeness")
        if completeness is None:
            print("  Matrix Completeness: SKIPPED (no --report-file/--report-text given)")
        elif not completeness["matrix_workflows"]:
            print("  Matrix Completeness: Trigger Matrix section not found or empty")
        else:
            total = len(completeness["matrix_workflows"])
            missing = completeness["missing_from_report"]
            print(f"  Matrix Completeness: {total - len(missing)}/{total} workflows present in report")
            for name in missing:
                print(f"    MISSING FROM REPORT: {name}")

        phase_status = report.get("phase_status")
        if phase_status is None:
            print("  Phase/Task State: SKIPPED (no tasks.md found)")
        elif not phase_status["found"]:
            print("  Phase/Task State: tasks.md NOT FOUND")
        else:
            for p in phase_status["phases"]:
                cb = p["checkboxes"]
                print(f"    [{p['status']:>12}] {p['title']} "
                      f"(done={cb['done']} open={cb['open']} in_progress={cb['in_progress']})")

        coverage = report.get("receipt_coverage")
        if coverage is None:
            print("  Receipt Coverage: SKIPPED")
        elif not coverage.get("tasks_md_found", True):
            print("  Receipt Coverage: tasks.md NOT FOUND — " + coverage.get("note", ""))
        else:
            present = coverage["receipt_files_present"]
            print(f"  Receipt Coverage: build={present['build']} validation={present['validation']} "
                  f"harden={present['harden']} docs={present['docs']} design={present['design']} "
                  f"triage={present['triage']}")

        print("  ADVISORY: this engine reports facts only — workflow-name presence in report text, "
              "checkbox tallies, receipt-file presence. It never judges whether a workflow's "
              "triggers were genuinely evaluated with rigor, nor which priority a finding deserves.")
        print("=" * 60)
