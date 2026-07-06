import unittest
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import yaml
import json  # for substrate_index test (PR 01-01)
import re    # for robust json extraction from mixed stdout logs

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

    def test_doorway_substrate_index_emission(self):
        """Basic test for PR 01-01: substrate_index.json emission + CLI + JSON fields."""
        # Reuse self.root (minimal ws with py + git); doorway is workspace-agnostic.
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.scripts_dir)
        # Use -m to run as package (avoids direct-script sys.path[0]=doorway/ shadowing 'doorway' package import)
        cmd = [
            "python3", "-m", "doorway.doorway",
            "--workspace", str(self.root),
            "--output-json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0, f"doorway failed: {res.stderr}")
        # Parse emitted JSON (stdout may contain prior [ERROR]/[DOORWAY] logs; use regex for top-level object)
        m = re.search(r"(\{.*\})", res.stdout, re.DOTALL)
        payload = json.loads(m.group(1)) if m else json.loads(res.stdout)
        self.assertIn("substrate_index", payload)
        idx = payload["substrate_index"]
        self.assertEqual(idx.get("schema_version"), "1.0")
        self.assertIn("directories", idx)
        self.assertIn(".", idx["directories"])
        self.assertIn("owner_ref", idx["directories"]["."])
        self.assertIn("content_hash", idx["directories"]["."])
        self.assertTrue(idx.get("zero_finding_candidate") in (True, False))
        # Also verify .doorway/substrate_index.json was written (atomic)
        idx_file = self.root / ".doorway" / "substrate_index.json"
        self.assertTrue(idx_file.exists())
        with open(idx_file) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk.get("schema_version"), "1.0")
        # context-only path (minimal)
        cmd2 = cmd + ["--context-only"]
        res2 = subprocess.run(cmd2, capture_output=True, text=True, env=env)
        self.assertEqual(res2.returncode, 0)
        m2 = re.search(r"(\{.*\})", res2.stdout, re.DOTALL)
        p2 = json.loads(m2.group(1)) if m2 else json.loads(res2.stdout)
        self.assertIn("substrate_index", p2)
        self.assertNotIn("drift", p2)  # minimal omits full

if __name__ == '__main__':
    unittest.main()
