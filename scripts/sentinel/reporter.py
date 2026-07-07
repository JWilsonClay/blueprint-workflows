"""
reporter.py — Recommender/Routing-Table Parity report rendering (human + JSON)
"""

import json


class SentinelParityReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  SENTINEL RECOMMENDER/ROUTING-TABLE PARITY ENGINE")

        parity = report.get("parity")
        if parity is None:
            print("  Parity Check: SKIPPED (missing input file)")
        else:
            print(f"  Recommender emits {len(parity['recommender_ids'])} recommendation(s), "
                  f"table documents {len(parity['table_ids'])} row(s)")
            if parity["missing_from_table"]:
                print(f"  MISSING FROM TABLE: {parity['missing_from_table']}")
            if parity["undercounted_ids"]:
                print(f"  UNDERCOUNTED (engine emits more blocks than table has rows): "
                      f"{parity['undercounted_ids']}")
            if parity["undocumented_severities"]:
                print(f"  UNDOCUMENTED SEVERITIES: {parity['undocumented_severities']}")
            if not (parity["missing_from_table"] or parity["undercounted_ids"]
                    or parity["undocumented_severities"]):
                print("  PARITY: CLEAN — table matches engine's actual emitted behavior")

        print("  ADVISORY: this engine reports documentation-vs-engine text facts only — it "
              "never judges whether a routing decision itself is correct, only whether the "
              "table's documentation of the engine's existing, already-decided behavior is "
              "complete and current.")
        print("=" * 60)
