"""
reporter.py — Receipt coverage report rendering (human + JSON)
"""

import json


class CoverageReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return
        print("=" * 60)
        print("  RECEIPT COVERAGE ENGINE")
        if not report["tasks_md_found"]:
            print("  tasks.md: NOT FOUND — " + report.get("note", ""))
        else:
            present = report["receipt_files_present"]
            print(f"  Receipt files present: build={present['build']} "
                  f"validation={present['validation']} harden={present['harden']} "
                  f"docs={present['docs']} design={present['design']} triage={present['triage']}")
            for p in report["phases"]:
                print(f"  [{p['checkbox_status']:>16}] {p['title']}: "
                      f"built={p['built']} validated={p['validated']} hardened={p['hardened']} "
                      f"designed={p['designed']} triaged={p['triaged']}")
            gp = report["gap_percent"]
            print(f"  Gap: {gp}%  ({report['covered_dimensions']}/{report['checkable_dimensions']} "
                  f"checkable dimensions covered)" if gp is not None
                  else "  Gap: N/A (no completed phases with checkable dimensions)")
            doc = report["documented_dimension"]
            print(f"  Documented (existence-only): {doc['entries_present']} "
                  f"({doc['entry_count']} entries)")
        qp = report["quality_process"]
        print(f"  Quality-Process: {qp['verdict_hint'] if qp['available'] else 'UNAVAILABLE'}")
        print("=" * 60)
