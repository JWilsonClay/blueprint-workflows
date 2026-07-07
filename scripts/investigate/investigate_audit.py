#!/usr/bin/env python3
"""
investigate_audit.py — Citation & Search Log Fidelity Engine CLI
====================================================================
The read-only mechanical layer behind /investigate's Phase 3 citation
checks and Phase 1c search-log verification. Schema-agnostic — operates on
the Investigation Report's own text plus the real filesystem, never the
target codebase's unknown internal schema. See
scripts/investigate/__init__.py for the full contract.

Usage:
    python investigate_audit.py [options]

Optional:
    --report-file PATH     Path to the Investigation Report's text.
    --report-text TEXT     Inline report text, alternative to --report-file.
    --output-json          Emit JSON to stdout.
    --quiet                Suppress human-readable output.

Origin: implementation-plan.md Phase 5.4 (Sovereign Scaling Cluster),
docs/compression-staging/investigate-honest-design.md Section 4.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from investigate.citation_fidelity import extract_citations, verify_citation
from investigate.reporter import InvestigateFidelityReporter
from investigate.search_log_verifier import extract_search_log_entries, verify_search_entry


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="investigate_audit.py",
        description="Citation & Search Log Fidelity Engine — verifies /investigate's own "
                    "reporting conventions resolve to real evidence. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--report-file", type=str, default=None,
                   help="Path to the Investigation Report's text.")
    p.add_argument("--report-text", type=str, default=None,
                   help="Inline report text, alternative to --report-file.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    report_text = None
    if args.report_text is not None:
        report_text = args.report_text
    elif args.report_file is not None:
        report_text = Path(args.report_file).read_text(encoding="utf-8")

    citations = None
    search_log = None
    if report_text is not None:
        citations = [verify_citation(c).as_dict() for c in extract_citations(report_text)]
        search_log = [verify_search_entry(e).as_dict() for e in extract_search_log_entries(report_text)]

    report = {"citations": citations, "search_log": search_log}
    InvestigateFidelityReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
