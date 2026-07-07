"""
reporter.py — Session Close Evidence report rendering (human + JSON)
"""

import json


class SecretaryEvidenceReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        print("=" * 60)
        print("  SESSION CLOSE EVIDENCE ENGINE")

        freshness = report.get("freshness")
        if freshness is None:
            print("  Artifact Freshness: SKIPPED (no --check-paths given)")
        else:
            print("  Artifact Freshness:")
            for f in freshness:
                if not f["exists"]:
                    print(f"    MISSING: {f['path']}")
                else:
                    flag = "TOUCHED" if f["touched_since"] else "STALE"
                    print(f"    [{flag:>7}] {f['path']} (mtime={f['mtime_iso']})")

        retro = report.get("retrospective_freshness")
        if retro is None:
            print("  Retrospective Freshness: SKIPPED")
        else:
            status = "MATCHES TODAY" if retro["matches_today"] else "DOES NOT MATCH TODAY"
            print(f"  Retrospective Freshness: latest={retro['latest_entry_date']} "
                  f"today={retro['today']} — {status}")

        lag = report.get("retrospective_lag")
        if lag is None:
            print("  Retrospective Lag: SKIPPED")
        else:
            verdict = "GAP DETECTED" if lag["gap_detected"] else "NO GAP"
            print(f"  Retrospective Lag: narrative={lag['narrative_latest_date']} "
                  f"process_learnings={lag['process_learnings_latest_date']} — {verdict} "
                  f"({lag['reason']})")

        receipts = report.get("receipt_family")
        if receipts is None:
            print("  Receipt Family: SKIPPED")
        else:
            for r in receipts:
                status = "present" if r["present"] else "absent"
                print(f"    {r['filename']}: {status}")

        print("  ADVISORY: this engine reports facts only — mtime, date comparisons, file "
              "presence. Whether the SESSION MANIFEST is honest, an anomaly's rationale is "
              "sound, or the retrospective's content is insightful remains the agent's "
              "judgment call, never this engine's.")
        print("=" * 60)
