#!/usr/bin/env python3
"""
secretary_audit.py — Session Close Evidence Engine CLI
=========================================================
The read-only mechanical layer behind `/secretary`'s artifact-freshness,
retrospective-presence, Retrospective Lag, and receipt-family-presence
checks. Emits a structured JSON evidence report the agent reasons over — it
never judges session-scope honesty, anomaly rationale, or retrospective
insight. See scripts/secretary/__init__.py for the full contract.

Usage:
    python secretary_audit.py --workspace /abs/path [options]

Optional:
    --check-paths PATH [...]     Paths whose mtime freshness to check
                                  (e.g. SUITE_HEALTH.md, HANDOFF.md,
                                  ANOMALY_LOG.md, the active narrative shard).
    --since ISO_DATETIME          Reference time for freshness (default: today).
    --process-learnings PATH      Path to PROCESS_LEARNINGS.md (enables
                                  retrospective-freshness + lag checks).
    --history-glob PATTERN [...]  Glob pattern(s) for manifest/history/ shards
                                  (enables the Retrospective Lag check).
    --receipts-dir PATH           Receipts directory (enables receipt-family
                                  presence check).
    --receipt-files NAME [...]    Filenames to check under --receipts-dir.
    --output-json                 Emit the evidence report as JSON to stdout.
    --quiet                       Suppress human-readable output.

Origin: implementation-plan.md Phase 4.3-4.4 (Sovereign Scaling Cluster),
docs/compression-staging/secretary-honest-design.md Section 4.
"""

import argparse
import glob
import os
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from secretary.freshness import check_freshness
from secretary.receipt_presence import check_receipt_family
from secretary.reporter import SecretaryEvidenceReporter
from secretary.retrospective_check import check_retrospective_freshness, compute_retrospective_lag


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="secretary_audit.py",
        description="Session Close Evidence Engine — artifact freshness, retrospective "
                    "presence/lag, and receipt-family presence for /secretary. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the target workspace root.")
    p.add_argument("--check-paths", nargs="*", default=None,
                   help="Paths whose mtime freshness to check.")
    p.add_argument("--since", type=str, default=None,
                   help="ISO datetime reference for freshness (default: today).")
    p.add_argument("--process-learnings", type=str, default=None,
                   help="Path to PROCESS_LEARNINGS.md.")
    p.add_argument("--history-glob", nargs="*", default=None,
                   help="Glob pattern(s) for manifest/history/ shards.")
    p.add_argument("--receipts-dir", type=str, default=None,
                   help="Receipts directory for the receipt-family presence check.")
    p.add_argument("--receipt-files", nargs="*", default=None,
                   help="Filenames to check under --receipts-dir.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1

    since = datetime.fromisoformat(args.since) if args.since else None

    # Expand `~` on every path-like argument here, at the CLI boundary — the
    # library functions in secretary/ deliberately take plain paths and do
    # not each re-implement shell-style expansion (mirrors focus.py/
    # build_audit.py resolving --workspace once at the CLI layer, not deep
    # inside library calls). Caught live: glob.glob() does not expand `~`,
    # so an unexpanded --history-glob silently found zero shards.
    process_learnings = os.path.expanduser(args.process_learnings) if args.process_learnings else None
    receipts_dir = os.path.expanduser(args.receipts_dir) if args.receipts_dir else None

    freshness = None
    if args.check_paths is not None:
        expanded_paths = [os.path.expanduser(p) for p in args.check_paths]
        freshness = [f.as_dict() for f in check_freshness(expanded_paths, since=since)]

    retrospective_freshness = None
    if process_learnings is not None:
        retrospective_freshness = check_retrospective_freshness(process_learnings).as_dict()

    retrospective_lag = None
    if process_learnings is not None and args.history_glob is not None:
        history_paths = []
        for pattern in args.history_glob:
            history_paths.extend(sorted(glob.glob(os.path.expanduser(pattern))))
        retrospective_lag = compute_retrospective_lag(history_paths, process_learnings).as_dict()

    receipt_family = None
    if receipts_dir is not None and args.receipt_files is not None:
        receipt_family = [
            r.as_dict() for r in check_receipt_family(receipts_dir, args.receipt_files)
        ]

    report = {
        "freshness": freshness,
        "retrospective_freshness": retrospective_freshness,
        "retrospective_lag": retrospective_lag,
        "receipt_family": receipt_family,
    }
    SecretaryEvidenceReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
