import os
import stat
import unittest
import tempfile
import shutil
from pathlib import Path

from engine_utils import safe_read, DEFAULT_MAX_BYTES, atomic_write, safe_mkdir, assert_within


class TestSafeRead(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_reads_normal_file(self):
        p = self.root / "a.txt"
        p.write_text("hello world")
        self.assertEqual(safe_read(p), "hello world")

    def test_missing_file_returns_empty(self):
        self.assertEqual(safe_read(self.root / "does_not_exist.txt"), "")

    def test_oversized_file_returns_empty_not_raises(self):
        p = self.root / "big.txt"
        p.write_text("x" * 100)
        self.assertEqual(safe_read(p, max_bytes=10), "")

    def test_custom_max_bytes_preserved_per_caller(self):
        p = self.root / "mid.txt"
        p.write_text("x" * 50)
        self.assertEqual(safe_read(p, max_bytes=10), "")
        self.assertEqual(safe_read(p, max_bytes=100), "x" * 50)

    def test_default_max_bytes_is_five_mb(self):
        self.assertEqual(DEFAULT_MAX_BYTES, 5 * 1024 * 1024)

    def test_undecodable_file_returns_empty(self):
        p = self.root / "binary.dat"
        p.write_bytes(b"\xff\xfe\x00\x01binary garbage \x80\x81")
        # Force a decode failure regardless of platform default encoding leniency.
        result = safe_read(p, encoding="ascii")
        self.assertEqual(result, "")

    def test_directory_path_returns_empty_not_raises(self):
        # A directory has no meaningful "read" — must degrade, not crash.
        self.assertEqual(safe_read(self.root), "")


class TestAtomicWrite(unittest.TestCase):
    """[ADDED 2026-07-07 — Sovereign Redesign Cluster Stage 5] Promoted from
    doorway/_utils.py at the point of a second consumer (scripts/plan/); see
    engine_utils.py's module docstring. Logic unchanged from the original."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_writes_new_file(self):
        p = self.root / "out.txt"
        atomic_write(p, "hello")
        self.assertEqual(p.read_text(), "hello")

    def test_overwrites_existing_file(self):
        p = self.root / "out.txt"
        p.write_text("old")
        atomic_write(p, "new")
        self.assertEqual(p.read_text(), "new")

    def test_creates_parent_directories(self):
        p = self.root / "a" / "b" / "out.txt"
        atomic_write(p, "nested")
        self.assertEqual(p.read_text(), "nested")

    def test_no_leftover_temp_files(self):
        p = self.root / "out.txt"
        atomic_write(p, "content")
        remaining = list(self.root.iterdir())
        self.assertEqual(remaining, [p])

    def test_sets_file_mode(self):
        p = self.root / "out.txt"
        atomic_write(p, "content", mode=0o600)
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)


class TestSafeMkdir(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_creates_directory_with_parents(self):
        p = self.root / "a" / "b" / "c"
        safe_mkdir(p)
        self.assertTrue(p.is_dir())

    def test_idempotent_on_existing_directory(self):
        p = self.root / "a"
        safe_mkdir(p)
        safe_mkdir(p)  # must not raise
        self.assertTrue(p.is_dir())

    def test_sets_directory_mode(self):
        p = self.root / "a"
        safe_mkdir(p, mode=0o700)
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o700)


class TestAssertWithin(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.workspace = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_path_inside_workspace_returns_resolved_path(self):
        target = self.workspace / "sub" / "file.txt"
        result = assert_within(target, self.workspace)
        self.assertEqual(result, target.resolve())

    def test_path_outside_workspace_raises(self):
        outside = self.workspace.parent / "elsewhere" / "file.txt"
        with self.assertRaises(ValueError):
            assert_within(outside, self.workspace)

    def test_traversal_attempt_raises(self):
        traversal = self.workspace / ".." / ".." / "etc" / "passwd"
        with self.assertRaises(ValueError):
            assert_within(traversal, self.workspace)


if __name__ == '__main__':
    unittest.main()
