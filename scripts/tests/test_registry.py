"""
test_registry.py — Test suite for the Suite Learning Registry engine.

Covers: event collection from tickets + .history ledgers, pattern/workflow/source
aggregation, registry-file creation (snapshot block + append-only event log),
idempotency (no duplicate events on re-run), reviewed-watermark delta + threshold
verdict, the --report-only read-only invariant, and graceful empty-workspace.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from registry.aggregator import aggregate, collect_events
from registry.registry import RegistryEngine

TICKET_A = "**Date**: 2026-01-01\nRoot cause: Ghost Logic detected.\n"
TICKET_B = "**Date**: 2026-01-02\nThis was a Mock Trap and also Ghost Logic.\n"
HISTORY = (
    "# .history ledger — foo.md\n\n"
    "## 2026-01-03 — Pruned dead feature (Ghost Logic)\n"
    "Why: it was Ghost Logic.\n\n"
    "## 2026-01-04 — Removed contradiction\n"
    "A Context Erosion issue.\n"
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _all_paths(root: Path) -> set:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


class TestAggregator(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        _write(self.ws / "helpdesk-tickets" / "20260101_alpha_workflow.md", TICKET_A)
        _write(self.ws / "helpdesk-tickets" / "20260102_beta_workflow.md", TICKET_B)
        _write(self.ws / ".history" / "foo.md.ledger.md", HISTORY)

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_collect_and_aggregate(self):
        events = collect_events(self.ws)
        self.assertEqual(len(events), 4)  # 2 tickets + 2 history sections
        agg = aggregate(events)
        self.assertEqual(agg["total_events"], 4)
        # Ghost Logic: ticket A + ticket B + history section 1 = 3
        self.assertEqual(agg["by_pattern"]["Ghost Logic"], 3)
        self.assertEqual(agg["by_pattern"]["Mock Trap"], 1)
        self.assertEqual(agg["by_pattern"]["Context Erosion"], 1)
        self.assertEqual(agg["by_source"]["ticket"], 2)
        self.assertEqual(agg["by_source"]["history"], 2)
        self.assertEqual(agg["by_workflow"].get("/alpha"), 1)
        self.assertEqual(agg["by_workflow"].get("/foo"), 2)  # both history sections

    def test_date_from_field(self):
        events = [e for e in collect_events(self.ws) if e.source == "ticket"]
        self.assertEqual(sorted(e.date for e in events), ["2026-01-01", "2026-01-02"])


class TestRegistryWrite(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        _write(self.ws / "helpdesk-tickets" / "20260101_alpha_workflow.md", TICKET_A)
        _write(self.ws / ".history" / "foo.md.ledger.md", HISTORY)
        self.rpath = self.ws / "manifest" / "CONTRADICTION_REGISTRY.md"

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_write_creates_registry(self):
        rep = RegistryEngine(self.ws, threshold=2).run()
        self.assertTrue(self.rpath.exists())
        text = self.rpath.read_text()
        self.assertIn("REGISTRY-SNAPSHOT-START", text)
        self.assertIn("Event Log (append-only)", text)
        self.assertEqual(rep["aggregate"]["total_events"], 3)  # 1 ticket + 2 history
        self.assertTrue(rep["wrote"])

    def test_idempotent_no_duplicate_events(self):
        RegistryEngine(self.ws, threshold=2).run()
        first = self.rpath.read_text()
        n_first = first.count("\n- ")
        RegistryEngine(self.ws, threshold=2).run()
        second = self.rpath.read_text()
        self.assertEqual(n_first, second.count("\n- "))  # no duplicated lines

    def test_preserves_user_content_outside_blocks(self):
        # A human note appended outside the managed snapshot must survive a re-run.
        RegistryEngine(self.ws, threshold=2).run()
        with open(self.rpath, "a", encoding="utf-8") as f:
            f.write("\n<!-- human note: investigate /foo -->\n")
        RegistryEngine(self.ws, threshold=2).run()
        self.assertIn("human note: investigate /foo", self.rpath.read_text())

    def test_threshold_verdict(self):
        self.assertEqual(RegistryEngine(self.ws, threshold=2, apply=False).run()["verdict"], "REVIEW")
        self.assertEqual(RegistryEngine(self.ws, threshold=99, apply=False).run()["verdict"], "NONE")

    def test_watermark_resets_unreviewed(self):
        RegistryEngine(self.ws, threshold=2).run()
        with open(self.rpath, "a", encoding="utf-8") as f:
            f.write("\n[REVIEWED 2026-12-31]\n")
        rep = RegistryEngine(self.ws, threshold=1, apply=False).run()
        self.assertEqual(rep["watermark"], "2026-12-31")
        self.assertEqual(rep["unreviewed"], 0)
        self.assertEqual(rep["verdict"], "NONE")

    def test_report_only_is_read_only(self):
        before = _all_paths(self.ws)
        RegistryEngine(self.ws, apply=False).run()
        self.assertEqual(before, _all_paths(self.ws))


class TestEmptyWorkspace(unittest.TestCase):
    def test_graceful(self):
        empty = Path(tempfile.mkdtemp())
        try:
            rep = RegistryEngine(empty, threshold=2).run()
            self.assertEqual(rep["aggregate"]["total_events"], 0)
            self.assertEqual(rep["verdict"], "NONE")
        finally:
            shutil.rmtree(empty, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
