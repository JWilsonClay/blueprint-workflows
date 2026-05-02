import unittest
from pathlib import Path
import tempfile
import shutil
from core.filesystem import walk_project, is_shim_file, get_source_extensions

class TestFilesystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_walk_project_skips(self):
        (self.root / "src").mkdir()
        (self.root / ".git").mkdir()
        (self.root / "node_modules").mkdir()
        (self.root / "src/app.py").touch()
        (self.root / ".git/config").touch()
        (self.root / "node_modules/pkg.js").touch()
        
        files = []
        for dp, dn, fn in walk_project(self.root):
            for f in fn:
                files.append(f)
        
        self.assertIn("app.py", files)
        self.assertNotIn("config", files)
        self.assertNotIn("pkg.js", files)

    def test_is_shim_file(self):
        shim_p = self.root / "shim.py"
        shim_p.write_text("# ⚠️ SHIM FILE\npass")
        self.assertTrue(is_shim_file(shim_p))
        
        rev_p = self.root / "rev.py"
        rev_p.write_text("# ⚠️ REVERSE SHIM\npass")
        self.assertTrue(is_shim_file(rev_p))
        
        real_p = self.root / "real.py"
        real_p.write_text("import os")
        self.assertFalse(is_shim_file(real_p))

    def test_get_source_extensions(self):
        self.assertEqual(get_source_extensions("python"), {".py"})
        self.assertEqual(get_source_extensions("javascript"), {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"})

    def test_walk_performance(self):
        import time
        # Create 100 dummy files
        for i in range(100):
            (self.root / f"file_{i}.py").touch()
            
        start = time.time()
        count = 0
        for dp, dn, fn in walk_project(self.root):
            count += len(fn)
        end = time.time()
        
        self.assertGreaterEqual(count, 100)
        # Should be very fast (< 0.1s for 100 files)
        self.assertLess(end - start, 0.5)

if __name__ == '__main__':
    unittest.main()
