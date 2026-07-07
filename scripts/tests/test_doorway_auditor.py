"""
test_doorway_auditor.py — Direct unit tests for scripts/doorway/auditor.py's
StructuralAuditor, specifically the Tier 1 ownership_incomplete gate
(PR 01-02, recovered from the Sovereign Redesign Cluster's orphaned
execute-plan branches) and the substrate_index builder (PR 01-01).

[ADDED 2026-07-06 — Sovereign Redesign Cluster Stage 2, Task 2.3]
No dedicated unit test file for StructuralAuditor existed prior to this --
its behavior was previously verified only via manual "unit simulations"
noted in commit messages (9d12060, 620c609), never captured as a
persisted, re-runnable test. This closes that specific gap for the
Tier 1 ownership_incomplete gate, a genuinely new zero_finding-blocking
condition where a silent logic inversion or off-by-one would misreport
workspace cleanliness.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from doorway.auditor import StructuralAuditor


class TestOwnershipIncompleteGate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ownership_file = self.tmp / "FOLDER_OWNERSHIP.md"
        self.auditor = StructuralAuditor(
            workspace=self.tmp,
            ownership_file=self.ownership_file,
            breadcrumb_manager=None,
            integrity_manager=None,
            metrics={"created": 0, "ingested": 0, "repairs": 0},
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _audit_empty_map(self):
        # Empty current_map/previous_map: the main new/modified/missing_readme
        # loop never executes, so breadcrumb_manager/integrity_manager (both
        # None here) are never touched -- isolates the ownership_incomplete
        # check, which reads self.ownership_file directly.
        return self.auditor.audit(current_map={}, previous_map={})

    def test_placeholder_sentence_flagged(self):
        self.ownership_file.write_text("- src/: TODO\n- docs/: add description\n")
        drift = self._audit_empty_map()
        self.assertIn("src", drift["ownership_incomplete"])
        self.assertIn("docs", drift["ownership_incomplete"])

    def test_real_sentence_not_flagged(self):
        self.ownership_file.write_text(
            "- src/: Application source code and core business logic\n"
        )
        drift = self._audit_empty_map()
        self.assertEqual(drift["ownership_incomplete"], [])

    def test_short_sentence_flagged(self):
        # Under the 8-char floor in _is_placeholder_sentence.
        self.ownership_file.write_text("- x/: misc\n")
        drift = self._audit_empty_map()
        self.assertIn("x", drift["ownership_incomplete"])

    def test_missing_ownership_file_yields_no_crash_no_flags(self):
        # ownership_file was never created in setUp.
        drift = self._audit_empty_map()
        self.assertEqual(drift["ownership_incomplete"], [])

    def test_mixed_real_and_placeholder(self):
        self.ownership_file.write_text(
            "- src/: Application source code and core business logic\n"
            "- scripts/: placeholder\n"
        )
        drift = self._audit_empty_map()
        self.assertNotIn("src", drift["ownership_incomplete"])
        self.assertIn("scripts", drift["ownership_incomplete"])


class TestSubstrateIndexBuilder(unittest.TestCase):
    """PR 01-01: build_substrate_index() -- also previously unit-tested only
    via the subprocess-level test_integration.py::test_doorway_substrate_index_emission.
    This adds a direct-call check on the method itself."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.auditor = StructuralAuditor(
            workspace=self.tmp,
            ownership_file=self.tmp / "FOLDER_OWNERSHIP.md",
            breadcrumb_manager=None,
            integrity_manager=None,
            metrics={"created": 0, "ingested": 0, "repairs": 0},
            readme_exclude_dirs={"claude-commands"},
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_builds_expected_shape(self):
        current_map = {
            ".": {"has_readme": True, "files_count": 3, "py_files": [], "subdirs": ["src"],
                  "last_seen": "2026-07-06T00:00:00", "last_modified": "2026-07-06T00:00:00",
                  "content_hash": "abc"},
            "src": {"has_readme": False, "files_count": 1, "py_files": ["a.py"], "subdirs": [],
                    "last_seen": "2026-07-06T00:00:00", "last_modified": "2026-07-06T00:00:00",
                    "content_hash": "def"},
        }
        index = self.auditor.build_substrate_index(current_map)
        self.assertEqual(index["schema_version"], "1.0")
        self.assertIn("directories", index)
        self.assertEqual(index["directories"]["."]["owner_ref"], "FOLDER_OWNERSHIP:.")
        self.assertIn("FILES:3", index["directories"]["."]["breadcrumb_summary"])
        self.assertEqual(index["excluded_dirs"], ["claude-commands"])
        self.assertEqual(index["metrics"]["total_dirs"], 2)
        self.assertEqual(index["metrics"]["ingested_readmes"], 1)


if __name__ == "__main__":
    unittest.main()
