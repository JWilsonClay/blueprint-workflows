#!/usr/bin/env python3
"""
redteam_audit.py — Static Evidence Scanner CLI
=================================================
The read-only mechanical layer behind `/redteam`'s Phase 1a (Coverage Gap
Analysis), Phase 1b (Mock Audit enumeration), and Phase 3a (Secret Leakage
Scan). Schema-agnostic — makes no assumption about the audited project's
test framework, log format, or database schema. See
scripts/redteam/__init__.py for the full contract and what is explicitly
NOT covered.

Usage:
    python redteam_audit.py [options]

Optional:
    --scan-paths PATH [...]   Files to scan for mock usage and secret
                              patterns (Phase 1b / 3a). Omit to skip both.
    --coverage-json PATH      Path to a `coverage json`-produced report
                              (Phase 1a). Omit to skip.
    --surface-map-file PATH [...]  Files from Phase 0c's Adversarial
                              Surface Map — get the stricter 100% coverage
                              threshold instead of the default 80%.
    --output-json             Emit JSON to stdout.
    --quiet                   Suppress human-readable output.

Origin: implementation-plan.md Phase 5.1 (Sovereign Scaling Cluster),
docs/compression-staging/redteam-honest-design.md Section 4.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from redteam.coverage_gap import parse_coverage_json
from redteam.mock_scanner import scan_for_mocks
from redteam.reporter import RedteamReporter
from redteam.secret_scanner import scan_for_secrets


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="redteam_audit.py",
        description="Static Evidence Scanner — mock enumeration, secret-pattern scan "
                    "(redacted), and coverage-gap parsing for /redteam. Read-only, "
                    "schema-agnostic.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--scan-paths", nargs="*", default=None,
                   help="Files to scan for mock usage and secret patterns.")
    p.add_argument("--coverage-json", type=str, default=None,
                   help="Path to a `coverage json`-produced report.")
    p.add_argument("--surface-map-file", nargs="*", default=None,
                   help="Files from Phase 0c's Adversarial Surface Map (100%% threshold).")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    mocks = None
    secrets = None
    if args.scan_paths is not None:
        mocks = [m.as_dict() for m in scan_for_mocks(args.scan_paths)]
        secrets = [s.as_dict() for s in scan_for_secrets(args.scan_paths)]

    coverage_gaps = None
    if args.coverage_json is not None:
        coverage_gaps = [
            c.as_dict() for c in parse_coverage_json(
                args.coverage_json, surface_map_files=args.surface_map_file
            )
        ]

    report = {
        "mocks": mocks,
        "secrets": secrets,
        "coverage_gaps": coverage_gaps,
    }
    RedteamReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
