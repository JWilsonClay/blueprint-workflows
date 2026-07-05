"""
test_ledger.py — Test suite for the Ledger Growth Monitor engine.

Covers: warn-mode threshold crossing (entries and bytes, independently),
shard-mode first-run creation, no-rollover-needed, quarter-boundary rollover,
within-quarter size-safety-valve rollover (letter suffixing), and that a
rollover never loses content (old shard's own text is preserved verbatim
plus one appended closing marker).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ledger.monitor import (
    check_shard, check_warn, quarter_label, _extract_placeholder, _next_same_quarter_label,
)
from ledger.config import load_config, DEFAULT_CONFIG


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


WARN_CFG = {
    "name": "suite_phylogeny",
    "mode": "warn",
    "path": "manifest/SUITE_PHYLOGENY.md",
    "entry_pattern": r"^## Lineage Entry",
    "warn_threshold_entries": 3,
    "warn_threshold_bytes": 1000,
}

SHARD_CFG = {
    "name": "workflow_manifest_narrative",
    "mode": "shard",
    "active_dir": "manifest/history",
    "shard_name_pattern": "WORKFLOW_MANIFEST_{quarter}.md",
    "entry_pattern": r"^## \*\*\[",
    "warn_threshold_entries": 3,
    "warn_threshold_bytes": 500,
}


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_missing_file_falls_back_to_default(self):
        self.assertEqual(load_config(self.root / "nope.toml"), DEFAULT_CONFIG)

    def test_malformed_file_falls_back_to_default_not_raises(self):
        """Regression test: a hand-edited config with a syntax error must
        degrade the same way a missing one does, not crash the monitor."""
        bad = self.root / "bad.toml"
        _write(bad, "this is not [ valid toml =")
        self.assertEqual(load_config(bad), DEFAULT_CONFIG)

    def test_valid_file_loads_real_content(self):
        good = self.root / "good.toml"
        _write(good, '[[ledgers]]\nname = "x"\nmode = "warn"\n')
        result = load_config(good)
        self.assertEqual(result["ledgers"][0]["name"], "x")


class TestQuarterHelpers(unittest.TestCase):
    def test_quarter_label(self):
        self.assertEqual(quarter_label(date(2026, 1, 15)), "2026-Q1")
        self.assertEqual(quarter_label(date(2026, 4, 1)), "2026-Q2")
        self.assertEqual(quarter_label(date(2026, 7, 4)), "2026-Q3")
        self.assertEqual(quarter_label(date(2026, 12, 31)), "2026-Q4")

    def test_extract_placeholder(self):
        pat = "WORKFLOW_MANIFEST_{quarter}.md"
        self.assertEqual(_extract_placeholder("WORKFLOW_MANIFEST_2026-Q3.md", pat), "2026-Q3")
        self.assertEqual(_extract_placeholder("WORKFLOW_MANIFEST_2026-Q3b.md", pat), "2026-Q3b")
        self.assertEqual(_extract_placeholder("nope.md", pat), "")

    def test_next_same_quarter_label(self):
        self.assertEqual(_next_same_quarter_label("2026-Q3", "2026-Q3"), "2026-Q3b")
        self.assertEqual(_next_same_quarter_label("2026-Q3b", "2026-Q3"), "2026-Q3c")
        self.assertEqual(_next_same_quarter_label("2026-Q3c", "2026-Q3"), "2026-Q3d")


class TestCheckWarn(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_under_threshold_no_warn(self):
        _write(self.ws / "manifest/SUITE_PHYLOGENY.md",
               "## Lineage Entry — one\nshort\n\n## Lineage Entry — two\nshort\n")
        status = check_warn(self.ws, WARN_CFG)
        self.assertEqual(status.entries, 2)
        self.assertFalse(status.warn)

    def test_entry_count_crosses_threshold(self):
        text = "".join(f"## Lineage Entry — {i}\nbody\n\n" for i in range(4))
        _write(self.ws / "manifest/SUITE_PHYLOGENY.md", text)
        status = check_warn(self.ws, WARN_CFG)
        self.assertEqual(status.entries, 4)
        self.assertTrue(status.warn)

    def test_byte_size_crosses_threshold_independent_of_entry_count(self):
        # Two entries, but padded past the 1000-byte threshold.
        text = "## Lineage Entry — one\n" + ("x" * 600) + "\n\n## Lineage Entry — two\n" + ("y" * 600)
        _write(self.ws / "manifest/SUITE_PHYLOGENY.md", text)
        status = check_warn(self.ws, WARN_CFG)
        self.assertEqual(status.entries, 2)  # below entry threshold
        self.assertTrue(status.warn)          # but over byte threshold

    def test_missing_file_is_zero_not_a_crash(self):
        status = check_warn(self.ws, WARN_CFG)
        self.assertEqual(status.entries, 0)
        self.assertEqual(status.bytes, 0)
        self.assertFalse(status.warn)

    def test_warn_mode_never_writes(self):
        text = "".join(f"## Lineage Entry — {i}\nbody\n\n" for i in range(5))
        path = self.ws / "manifest/SUITE_PHYLOGENY.md"
        _write(path, text)
        before = path.read_text(encoding="utf-8")
        check_warn(self.ws, WARN_CFG)
        after = path.read_text(encoding="utf-8")
        self.assertEqual(before, after)


class TestCheckShard(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_first_run_creates_current_quarter_shard(self):
        status = check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 4))
        self.assertTrue(status.rolled_over)
        self.assertIn("first run", status.rollover_reason)
        self.assertTrue(Path(status.active_file).name.endswith("2026-Q3.md"))
        self.assertTrue(Path(status.active_file).exists())

    def test_no_rollover_same_quarter_under_threshold(self):
        check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 4))
        shard = self.ws / "manifest/history/WORKFLOW_MANIFEST_2026-Q3.md"
        shard.write_text(shard.read_text(encoding="utf-8") + "## **[ENTRY ONE]**\nbody\n",
                          encoding="utf-8")
        status = check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 20))
        self.assertFalse(status.rolled_over)
        self.assertTrue(status.active_file.endswith("2026-Q3.md"))

    def test_quarter_change_triggers_rollover_and_preserves_old_content(self):
        check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 4))
        old_path = self.ws / "manifest/history/WORKFLOW_MANIFEST_2026-Q3.md"
        old_path.write_text(old_path.read_text(encoding="utf-8") + "## **[REAL ENTRY]**\nimportant content\n",
                            encoding="utf-8")
        original_text = old_path.read_text(encoding="utf-8")

        status = check_shard(self.ws, SHARD_CFG, today=date(2026, 10, 1))  # Q4

        self.assertTrue(status.rolled_over)
        self.assertIn("quarter changed", status.rollover_reason)
        self.assertTrue(Path(status.active_file).name.endswith("2026-Q4.md"))
        # old content preserved verbatim, plus exactly one appended closing marker
        old_after = old_path.read_text(encoding="utf-8")
        self.assertIn(original_text.strip(), old_after)
        self.assertIn("SHARD CLOSED", old_after)
        self.assertIn("2026-Q4", old_after)  # points at its successor
        # new shard points back at its predecessor
        new_text = Path(status.active_file).read_text(encoding="utf-8")
        self.assertIn("2026-Q3", new_text)

    def test_within_quarter_size_overflow_triggers_lettered_rollover(self):
        check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 4))
        old_path = self.ws / "manifest/history/WORKFLOW_MANIFEST_2026-Q3.md"
        # Pad past the 500-byte safety valve, same quarter.
        old_path.write_text(old_path.read_text(encoding="utf-8") + ("z" * 600), encoding="utf-8")

        status = check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 5))  # still Q3

        self.assertTrue(status.rolled_over)
        self.assertIn("size threshold", status.rollover_reason)
        self.assertTrue(Path(status.active_file).name.endswith("2026-Q3b.md"))

    def test_second_within_quarter_overflow_increments_letter(self):
        check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 4))
        first = self.ws / "manifest/history/WORKFLOW_MANIFEST_2026-Q3.md"
        first.write_text(first.read_text(encoding="utf-8") + ("z" * 600), encoding="utf-8")
        check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 5))  # -> Q3b

        second = self.ws / "manifest/history/WORKFLOW_MANIFEST_2026-Q3b.md"
        second.write_text(second.read_text(encoding="utf-8") + ("z" * 600), encoding="utf-8")
        status = check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 6))  # -> Q3c

        self.assertTrue(Path(status.active_file).name.endswith("2026-Q3c.md"))

    def test_shard_mode_never_deletes_a_prior_shard_file(self):
        check_shard(self.ws, SHARD_CFG, today=date(2026, 7, 4))
        check_shard(self.ws, SHARD_CFG, today=date(2026, 10, 1))
        hist_dir = self.ws / "manifest/history"
        names = {p.name for p in hist_dir.iterdir()}
        self.assertIn("WORKFLOW_MANIFEST_2026-Q3.md", names)
        self.assertIn("WORKFLOW_MANIFEST_2026-Q4.md", names)


if __name__ == "__main__":
    unittest.main()
