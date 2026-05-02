import unittest
import subprocess
from pathlib import Path

class SmokeTest(unittest.TestCase):
    def setUp(self):
        self.scripts_dir = Path(__file__).parent.parent.resolve()
        self.scripts = [
            "refactor_scout.py",
            "refactor_bridge.py",
            "refactor_migrate.py",
            "refactor_audit.py",
            "refactor_clean.py",
            "refactor_diff.py"
        ]

    def test_help_messages(self):
        for script in self.scripts:
            with self.subTest(script=script):
                cmd = ["python3", str(self.scripts_dir / script), "--help"]
                res = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(res.returncode, 0)
                self.assertIn("usage:", res.stdout.lower())

if __name__ == '__main__':
    unittest.main()
