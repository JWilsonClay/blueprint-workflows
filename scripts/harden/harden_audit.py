#!/usr/bin/env python3
"""
harden_audit.py — Hardening Evidence Engine CLI (read-only)
============================================================
The deterministic verification rail behind /harden. It scans eligible script
files for deterministic CWE signatures, suggests a Threat Context (advisory), and
computes a Hardening Grade CEILING from real findings — replacing the historical
practice of asserting a grade by judgment with nothing detecting the signatures
that define it (Grade Fraud).

⚠ The grade ceiling is ONE-DIRECTIONAL. A CRITICAL/HIGH finding LOWERS it; a
clean scan certifies NOTHING. The /harden agent assigns the final grade AT OR
BELOW the ceiling after the threat model and Sound-Effect-Execution judgment.
Reading ``CLEAN_SCAN`` / ``ceiling=Diamond`` as a Diamond is the Grade Fraud this
engine prevents.

Usage:
    python harden_audit.py --workspace /abs/path [--file REL] [--output-json] [--quiet]

Read-only on the target workspace: it opens files for reading and writes nothing
(architectural sibling of doorway.py / focus.py / quality_audit.py). All output
goes to stdout.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from harden import __version__
from harden._utils import (
    IGNORE_DIRS, assert_within, is_test_path, looks_like_script, safe_read,
)
from harden.cwe_scanner import CWEScanner, first_line_of
from harden.grade_computer import compute_ceiling, lowest_ceiling
from harden.reporter import HardenReporter
from harden.threat_classifier import ThreatClassifier

SCHEMA_VERSION = "1.0"
_MAX_FILES = 5000  # Bound the scan (CWE-400).

_ADVISORY = (
    "This report verifies the DETERMINISTIC half of /harden: CWE signatures with "
    "exact matches, and a grade CEILING computed from them. The ceiling is "
    "ONE-DIRECTIONAL — a CRITICAL/HIGH finding forbids a higher grade, but a clean "
    "scan (ceiling=Diamond / verdict CLEAN_SCAN) is NEVER a certification. Threat "
    "modeling, exploitability, input-validation sufficiency, and Sound-Effect-"
    "Execution remain irreducible judgment owned by the /harden agent, who grades "
    "AT OR BELOW the ceiling. Reading a clean scan as a Diamond is Grade Fraud."
)


class HardenAuditor:
    """Orchestrates discovery, CWE scan, threat classification, grade ceiling."""

    def __init__(self, workspace: Path, file_override: str = None, max_files: int = _MAX_FILES):
        self.workspace = Path(workspace).resolve()
        self.file_override = file_override
        self.max_files = max_files
        self._scanner = CWEScanner()
        self._classifier = ThreatClassifier()

    def run(self) -> dict:
        report = {
            "schema_version": SCHEMA_VERSION,
            "tool": "harden",
            "tool_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(self.workspace),
            "files": [],
            "notes": [],
        }

        targets = self._discover()
        if self.file_override is not None and not targets:
            report["notes"].append(
                f"--file '{self.file_override}' is not an eligible script "
                f"(missing, a test path, or a non-script extension)."
            )

        file_reports = []
        for path, relpath, text in targets:
            findings = self._scanner.scan_text(relpath, text, Path(path).suffix)
            threat = self._classifier.classify(text)
            grade = compute_ceiling(findings)
            file_reports.append({
                "path": relpath,
                "threat_context": threat["context"],
                "threat_signals": threat["signals"],
                "findings": findings,
                "grade_ceiling": grade["grade_ceiling"],
                "ceiling_basis": grade["ceiling_basis"],
                "severity_counts": grade["severity_counts"],
                "firm_severity_counts": grade["firm_severity_counts"],
                "confirmation_pending": grade["confirmation_pending"],
                "advisory_count": grade["advisory_count"],
            })

        report["files"] = file_reports
        report["summary"] = self._summarize(file_reports)
        return report

    # ------------------------------------------------------------------
    # Discovery (read-only walk, bounded)
    # ------------------------------------------------------------------

    def _discover(self):
        """Yield (path, relpath, text) for eligible, non-test script files."""
        if self.file_override is not None:
            return list(self._discover_single())
        out = []
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for name in files:
                full = Path(root) / name
                relpath = str(full.relative_to(self.workspace)).replace("\\", "/")
                if is_test_path(relpath):
                    continue
                text = safe_read(full)
                if not text:
                    continue
                if not looks_like_script(full, first_line_of(text)):
                    continue
                out.append((full, relpath, text))
                if len(out) >= self.max_files:
                    return out
        return out

    def _discover_single(self):
        candidate = self.workspace / self.file_override
        try:
            resolved = assert_within(candidate, self.workspace)
        except ValueError:
            return
        if not resolved.is_file():
            return
        relpath = str(resolved.relative_to(self.workspace)).replace("\\", "/")
        if is_test_path(relpath):
            return
        text = safe_read(resolved)
        if not text or not looks_like_script(resolved, first_line_of(text)):
            return
        yield resolved, relpath, text

    # ------------------------------------------------------------------
    # Summary + advisory verdict
    # ------------------------------------------------------------------

    @staticmethod
    def _summarize(file_reports) -> dict:
        totals = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        firm_crit = firm_high = pending = advisory = 0
        files_with_findings = 0
        for f in file_reports:
            if f["findings"]:
                files_with_findings += 1
            for sev, n in f["severity_counts"].items():
                totals[sev] = totals.get(sev, 0) + n
            firm_crit += f["firm_severity_counts"].get("CRITICAL", 0)
            firm_high += f["firm_severity_counts"].get("HIGH", 0)
            pending += f["confirmation_pending"]
            advisory += f["advisory_count"]

        ceilings = [f["grade_ceiling"] for f in file_reports]

        if firm_crit:
            verdict = "BLOCKED"      # firm CRITICAL present — not certifiable
        elif firm_high or pending:
            verdict = "FINDINGS"     # firm HIGH, or credential candidates to confirm
        elif advisory:
            verdict = "ADVISORY"     # only advisory items remain
        else:
            verdict = "CLEAN_SCAN"   # no deterministic findings — NOT a grade

        return {
            "files_scanned": len(file_reports),
            "files_with_findings": files_with_findings,
            "total_findings": sum(totals.values()),
            "severity_totals": totals,
            "confirmation_pending": pending,
            "advisory_findings": advisory,
            "files_by_ceiling": {g: ceilings.count(g) for g in set(ceilings)},
            "lowest_ceiling": lowest_ceiling(ceilings),
            "verdict_hint": verdict,
            "advisory": _ADVISORY,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="harden_audit.py",
        description="Hardening Evidence Engine — read-only deterministic CWE scan + "
                    "grade ceiling behind /harden. Never certifies a grade; computes "
                    "the ceiling the agent grades beneath.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python harden_audit.py --workspace /home/user/project\n"
            "  python harden_audit.py --workspace /home/user/project --output-json\n"
            "  python harden_audit.py --workspace /home/user/project --file scripts/x.py --output-json\n"
        ),
    )
    parser.add_argument("--workspace", required=True, type=str,
                        help="Absolute path to the target workspace root.")
    parser.add_argument("--file", type=str, default=None,
                        help="Scan a single workspace-relative script file instead of walking.")
    parser.add_argument("--output-json", action="store_true",
                        help="Emit the evidence report as JSON to stdout.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress human-readable output.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        print(f"[ERROR] Workspace does not exist: {workspace}", file=sys.stderr)
        return 1
    if not workspace.is_dir():
        print(f"[ERROR] Workspace path is not a directory: {workspace}", file=sys.stderr)
        return 1

    report = HardenAuditor(workspace=workspace, file_override=args.file).run()
    HardenReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
