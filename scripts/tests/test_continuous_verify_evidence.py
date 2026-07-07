"""
test_continuous_verify_evidence.py — Test suite for scripts/continuous_verify/

Covers: file-anchor verification (bare-filename basename matching, missing
file), symbol-anchor verification (production match, test-only match with
the mock_trap_candidate flag set, absent symbol), plan-file exclusion (a
plan that mentions a symbol is not substrate), the CLI end-to-end, and the
read-only invariant.

This module wraps scripts/focus/anchor_scanner.py rather than duplicating
it — these tests focus on the wrapper's own logic (query tagging, the
mock_trap_candidate flag derivation, exclude passthrough) since
AnchorScanner's own parsing logic already has its own test coverage
(test_focus.py / equivalent, pre-existing).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from focus.anchor_scanner import AnchorScanner


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestAnchorWrapperLogic(unittest.TestCase):
    """
    Exercises the same verify_file/verify_symbol + mock_trap_candidate
    derivation the CLI performs, at the unit level (faster than subprocess
    for most cases; the CLI itself is covered end-to-end below).
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_file_anchor_exists(self):
        _write(self.tmp / "src" / "module.py", "x = 1\n")
        scanner = AnchorScanner(self.tmp)
        result = scanner.verify_file("module.py")
        self.assertEqual(result["status"], "EXISTS")

    def test_file_anchor_missing(self):
        scanner = AnchorScanner(self.tmp)
        result = scanner.verify_file("does_not_exist.py")
        self.assertEqual(result["status"], "MISSING")

    def test_symbol_found_in_production_no_mock_trap_flag(self):
        _write(self.tmp / "src" / "module.py", "def real_function():\n    pass\n")
        scanner = AnchorScanner(self.tmp)
        result = scanner.verify_symbol("real_function")
        mock_trap_candidate = result["status"] == "FOUND_TEST_ONLY"
        self.assertEqual(result["status"], "FOUND_PRODUCTION")
        self.assertFalse(mock_trap_candidate)

    def test_symbol_found_test_only_sets_mock_trap_flag(self):
        _write(self.tmp / "tests" / "test_module.py", "def fake_only_function():\n    pass\n")
        scanner = AnchorScanner(self.tmp)
        result = scanner.verify_symbol("fake_only_function")
        mock_trap_candidate = result["status"] == "FOUND_TEST_ONLY"
        self.assertEqual(result["status"], "FOUND_TEST_ONLY")
        self.assertTrue(mock_trap_candidate)

    def test_symbol_absent(self):
        scanner = AnchorScanner(self.tmp)
        result = scanner.verify_symbol("totally_nonexistent_symbol_xyz")
        self.assertEqual(result["status"], "ABSENT")

    def test_plan_file_excluded_from_its_own_verification(self):
        # A plan that *mentions* a symbol is intent, not substrate -- must
        # not count as FOUND when the plan file itself is excluded.
        plan = self.tmp / "implementation-plan.md"
        _write(plan, "This plan requires implementing `phantom_symbol_abc`.\n")
        scanner = AnchorScanner(self.tmp, exclude=[str(plan)])
        result = scanner.verify_symbol("phantom_symbol_abc")
        self.assertEqual(result["status"], "ABSENT")

    def test_plan_file_not_excluded_would_false_positive(self):
        # Confirms the exclude mechanism is actually doing something --
        # without it, the same query would incorrectly report FOUND.
        plan = self.tmp / "implementation-plan.md"
        _write(plan, "This plan requires implementing `phantom_symbol_abc`.\n")
        scanner = AnchorScanner(self.tmp)  # no exclude
        result = scanner.verify_symbol("phantom_symbol_abc")
        self.assertNotEqual(result["status"], "ABSENT")


class TestCliEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "src" / "module.py", "def real_function():\n    pass\n")
        _write(self.tmp / "tests" / "test_module.py", "def fake_only_function():\n    pass\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cli_reports_file_and_symbol_anchors(self):
        here = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [
                sys.executable,
                str(here / "continuous_verify" / "anchor_cli.py"),
                "--workspace", str(self.tmp),
                "--file-queries", "module.py", "missing.py",
                "--symbol-queries", "real_function", "fake_only_function",
                "--output-json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"EXISTS"', result.stdout)
        self.assertIn('"MISSING"', result.stdout)
        self.assertIn('"mock_trap_candidate": true', result.stdout)
        self.assertIn('"mock_trap_candidate": false', result.stdout)

    def test_cli_skips_sections_when_no_queries_given(self):
        here = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [
                sys.executable,
                str(here / "continuous_verify" / "anchor_cli.py"),
                "--workspace", str(self.tmp),
                "--output-json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"file_anchors": null', result.stdout)
        self.assertIn('"symbol_anchors": null', result.stdout)


class TestReadOnlyInvariant(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "src" / "module.py", "def real_function():\n    pass\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_writes_nothing(self):
        before = self._snapshot()
        scanner = AnchorScanner(self.tmp)
        scanner.verify_file("module.py")
        scanner.verify_symbol("real_function")
        self.assertEqual(before, self._snapshot())


if __name__ == "__main__":
    unittest.main()
