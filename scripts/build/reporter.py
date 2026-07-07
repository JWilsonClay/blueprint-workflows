"""
reporter.py — Build Evidence report rendering (human + JSON)
"""

import json


class BuildEvidenceReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  BUILD EVIDENCE ENGINE")

        phase_status = report.get("phase_status")
        if phase_status is None:
            print("  Phase Map: SKIPPED (no tasks.md found)")
        elif not phase_status["found"]:
            print("  Phase Map: tasks.md NOT FOUND")
        else:
            print(f"  Phase Map ({len(phase_status['phases'])} phases):")
            for p in phase_status["phases"]:
                cb = p["checkboxes"]
                print(f"    [{p['status']:>12}] {p['title']} "
                      f"(done={cb['done']} open={cb['open']} in_progress={cb['in_progress']}) "
                      f"receipt={p['receipt_status']}")

        completeness = report.get("completeness")
        if completeness is None:
            print("  Completeness Scan: SKIPPED (no --phase-files given)")
        elif not completeness:
            print("  Completeness Scan: 0 markers found")
        else:
            print(f"  Completeness Scan: {len(completeness)} marker(s) found")
            for m in completeness:
                print(f"    {m['file']}:{m['line']} [{m['marker']}] {m['snippet']}")

        scope = report.get("scope_diff")
        if scope is None:
            print("  Scope Diff: SKIPPED (no --declared-scope given)")
        elif not scope["git_available"]:
            print("  Scope Diff: UNAVAILABLE (git status failed or not a repo) — not scope-compliant, unverifiable")
        else:
            print(f"  Scope Diff: {len(scope['touched_not_declared'])} touched-not-declared, "
                  f"{len(scope['declared_not_touched'])} declared-not-touched")
            for f in scope["touched_not_declared"]:
                print(f"    OUT-OF-SCOPE TOUCH: {f}")

        print("  ADVISORY: this engine reports facts only — match presence, set differences, "
              "receipt status. Whether a match is justified, a scope deviation warranted, or a "
              "phase genuinely complete remains the agent's judgment call, never this engine's.")
        print("=" * 60)
