"""
reporter.py — Ticket Lifecycle Evidence report rendering (human + JSON)
"""

import json


class HelpdeskTicketsReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  HELPDESK-TICKETS LIFECYCLE ENGINE")

        validation = report.get("validation")
        if validation is not None:
            if validation["issues"]:
                print(f"  Validation: {len(validation['issues'])} issue(s) found")
                for issue in validation["issues"]:
                    print(f"    - {issue}")
            else:
                print("  Validation: CLEAN")

        duplicates = report.get("duplicates")
        if duplicates is not None:
            if duplicates["open_tickets_for_workflow"]:
                print(f"  Duplicate Check: {len(duplicates['open_tickets_for_workflow'])} "
                      f"existing open ticket(s) for '{duplicates['workflow_name']}': "
                      f"{duplicates['open_tickets_for_workflow']}")
            else:
                print(f"  Duplicate Check: no existing open tickets for '{duplicates['workflow_name']}'")

        staleness = report.get("staleness")
        if staleness is not None:
            stale = [s for s in staleness if s["exceeds_threshold"]]
            print(f"  Staleness: {len(stale)}/{len(staleness)} open ticket(s) exceed threshold")
            for s in stale:
                print(f"    {s['filename']}: {s['days_open']} days open")

        print("  ADVISORY: this engine reports schema presence/format, cross-field consistency, "
              "duplicate-filename facts, and days-open arithmetic only. It never judges failure-"
              "class correctness, root-cause narrative quality, urgency correctness, or whether a "
              "Phylogeny Disposition value is the right one — only whether it's present and "
              "consistent with Status.")
        print("=" * 60)
