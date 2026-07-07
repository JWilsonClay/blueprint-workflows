"""
reporter.py — Anchor Verification report rendering (human + JSON)
"""

import json


class AnchorVerifyReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  CONTINUOUS-VERIFY ANCHOR ENGINE")

        files = report.get("file_anchors")
        if files is not None:
            print("  File Anchors:")
            for f in files:
                print(f"    [{f['status']:>8}] {f['query']} — {f['locations']}")

        symbols = report.get("symbol_anchors")
        if symbols is not None:
            print("  Symbol Anchors:")
            for s in symbols:
                flag = " *** MOCK TRAP CANDIDATE ***" if s["mock_trap_candidate"] else ""
                print(f"    [{s['status']:>16}] {s['query']} "
                      f"(prod={s['production_matches']} test={s['test_matches']}){flag}")

        print("  ADVISORY: this engine reports anchor existence and production-vs-test-only "
              "location facts only. It never judges whether the code at an anchor actually "
              "implements a plan criterion correctly. mock_trap_candidate is one-directional "
              "and advisory — a symbol found only in test code MAY still be correct if the "
              "criterion is genuinely about test coverage; investigate, don't auto-fail.")
        print("=" * 60)
