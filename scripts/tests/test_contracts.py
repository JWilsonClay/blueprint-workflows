import unittest
import core.console
import core.manifest
import core.filesystem
import core.git_ops
import core.import_patterns
import core.shim_templates

class TestContracts(unittest.TestCase):
    def test_console_contract(self):
        self.assertTrue(hasattr(core.console, 'out'))
        self.assertTrue(hasattr(core.console, 'fail'))
        self.assertTrue(hasattr(core.console, 'section_header'))
        self.assertTrue(hasattr(core.console, 'section_rule'))

    def test_manifest_contract(self):
        self.assertTrue(hasattr(core.manifest, 'load_manifest'))
        self.assertTrue(hasattr(core.manifest, 'get_language'))
        self.assertTrue(hasattr(core.manifest, 'get_verification_gate'))

    def test_filesystem_contract(self):
        self.assertTrue(hasattr(core.filesystem, 'walk_project'))
        self.assertTrue(hasattr(core.filesystem, 'is_shim_file'))
        self.assertTrue(hasattr(core.filesystem, 'get_source_extensions'))

    def test_git_ops_contract(self):
        self.assertTrue(hasattr(core.git_ops, 'run_cmd'))
        self.assertTrue(hasattr(core.git_ops, 'run_gate'))

    def test_import_patterns_contract(self):
        self.assertTrue(hasattr(core.import_patterns, 'path_to_import_patterns'))

    def test_shim_templates_contract(self):
        self.assertTrue(hasattr(core.shim_templates, 'make_shim'))
        self.assertTrue(hasattr(core.shim_templates, 'make_reverse_shim'))

if __name__ == '__main__':
    unittest.main()
