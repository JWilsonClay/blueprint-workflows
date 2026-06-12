"""
reporter.py — Registry report rendering (human + JSON)
"""

import json


class RegistryReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return
        agg = report["aggregate"]
        print("=" * 60)
        print("  SUITE LEARNING REGISTRY")
        print(f"  Workspace:   {report['workspace']}")
        print(f"  Registry:    {report['registry_path']}")
        print(f"  Total events: {agg['total_events']}   (new this run: {report['new_events']})")
        print(f"  Unreviewed since {report['watermark'] or '(never)'}: "
              f"{report['unreviewed']}   threshold: {report['threshold']}")
        print(f"  VERDICT:     {report['verdict']}")
        print("=" * 60)
        if agg["by_pattern"]:
            print("  By failure pattern:")
            for k, v in agg["by_pattern"].items():
                print(f"    {v:>3}  {k}")
        if report["verdict"] == "REVIEW":
            print("  → REVIEW: ingest the registry aggregate and judge whether a real")
            print("    recurring pattern warrants a /helpdesk-tickets entry.")
        print(f"  (advisory) {report['summary']['advisory']}")
        print("=" * 60)
