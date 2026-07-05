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

    @patch('subprocess.run')
    def test_run_gate_uses_no_shell(self, mock_run):
        """CWE-78 regression test: run_gate must never invoke a shell."""
        mock_run.return_value = MagicMock(returncode=0)
        run_gate("npm test", Path("/tmp"))
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0], ["npm", "test"])
        self.assertFalse(kwargs.get("shell"))

    @patch('subprocess.run')
    def test_run_gate_sequential_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = run_gate("pytest && echo done", Path("/tmp"))
        self.assertTrue(res)
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_run_gate_short_circuits_on_first_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        res = run_gate("pytest && echo done", Path("/tmp"))
        self.assertFalse(res)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_gate_rejects_unsupported_shell_syntax(self, mock_run):
        bad_gates = [
            "pytest | tee out.log",
            "pytest > out.log",
            "pytest ; echo done",
            "echo `whoami`",
            "echo $HOME",
            "pytest &",
        ]
        for bad in bad_gates:
            with self.subTest(gate=bad):
                self.assertFalse(run_gate(bad, Path("/tmp")))
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_run_gate_rejects_empty_segment(self, mock_run):
        res = run_gate("pytest && ", Path("/tmp"))
        self.assertFalse(res)
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_run_gate_blocks_destructive_pattern(self, mock_run):
        res = run_gate("rm -rf /", Path("/tmp"))
        self.assertFalse(res)
        mock_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
