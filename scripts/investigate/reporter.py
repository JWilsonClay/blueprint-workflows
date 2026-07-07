"""
reporter.py — Citation & Search Log Fidelity report rendering (human + JSON)
"""

import json


class InvestigateFidelityReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  INVESTIGATE CITATION & SEARCH LOG FIDELITY ENGINE")

        citations = report.get("citations")
        if citations is None:
            print("  Citation Fidelity: SKIPPED (no --report-file/--report-text given)")
        else:
            bad = [c for c in citations if c["status"] not in ("VALID", "VALID_NO_LINE_RANGE")]
            print(f"  Citation Fidelity: {len(citations) - len(bad)}/{len(citations)} valid")
            for c in bad:
                print(f"    {c['status']}: {c['citation']['raw']}")

        searches = report.get("search_log")
        if searches is None:
            print("  Search Log Verification: SKIPPED")
        else:
            bad = [s for s in searches if s["status"] != "VERIFIED"]
            print(f"  Search Log Verification: {len(searches) - len(bad)}/{len(searches)} verified")
            for s in bad:
                print(f"    {s['status']}: claimed={s['entry']['claimed_count']} "
                      f"actual={s['actual_count']} — {s['entry']['raw']}")

        print("  ADVISORY: this engine reports citation/search-log fact-checks only — file "
              "existence, line-range validity, match-count accuracy. It never judges whether a "
              "finding's content is correct, whether a search was the right one to run, or "
              "whether cited evidence actually supports the conclusion attached to it.")
        print("=" * 60)
