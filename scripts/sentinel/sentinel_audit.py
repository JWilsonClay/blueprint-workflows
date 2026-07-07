#!/usr/bin/env python3
"""
sentinel_audit.py — Recommender/Routing-Table Parity Engine CLI
===================================================================
The read-only mechanical layer behind /sentinel's Phase 2b Routing Map —
confirms the table's documentation of scripts/doorway/recommender.py's
actual emitted id/workflow/severity triples is complete and current. See
scripts/sentinel/__init__.py for the full contract.

Usage:
    python sentinel_audit.py --recommender-py PATH --sentinel-md PATH [options]

Optional:
    --documented-severities SEV [...]  Severity tiers to treat as documented
                                        (default: HIGH MEDIUM LOW, matching
                                        sentinel.md's own GLOSSARY).
    --output-json                      Emit JSON to stdout.
    --quiet                            Suppress human-readable output.

Origin: implementation-plan.md Phase 5.2 (Sovereign Scaling Cluster),
docs/compression-staging/sentinel-honest-design.md Section 4.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from sentinel.recommender_parity import compute_parity, extract_recommender_triples, extract_routing_table
from sentinel.reporter import SentinelParityReporter

_DEFAULT_DOCUMENTED_SEVERITIES = ["HIGH", "MEDIUM", "LOW"]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="sentinel_audit.py",
        description="Recommender/Routing-Table Parity Engine — confirms sentinel.md's Phase "
                    "2b table matches recommender.py's actual emitted behavior. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--recommender-py", required=True, type=str,
                   help="Path to scripts/doorway/recommender.py.")
    p.add_argument("--sentinel-md", required=True, type=str,
                   help="Path to claude-commands/sentinel.md.")
    p.add_argument("--documented-severities", nargs="*", default=None,
                   help="Severity tiers to treat as documented (default: HIGH MEDIUM LOW).")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    triples = extract_recommender_triples(args.recommender_py)
    table_rows = extract_routing_table(args.sentinel_md)
    documented = set(args.documented_severities or _DEFAULT_DOCUMENTED_SEVERITIES)

    parity = None
    if triples or table_rows:
        parity = compute_parity(triples, table_rows, documented).as_dict()

    report = {"parity": parity}
    SentinelParityReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
