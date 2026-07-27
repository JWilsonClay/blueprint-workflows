"""
test_defect_classes.py — Test suite for the Defect-Class Preflight engine
(scripts/plan/defect_classes.py).

Covers: registry integrity, signal matching per class, the deliberate
over-inclusion bias, project PROCESS_LEARNINGS.md loading, the preflight
report contract, and CLI behavior.

Origin: helpdesk-tickets/20260727_implementation-plan_workflow.md, Component 3.
Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from plan.defect_classes import (
    SUITE_DEFECT_CLASSES,
    load_project_lessons,
    match_finding,
    preflight,
)

_CLI = Path(__file__).resolve().parents[1] / "plan" / "defect_classes.py"


def _finding(claim, raw=None, citations=None, code_spans=None):
    return {
        "id": "CRIT-01",
        "severity": "critical",
        "claim": claim,
        "raw": raw if raw is not None else claim,
        "citations": citations or [],
        "code_spans": code_spans or [],
    }


def _ids(matches):
    return {m["id"] for m in matches}


class RegistryIntegrityTests(unittest.TestCase):

    def test_every_class_is_complete_and_traceable(self):
        for dc in SUITE_DEFECT_CLASSES:
            with self.subTest(defect_class=dc.get("id")):
                for field in ("id", "name", "origin", "signals", "counter_measure"):
                    self.assertIn(field, dc)
                    self.assertTrue(dc[field], f"{field} is empty")
                self.assertIsInstance(dc["signals"], list)
                # An unearned entry dilutes every match it participates in.
                self.assertTrue(
                    any(token in dc["origin"] for token in ("audits/", "STRICT RULE",
                                                            "CLOSED_", "vocabulary",
                                                            "/iterate-test")),
                    "origin must cite a ticket, rule, audit, or the failure vocabulary",
                )

    def test_class_ids_are_unique(self):
        ids = [dc["id"] for dc in SUITE_DEFECT_CLASSES]
        self.assertEqual(len(ids), len(set(ids)))


class MatchingTests(unittest.TestCase):

    def test_receipt_path_defect_is_matched(self):
        matches = match_finding(_finding(
            "False completion markers on Phase 29 and Phase 30",
            raw="the receipt-writing heredocs used inconsistent relative paths "
                "(`../.workflow_state/receipts/BUILD_RECEIPTS.md`) landing in the "
                "wrong workspace; phase_status.py returns receipt_status: not_found",
        ))
        self.assertIn("receipt-path-resolution", _ids(matches))

    def test_dual_check_defect_is_matched(self):
        matches = match_finding(_finding(
            "Phase marked complete without a matching receipt",
            raw="the phase was marked complete without the receipt half of the "
                "dual check ever confirming",
        ))
        self.assertIn("checkbox-without-receipt", _ids(matches))

    def test_claim_without_verification_is_matched(self):
        matches = match_finding(_finding(
            '"Verified Balance Check remains 0/PASS" claimed with no '
            "recalculation ever performed",
        ))
        self.assertIn("claim-without-verification", _ids(matches))

    def test_header_contamination_is_matched(self):
        matches = match_finding(_finding(
            "tasks.md header title contamination blocks Completion Marking",
            raw="headers carry inline bold status annotations that contaminate "
                "the title string used for exact-match comparison",
        ))
        self.assertIn("header-contamination", _ids(matches))

    def test_mock_trap_is_matched(self):
        matches = match_finding(_finding(
            "The entire phase is an unwired island (Ghost Logic)",
            raw="a stub stands in for the real implementation; nothing bridges "
                "the pipeline",
        ))
        self.assertIn("mock-trap", _ids(matches))

    def test_stale_derived_artifact_is_matched(self):
        matches = match_finding(_finding(
            "Client-facing inventory was never regenerated from the workbook",
            raw="file timestamps prove the sequence; the renderer consumes only "
                "the stale JSON",
        ))
        self.assertIn("stale-derived-artifact", _ids(matches))

    def test_unrelated_finding_matches_nothing(self):
        matches = match_finding(_finding(
            "Chart legend colours are hard to distinguish in greyscale print",
            raw="the palette lacks luminance separation for accessible printing",
        ))
        self.assertEqual(matches, [])

    def test_matches_expose_why_they_fired(self):
        matches = match_finding(_finding(
            "no recalculation was performed before the receipt claimed Verified",
        ))
        self.assertTrue(matches)
        for match in matches:
            self.assertTrue(match["matched_signals"])
            self.assertEqual(match["scope"], "suite")

    def test_citations_and_code_spans_participate_in_matching(self):
        matches = match_finding(_finding(
            "Something went wrong in the build",
            raw="Something went wrong in the build",
            citations=["../.workflow_state/receipts/BUILD_RECEIPTS.md"],
        ))
        self.assertIn("receipt-path-resolution", _ids(matches))


class ProjectLessonTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_absent_learnings_file_is_not_an_error(self):
        self.assertEqual(load_project_lessons(self.workspace), [])

    def test_none_workspace_is_not_an_error(self):
        self.assertEqual(load_project_lessons(None), [])

    def test_headings_become_project_scoped_classes(self):
        (self.workspace / "PROCESS_LEARNINGS.md").write_text(
            "# Process Learnings\n\n"
            "## Writing to the wrong file path bypasses the engine entirely\n"
            "Detail about the lesson.\n\n"
            "## Always recalculate before claiming verified\n"
            "More detail.\n",
            encoding="utf-8",
        )
        classes = load_project_lessons(self.workspace)
        self.assertEqual(len(classes), 2)
        for dc in classes:
            self.assertEqual(dc["scope"], "project")
            self.assertTrue(dc["id"].startswith("project:"))
            self.assertTrue(dc["signals"])

    def test_nested_learnings_location_is_found(self):
        nested = self.workspace / "process_learnings"
        nested.mkdir()
        (nested / "PROCESS_LEARNINGS.md").write_text(
            "## A lesson about receipt path resolution\nDetail.\n", encoding="utf-8",
        )
        self.assertEqual(len(load_project_lessons(self.workspace)), 1)

    def test_project_classes_participate_in_matching(self):
        (self.workspace / "PROCESS_LEARNINGS.md").write_text(
            "## Beware the frobnicator cascade in exports\nDetail.\n", encoding="utf-8",
        )
        project = load_project_lessons(self.workspace)
        matches = match_finding(
            _finding("The frobnicator cascade corrupted the export"),
            extra_classes=project,
        )
        self.assertTrue(any(m["scope"] == "project" for m in matches))


class PreflightReportTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _audit(self, content, name="20260727-1200-proj.md"):
        path = self.tmp / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_report_shape_and_counts(self):
        audit = self._audit(
            "## Critical Weaknesses\n\n"
            "1. **Receipt written via a relative ../ path to the wrong workspace** "
            "— `a.py` — Score deduction: 18 points.\n"
            "2. **Legend colours are hard to read in greyscale** — `b.py` "
            "— Score deduction: 3 points.\n"
        )
        report = preflight(audit)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["findings"], 2)
        self.assertEqual(report["summary"]["matched"], 1)
        self.assertEqual(report["summary"]["unmatched"], 1)
        self.assertEqual(report["findings"][0]["id"], "CRIT-01")

    def test_unparseable_audit_short_circuits_without_claiming_a_clean_pass(self):
        audit = self._audit("# Report\n\n## Audit Findings\n- Weakness 1: thing.\n")
        report = preflight(audit)
        self.assertEqual(report["status"], "no_findings_section")
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["summary"]["findings"], 0)
        self.assertTrue(report["errors"])


class CliTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_CLI), *args], capture_output=True, text=True,
        )

    def test_list_emits_the_registry(self):
        result = self._run("--list", "--output-json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload), len(SUITE_DEFECT_CLASSES))

    def test_audit_preflight_json(self):
        audit = self.tmp / "20260727-1200-proj.md"
        audit.write_text(
            "## Critical Weaknesses\n\n"
            "1. **Verified was claimed with no recalculation performed** — `a.py` "
            "— Score deduction: 14 points.\n",
            encoding="utf-8",
        )
        result = self._run("--audit", str(audit), "--output-json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["matched"], 1)

    def test_missing_audit_exits_one(self):
        result = self._run("--audit", str(self.tmp / "nope.md"))
        self.assertEqual(result.returncode, 1)

    def test_no_arguments_is_a_usage_error(self):
        result = self._run()
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
