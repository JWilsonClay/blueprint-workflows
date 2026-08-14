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

        delivery = report.get("delivery_surfaces")
        if delivery is None:
            print("  Delivery Surfaces: SKIPPED (no --delivery-registry given)")
        elif not delivery.get("registry_found"):
            print(f"  Delivery Surfaces: REGISTRY FAILURE — {delivery.get('error')}")
        else:
            print(f"  Delivery Surfaces (canonical: {delivery['canonical_count']} files):")
            for s in delivery["surfaces"]:
                if not s["checked"]:
                    print(f"    [{'SKIP':>6}] {s['name']} ({s['type']}) — {s['note']}")
                    continue
                flag = "OK" if s["ok"] else "FAIL"
                print(f"    [{flag:>6}] {s['name']} ({s['type']}): "
                      f"{s['resolved']}/{s['expected']} resolved")
                for category in ("missing", "dangling", "mismatched"):
                    for f in s[category]:
                        print(f"             {category.upper()}: {f['name']} — {f['detail']}")
                for f in s["orphaned"]:
                    print(f"             orphan (info): {f['name']} — {f['detail']}")
            for r in delivery["state_roots"]:
                mark = r["finding"] or ("present" if r["exists"] else "absent")
                print(f"    state root {r['name']} [{r['data_class']}]: {mark}")

        print("  ADVISORY: this engine reports facts only — mtime, date comparisons, file "
              "presence. Whether the SESSION MANIFEST is honest, an anomaly's rationale is "
              "sound, or the retrospective's content is insightful remains the agent's "
              "judgment call, never this engine's.")
        print("=" * 60)
