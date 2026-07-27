#!/usr/bin/env python3
"""
remediation_ledger.py — Findings Ledger Engine CLI
======================================================
Mechanically enumerates the Critical and Medium/Lesser findings in a persisted
`/implementation-plan --audit` report, so Phase 8 (`--remediate`) can account
for every one of them — mapped to a numbered `Fix N`, or explicitly declined
with a stated reason.

This is the Findings Ledger's evidence engine: the structural mirror of the
Coverage Ledger's `git diff --stat`. Read-only; writes nothing.

Usage:
    python3 remediation_ledger.py --audit /abs/path/to/audit.md [--output-json] [--quiet]
    python3 remediation_ledger.py --workspace /abs/path [--output-json] [--quiet]

`--workspace` resolves the most recent non-workstream audit for that workspace
from the global registry, making Phase 8a's resolution mechanical rather than a
judgment call.

Exit codes:
    0  findings enumerated (including a genuine zero-findings audit)
    1  invalid invocation, unreadable report, or unresolvable audit
    2  report read, but no findings section could be located — a parse failure,
       NOT a zero-findings result. Phase 8 HALTs here.

Origin: helpdesk-tickets/20260727_implementation-plan_workflow.md. See
`claude-commands/implementation-plan.md` Phase 8 and STRICT RULE 29.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from plan.findings import parse_audit, resolve_latest_audit  # noqa: E402
from plan.reporter import LedgerReporter  # noqa: E402


def _parse_args():
    p = argparse.ArgumentParser(
        prog="remediation_ledger.py",
        description="Findings Ledger Engine — enumerates an adversarial audit's "
                    "Critical and Medium findings for /implementation-plan --remediate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--audit", type=str,
                        help="Absolute path to a persisted audit report.")
    source.add_argument("--workspace", type=str,
                        help="Workspace root; resolves its most recent persisted audit.")
    p.add_argument("--audits-dir", type=str, default=None,
                   help="Override the global audit registry directory (testing).")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main():
    args = _parse_args()

    if args.audit:
        audit_path = Path(args.audit).expanduser().resolve()
        if not audit_path.is_file():
            print(f"[ERROR] Audit report not found: {audit_path}", file=sys.stderr)
            return 1
    else:
        workspace = Path(args.workspace).expanduser().resolve()
        if not workspace.is_dir():
            print(f"[ERROR] Workspace is not a directory: {workspace}", file=sys.stderr)
            return 1
        audit_path = resolve_latest_audit(workspace, audits_dir=args.audits_dir)
        if audit_path is None:
            print(
                f"[ERROR] No persisted audit found for workspace '{workspace.name}'. "
                "Run /implementation-plan --audit first, or pass --audit explicitly. "
                "Do NOT proceed against an inferred audit.",
                file=sys.stderr,
            )
            return 1

    report = parse_audit(audit_path)
    LedgerReporter().render(report, quiet=args.quiet, output_json=args.output_json)

    if report["status"] == "unreadable":
        return 1
    if report["status"] == "no_findings_section":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
