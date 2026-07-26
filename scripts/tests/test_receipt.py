"""
test_receipt.py — Test suite for the Receipt Coverage engine.

Covers: receipt-block parsing (generic across Build/Harden/Docs formats),
per-phase Built/Validated matching, Hardened file-mention matching (incl. the
no-file-list-named honesty case), the PENDING-is-not-a-gap invariant
(/focus-plan v4's exact lesson, must not regress here), gap-percent
computation, receipt-file-absent vs. missing-entry distinction, the
Documented dimension's existence-only honesty, the quality_audit.py wiring,
graceful no-tasks.md handling, and the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from receipt.coverage import compute_coverage, parse_receipt_records, ReceiptRecord

TASKS_MD = """# Tasks

## Phase 1: Setup
- [x] create src/app.py
- [x] create src/utils.py

## Phase 2: Build feature
- [x] implement feature in src/feature.py

## Phase 3: Future work
- [ ] not started yet
"""

BUILD_RECEIPTS = """## 2026-01-01 — /execute-build — Phase 1: Setup
- Phase/Stage: Phase 1: Setup
- Grade/Status: PHASE COMPLETE
- Files: src/app.py, src/utils.py
- Commit: abc123
---
"""

HARDEN_GRADES = """## 2026-01-02 — /harden — src/app.py
- Phase/Stage: Security Hardening
- Grade/Status: DIAMOND
- Files: src/app.py
- Commit: abc123
---
"""

DOCS_RECEIPTS = """## 2026-01-03 — /document — DevJournal.md
- Phase/Stage: Journal Update
- Grade/Status: DOCUMENTED
- Files: DevJournal.md
- Commit: abc123
---
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestParseReceiptRecords(unittest.TestCase):
    def test_generic_across_receipt_types(self):
        # Same parser, same field vocabulary, regardless of what Phase/Stage
        # semantically means for that receipt type.
        build = parse_receipt_records(BUILD_RECEIPTS)
        harden = parse_receipt_records(HARDEN_GRADES)
        docs = parse_receipt_records(DOCS_RECEIPTS)
        self.assertEqual(len(build), 1)
        self.assertEqual(len(harden), 1)
        self.assertEqual(len(docs), 1)
        self.assertEqual(build[0].target, "Phase 1: Setup")
        self.assertEqual(harden[0].target, "Security Hardening")
        self.assertEqual(harden[0].files, "src/app.py")
        self.assertEqual(docs[0].target, "Journal Update")  # the fixed constant, confirmed

    def test_malformed_block_skipped_not_raised(self):
        malformed = "## 2026-01-01 — /x — y\n- Phase/Stage: incomplete block, no grade\n---\n"
        self.assertEqual(parse_receipt_records(malformed), [])

    def test_empty_text(self):
        self.assertEqual(parse_receipt_records(""), [])


class TestComputeCoverage(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        # Quality audit is exercised independently in TestQualityAuditWiring;
        # stub it here so these tests focus purely on receipt-coverage logic.
        self._qa_patch = mock.patch(
            "receipt.coverage._run_quality_audit",
            return_value={"available": True, "verdict_hint": "CLEAN"},
        )
        self._qa_patch.start()

    def tearDown(self):
        self._qa_patch.stop()
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_no_tasks_md_graceful(self):
        report = compute_coverage(self.ws)
        self.assertFalse(report["tasks_md_found"])
        self.assertIsNone(report["gap_percent"])
        self.assertEqual(report["phases"], [])

    def test_structure_recognized_and_note(self):
        # helpdesk-tickets/20260722_phase-status-empty-phases-contract: a tasks.md
        # that EXISTS but uses only unrecognized headers must not read as a clean
        # empty plan. gap_percent is None (as when absent), but structure_recognized
        # is False and a structure_note disambiguates it from the no-tasks.md case.
        _write(self.ws / "tasks.md", "## Scope\n- [ ] x\n\n## Milestone A\n- [ ] y\n")
        r = compute_coverage(self.ws)
        self.assertTrue(r["tasks_md_found"])
        self.assertFalse(r["structure_recognized"])
        self.assertIsNone(r["gap_percent"])
        self.assertIn("UNRECOGNIZED STRUCTURE", r["structure_note"])
        # Recognized: a real Phase header → recognized True, note cleared.
        _write(self.ws / "tasks.md", "## Phase 1: A\n- [x] a\n")
        r2 = compute_coverage(self.ws)
        self.assertTrue(r2["structure_recognized"])
        self.assertIsNone(r2["structure_note"])

    def test_pending_phase_is_not_a_gap(self):
        # The exact /focus-plan v4 lesson: not-yet-built must never be
        # checked against receipts as though it were a claimed-done gap.
        _write(self.ws / "tasks.md", TASKS_MD)
        report = compute_coverage(self.ws)
        phase3 = next(p for p in report["phases"] if p["title"] == "Phase 3: Future work")
        self.assertEqual(phase3["checkbox_status"], "not_started")
        self.assertEqual(phase3["built"], "not_applicable_pending")
        self.assertEqual(phase3["hardened"], "not_applicable_pending")

    def test_built_and_hardened_found_by_correct_key(self):
        _write(self.ws / "tasks.md", TASKS_MD)
        _write(self.ws / ".workflow_state/receipts/BUILD_RECEIPTS.md", BUILD_RECEIPTS)
        _write(self.ws / ".workflow_state/receipts/HARDEN_GRADES.md", HARDEN_GRADES)
        report = compute_coverage(self.ws)
        phase1 = next(p for p in report["phases"] if p["title"] == "Phase 1: Setup")
        self.assertEqual(phase1["built"], "found")       # matched by phase-name key
        self.assertEqual(phase1["hardened"], "found")    # matched by file-mention key, not phase name

    def test_missing_receipt_is_a_real_gap(self):
        _write(self.ws / "tasks.md", TASKS_MD)
        _write(self.ws / ".workflow_state/receipts/BUILD_RECEIPTS.md", BUILD_RECEIPTS)  # only Phase 1
        report = compute_coverage(self.ws)
        phase2 = next(p for p in report["phases"] if p["title"] == "Phase 2: Build feature")
        self.assertEqual(phase2["checkbox_status"], "complete")
        self.assertEqual(phase2["built"], "missing")  # complete but no receipt = real gap

    def test_hardened_unverifiable_when_phase_names_no_files(self):
        no_files_tasks = "## Phase 1: Setup\n- [x] do the thing\n"
        _write(self.ws / "tasks.md", no_files_tasks)
        _write(self.ws / ".workflow_state/receipts/HARDEN_GRADES.md", HARDEN_GRADES)
        report = compute_coverage(self.ws)
        phase1 = report["phases"][0]
        self.assertEqual(phase1["hardened"], "unverifiable_no_file_list")

    def test_receipts_file_absent_distinct_from_missing_entry(self):
        _write(self.ws / "tasks.md", TASKS_MD)
        # No BUILD_RECEIPTS.md at all — infrastructure absent, not a coverage gap.
        report = compute_coverage(self.ws)
        phase1 = next(p for p in report["phases"] if p["title"] == "Phase 1: Setup")
        self.assertEqual(phase1["built"], "receipts_file_absent")
        # Infrastructure-absent must not inflate the checkable-dimensions count
        # (distinct from "missing", which does count as a real, checkable gap).
        self.assertEqual(report["checkable_dimensions"], 0)

    def test_gap_percent_computation(self):
        _write(self.ws / "tasks.md", TASKS_MD)
        _write(self.ws / ".workflow_state/receipts/BUILD_RECEIPTS.md", BUILD_RECEIPTS)
        _write(self.ws / ".workflow_state/receipts/HARDEN_GRADES.md", HARDEN_GRADES)
        report = compute_coverage(self.ws)
        # Phase 1: built=found, hardened=found (2 covered). Phase 2: built=missing,
        # hardened=missing (2 gaps). Validation file absent entirely, excluded.
        self.assertEqual(report["checkable_dimensions"], 4)
        self.assertEqual(report["covered_dimensions"], 2)
        self.assertEqual(report["gap_percent"], 50.0)

    def test_gap_percent_none_when_nothing_checkable(self):
        only_pending = "## Phase 1: Not done\n- [ ] todo\n"
        _write(self.ws / "tasks.md", only_pending)
        report = compute_coverage(self.ws)
        self.assertIsNone(report["gap_percent"])

    def test_documented_dimension_is_existence_only_never_per_phase(self):
        _write(self.ws / "tasks.md", TASKS_MD)
        _write(self.ws / ".workflow_state/receipts/DOCS_RECEIPTS.md", DOCS_RECEIPTS)
        report = compute_coverage(self.ws)
        doc = report["documented_dimension"]
        self.assertTrue(doc["entries_present"])
        self.assertEqual(doc["entry_count"], 1)
        # No phase dict carries a "documented" key — never claimed as a per-phase match.
        for p in report["phases"]:
            self.assertNotIn("documented", p)

    def test_read_only_no_files_written(self):
        _write(self.ws / "tasks.md", TASKS_MD)
        _write(self.ws / ".workflow_state/receipts/BUILD_RECEIPTS.md", BUILD_RECEIPTS)
        before = {p: p.stat().st_mtime for p in self.ws.rglob("*") if p.is_file()}
        compute_coverage(self.ws)
        after = {p: p.stat().st_mtime for p in self.ws.rglob("*") if p.is_file()}
        self.assertEqual(before.keys(), after.keys())  # no new files
        self.assertEqual(before, after)                 # no files touched


class TestQualityAuditWiring(unittest.TestCase):
    def test_real_subprocess_call_against_this_suite(self):
        from receipt.coverage import _run_quality_audit
        result = _run_quality_audit(Path("/home/jwils/blueprint-workflows"))
        self.assertTrue(result["available"])
        self.assertIn(result["verdict_hint"], ("CLEAN", "REVIEW"))

    def test_missing_script_degrades_gracefully(self):
        from receipt import coverage
        with mock.patch.object(coverage, "QUALITY_AUDIT_PATH", Path("/nonexistent/quality_audit.py")):
            result = coverage._run_quality_audit(Path("/tmp"))
        self.assertFalse(result["available"])
        self.assertIsNone(result["verdict_hint"])


if __name__ == "__main__":
    unittest.main()
