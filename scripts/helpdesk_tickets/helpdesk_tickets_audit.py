#!/usr/bin/env python3
"""
helpdesk_tickets_audit.py — Ticket Lifecycle Evidence Engine CLI
====================================================================
The read-only mechanical layer behind /helpdesk-tickets's Phase 2 TICKET
VALIDATION checklist, STRICT RULE 7 (duplicate-ticket check), and staleness
detection. See scripts/helpdesk_tickets/__init__.py for the full contract.

Usage:
    python helpdesk_tickets_audit.py --tickets-dir /abs/path [options]

Optional:
    --validate-file PATH       Path to a ticket file to validate (Phase 2).
    --check-duplicate WORKFLOW Faulting workflow name to check for existing
                               open tickets (STRICT RULE 7).
    --staleness-threshold N   Days-open threshold for the staleness flag
                              (default: 14).
    --output-json             Emit JSON to stdout.
    --quiet                   Suppress human-readable output.

Origin: implementation-plan.md Phase 5.5 (Sovereign Scaling Cluster),
docs/compression-staging/helpdesk-tickets-honest-design.md Section 4.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from helpdesk_tickets.duplicate_detector import find_open_tickets_for_workflow
from helpdesk_tickets.reporter import HelpdeskTicketsReporter
from helpdesk_tickets.schema_validator import validate_ticket
from helpdesk_tickets.staleness import compute_staleness
from helpdesk_tickets.ticket_parser import parse_ticket


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="helpdesk_tickets_audit.py",
        description="Ticket Lifecycle Evidence Engine — schema validation, duplicate "
                    "detection, and staleness for /helpdesk-tickets. Read-only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--tickets-dir", required=True, type=str,
                   help="Absolute path to helpdesk-tickets/.")
    p.add_argument("--validate-file", type=str, default=None,
                   help="Path to a ticket file to validate.")
    p.add_argument("--check-duplicate", type=str, default=None,
                   help="Faulting workflow name to check for existing open tickets.")
    p.add_argument("--staleness-threshold", type=int, default=14,
                   help="Days-open threshold for the staleness flag (default: 14).")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    validation = None
    if args.validate_file is not None:
        text = Path(args.validate_file).read_text(encoding="utf-8")
        fields = parse_ticket(text)
        validation = validate_ticket(fields, Path(args.validate_file).name, text).as_dict()

    duplicates = None
    if args.check_duplicate is not None:
        duplicates = find_open_tickets_for_workflow(args.tickets_dir, args.check_duplicate).as_dict()

    staleness = [
        s.as_dict() for s in compute_staleness(args.tickets_dir, threshold_days=args.staleness_threshold)
    ]

    report = {"validation": validation, "duplicates": duplicates, "staleness": staleness}
    HelpdeskTicketsReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
