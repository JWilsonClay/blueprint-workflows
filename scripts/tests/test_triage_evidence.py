"""
test_triage_evidence.py — Test suite for scripts/triage/matrix_completeness.py

Covers: Trigger Matrix block-header extraction (plain names, flagged
variants like "--workstreams", annotated headers like "(audit trigger)" and
"**[INJECTED ...]**"), section-boundary scoping (text outside the Trigger
Matrix is never scanned), dedup of repeated block names, report
completeness set-difference, missing-file/missing-section degradation, and
the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from triage.matrix_completeness import check_report_completeness, extract_matrix_workflows


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_SAMPLE_TRIAGE_MD = """\
## PHASE 1 — TRIGGER EVALUATION

### Trigger Matrix

**`/harden`**
| Trigger | Priority |
|---|---|
| row | P1 |

**`/quality` (audit trigger)** **[INJECTED 2026-05-25]**
| Trigger | Priority |
|---|---|
| row | P3 |

**`/implementation-plan`** **[INJECTED 2026-05-23]**
| Trigger | Priority |
|---|---|
| row | P1 |

**`/implementation-plan --workstreams`** **[INJECTED 2026-05-23]**
| Trigger | Priority |
|---|---|
| row | P2 |

**`/focus-plan`**
| Trigger | Priority |
|---|---|
| row | P1 |

**`/focus-plan` (pre-build gate)**
| Trigger | Priority |
|---|---|
| row | P0 |

---

## PHASE 2 — THE TRIAGE REPORT

This section's own **`/not-a-real-row`** must NOT be extracted -- outside the Trigger Matrix.
"""


class TestExtractMatrixWorkflows(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.triage_md = self.tmp / "triage.md"
        _write(self.triage_md, _SAMPLE_TRIAGE_MD)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_extracts_plain_names(self):
        workflows = extract_matrix_workflows(str(self.triage_md))
        self.assertIn("/harden", workflows)

    def test_extracts_annotated_header_bare_name_only(self):
        workflows = extract_matrix_workflows(str(self.triage_md))
        self.assertIn("/quality", workflows)

    def test_extracts_flagged_variant_as_distinct_entry(self):
        workflows = extract_matrix_workflows(str(self.triage_md))
        self.assertIn("/implementation-plan", workflows)
        self.assertIn("/implementation-plan --workstreams", workflows)

    def test_dedups_repeated_bare_names_with_different_annotations(self):
        workflows = extract_matrix_workflows(str(self.triage_md))
        self.assertEqual(workflows.count("/focus-plan"), 1)

    def test_does_not_extract_outside_trigger_matrix_section(self):
        workflows = extract_matrix_workflows(str(self.triage_md))
        self.assertNotIn("/not-a-real-row", workflows)

    def test_missing_file_returns_empty(self):
        self.assertEqual(extract_matrix_workflows(str(self.tmp / "nope.md")), [])

    def test_file_with_no_trigger_matrix_section_returns_empty(self):
        f = self.tmp / "no_matrix.md"
        _write(f, "# Some file\n\nNo trigger matrix here.\n")
        self.assertEqual(extract_matrix_workflows(str(f)), [])

    def test_preserves_first_appearance_order(self):
        workflows = extract_matrix_workflows(str(self.triage_md))
        self.assertEqual(
            workflows,
            ["/harden", "/quality", "/implementation-plan",
             "/implementation-plan --workstreams", "/focus-plan"],
        )


class TestCheckReportCompleteness(unittest.TestCase):
    def test_all_present(self):
        result = check_report_completeness(
            ["/harden", "/quality"],
            "RECOMMENDATIONS: /harden\nNO ACTION NEEDED: /quality\n",
        )
        self.assertEqual(result.missing_from_report, [])
        self.assertEqual(result.present_in_report, ["/harden", "/quality"])

    def test_some_missing(self):
        result = check_report_completeness(
            ["/harden", "/quality", "/redteam"],
            "RECOMMENDATIONS: /harden\nNO ACTION NEEDED: /quality\n",
        )
        self.assertEqual(result.missing_from_report, ["/redteam"])

    def test_flagged_variant_distinct_from_bare_name(self):
        # The bare name appearing in the report does NOT satisfy the flagged
        # variant's own row -- they are different Trigger Matrix entries.
        result = check_report_completeness(
            ["/implementation-plan", "/implementation-plan --workstreams"],
            "NO ACTION NEEDED: /implementation-plan\n",
        )
        self.assertEqual(result.present_in_report, ["/implementation-plan"])
        self.assertEqual(result.missing_from_report, ["/implementation-plan --workstreams"])

    def test_empty_matrix_workflows_reports_nothing_missing(self):
        result = check_report_completeness([], "any report text")
        self.assertEqual(result.missing_from_report, [])
        self.assertEqual(result.matrix_workflows, [])


class TestReadOnlyInvariant(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.triage_md = self.tmp / "triage.md"
        _write(self.triage_md, _SAMPLE_TRIAGE_MD)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_writes_nothing(self):
        before = self._snapshot()
        workflows = extract_matrix_workflows(str(self.triage_md))
        check_report_completeness(workflows, "some report text")
        self.assertEqual(before, self._snapshot())


if __name__ == "__main__":
    unittest.main()
