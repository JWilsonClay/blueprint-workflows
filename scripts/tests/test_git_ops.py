import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from core.git_ops import run_cmd, run_gate

class TestGitOps(unittest.TestCase):
    @patch('subprocess.run')
    def test_run_cmd(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="success")
        res = run_cmd(["ls"], Path("/tmp"))
        mock_run.assert_called_once()
        self.assertEqual(res.returncode, 0)

    @patch('subprocess.run')
    def test_run_gate_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = run_gate("pytest", Path("/tmp"))
        self.assertTrue(res)

    @patch('subprocess.run')
    def test_run_gate_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        res = run_gate("pytest", Path("/tmp"))
        self.assertFalse(res)

if __name__ == '__main__':
    unittest.main()
