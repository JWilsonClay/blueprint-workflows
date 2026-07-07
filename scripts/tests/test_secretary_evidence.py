"""
test_secretary_evidence.py — Test suite for scripts/secretary/

Covers: freshness mtime comparison, missing-file handling, last-dated-entry
extraction (both PROCESS_LEARNINGS.md and SESSION APPEND conventions,
including the "YYYY-MM-DD to YYYY-MM-DD" range-header case), retrospective
freshness, Retrospective Lag gap detection in both directions, receipt-family
presence, the CLI's `~`-expansion of --history-glob (a real defect caught
during this module's own live-run against this workspace — glob.glob() does
not expand `~` the way a shell would), and the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from secretary.freshness import check_freshness
from secretary.receipt_presence import check_receipt_family
from secretary.retrospective_check import (
    PROCESS_LEARNINGS_ENTRY_RE,
    SESSION_APPEND_RE,
    check_retrospective_freshness,
    compute_retrospective_lag,
    last_dated_entry,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestCheckFreshness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_missing_file_reports_not_exists(self):
        results = check_freshness([str(self.tmp / "nope.md")])
        self.assertFalse(results[0].exists)
        self.assertFalse(results[0].touched_since)

    def test_file_touched_today_by_default(self):
        f = self.tmp / "a.md"
        _write(f, "content")
        results = check_freshness([str(f)])
        self.assertTrue(results[0].exists)
        self.assertTrue(results[0].touched_since)

    def test_file_older_than_since_reports_stale(self):
        f = self.tmp / "a.md"
        _write(f, "content")
        future = datetime.now(timezone.utc) + timedelta(days=1)
        results = check_freshness([str(f)], since=future)
        self.assertFalse(results[0].touched_since)

    def test_since_as_bare_date_treated_as_midnight(self):
        f = self.tmp / "a.md"
        _write(f, "content")
        # mtime is "now" (today) -- since=today at midnight should still count as touched.
        results = check_freshness([str(f)], since=date.today())
        self.assertTrue(results[0].touched_since)

    def test_multiple_paths_reported_independently(self):
        f1 = self.tmp / "a.md"
        _write(f1, "x")
        results = check_freshness([str(f1), str(self.tmp / "missing.md")])
        self.assertTrue(results[0].exists)
        self.assertFalse(results[1].exists)


class TestLastDatedEntry(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_process_learnings_simple_date_header(self):
        f = self.tmp / "PROCESS_LEARNINGS.md"
        _write(f, "## 2026-07-01 — first\n## 2026-07-05 — second\n")
        result = last_dated_entry([str(f)], PROCESS_LEARNINGS_ENTRY_RE)
        self.assertEqual(result, date(2026, 7, 5))

    def test_process_learnings_range_header_uses_first_date(self):
        f = self.tmp / "PROCESS_LEARNINGS.md"
        _write(f, "## 2026-07-06 to 2026-07-07 — Recovery Cluster\n")
        result = last_dated_entry([str(f)], PROCESS_LEARNINGS_ENTRY_RE)
        self.assertEqual(result, date(2026, 7, 6))

    def test_takes_max_not_last_line(self):
        # Out-of-order entries -- max must win, not last-line.
        f = self.tmp / "PROCESS_LEARNINGS.md"
        _write(f, "## 2026-07-07 — later but written first\n## 2026-07-01 — earlier, written second\n")
        result = last_dated_entry([str(f)], PROCESS_LEARNINGS_ENTRY_RE)
        self.assertEqual(result, date(2026, 7, 7))

    def test_session_append_convention(self):
        f = self.tmp / "shard.md"
        _write(f, "## **[SESSION APPEND — 2026-07-04 — some note]**\n")
        result = last_dated_entry([str(f)], SESSION_APPEND_RE)
        self.assertEqual(result, date(2026, 7, 4))

    def test_multiple_files_max_across_all(self):
        f1 = self.tmp / "shard1.md"
        f2 = self.tmp / "shard2.md"
        _write(f1, "## **[SESSION APPEND — 2026-07-01 — old]**\n")
        _write(f2, "## **[SESSION APPEND — 2026-07-07 — new]**\n")
        result = last_dated_entry([str(f1), str(f2)], SESSION_APPEND_RE)
        self.assertEqual(result, date(2026, 7, 7))

    def test_no_matches_returns_none(self):
        f = self.tmp / "empty.md"
        _write(f, "no dates here\n")
        self.assertIsNone(last_dated_entry([str(f)], PROCESS_LEARNINGS_ENTRY_RE))

    def test_missing_file_skipped(self):
        self.assertIsNone(last_dated_entry([str(self.tmp / "nope.md")], PROCESS_LEARNINGS_ENTRY_RE))


class TestRetrospectiveFreshness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_matches_today(self):
        f = self.tmp / "PROCESS_LEARNINGS.md"
        today = date(2026, 7, 7)
        _write(f, f"## {today.isoformat()} — session\n")
        result = check_retrospective_freshness(str(f), today=today)
        self.assertTrue(result.matches_today)

    def test_does_not_match_today(self):
        f = self.tmp / "PROCESS_LEARNINGS.md"
        _write(f, "## 2026-07-01 — old session\n")
        result = check_retrospective_freshness(str(f), today=date(2026, 7, 7))
        self.assertFalse(result.matches_today)


class TestRetrospectiveLag(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_no_gap_when_consistent(self):
        shard = self.tmp / "shard.md"
        pl = self.tmp / "PROCESS_LEARNINGS.md"
        _write(shard, "## **[SESSION APPEND — 2026-07-05 — x]**\n")
        _write(pl, "## 2026-07-05 — retro\n")
        report = compute_retrospective_lag([str(shard)], str(pl))
        self.assertFalse(report.gap_detected)

    def test_gap_when_narrative_ahead(self):
        shard = self.tmp / "shard.md"
        pl = self.tmp / "PROCESS_LEARNINGS.md"
        _write(shard, "## **[SESSION APPEND — 2026-07-07 — x]**\n")
        _write(pl, "## 2026-07-04 — stale retro\n")
        report = compute_retrospective_lag([str(shard)], str(pl))
        self.assertTrue(report.gap_detected)

    def test_no_gap_when_process_learnings_ahead(self):
        # Not the failure mode this check guards against -- retrospective is
        # never "ahead" of the narrative in the sense that matters, but this
        # confirms the comparison direction is correct either way.
        shard = self.tmp / "shard.md"
        pl = self.tmp / "PROCESS_LEARNINGS.md"
        _write(shard, "## **[SESSION APPEND — 2026-07-01 — x]**\n")
        _write(pl, "## 2026-07-07 — retro\n")
        report = compute_retrospective_lag([str(shard)], str(pl))
        self.assertFalse(report.gap_detected)

    def test_no_narrative_entries_reports_no_gap(self):
        shard = self.tmp / "shard.md"
        pl = self.tmp / "PROCESS_LEARNINGS.md"
        _write(shard, "nothing dated here\n")
        _write(pl, "## 2026-07-07 — retro\n")
        report = compute_retrospective_lag([str(shard)], str(pl))
        self.assertFalse(report.gap_detected)

    def test_no_process_learnings_entries_reports_gap(self):
        shard = self.tmp / "shard.md"
        pl = self.tmp / "PROCESS_LEARNINGS.md"
        _write(shard, "## **[SESSION APPEND — 2026-07-07 — x]**\n")
        _write(pl, "nothing dated here\n")
        report = compute_retrospective_lag([str(shard)], str(pl))
        self.assertTrue(report.gap_detected)


class TestReceiptPresence(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_present_file_reports_tail(self):
        _write(self.tmp / "TRIAGE_RECEIPTS.md", "line1\nline2\nline3\nline4\nline5\nline6\n")
        results = check_receipt_family(str(self.tmp), ["TRIAGE_RECEIPTS.md"], tail_lines=3)
        self.assertTrue(results[0].present)
        self.assertEqual(results[0].last_lines, ["line4", "line5", "line6"])

    def test_absent_file_reports_absent(self):
        results = check_receipt_family(str(self.tmp), ["DESIGN_RECEIPTS.md"])
        self.assertFalse(results[0].present)
        self.assertEqual(results[0].last_lines, [])

    def test_multiple_filenames_independent(self):
        _write(self.tmp / "TRIAGE_RECEIPTS.md", "present\n")
        results = check_receipt_family(str(self.tmp), ["TRIAGE_RECEIPTS.md", "DESIGN_RECEIPTS.md"])
        self.assertTrue(results[0].present)
        self.assertFalse(results[1].present)


class TestReadOnlyInvariant(unittest.TestCase):
    """Mirrors the read-only invariant convention (test_phase_status.py, test_build_evidence.py)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "PROCESS_LEARNINGS.md", "## 2026-07-07 — session\n")
        _write(self.tmp / "shard.md", "## **[SESSION APPEND — 2026-07-07 — x]**\n")
        _write(self.tmp / "TRIAGE_RECEIPTS.md", "entry\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_all_functions_write_nothing(self):
        before = self._snapshot()
        check_freshness([str(self.tmp / "PROCESS_LEARNINGS.md")])
        check_retrospective_freshness(str(self.tmp / "PROCESS_LEARNINGS.md"))
        compute_retrospective_lag([str(self.tmp / "shard.md")], str(self.tmp / "PROCESS_LEARNINGS.md"))
        check_receipt_family(str(self.tmp), ["TRIAGE_RECEIPTS.md", "DESIGN_RECEIPTS.md"])
        self.assertEqual(before, self._snapshot())


class TestCliTildeExpansion(unittest.TestCase):
    """
    Regression test for a real defect caught during this module's live-run
    against this workspace: `glob.glob("~/foo/*.md")` returns [] because
    glob.glob() does not perform shell-style `~` expansion — only
    `os.path.expanduser()` does. The CLI's --history-glob handling must
    expanduser() each pattern before globbing, or a `~`-relative pattern
    silently finds nothing (a false "no narrative entries" rather than an
    error), which is exactly the false-negative shape this suite's read-only
    engines are held to avoid creating.
    """

    def setUp(self):
        self.fake_home = Path(tempfile.mkdtemp())
        self.history_dir = self.fake_home / "history"
        _write(self.history_dir / "shard.md", "## **[SESSION APPEND — 2026-07-07 — x]**\n")
        _write(self.fake_home / "PROCESS_LEARNINGS.md", "## 2026-07-07 — retro\n")
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(self.fake_home)

    def tearDown(self):
        if self._old_home is not None:
            os.environ["HOME"] = self._old_home
        shutil.rmtree(self.fake_home, ignore_errors=True)

    def test_tilde_pattern_expands_via_cli(self):
        here = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [
                sys.executable,
                str(here / "secretary" / "secretary_audit.py"),
                "--workspace", str(self.fake_home),
                "--process-learnings", "~/PROCESS_LEARNINGS.md",
                "--history-glob", "~/history/*.md",
                "--output-json",
            ],
            capture_output=True,
            text=True,
            env={**os.environ},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"narrative_latest_date": "2026-07-07"', result.stdout)
        self.assertIn('"gap_detected": false', result.stdout)


if __name__ == "__main__":
    unittest.main()
