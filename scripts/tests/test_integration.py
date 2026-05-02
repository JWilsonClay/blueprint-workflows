import unittest
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import yaml

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.scripts_dir = Path(__file__).parent.parent.resolve()
        
        # Setup mock project
        (self.root / "src").mkdir()
        (self.root / "src/main.py").write_text("print('hello')")
        (self.root / "src/utils.py").write_text("def add(a, b): return a + b")
        
        # Initialize git
        subprocess.run(["git", "init"], cwd=str(self.root), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(self.root))
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(self.root))
        subprocess.run(["git", "add", "."], cwd=str(self.root))
        subprocess.run(["git", "commit", "-m", "initial"], cwd=str(self.root))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def run_script(self, script_name, args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.scripts_dir)
        cmd = ["python3", str(self.scripts_dir / script_name)] + args
        return subprocess.run(cmd, capture_output=True, text=True, env=env)

    def test_scout_and_bridge_flow(self):
        # 1. Run Scout
        res = self.run_script("refactor_scout.py", ["--project-root", str(self.root)])
        self.assertEqual(res.returncode, 0)
        
        manifest_path = self.root / "REFACTOR_MANIFEST.yaml"
        self.assertTrue(manifest_path.exists())
        
        # 2. Modify Manifest (MOVE src/utils.py to src/core/utils.py)
        with open(manifest_path, "r") as f:
            data = yaml.safe_load(f)
        
        for entry in data["files"]:
            if entry["current"] == "src/utils.py":
                entry["action"] = "MOVE"
                entry["target"] = "src/core/utils.py"
        
        with open(manifest_path, "w") as f:
            yaml.dump(data, f)
            
        # 3. Run Bridge
        res = self.run_script("refactor_bridge.py", ["--project-root", str(self.root)])
        self.assertEqual(res.returncode, 0)
        
        # 4. Verify Bridge Results
        target_path = self.root / "src/core/utils.py"
        self.assertTrue(target_path.exists())
        self.assertIn("⚠️ SHIM FILE", target_path.read_text())
        self.assertIn("from src.utils import *", target_path.read_text())

    def test_dry_run_safety(self):
        # 1. Run Scout
        self.run_script("refactor_scout.py", ["--project-root", str(self.root)])
        
        # 2. Modify Manifest
        manifest_path = self.root / "REFACTOR_MANIFEST.yaml"
        with open(manifest_path, "r") as f:
            data = yaml.safe_load(f)
        data["files"][0]["action"] = "MOVE"
        data["files"][0]["target"] = "src/core/moved.py"
        with open(manifest_path, "w") as f:
            yaml.dump(data, f)
            
        # 3. Run Bridge with --dry-run
        res = self.run_script("refactor_bridge.py", ["--project-root", str(self.root), "--dry-run"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("[DRY RUN]", res.stdout)
        
        # 4. Verify no files were created
        target_path = self.root / "src/core/moved.py"
        self.assertFalse(target_path.exists())

if __name__ == '__main__':
    unittest.main()
