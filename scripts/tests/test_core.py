import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.console import out
from core.manifest import get_language, get_verification_gate
from core.filesystem import is_shim_file, walk_project
from core.import_patterns import path_to_import_patterns
from core.shim_templates import make_shim, make_reverse_shim

class TestRefactorCore(unittest.TestCase):

    def test_console_out(self):
        # Basic smoke test for console output
        try:
            out("✅", "Test console output")
        except Exception as e:
            self.fail(f"console.out raised {type(e).__name__} unexpectedly!")

    def test_manifest_getters(self):
        manifest = {
            "language": "javascript",
            "verification_gate": "npm test"
        }
        self.assertEqual(get_language(manifest), "javascript")
        self.assertEqual(get_verification_gate(manifest), "npm test")
        
        # Test defaults
        self.assertEqual(get_language({}), "python")
        self.assertEqual(get_verification_gate({}), "")
        
        # Test placeholder stripping
        self.assertEqual(get_verification_gate({"verification_gate": "# TODO: test"}), "")

    def test_import_patterns_python(self):
        patterns = path_to_import_patterns("foo/bar/baz.py", "python")
        self.assertIn("from foo.bar.baz", patterns)
        self.assertIn("import foo.bar.baz", patterns)
        self.assertIn("from foo.bar", patterns)
        # The bare root module is deliberately NOT generated when the path has
        # more than one segment — see import_patterns.py:31 ("Skip the root
        # module to avoid massive false positives"). Grepping `import foo` for a
        # moved file under package `foo/` would match every file in the project.
        self.assertNotIn("import foo", patterns)
        self.assertNotIn("from foo", patterns)

    def test_import_patterns_javascript(self):
        patterns = path_to_import_patterns("src/utils.ts", "javascript")
        self.assertIn("from 'src/utils'", patterns)
        self.assertIn('from "src/utils"', patterns)
        self.assertIn("require('src/utils')", patterns)
        self.assertIn("from 'src/utils.ts'", patterns)

    def test_shim_templates_python(self):
        shim = make_shim("python", "src/old.py", "src/new.py")
        self.assertIn("from src.old import *", shim)
        self.assertIn("⚠️ SHIM FILE", shim)
        
        rev = make_reverse_shim("python", "src/old.py", "src/new.py")
        self.assertIn("from src.new import *", rev)
        self.assertIn("⚠️ REVERSE SHIM", rev)

    def test_shim_templates_javascript_relative(self):
        # Test relative path calculation for JS shims
        # Target: src/components/Button.js
        # Source: src/legacy/Button.js
        # Import should be: ../legacy/Button
        target = "src/components/Button.js"
        source = "src/legacy/Button.js"
        
        shim = make_shim("javascript", source, target)
        self.assertIn("export * from '../legacy/Button';", shim)
        self.assertIn("⚠️ SHIM FILE", shim)

    def test_filesystem_is_shim(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("# ⚠️ SHIM FILE\nimport sys")
            temp_path = f.name
        
        try:
            self.assertTrue(is_shim_file(Path(temp_path)))
            
            with open(temp_path, 'w') as f:
                f.write("import sys")
            self.assertFalse(is_shim_file(Path(temp_path)))
        finally:
            os.remove(temp_path)

    def test_walk_project(self):
        # Test skip logic in walk_project
        tmpdir = tempfile.mkdtemp()
        try:
            Path(tmpdir, "src").mkdir()
            Path(tmpdir, "node_modules").mkdir()
            Path(tmpdir, "src/index.py").touch()
            Path(tmpdir, "node_modules/bad.py").touch()
            
            found_files = []
            for dp, dn, fn in walk_project(Path(tmpdir)):
                found_files.extend(fn)
            
            self.assertIn("index.py", found_files)
            self.assertNotIn("bad.py", found_files)
        finally:
            shutil.rmtree(tmpdir)

if __name__ == '__main__':
    unittest.main()
