#!/usr/bin/env python3
"""
quality_audit.py — Quality Process Auditor CLI (read-only)
===========================================================
The deterministic verification rail behind /quality. It does NOT assess quality
(that is irreducible judgment owned by the /quality 7-step protocol). It verifies
the quality PROCESS RECEIPTS and flags mechanical anti-pattern SMELLS:

  * Ledger audit   — validates .workflow_state/quality_witness.log, computes the
                     unreviewed-entry count and the /triage P3 trigger.
  * Tag verify     — (with --scan FILE) validates Quality Chain Tags in an output.
  * Smell lint     — (with --scan FILE) flags mechanical anti-patterns. Advisory,
                     one-directional: smells => likely defect; no smells says
                     NOTHING about quality (reading otherwise is the Mock Trap).

Usage:
    python quality_audit.py --workspace /abs/path [--scan FILE] [--output-json] [--quiet]

Read-only on the workspace: the witness log is appended by the model (the
/quality protocol), never by this tool. All output goes to stdout.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from quality import __version__
from engine_utils import safe_read
from quality.ledger_auditor import LedgerAuditor
from quality.reporter import QualityReporter
from quality.smell_linter import SmellLinter
from quality.tag_verifier import TagVerifier

SCHEMA_VERSION = "1.0"
WITNESS_RELPATH = ".workflow_state/quality_witness.log"
_ADVISORY = (
    "This report verifies quality PROCESS RECEIPTS (witness ledger, chain tags) "
    "and flags mechanical anti-pattern SMELLS. It does NOT and cannot assess "
    "whether output is high quality — that is irreducible judgment owned by the "
    "/quality 7-step protocol. CLEAN means 'no mechanical issues detected', never "
    "'high quality'. Reading absence-of-smells as quality is the Mock Trap."
)


class QualityAuditor:
    """Orchestrates the ledger audit and (optionally) a single-output scan."""

    def __init__(self, workspace: Path, scan_file: Path = None):
        self.workspace = Path(workspace).resolve()
        self.scan_file = Path(scan_file).resolve() if scan_file else None

    def run(self) -> dict:
        ledger = LedgerAuditor().audit(self.workspace / WITNESS_RELPATH)
        scan = None
        if self.scan_file is not None:
            text = safe_read(self.scan_file)
            scan = {
                "target_file": str(self.scan_file),
                "chain_tag": TagVerifier().verify_text(text),
                "smells": SmellLinter().scan(text),
            }
        return {
            "schema_version": SCHEMA_VERSION,
            "tool": "quality",
            "tool_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(self.workspace),
            "ledger": ledger,
            "scan": scan,
            "summary": {"verdict_hint": self._verdict(ledger, scan), "advisory": _ADVISORY},
            "notes": [],
        }

    @staticmethod
    def _verdict(ledger: dict, scan: dict) -> str:
        # REVIEW on a concrete, mechanical problem only. Never a quality claim.
        if ledger["audit_trigger"] == "P3" or ledger["malformed_lines"]:
            return "REVIEW"
        if scan and (scan["smells"]["smell_total"] > 0
                     or scan["chain_tag"]["status"] == "MALFORMED"):
            return "REVIEW"
        return "CLEAN"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="quality_audit.py",
        description="Quality Process Auditor — read-only verification rail behind "
                    "/quality. Verifies process receipts + mechanical smells; never "
                    "assesses quality itself.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python quality_audit.py --workspace /home/user/project\n"
            "  python quality_audit.py --workspace /home/user/project --scan out.md --output-json\n"
        ),
    )
    parser.add_argument("--workspace", required=True, type=str,
                        help="Absolute path to the target workspace root.")
    parser.add_argument("--scan", type=str, default=None,
                        help="Optional output file to check for chain tags + smells.")
    parser.add_argument("--output-json", action="store_true",
                        help="Emit the report as JSON to stdout.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress human-readable output.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
        return 1
    if args.scan and not Path(args.scan).is_file():
        print(f"[ERROR] --scan file not found: {args.scan}", file=sys.stderr)
        return 1

    report = QualityAuditor(workspace=workspace, scan_file=args.scan).run()
    QualityReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
