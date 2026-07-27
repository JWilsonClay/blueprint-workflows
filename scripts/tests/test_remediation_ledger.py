"""
test_remediation_ledger.py — Test suite for the Findings Ledger engine
(scripts/plan/findings.py + scripts/plan/remediation_ledger.py).

Covers: all four findings-item conventions present in the persisted audit
corpus, declared vs positional Finding IDs, the genuine-zero vs
no-findings-section distinction (the engine's single most important
correctness property), citation/code-span splitting, deduction formats,
latest-audit resolution, and CLI exit codes.

Origin: helpdesk-tickets/20260727_implementation-plan_workflow.md.
Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from plan.findings import parse_audit, resolve_latest_audit

_LEDGER_CLI = Path(__file__).resolve().parents[1] / "plan" / "remediation_ledger.py"


def _write(directory, name, content):
    path = Path(directory) / name
    path.write_text(content, encoding="utf-8")
    return path


class TempAuditCase(unittest.TestCase):
    """Base case providing a scratch directory for synthetic audit reports."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def parse(self, content, name="20260727-1200-proj.md"):
        return parse_audit(_write(self.tmp, name, content))


# --------------------------------------------------------------------------
# The four item conventions
# --------------------------------------------------------------------------

class ItemConventionTests(TempAuditCase):

    def test_list_convention_with_declared_ids(self):
        report = self.parse(
            "## Critical Weaknesses (no minimum, no maximum)\n\n"
            "1. CRIT-01 — **Receipt written to the wrong workspace** — "
            "`scripts/build/phase.py:75` — Impact: the engine never sees it. "
            "— Score deduction: 18 points.\n"
            "2. CRIT-02 — **Balance check never recalculated** — `book.xlsx` "
            "— Score deduction: 14 points.\n\n"
            "## Honest Assessment\nSomething.\n"
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["id_source"], "declared")
        self.assertEqual([f["id"] for f in report["findings"]], ["CRIT-01", "CRIT-02"])
        self.assertEqual(report["findings"][0]["claim"],
                         "Receipt written to the wrong workspace")
        self.assertEqual(report["findings"][0]["deduction"], 18)
        self.assertEqual(report["summary"]["total_deduction"], 32)

    def test_list_convention_without_ids_is_positional(self):
        report = self.parse(
            "## Critical Weaknesses\n\n"
            "1. **First problem** — `a.py:10` — Score deduction: 12 points.\n"
            "2. **Second problem** — `b.py` — Score deduction: 10 points.\n"
        )
        self.assertEqual(report["id_source"], "positional")
        self.assertEqual([f["id"] for f in report["findings"]], ["CRIT-01", "CRIT-02"])

    def test_sub_heading_convention(self):
        """`### W1 — claim (−12)` items, with detail lines folded in beneath."""
        report = self.parse(
            "## Critical Weaknesses (each deduction 7-15 points; total -23)\n\n"
            "### W1 - The mandated marker is rejected by its own linter. (-12)\n\n"
            "**Citations:** `CLAUDE.md:82`, `rules.py:39` mandate the marker.\n\n"
            "### W2 - The monitoring check false-fires on its own docs. (-11)\n\n"
            "**Citations:** `main.py` matches the substring anywhere.\n\n"
            "## Honest Assessment\nSomething.\n"
        )
        self.assertEqual(report["summary"]["critical"], 2)
        self.assertEqual(report["findings"][0]["claim"],
                         "The mandated marker is rejected by its own linter.")
        self.assertEqual(report["findings"][0]["deduction"], 12)
        self.assertEqual(report["findings"][1]["deduction"], 11)
        # Detail lines beneath a sub-heading are that finding's own, not siblings.
        self.assertIn("CLAUDE.md:82", report["findings"][0]["citations"])

    def test_sub_heading_convention_with_nested_detail_lists(self):
        """`- **Deduction:** 8 points` beneath a heading is detail, not a finding."""
        report = self.parse(
            "## Critical Weaknesses (Minimum 4 Required):\n\n"
            "### 1. Discarded Closing Quotes in Sentence Chunker (Robustness)\n"
            "- **Citation:** `utils/vtt.py` L51\n"
            "- **Description & Impact:** quotes are silently eaten.\n"
            "- **Deduction:** 8 points\n\n"
            "### 2. Fragile VTT Timestamp Stripping (Risk Management)\n"
            "- **Citation:** `utils/vtt.py` L57\n"
            "- **Deduction:** 7 points\n"
        )
        self.assertEqual(report["summary"]["critical"], 2)
        self.assertEqual(report["findings"][0]["deduction"], 8)
        self.assertEqual(report["findings"][1]["deduction"], 7)

    def test_labelled_paragraph_convention(self):
        """`**C1 — claim**` / `**CRITICAL WEAKNESS #1 — claim**` lines."""
        report = self.parse(
            "## CRITICAL WEAKNESSES (uncapped - 2 found)\n\n"
            "**C1 - The entire phase is an unwired island (Ghost Logic).**\n"
            "`grep` for importers returns nothing. **Deduction: 15.**\n\n"
            "**C2 - The DB is permanently empty in production.**\n"
            "Nothing bridges the pipeline. **Deduction: 12.**\n"
        )
        self.assertEqual(report["summary"]["critical"], 2)
        self.assertEqual(report["findings"][0]["deduction"], 15)
        self.assertIn("unwired island", report["findings"][0]["claim"])

    def test_labelled_convention_plain_weakness_prefix(self):
        report = self.parse(
            "Critical Weaknesses (Minimum 4 Required):\n"
            "---------------------------------------\n\n"
            "WEAKNESS 1 - Task 3B.9 Accepted With a Structurally Broken Prompt\n"
            "Details here. Score deduction: 15 points.\n\n"
            "WEAKNESS 2 - Second real problem\n"
            "More detail. Score deduction: 10 points.\n"
        )
        self.assertEqual(report["summary"]["critical"], 2)
        self.assertEqual(report["findings"][0]["deduction"], 15)


# --------------------------------------------------------------------------
# The load-bearing distinction
# --------------------------------------------------------------------------

class ZeroVersusMissingSectionTests(TempAuditCase):
    """
    A genuine zero and an unlocatable findings section must never be conflated.
    Collapsing the second into the first reports 'nothing to remediate' about a
    report full of Critical findings — Hallucinated Success in engine form.
    """

    def test_inline_zero_is_a_genuine_result(self):
        report = self.parse(
            "Critical Weaknesses: none found. This is a genuine zero, not an "
            "incomplete critique - the Coverage Ledger accounts for every file.\n\n"
            "Medium/Lesser Weaknesses (max 4)\n"
            "1. **Label no longer describes the cell** — `book.xlsx` "
            "— Score deduction: 6 points.\n"
        )
        self.assertEqual(report["status"], "ok")
        self.assertTrue(report["sections"]["critical"])
        self.assertEqual(report["summary"]["critical"], 0)
        self.assertEqual(report["summary"]["medium"], 1)

    def test_missing_section_is_a_parse_failure_not_a_zero(self):
        report = self.parse(
            "# Adversarial Audit Report\n\n"
            "**Comparative Score: 82/100**\n\n"
            "## Audit Findings\n"
            "- **Weakness 1**: Registry validation missing.\n"
            "- **Weakness 2**: Serialization fragility.\n\n"
            "## Recommendations\n- Inject a watchdog.\n"
        )
        self.assertEqual(report["status"], "no_findings_section")
        self.assertEqual(report["findings"], [])
        self.assertTrue(report["errors"])
        self.assertIn("NOT a zero-findings result", " ".join(report["errors"]))

    def test_unreadable_report(self):
        report = parse_audit(self.tmp / "does-not-exist.md")
        self.assertEqual(report["status"], "unreadable")
        self.assertTrue(report["errors"])

    def test_singular_weakness_line_is_not_mistaken_for_a_heading(self):
        """`**CRITICAL WEAKNESS #1 - ...**` is a finding, not a section heading."""
        report = self.parse(
            "## Critical Weaknesses\n\n"
            "**CRITICAL WEAKNESS #1 - tasks.md header contamination blocks "
            "Completion Marking.**\n"
            "Citation: `phase_status.py` output. Score deduction: 15 points.\n"
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["critical"], 1)
        self.assertIn("header contamination", report["findings"][0]["claim"])


# --------------------------------------------------------------------------
# Field extraction
# --------------------------------------------------------------------------

class FieldExtractionTests(TempAuditCase):

    def test_citations_are_split_from_code_spans_and_deduplicated(self):
        report = self.parse(
            "## Critical Weaknesses\n\n"
            "1. **Wrong path** — `tasks.md:311`, `tasks.md:311`, "
            "`scripts/build/x.py`, `None`, `wb.save()`, `FAIL` "
            "— Score deduction: 18 points.\n"
        )
        finding = report["findings"][0]
        self.assertEqual(finding["citations"], ["tasks.md:311", "scripts/build/x.py"])
        self.assertIn("None", finding["code_spans"])
        self.assertIn("wb.save()", finding["code_spans"])
        self.assertNotIn("FAIL", finding["citations"])

    def test_missing_deduction_is_none_not_zero(self):
        report = self.parse(
            "## Critical Weaknesses\n\n1. **Something wrong** — `a.py`\n"
        )
        self.assertIsNone(report["findings"][0]["deduction"])
        self.assertIsNone(report["summary"]["total_deduction"])

    def test_raw_preserves_the_finding_verbatim(self):
        report = self.parse(
            "## Critical Weaknesses\n\n"
            "1. **Short claim** — a much longer body with `a.py` detail "
            "— Score deduction: 11 points.\n"
        )
        self.assertIn("much longer body", report["findings"][0]["raw"])
        self.assertEqual(report["findings"][0]["claim"], "Short claim")

    def test_both_severities_enumerated_with_independent_numbering(self):
        report = self.parse(
            "## Critical Weaknesses\n\n"
            "1. **Crit one** — `a.py` — Score deduction: 15 points.\n\n"
            "## Medium/Lesser Weaknesses (max 4)\n\n"
            "1. **Med one** — `b.py` — Score deduction: 3 points.\n"
            "2. **Med two** — `c.py` — Score deduction: 4 points.\n"
        )
        self.assertEqual([f["id"] for f in report["findings"]],
                         ["CRIT-01", "MED-01", "MED-02"])
        self.assertEqual(report["summary"], {
            "critical": 1, "medium": 2, "total": 3, "total_deduction": 22,
        })


# --------------------------------------------------------------------------
# Audit resolution
# --------------------------------------------------------------------------

class ResolveLatestAuditTests(TempAuditCase):

    def test_resolves_most_recent_by_filename_timestamp(self):
        for name in ("20260726-0900-proj.md", "20260727-1215-proj.md",
                     "20260727-0905-proj.md"):
            _write(self.tmp, name, "x")
        resolved = resolve_latest_audit(Path("/some/where/proj"), audits_dir=self.tmp)
        self.assertEqual(resolved.name, "20260727-1215-proj.md")

    def test_workstream_audits_are_excluded(self):
        _write(self.tmp, "20260727-0900-proj.md", "x")
        _write(self.tmp, "20260727-2300-proj-workstreams.md", "x")
        resolved = resolve_latest_audit(Path("/some/where/proj"), audits_dir=self.tmp)
        self.assertEqual(resolved.name, "20260727-0900-proj.md")

    def test_other_workspaces_are_not_matched(self):
        _write(self.tmp, "20260727-0900-otherproj.md", "x")
        self.assertIsNone(
            resolve_latest_audit(Path("/some/where/proj"), audits_dir=self.tmp)
        )

    def test_missing_registry_directory_returns_none(self):
        self.assertIsNone(
            resolve_latest_audit(Path("/some/where/proj"),
                                 audits_dir=self.tmp / "nope")
        )


# --------------------------------------------------------------------------
# CLI contract
# --------------------------------------------------------------------------

class CliTests(TempAuditCase):

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_LEDGER_CLI), *args],
            capture_output=True, text=True,
        )

    def test_json_output_and_exit_zero(self):
        audit = _write(self.tmp, "20260727-1200-proj.md",
                       "## Critical Weaknesses\n\n"
                       "1. **A problem** — `a.py` — Score deduction: 12 points.\n")
        result = self._run("--audit", str(audit), "--output-json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["critical"], 1)

    def test_missing_findings_section_exits_two(self):
        audit = _write(self.tmp, "20260727-1200-proj.md",
                       "# Report\n\n## Audit Findings\n- Weakness 1: thing.\n")
        result = self._run("--audit", str(audit), "--quiet")
        self.assertEqual(result.returncode, 2)

    def test_nonexistent_audit_exits_one(self):
        result = self._run("--audit", str(self.tmp / "nope.md"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("not found", result.stderr)

    def test_unresolvable_workspace_audit_exits_one_and_refuses_to_infer(self):
        workspace = self.tmp / "proj"
        workspace.mkdir()
        result = self._run("--workspace", str(workspace),
                           "--audits-dir", str(self.tmp))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Do NOT proceed against an inferred audit", result.stderr)

    def test_audit_and_workspace_are_mutually_exclusive(self):
        result = self._run("--audit", "a.md", "--workspace", "/tmp")
        self.assertEqual(result.returncode, 2)  # argparse usage error

    def test_quiet_suppresses_human_output(self):
        audit = _write(self.tmp, "20260727-1200-proj.md",
                       "## Critical Weaknesses\n\n1. **A** — `a.py` — "
                       "Score deduction: 5 points.\n")
        result = self._run("--audit", str(audit), "--quiet")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
