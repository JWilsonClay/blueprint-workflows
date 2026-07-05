#!/usr/bin/env python3
"""
ledger.py — Ledger Growth Monitor CLI
=======================================
Runs every tracked ledger from ledger_config.toml: "shard" mode rolls over a
dated shard directory when the real calendar quarter changes or a
within-quarter size safety-valve is crossed; "warn" mode reports (never
writes) when a single file's entry/byte count crosses an advisable threshold.

The date used for quarter determination is always the real OS clock
(datetime.date.today()) — never an LLM's own sense of what day it is.

Usage:
    python ledger.py --workspace /abs/path [--output-json] [--quiet]

Hook: called by /secretary Phase 1 (every session close), unconditionally,
independent of which ticket-closure path ran this session.

Origin: helpdesk ticket 20260704_workflow-manifest-growth_workflow.md.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from ledger.config import load_config, iter_ledgers
from ledger.monitor import run_all
from ledger.reporter import LedgerReporter


def _parse_args():
    p = argparse.ArgumentParser(
        prog="ledger.py",
        description="Ledger Growth Monitor — shard rollover + growth warnings for "
                    "tracked Append-Only files, config-driven via ledger_config.toml.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the workspace root.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main():
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1
    config = load_config()
    statuses = run_all(workspace, list(iter_ledgers(config)))
    LedgerReporter().render(statuses, quiet=args.quiet, output_json=args.output_json)
    # Exit 0 always: WARN is advisory, a rollover is a normal outcome, neither is an error.
    return 0


if __name__ == "__main__":
    sys.exit(main())
