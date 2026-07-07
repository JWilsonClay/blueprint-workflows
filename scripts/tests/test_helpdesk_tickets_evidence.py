"""
test_helpdesk_tickets_evidence.py — Test suite for scripts/helpdesk_tickets/

Covers: filename convention parsing (open/closed, malformed), ticket text
parsing (header fields, section presence, status), schema validation
(clean ticket, missing sections, invalid Root Cause Type, missing
Phylogeny Disposition, insufficient/unresolved citations, and — the
regression test — the STRICT RULE 12 Phylogeny/Status contradiction on a
ticket that claims REMEDIATED while still PENDING), duplicate detection,
staleness computation, and the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from helpdesk_tickets.duplicate_detector import find_open_tickets_for_workflow
from helpdesk_tickets.schema_validator import validate_ticket
from helpdesk_tickets.staleness import compute_staleness
from helpdesk_tickets.ticket_parser import parse_filename, parse_ticket


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sample_ticket(root_cause_type="STRUCTURAL", phylogeny="PENDING", status="OPEN",
                    citation_path="/tmp/does_not_matter.py", n_citations=2, sections="12345"):
    section_blocks = {
        "1": "## 1. Executive Summary\ntext",
        "2": "## 2. Root Cause Analysis: \"X\"\ntext",
        "3": "## 3. Forensic Evidence\n" + "\n".join(
            f"- [c{i}](file://{citation_path}#L1-L2)" for i in range(n_citations)
        ),
        "4": "## 4. Remediation: X\ntext",
        "5": "## 5. Recommendation to Senior Architect\ntext",
    }
    body = "\n\n".join(section_blocks[n] for n in sections)
    return f"""# Helpdesk Ticket: Sample

**To**: Senior Architect of Workflows
**From**: Test
**Date**: 2026-07-07
**Subject**: A sample failure
**Urgency**: MEDIUM
**Root Cause Type**: {root_cause_type}
**Phylogeny Disposition**: {phylogeny}

---

{body}

---
**Status**: **{status}**
**Verification**: N/A
"""


class TestParseFilename(unittest.TestCase):
    def test_open_ticket(self):
        info = parse_filename("20260707_focus-plan_workflow.md")
        self.assertFalse(info.closed)
        self.assertEqual(info.date, "20260707")
        self.assertEqual(info.workflow_name, "focus-plan")

    def test_closed_ticket(self):
        info = parse_filename("CLOSED_20260707_focus-plan_workflow.md")
        self.assertTrue(info.closed)

    def test_malformed_filename_returns_none(self):
        self.assertIsNone(parse_filename("not_a_ticket.md"))


class TestParseTicket(unittest.TestCase):
    def test_extracts_header_fields(self):
        fields = parse_ticket(_sample_ticket())
        self.assertEqual(fields.header_fields["Root Cause Type"], "STRUCTURAL")
        self.assertEqual(fields.header_fields["Phylogeny Disposition"], "PENDING")

    def test_extracts_all_sections_present(self):
        fields = parse_ticket(_sample_ticket())
        self.assertEqual(fields.sections_present, {"1", "2", "3", "4", "5"})

    def test_extracts_missing_sections(self):
        fields = parse_ticket(_sample_ticket(sections="123"))
        self.assertEqual(fields.sections_present, {"1", "2", "3"})

    def test_extracts_status(self):
        fields = parse_ticket(_sample_ticket(status="REMEDIATED (fixed it)"))
        self.assertEqual(fields.status, "REMEDIATED (fixed it)")


class TestValidateTicket(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.evidence_file = self.tmp / "evidence.py"
        _write(self.evidence_file, "\n".join(f"line{i}" for i in range(1, 10)))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_clean_ticket_no_issues(self):
        text = _sample_ticket(citation_path=str(self.evidence_file))
        fields = parse_ticket(text)
        result = validate_ticket(fields, "20260707_focus-plan_workflow.md", text)
        self.assertEqual(result.issues, [])

    def test_missing_sections_flagged(self):
        text = _sample_ticket(citation_path=str(self.evidence_file), sections="123")
        fields = parse_ticket(text)
        result = validate_ticket(fields, "20260707_focus-plan_workflow.md", text)
        self.assertIn("4", result.sections_missing)
        self.assertIn("5", result.sections_missing)

    def test_invalid_root_cause_type_flagged(self):
        text = _sample_ticket(citation_path=str(self.evidence_file), root_cause_type="VIBES")
        fields = parse_ticket(text)
        result = validate_ticket(fields, "20260707_focus-plan_workflow.md", text)
        self.assertFalse(result.root_cause_type_valid)

    def test_insufficient_citations_flagged(self):
        text = _sample_ticket(citation_path=str(self.evidence_file), n_citations=1)
        fields = parse_ticket(text)
        result = validate_ticket(fields, "20260707_focus-plan_workflow.md", text)
        self.assertTrue(any("citation" in i.lower() for i in result.issues))

    def test_unresolved_citation_flagged(self):
        text = _sample_ticket(citation_path="/nonexistent/path.py")
        fields = parse_ticket(text)
        result = validate_ticket(fields, "20260707_focus-plan_workflow.md", text)
        self.assertGreater(len(result.citation_findings), 0)

    def test_malformed_filename_flagged(self):
        text = _sample_ticket(citation_path=str(self.evidence_file))
        fields = parse_ticket(text)
        result = validate_ticket(fields, "not_a_valid_name.md", text)
        self.assertFalse(result.filename_valid)

    def test_phylogeny_status_contradiction_regression(self):
        """
        Regression test: a ticket claiming REMEDIATED while Phylogeny
        Disposition is still PENDING is a real, named contradiction
        (STRICT RULE 12) -- this proves the checker actually catches it.
        """
        text = _sample_ticket(
            citation_path=str(self.evidence_file), phylogeny="PENDING", status="REMEDIATED (done)"
        )
        fields = parse_ticket(text)
        result = validate_ticket(fields, "20260707_focus-plan_workflow.md", text)
        self.assertTrue(result.phylogeny_status_contradiction)

    def test_no_contradiction_when_phylogeny_resolved(self):
        text = _sample_ticket(
            citation_path=str(self.evidence_file), phylogeny="NO TRANSFER", status="REMEDIATED (done)"
        )
        fields = parse_ticket(text)
        result = validate_ticket(fields, "20260707_focus-plan_workflow.md", text)
        self.assertFalse(result.phylogeny_status_contradiction)


class TestDuplicateDetector(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_finds_open_ticket_for_same_workflow(self):
        _write(self.tmp / "20260701_focus-plan_workflow.md", "content")
        result = find_open_tickets_for_workflow(str(self.tmp), "focus-plan")
        self.assertIn("20260701_focus-plan_workflow.md", result.open_tickets_for_workflow)

    def test_ignores_closed_tickets(self):
        _write(self.tmp / "CLOSED_20260701_focus-plan_workflow.md", "content")
        result = find_open_tickets_for_workflow(str(self.tmp), "focus-plan")
        self.assertEqual(result.open_tickets_for_workflow, [])

    def test_no_match_for_different_workflow(self):
        _write(self.tmp / "20260701_triage_workflow.md", "content")
        result = find_open_tickets_for_workflow(str(self.tmp), "focus-plan")
        self.assertEqual(result.open_tickets_for_workflow, [])


class TestStaleness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_computes_days_open(self):
        _write(self.tmp / "20260601_focus-plan_workflow.md", "content")
        results = compute_staleness(str(self.tmp), today=date(2026, 7, 7))
        self.assertEqual(results[0].days_open, 36)

    def test_exceeds_threshold_flag(self):
        _write(self.tmp / "20260601_focus-plan_workflow.md", "content")
        results = compute_staleness(str(self.tmp), today=date(2026, 7, 7), threshold_days=14)
        self.assertTrue(results[0].exceeds_threshold)

    def test_within_threshold_not_flagged(self):
        _write(self.tmp / "20260707_focus-plan_workflow.md", "content")
        results = compute_staleness(str(self.tmp), today=date(2026, 7, 7), threshold_days=14)
        self.assertFalse(results[0].exceeds_threshold)

    def test_closed_tickets_excluded(self):
        _write(self.tmp / "CLOSED_20260101_focus-plan_workflow.md", "content")
        results = compute_staleness(str(self.tmp), today=date(2026, 7, 7))
        self.assertEqual(results, [])


class TestReadOnlyInvariant(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "20260701_focus-plan_workflow.md", _sample_ticket())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_writes_nothing(self):
        before = self._snapshot()
        text = _sample_ticket()
        fields = parse_ticket(text)
        validate_ticket(fields, "20260701_focus-plan_workflow.md", text)
        find_open_tickets_for_workflow(str(self.tmp), "focus-plan")
        compute_staleness(str(self.tmp))
        self.assertEqual(before, self._snapshot())


if __name__ == "__main__":
    unittest.main()
