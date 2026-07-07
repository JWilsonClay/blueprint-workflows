"""
test_sentinel_evidence.py — Test suite for scripts/sentinel/recommender_parity.py

Covers: triple extraction from recommender.py-shaped source (including the
duplicate-id case), routing-table row extraction (including backtick-
wrapped IDs and the parenthesized scan_failure marker), parity computation
in the clean case, and — critically — REGRESSION tests proving the checker
actually catches the two real, live defects found in this repo's own
sentinel.md during the honest-design pass (a missing table row for a
duplicate-emitting id, and an undocumented severity), plus the read-only
invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from sentinel.recommender_parity import (
    compute_parity,
    extract_recommender_triples,
    extract_routing_table,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_SAMPLE_RECOMMENDER_PY = '''
class Recommender:
    def recommend(self, drift):
        recs = []
        if drift.get("new"):
            recs.append({
                "id": "SEQ-SUBSTRATE-HEALTH",
                "workflow": "/investigate",
                "reason": "New directories detected.",
                "severity": "MEDIUM",
            })
        if drift.get("missing_readme"):
            recs.append({
                "id": "SEQ-SUBSTRATE-MAINTAIN",
                "workflow": "/document",
                "reason": "Missing READMEs.",
                "severity": "INFO",
            })
        tier1_issues = drift.get("stale_index")
        if tier1_issues:
            recs.append({
                "id": "SEQ-SUBSTRATE-HEALTH",
                "workflow": "/investigate",
                "reason": "Tier 1 index/ownership issue.",
                "severity": "MEDIUM",
            })
        return recs
'''

# Deliberately mirrors the REAL pre-fix sentinel.md defect: one row for
# SEQ-SUBSTRATE-HEALTH (only covers the "new dirs" condition, not the
# Tier-1 issues condition), and the table only documents HIGH/MEDIUM/LOW
# anywhere (INFO used by the engine is absent).
_SAMPLE_SENTINEL_MD_WITH_DEFECTS = """
### Step 2b — Routing Map Construction

| Doorway Protocol ID | Workflow Trigger | When to route |
|---------------------|-----------------|---------------|
| SEQ-SUBSTRATE-HEALTH | `/investigate` | New or deleted directories detected |
| SEQ-SUBSTRATE-MAINTAIN | `/document` | Missing READMEs found |
| `(scan_failure)` | `/helpdesk-tickets` | Doorway scan itself failed |
"""

# The corrected version: a second row is added so the table's row-count for
# SEQ-SUBSTRATE-HEALTH matches the engine's block-count (2), closing the
# undercount defect.
_SAMPLE_SENTINEL_MD_FIXED = """
### Step 2b — Routing Map Construction

| Doorway Protocol ID | Workflow Trigger | When to route |
|---------------------|-----------------|---------------|
| SEQ-SUBSTRATE-HEALTH | `/investigate` | New or deleted directories detected |
| SEQ-SUBSTRATE-HEALTH | `/investigate` | Tier-1 index/ownership issue detected |
| SEQ-SUBSTRATE-MAINTAIN | `/document` | Missing READMEs found |
| `(scan_failure)` | `/helpdesk-tickets` | Doorway scan itself failed |
"""


class TestExtractRecommenderTriples(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.recommender_py = self.tmp / "recommender.py"
        _write(self.recommender_py, _SAMPLE_RECOMMENDER_PY)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_extracts_all_three_blocks(self):
        triples = extract_recommender_triples(str(self.recommender_py))
        self.assertEqual(len(triples), 3)

    def test_duplicate_id_both_extracted(self):
        triples = extract_recommender_triples(str(self.recommender_py))
        health_triples = [t for t in triples if t.id == "SEQ-SUBSTRATE-HEALTH"]
        self.assertEqual(len(health_triples), 2)

    def test_severity_extracted_correctly(self):
        triples = extract_recommender_triples(str(self.recommender_py))
        maintain = next(t for t in triples if t.id == "SEQ-SUBSTRATE-MAINTAIN")
        self.assertEqual(maintain.severity, "INFO")

    def test_missing_file_returns_empty(self):
        self.assertEqual(extract_recommender_triples(str(self.tmp / "nope.py")), [])


class TestExtractRoutingTable(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_extracts_seq_rows(self):
        f = self.tmp / "sentinel.md"
        _write(f, _SAMPLE_SENTINEL_MD_WITH_DEFECTS)
        rows = extract_routing_table(str(f))
        ids = [r.id for r in rows]
        self.assertIn("SEQ-SUBSTRATE-HEALTH", ids)
        self.assertIn("SEQ-SUBSTRATE-MAINTAIN", ids)

    def test_extracts_parenthesized_scan_failure_row(self):
        f = self.tmp / "sentinel.md"
        _write(f, _SAMPLE_SENTINEL_MD_WITH_DEFECTS)
        rows = extract_routing_table(str(f))
        scan_failure = next(r for r in rows if r.id == "(scan_failure)")
        self.assertEqual(scan_failure.workflow, "/helpdesk-tickets")

    def test_skips_header_and_separator_rows(self):
        f = self.tmp / "sentinel.md"
        _write(f, _SAMPLE_SENTINEL_MD_WITH_DEFECTS)
        rows = extract_routing_table(str(f))
        ids = [r.id for r in rows]
        self.assertNotIn("Doorway Protocol ID", ids)

    def test_missing_file_returns_empty(self):
        self.assertEqual(extract_routing_table(str(self.tmp / "nope.md")), [])


class TestComputeParityRegressionOnRealDefects(unittest.TestCase):
    """
    These are regression tests, not just clean-input tests: they prove the
    checker actually catches the two real, live defects found in this
    repo's own sentinel.md during the Phase 5.2 honest-design pass.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.recommender_py = self.tmp / "recommender.py"
        _write(self.recommender_py, _SAMPLE_RECOMMENDER_PY)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_catches_undercounted_duplicate_id(self):
        sentinel_md = self.tmp / "sentinel_defective.md"
        _write(sentinel_md, _SAMPLE_SENTINEL_MD_WITH_DEFECTS)

        triples = extract_recommender_triples(str(self.recommender_py))
        table_rows = extract_routing_table(str(sentinel_md))
        result = compute_parity(triples, table_rows, {"HIGH", "MEDIUM", "LOW"})

        self.assertIn("SEQ-SUBSTRATE-HEALTH", result.undercounted_ids)

    def test_catches_undocumented_info_severity(self):
        sentinel_md = self.tmp / "sentinel_defective.md"
        _write(sentinel_md, _SAMPLE_SENTINEL_MD_WITH_DEFECTS)

        triples = extract_recommender_triples(str(self.recommender_py))
        table_rows = extract_routing_table(str(sentinel_md))
        result = compute_parity(triples, table_rows, {"HIGH", "MEDIUM", "LOW"})

        self.assertIn("INFO", result.undocumented_severities)

    def test_fixed_table_no_longer_undercounted(self):
        sentinel_md = self.tmp / "sentinel_fixed.md"
        _write(sentinel_md, _SAMPLE_SENTINEL_MD_FIXED)

        triples = extract_recommender_triples(str(self.recommender_py))
        table_rows = extract_routing_table(str(sentinel_md))
        result = compute_parity(triples, table_rows, {"HIGH", "MEDIUM", "LOW"})

        self.assertEqual(result.undercounted_ids, [])
        # INFO severity is still undocumented in the "fixed" fixture on
        # purpose -- this test isolates the undercount fix from the
        # severity-vocabulary fix, confirmed independently by the next test.

    def test_documented_severities_expanding_to_include_info_clears_it(self):
        sentinel_md = self.tmp / "sentinel_defective.md"
        _write(sentinel_md, _SAMPLE_SENTINEL_MD_WITH_DEFECTS)

        triples = extract_recommender_triples(str(self.recommender_py))
        table_rows = extract_routing_table(str(sentinel_md))
        result = compute_parity(triples, table_rows, {"HIGH", "MEDIUM", "LOW", "INFO"})

        self.assertEqual(result.undocumented_severities, [])

    def test_missing_from_table_when_id_entirely_absent(self):
        sentinel_md = self.tmp / "sentinel_missing_row.md"
        _write(sentinel_md, "| Doorway Protocol ID | Workflow Trigger | When |\n"
                            "|---|---|---|\n"
                            "| SEQ-SUBSTRATE-MAINTAIN | `/document` | x |\n")
        triples = extract_recommender_triples(str(self.recommender_py))
        table_rows = extract_routing_table(str(sentinel_md))
        result = compute_parity(triples, table_rows, {"HIGH", "MEDIUM", "LOW", "INFO"})

        self.assertIn("SEQ-SUBSTRATE-HEALTH", result.missing_from_table)


class TestReadOnlyInvariant(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.recommender_py = self.tmp / "recommender.py"
        self.sentinel_md = self.tmp / "sentinel.md"
        _write(self.recommender_py, _SAMPLE_RECOMMENDER_PY)
        _write(self.sentinel_md, _SAMPLE_SENTINEL_MD_WITH_DEFECTS)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_writes_nothing(self):
        before = self._snapshot()
        triples = extract_recommender_triples(str(self.recommender_py))
        table_rows = extract_routing_table(str(self.sentinel_md))
        compute_parity(triples, table_rows, {"HIGH", "MEDIUM", "LOW"})
        self.assertEqual(before, self._snapshot())


if __name__ == "__main__":
    unittest.main()
