"""
test_quality.py — Test suite for the quality Process Auditor.

Covers: witness-ledger parsing/validation (incl. the [REVIEWED] marker and the
P3 trigger), chain-tag verification (VALID/MALFORMED/ABSENT), the mechanical
smell linter (and its one-directional contract: clean text => zero smells, which
is NOT a quality claim), the end-to-end report, and the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from quality.ledger_auditor import AUDIT_THRESHOLD, LedgerAuditor
from quality.quality_audit import QualityAuditor
from quality.smell_linter import SmellLinter
from quality.tag_verifier import TagVerifier

# MRC witness log: one valid line, one malformed line, a REVIEWED marker, then
# one more valid line after the marker.
_MRC_LOG = (
    "[2026-06-01 10:00] | type=Factual/Technical | level=Standard | findings=2 | agent=Opus 4.8 | target=x\n"
    "[2026-06-01 10:05] | type=Bad | level=Nope | findings=notanint | agent=Opus\n"
    "[REVIEWED 2026-06-01]\n"
    "[2026-06-02 09:00] | type=Analytical/Diagnostic | level=Maximum | findings=3 | agent=Opus 4.8 | target=y\n"
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _all_paths(root: Path) -> set:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


class TestLedgerAuditor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.log = self.tmp / "quality_witness.log"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_mrc_parsing(self):
        _write(self.log, _MRC_LOG)
        r = LedgerAuditor().audit(self.log)
        self.assertTrue(r["log_found"])
        self.assertEqual(r["total_entries"], 3)
        self.assertEqual(r["valid_entries"], 2)
        self.assertEqual(len(r["malformed_lines"]), 1)
        self.assertEqual(r["last_reviewed"], "2026-06-01")
        # Only the post-marker valid entry counts as unreviewed.
        self.assertEqual(r["unreviewed_entries"], 1)
        self.assertEqual(r["audit_trigger"], "NONE")

    def test_p3_trigger(self):
        line = "[2026-06-02 09:00] | type=Factual | level=Standard | findings=0 | agent=A | target=t\n"
        _write(self.log, line * AUDIT_THRESHOLD)
        r = LedgerAuditor().audit(self.log)
        self.assertEqual(r["unreviewed_entries"], AUDIT_THRESHOLD)
        self.assertEqual(r["audit_trigger"], "P3")

    def test_hash_style_reviewed_marker(self):
        # The '## REVIEWED' form documented in triage.md must reset the count too.
        log = (
            "[2026-06-02 09:00] | type=Factual | level=Standard | findings=1 | agent=A | target=t\n"
            "## REVIEWED 2026-06-02\n"
            "[2026-06-02 10:00] | type=Factual | level=Standard | findings=1 | agent=A | target=t\n"
        )
        _write(self.log, log)
        r = LedgerAuditor().audit(self.log)
        self.assertEqual(r["last_reviewed"], "2026-06-02")
        self.assertEqual(r["unreviewed_entries"], 1)

    def test_absent_log_graceful(self):
        r = LedgerAuditor().audit(self.tmp / "nope.log")
        self.assertFalse(r["log_found"])
        self.assertEqual(r["audit_trigger"], "NONE")


class TestTagVerifier(unittest.TestCase):
    def test_valid(self):
        text = "output\n[QUALITY: type=Factual | level=Maximum | critique_findings=3 | agent=Opus 4.8]"
        self.assertEqual(TagVerifier().verify_text(text)["status"], "VALID")

    def test_malformed_bad_level(self):
        text = "[QUALITY: type=Factual | level=Nope | critique_findings=3 | agent=Opus]"
        self.assertEqual(TagVerifier().verify_text(text)["status"], "MALFORMED")

    def test_malformed_missing_field(self):
        text = "[QUALITY: type=Factual | level=Maximum | agent=Opus]"
        self.assertEqual(TagVerifier().verify_text(text)["status"], "MALFORMED")

    def test_absent(self):
        self.assertEqual(TagVerifier().verify_text("no tag here")["status"], "ABSENT")

    def test_documentation_mention_is_not_a_tag(self):
        # A prose reference like [QUALITY: ...] with no key=value is documentation,
        # not an emitted tag — it must read as ABSENT, not MALFORMED.
        text = "The verifier extracts [QUALITY: ...] tags from any text."
        self.assertEqual(TagVerifier().verify_text(text)["status"], "ABSENT")


class TestSmellLinter(unittest.TestCase):
    def test_hedge(self):
        r = SmellLinter().scan("Well, it depends on your needs.")
        self.assertEqual(r["smell_total"], 1)

    def test_closing_pleasantry(self):
        r = SmellLinter().scan("Here is the answer.\n\nI hope this helps!")
        patterns = {s["pattern"] for s in r["smells"]}
        self.assertIn("closing_pleasantry", patterns)

    def test_filler_opener(self):
        r = SmellLinter().scan("Great question! The answer is 42.")
        patterns = {s["pattern"] for s in r["smells"]}
        self.assertIn("filler_opener", patterns)

    def test_truncation_unclosed_fence(self):
        r = SmellLinter().scan("Here is code:\n```python\nx = 1")
        patterns = {s["pattern"] for s in r["smells"]}
        self.assertIn("truncation", patterns)

    def test_truncation_no_terminal_punctuation(self):
        r = SmellLinter().scan("This sentence just stops")
        patterns = {s["pattern"] for s in r["smells"]}
        self.assertIn("truncation", patterns)

    def test_clean_text_is_zero_smells_not_a_quality_claim(self):
        # The one-directional contract: clean prose => zero smells. This asserts
        # the mechanical absence only; it is explicitly NOT a quality verdict.
        r = SmellLinter().scan("This is a complete, well-formed sentence.")
        self.assertEqual(r["smell_total"], 0)

    def test_markdown_table_end_not_flagged_as_truncation(self):
        r = SmellLinter().scan("| a | b |\n| 1 | 2 |")
        patterns = {s["pattern"] for s in r["smells"]}
        self.assertNotIn("truncation", patterns)


class TestQualityAuditor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / ".workflow_state" / "quality_witness.log", _MRC_LOG)
        self.scan = self.tmp / "output.md"
        _write(self.scan, "Well, it depends.\n\nThis sentence just stops")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_end_to_end(self):
        report = QualityAuditor(self.tmp, scan_file=self.scan).run()
        self.assertEqual(report["ledger"]["valid_entries"], 2)
        self.assertIsNotNone(report["scan"])
        self.assertGreater(report["scan"]["smells"]["smell_total"], 0)
        # A detected smell forces the advisory hint to REVIEW.
        self.assertEqual(report["summary"]["verdict_hint"], "REVIEW")
        # The advisory must loudly disclaim being a quality verdict (Mock Trap guard).
        self.assertIn("Mock Trap", report["summary"]["advisory"])

    def test_ledger_only_clean(self):
        clean_ws = Path(tempfile.mkdtemp())
        try:
            _write(clean_ws / ".workflow_state" / "quality_witness.log",
                   "[2026-06-02 09:00] | type=Factual | level=Standard | findings=1 | agent=A | target=t\n")
            report = QualityAuditor(clean_ws).run()
            self.assertIsNone(report["scan"])
            self.assertEqual(report["summary"]["verdict_hint"], "CLEAN")
        finally:
            shutil.rmtree(clean_ws, ignore_errors=True)

    def test_auditor_is_read_only(self):
        before = _all_paths(self.tmp)
        QualityAuditor(self.tmp, scan_file=self.scan).run()
        after = _all_paths(self.tmp)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
