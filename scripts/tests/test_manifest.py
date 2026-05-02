import unittest
from pathlib import Path
import tempfile
import shutil
import yaml
from core.manifest import load_manifest, get_language, get_verification_gate

class TestManifest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_load_manifest_success(self):
        data = {"project_name": "test", "files": []}
        manifest_path = self.root / "REFACTOR_MANIFEST.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(data, f)
        
        loaded = load_manifest(self.root)
        self.assertEqual(loaded["project_name"], "test")

    def test_get_language_defaults(self):
        self.assertEqual(get_language({}), "python")
        self.assertEqual(get_language({"language": "javascript"}), "javascript")
        self.assertEqual(get_language({"language": "TBD"}), "python")

    def test_get_verification_gate_stripping(self):
        self.assertEqual(get_verification_gate({"verification_gate": "pytest"}), "pytest")
        self.assertEqual(get_verification_gate({"verification_gate": "# TODO: add test"}), "")
        self.assertEqual(get_verification_gate({"verification_gate": ""}), "")
        self.assertEqual(get_verification_gate({}), "")

if __name__ == '__main__':
    unittest.main()
