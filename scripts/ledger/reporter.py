"""
reporter.py — Ledger report rendering (human + JSON)
"""

import json


class LedgerReporter:
    def render(self, statuses: list, quiet: bool = False, output_json: bool = False) -> None:
        payload = [s.as_dict() for s in statuses]
        if output_json:
            print(json.dumps(payload, indent=2))
            return
        if quiet:
            return
        print("=" * 60)
        print("  LEDGER GROWTH MONITOR")
        for s in statuses:
            print(f"  [{s.mode.upper()}] {s.name}")
            print(f"    Active file: {s.active_file}")
            print(f"    Entries: {s.entries} (threshold {s.threshold_entries or '-'})"
                  f"   Bytes: {s.bytes} (threshold {s.threshold_bytes or '-'})")
            if s.mode == "shard" and s.rolled_over:
                print(f"    ROLLED OVER — {s.rollover_reason}")
            if s.mode == "warn" and s.warn:
                print("    -> WARN: advisable size crossed. Not a decision — judge whether "
                      "this file now warrants a split/shard, or revisit later.")
        print("=" * 60)
