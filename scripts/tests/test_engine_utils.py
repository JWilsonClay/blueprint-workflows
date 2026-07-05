import unittest
import tempfile
import shutil
from pathlib import Path

from engine_utils import safe_read, DEFAULT_MAX_BYTES


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


if __name__ == '__main__':
    unittest.main()
