"""
test_suite_checks.py — Targeted tests for the runtime-directory-gating fix.

Scope: only the behavior changed 2026-07-05 (resolves helpdesk-tickets/
20260705_opencode-to-grok-build-transition_workflow.md) — check_symlinks now
gates its per-file OpenCode/Antigravity pointer checks on whether the runtime
directory exists at all, and check_runtime_availability reports that fact once
per scan rather than once per file. Pre-existing linter behavior (frontmatter,
structure, cross-reference, hash checks) is not otherwise covered here; this
suite predates unit tests entirely and a full retrofit is out of scope for
this fix.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import unittest
from pathlib import Path
from unittest import mock

from suite import checks
from suite.models import LintReport


class TestRuntimeAvailability(unittest.TestCase):
    def test_reports_info_when_directory_missing(self):
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent/opencode"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/nonexistent/antigravity"), \
             mock.patch.object(checks, "GROK_BUILD_DIR", "/nonexistent/grok"):
            checks.check_runtime_availability(report)
        self.assertEqual(len(report.findings), 3)
        self.assertTrue(all(f.severity == "INFO" for f in report.findings))
        self.assertTrue(all(f.workflow == "(suite)" for f in report.findings))
        messages = [f.message for f in report.findings]
        self.assertTrue(any("OpenCode" in m for m in messages))
        self.assertTrue(any("Antigravity" in m for m in messages))
        self.assertTrue(any("Grok Build" in m for m in messages))

    def test_no_finding_when_directory_present(self):
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/tmp"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/tmp"), \
             mock.patch.object(checks, "GROK_BUILD_DIR", "/tmp"):
            checks.check_runtime_availability(report)
        self.assertEqual(report.findings, [])

    def test_never_a_warning_or_critical(self):
        # A retired/replaced runtime is informational, not a defect — must
        # never inflate the WARNING/CRITICAL counts other checks rely on.
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent"):
            checks.check_runtime_availability(report)
        self.assertEqual(report.criticals, [])
        self.assertEqual(report.warnings, [])


class TestSymlinksGating(unittest.TestCase):
    def test_missing_directory_produces_no_per_file_warning(self):
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent/opencode"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/nonexistent/antigravity"), \
             mock.patch.object(checks, "SYMLINK_DIR", "/tmp/definitely-not-here-either"):
            checks.check_symlinks("some_workflow.md", "/home/jwils/blueprint-workflows", report)
        pointer_findings = [f for f in report.findings if f.check == "pointer"]
        self.assertEqual(pointer_findings, [])  # gated out — no per-file noise

    def test_present_directory_missing_file_still_warns(self):
        # The genuinely different case: the runtime IS installed, but this
        # one specific file's pointer wasn't created — that's a real gap.
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/tmp"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/tmp"), \
             mock.patch.object(checks, "SYMLINK_DIR", "/tmp"):
            checks.check_symlinks("definitely_not_a_real_pointer_file.md",
                                  "/home/jwils/blueprint-workflows", report)
        pointer_findings = [f for f in report.findings if f.check == "pointer"]
        self.assertEqual(len(pointer_findings), 2)  # OpenCode + Antigravity, both real gaps
        self.assertTrue(all(f.severity == "WARNING" for f in pointer_findings))

    def test_thirty_two_files_missing_directory_yields_zero_pointer_warnings(self):
        # Regression guard for the exact symptom this ticket fixed: one
        # missing directory must never produce N per-file warnings again.
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/nonexistent"), \
             mock.patch.object(checks, "SYMLINK_DIR", "/tmp"):
            for i in range(32):
                checks.check_symlinks(f"workflow_{i}.md", "/home/jwils/blueprint-workflows", report)
        pointer_findings = [f for f in report.findings if f.check == "pointer"]
        self.assertEqual(pointer_findings, [])


if __name__ == "__main__":
    unittest.main()
