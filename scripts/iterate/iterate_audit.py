#!/usr/bin/env python3
"""
iterate_audit.py — Mock-Trap Detector CLI (read-only, Python-first)
====================================================================
The deterministic verification rail behind /iterate-test. It parses Python test
files (NO execution) and reports, per file, which imported production symbols are
replaced by mocks, which are called un-patched, and whether a mock's canned
return value is echoed in an assertion — the mechanical evidence behind the
Step-4b Intelligence Bridge Declaration, which was historically an unverified
attestation.

⚠ The signal is ONE-DIRECTIONAL. A ``MOCK_TRAP_CANDIDATE`` means an imported
production symbol is mocked — IF it is the PRIMARY intelligence under test, that
is a Mock Trap; the engine does NOT decide PRIMARY vs INFRASTRUCTURE (the agent's
Step-4b judgment). A clean scan (``NO_FINDINGS``) certifies NOTHING about
fidelity. Reading a clean scan as a HOT pass is the Mock Trap this engine surfaces.

Usage:
    python iterate_audit.py --workspace /abs/path [--test REL] [--subject SYM]
                            [--output-json] [--quiet]

    --test SYM      Analyze one workspace-relative Python test file (the common
                    single-stage case) instead of walking the workspace.
    --subject SYM   The production module/symbol the test CLAIMS to validate
                    (e.g. 'app.core.governor' or 'Governor'). Sharpens the signal:
                    a mocked symbol matching --subject is flagged is_subject.

Read-only on the target workspace: it parses files for reading and writes nothing
(architectural sibling of doorway.py / focus.py / quality_audit.py /
harden_audit.py). All output goes to stdout.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from iterate import __version__
from iterate._utils import (
    IGNORE_DIRS, PY_EXTENSIONS, assert_within, is_test_path, safe_read,
)
from iterate.bridge_classifier import classify_file
from iterate.mock_analyzer import MockTrapAnalyzer
from iterate.reporter import IterateReporter

SCHEMA_VERSION = "1.0"
_MAX_FILES = 5000  # Bound the walk (CWE-400).

_ADVISORY = (
    "This report verifies the DETERMINISTIC half of /iterate-test: which imported "
    "production symbols a Python test mocks vs calls un-patched, and canned-value "
    "assertion tautologies. The signal is ONE-DIRECTIONAL — a MOCK_TRAP_CANDIDATE "
    "means an imported production symbol is mocked, but the engine does NOT decide "
    "whether it is the PRIMARY intelligence under test (a Mock Trap) or "
    "INFRASTRUCTURE (a valid mock); that is the agent's Step-4b judgment. A clean "
    "scan (NO_FINDINGS) is NEVER a fidelity certification — a live-called test can "
    "still be a tautology or never reach the intelligence (Sound Effect Execution). "
    "Reading a clean scan as a HOT pass is the Mock Trap this engine surfaces."
)


class IterateAuditor:
    """Orchestrates test discovery, AST analysis, and fidelity classification."""

    def __init__(self, workspace: Path, test_override: str = None,
                 subject: str = None, max_files: int = _MAX_FILES):
        self.workspace = Path(workspace).resolve()
        self.test_override = test_override
        self.subject = subject
        self.max_files = max_files
        self._analyzer = MockTrapAnalyzer()

    def run(self) -> dict:
        report = {
            "schema_version": SCHEMA_VERSION,
            "tool": "iterate",
            "tool_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(self.workspace),
            "subject": self.subject,
            "files": [],
            "notes": [],
        }

        targets = self._discover(report)
        file_reports = []
        for relpath, text in targets:
            analysis = self._analyzer.analyze(relpath, text, subject=self.subject)
            file_reports.append(classify_file(analysis))

        report["files"] = file_reports
        report["summary"] = self._summarize(file_reports)
        return report

    # ------------------------------------------------------------------
    # Discovery (read-only walk, bounded)
    # ------------------------------------------------------------------

    def _discover(self, report):
        """Yield (relpath, text) for eligible Python test files."""
        if self.test_override is not None:
            return list(self._discover_single(report))
        out = []
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for name in files:
                full = Path(root) / name
                if full.suffix.lower() not in PY_EXTENSIONS:
                    continue
                if name == "__init__.py":
                    continue  # package marker, never a test-case module
                relpath = str(full.relative_to(self.workspace)).replace("\\", "/")
                if not is_test_path(relpath):
                    continue
                text = safe_read(full)
                if not text:
                    continue
                out.append((relpath, text))
                if len(out) >= self.max_files:
                    return out
        return out

    def _discover_single(self, report):
        candidate = self.workspace / self.test_override
        try:
            resolved = assert_within(candidate, self.workspace)
        except ValueError:
            report["notes"].append(
                f"--test '{self.test_override}' resolves outside the workspace; rejected."
            )
            return
        if not resolved.is_file():
            report["notes"].append(f"--test '{self.test_override}' is not a file.")
            return
        relpath = str(resolved.relative_to(self.workspace)).replace("\\", "/")
        if resolved.suffix.lower() not in PY_EXTENSIONS:
            report["notes"].append(
                f"--test '{relpath}' is not a .py file. The Mock-Trap detector is "
                f"Python-first; other languages are out of scope (analyze by hand)."
            )
            return
        if not is_test_path(relpath):
            report["notes"].append(
                f"--test '{relpath}' does not look like a test file (no test/ marker "
                f"or test_/_test name). Analyzing anyway as instructed."
            )
        text = safe_read(resolved)
        if not text:
            report["notes"].append(f"--test '{relpath}' is empty or unreadable.")
            return
        yield relpath, text

    # ------------------------------------------------------------------
    # Summary + advisory verdict
    # ------------------------------------------------------------------

    @staticmethod
    def _summarize(file_reports) -> dict:
        def n(sig):
            return sum(1 for f in file_reports if f.get("file_signal") == sig)

        mock_trap = n("MOCK_TRAP_CANDIDATE")
        hardcoded = n("HARDCODED_ASSERTION")
        no_import = n("NO_PRODUCTION_IMPORT")
        parse_err = n("PARSE_ERROR")

        verdict = "FINDINGS" if (mock_trap or hardcoded) else "NO_FINDINGS"

        return {
            "tests_scanned": len(file_reports),
            "mock_trap_candidate_files": mock_trap,
            "hardcoded_assertion_files": hardcoded,
            "no_production_import_files": no_import,
            "parse_error_files": parse_err,
            "verdict_hint": verdict,
            "advisory": _ADVISORY,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="iterate_audit.py",
        description="Mock-Trap Detector — read-only, Python-first AST analysis "
                    "behind /iterate-test. Reports which imported production "
                    "symbols a test mocks vs calls live; never decides "
                    "PRIMARY-vs-INFRASTRUCTURE and never certifies fidelity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python iterate_audit.py --workspace /home/user/project\n"
            "  python iterate_audit.py --workspace /home/user/project --test tests/test_x.py\n"
            "  python iterate_audit.py --workspace /proj --test tests/test_gov.py "
            "--subject app.core.governor --output-json\n"
        ),
    )
    parser.add_argument("--workspace", required=True, type=str,
                        help="Absolute path to the target workspace root.")
    parser.add_argument("--test", type=str, default=None,
                        help="Analyze a single workspace-relative Python test file.")
    parser.add_argument("--subject", type=str, default=None,
                        help="Production module/symbol the test claims to validate.")
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

    report = IterateAuditor(
        workspace=workspace, test_override=args.test, subject=args.subject,
    ).run()
    IterateReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
