import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from core.git_ops import run_cmd, run_gate, auto_commit


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


class TestAutoCommit(unittest.TestCase):
    """Tests for auto_commit() — phase-boundary sealing utility."""

    def _make_proc(self, returncode=0, stdout="", stderr=""):
        m = MagicMock()
        m.returncode = returncode
        m.stdout = stdout
        m.stderr = stderr
        return m

    @patch('subprocess.run')
    def test_auto_commit_success(self, mock_run):
        """Happy path: repo detected, add succeeds, commit succeeds."""
        mock_run.side_effect = [
            self._make_proc(0, "true\n"),          # rev-parse --is-inside-work-tree
            self._make_proc(0),                     # git add -A
            self._make_proc(0, "[main abc1234]"),   # git commit
            self._make_proc(0, "abc1234\n"),        # rev-parse --short HEAD
            self._make_proc(0, "3 files changed"), # git diff --stat
        ]
        result = auto_commit(Path("/tmp"), "phase-1: test [ws]")
        self.assertTrue(result["success"])
        self.assertEqual(result["short_hash"], "abc1234")
        self.assertEqual(result["message"], "phase-1: test [ws]")
        self.assertIsNone(result["note"])
        self.assertIsNone(result["reason"])

    @patch('subprocess.run')
    def test_auto_commit_nothing_to_commit(self, mock_run):
        """Clean workspace: git commit exits 1 with 'nothing to commit' — not an error."""
        mock_run.side_effect = [
            self._make_proc(0, "true\n"),                        # rev-parse
            self._make_proc(0),                                   # git add -A
            self._make_proc(1, "nothing to commit, working tree clean"),  # git commit
        ]
        result = auto_commit(Path("/tmp"), "phase-2: boundary seal [ws]")
        self.assertTrue(result["success"])
        self.assertIsNone(result["short_hash"])
        self.assertEqual(result["note"], "nothing-to-commit")

    @patch('subprocess.run')
    def test_auto_commit_not_a_git_repo(self, mock_run):
        """Non-git directory: returns success=False with reason 'not-a-git-repo'."""
        mock_run.return_value = self._make_proc(128, stderr="not a git repository")
        result = auto_commit(Path("/tmp/not-a-repo"), "phase-3: seal [ws]")
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "not-a-git-repo")
        self.assertIsNone(result["short_hash"])

    @patch('subprocess.run')
    def test_auto_commit_git_add_failure(self, mock_run):
        """git add -A fails (e.g. permission error): returns success=False."""
        mock_run.side_effect = [
            self._make_proc(0, "true\n"),                    # rev-parse
            self._make_proc(1, stderr="permission denied"),  # git add -A fails
        ]
        result = auto_commit(Path("/tmp"), "phase-4: seal [ws]")
        self.assertFalse(result["success"])
        self.assertIn("permission denied", result["reason"])


if __name__ == '__main__':
    unittest.main()
