#!/usr/bin/env python3
"""
anchor_cli.py — Anchor Verification CLI
==========================================
Thin CLI wrapper around scripts/focus/anchor_scanner.py's AnchorScanner,
exposing verify_file()/verify_symbol() directly for caller-supplied queries.
The read-only mechanical layer behind /continuous-verify's Phase 1
(Acceptance Criteria Verification) and Phase 2 (Forward Contract
Verification). See scripts/continuous_verify/__init__.py for the full
contract.

Usage:
    python anchor_cli.py --workspace /abs/path [options]

Optional:
    --file-queries QUERY [...]    File anchors to verify (bare filenames
                                   match by basename anywhere in the tree).
    --symbol-queries QUERY [...]  Symbol anchors to verify (whole-word
                                   search, production vs. test-only split).
    --exclude PATH [...]          Paths to exclude from the substrate index
                                   (e.g. the plan file itself — a plan that
                                   *mentions* a symbol is intent, not
                                   substrate).
    --output-json                 Emit JSON to stdout.
    --quiet                       Suppress human-readable output.

Origin: implementation-plan.md Phase 5.3 (Sovereign Scaling Cluster),
docs/compression-staging/continuous-verify-honest-design.md Section 4.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from continuous_verify.reporter import AnchorVerifyReporter
from focus.anchor_scanner import AnchorScanner


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="anchor_cli.py",
        description="Anchor Verification CLI — wraps scripts/focus/anchor_scanner.py for "
                    "/continuous-verify's Phase 1/2 anchor checks. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the target workspace root.")
    p.add_argument("--file-queries", nargs="*", default=None,
                   help="File anchors to verify.")
    p.add_argument("--symbol-queries", nargs="*", default=None,
                   help="Symbol anchors to verify.")
    p.add_argument("--exclude", nargs="*", default=None,
                   help="Paths to exclude from the substrate index (e.g. the plan file itself).")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1

    scanner = AnchorScanner(workspace, exclude=args.exclude)

    file_anchors = None
    if args.file_queries is not None:
        file_anchors = []
        for query in args.file_queries:
            result = scanner.verify_file(query)
            file_anchors.append({"query": query, **result})

    symbol_anchors = None
    if args.symbol_queries is not None:
        symbol_anchors = []
        for query in args.symbol_queries:
            result = scanner.verify_symbol(query)
            result["mock_trap_candidate"] = result["status"] == "FOUND_TEST_ONLY"
            symbol_anchors.append({"query": query, **result})

    report = {"file_anchors": file_anchors, "symbol_anchors": symbol_anchors}
    AnchorVerifyReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
