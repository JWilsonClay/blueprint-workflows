"""
test_focus.py — Test suite for the focus Triad Evidence Engine.

Covers: plan location (the hyphen/underscore bug fix), parsing + anchor
extraction, substrate verification (file/symbol, Mock Trap test-path
separation), the end-to-end FocusVerifier report, and the architectural
read-only invariant (the verifier must never write to the workspace).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from focus.anchor_scanner import AnchorScanner
from focus.focus import FocusVerifier
from focus.plan_parser import (
    CANONICAL_PLAN_NAME,
    LEGACY_PLAN_NAME,
    extract_anchors,
    locate_plan,
    parse,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _all_paths(root: Path) -> set:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


class TestPlanLocator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_prefers_canonical_hyphen(self):
        _write(self.tmp / CANONICAL_PLAN_NAME, "# Plan\n")
        _write(self.tmp / LEGACY_PLAN_NAME, "# Old Plan\n")
        path, spelling = locate_plan(self.tmp)
        self.assertEqual(path.name, CANONICAL_PLAN_NAME)
        self.assertEqual(spelling, "hyphen")

    def test_falls_back_to_underscore(self):
        # The historical bug: only the underscore file exists. The fixed
        # locator must still find it rather than report "no plan".
        _write(self.tmp / LEGACY_PLAN_NAME, "# Old Plan\n")
        path, spelling = locate_plan(self.tmp)
        self.assertEqual(path.name, LEGACY_PLAN_NAME)
        self.assertEqual(spelling, "underscore")

    def test_no_plan(self):
        path, spelling = locate_plan(self.tmp)
        self.assertIsNone(path)
        self.assertIsNone(spelling)


class TestPlanParser(unittest.TestCase):
    def test_items_split_on_headers(self):
        plan = "# Title\n\n## Step 1: A\nbody a\n\n### Step 2: B\nbody b\n"
        items = parse(plan)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "Step 1: A")
        self.assertEqual(items[0].level, 2)
        self.assertEqual(items[1].level, 3)
        # source_line is 1-based and points at the header.
        self.assertEqual(plan.splitlines()[items[0].source_line - 1], "## Step 1: A")

    def test_anchor_extraction_files_and_symbols(self):
        text = "Implement `RealClass` in `real_module.py`. We must always proceed."
        anchors = extract_anchors(text)
        kinds = {(a.kind, a.query) for a in anchors}
        self.assertIn(("file", "real_module.py"), kinds)
        self.assertIn(("symbol", "RealClass"), kinds)

    def test_prose_words_are_not_symbols(self):
        # Bare English words (even capitalized) must not become anchors.
        text = "We must Build the Thing and Always Proceed."
        self.assertEqual(extract_anchors(text), [])

    def test_backticked_commands_are_not_anchors(self):
        # Multi-word backtick spans are commands, not anchors.
        text = "Run `python focus.py --workspace .` to verify."
        queries = {a.query for a in extract_anchors(text)}
        self.assertNotIn("python focus.py --workspace .", queries)

    def test_headers_inside_fences_ignored(self):
        plan = "## Real Item\n```\n## not a header\n```\nbody\n"
        items = parse(plan)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Real Item")


class TestAnchorScanner(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "real_module.py", "class RealClass:\n    pass\n")
        _write(self.tmp / "tests" / "test_mock.py", "MockOnlySymbol = 1\n")
        self.scanner = AnchorScanner(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_file_exists_by_basename(self):
        self.assertEqual(self.scanner.verify_file("real_module.py")["status"], "EXISTS")

    def test_file_missing(self):
        self.assertEqual(self.scanner.verify_file("ghost_module.py")["status"], "MISSING")

    def test_path_traversal_rejected(self):
        self.assertEqual(self.scanner.verify_file("../../etc/passwd")["status"], "INVALID")

    def test_symbol_found_in_production(self):
        res = self.scanner.verify_symbol("RealClass")
        self.assertEqual(res["status"], "FOUND_PRODUCTION")
        self.assertGreaterEqual(res["production_matches"], 1)

    def test_symbol_absent(self):
        self.assertEqual(self.scanner.verify_symbol("GhostClass")["status"], "ABSENT")

    def test_symbol_mock_trap(self):
        # Present only under tests/ → Mock Trap candidate, not production.
        res = self.scanner.verify_symbol("MockOnlySymbol")
        self.assertEqual(res["status"], "FOUND_TEST_ONLY")
        self.assertEqual(res["production_matches"], 0)
        self.assertGreaterEqual(res["test_matches"], 1)


class TestFocusVerifier(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        plan = (
            "# Test Plan\n\n"
            "## Step 1: Build the real module\n"
            "Implement `RealClass` in `real_module.py`.\n\n"
            "## Step 2: Ghost feature\n"
            "Add `GhostClass` to `ghost_module.py` — not yet built.\n\n"
            "## Step 3: Mock-trap feature\n"
            "Wire in `MockOnlySymbol`.\n"
        )
        _write(self.tmp / CANONICAL_PLAN_NAME, plan)
        _write(self.tmp / "real_module.py", "class RealClass:\n    pass\n")
        _write(self.tmp / "tests" / "test_mock.py", "MockOnlySymbol = 1\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_end_to_end_report(self):
        report = FocusVerifier(self.tmp).run()
        self.assertTrue(report["plan_found"])
        self.assertEqual(report["plan_spelling"], "hyphen")
        summary = report["summary"]
        self.assertEqual(summary["present"], 2)   # RealClass + real_module.py
        self.assertEqual(summary["absent"], 2)     # GhostClass + ghost_module.py
        self.assertEqual(summary["mock_trap_candidates"], 1)  # MockOnlySymbol
        # A Mock Trap candidate forces the mechanical hint to RED.
        self.assertEqual(summary["verdict_hint"], "RED")

    def test_plan_not_excluded_would_have_hidden_ghost(self):
        # Regression guard: GhostClass appears in the plan text but the plan is
        # excluded from the index, so it must still read as ABSENT.
        report = FocusVerifier(self.tmp).run()
        ghost = [
            a for item in report["items"] for a in item["anchors"]
            if a["query"] == "GhostClass"
        ]
        self.assertEqual(ghost[0]["status"], "ABSENT")

    def test_missing_plan_is_graceful(self):
        empty = Path(tempfile.mkdtemp())
        try:
            report = FocusVerifier(empty).run()
            self.assertFalse(report["plan_found"])
            self.assertEqual(report["summary"]["verdict_hint"], "RED")
            self.assertTrue(report["notes"])
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_verifier_is_read_only(self):
        # The architectural guarantee: a verification run must not mutate the
        # workspace in any way. Snapshot every path before and after.
        before = _all_paths(self.tmp)
        FocusVerifier(self.tmp).run()
        after = _all_paths(self.tmp)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
