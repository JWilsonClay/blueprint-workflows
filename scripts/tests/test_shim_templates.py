import unittest
from core.shim_templates import make_shim, make_reverse_shim

class TestShimTemplates(unittest.TestCase):
    def test_python_shim(self):
        content = make_shim("python", "old.py", "new.py")
        self.assertIn("from old import *", content)
        self.assertIn("⚠️ SHIM FILE", content)

    def test_javascript_shim_relative(self):
        # src/lib/old.js -> src/modules/new.js
        # import from ../lib/old
        content = make_shim("javascript", "src/lib/old.js", "src/modules/new.js")
        self.assertIn("export * from '../lib/old';", content)

    def test_python_reverse_shim(self):
        content = make_reverse_shim("python", "old.py", "new.py")
        self.assertIn("from new import *", content)
        self.assertIn("⚠️ REVERSE SHIM", content)

    def test_javascript_reverse_shim_relative(self):
        # src/old.js -> src/components/new.js
        # import from ./components/new
        content = make_reverse_shim("javascript", "src/old.js", "src/components/new.js")
        self.assertIn("export * from './components/new';", content)

if __name__ == '__main__':
    unittest.main()
