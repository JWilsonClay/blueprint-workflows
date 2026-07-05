import unittest
import subprocess
import tempfile
import shutil
import io
import contextlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from workstream.verify import (
    run_cmd,
    _line_count_violations,
    _filter_out,
    mode_preflight,
    mode_diff_oracle,
    mode_dependency,
    mode_callers,
)


class TestRunCmd(unittest.TestCase):
    def test_run_cmd_real_no_shell(self):
        """Live subprocess call (not mocked) proves argv execution genuinely works."""
        stdout, stderr, rc = run_cmd(["echo", "hello"])
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "hello")

    @patch('subprocess.run')
    def test_run_cmd_passes_shell_false(self, mock_run):
        """CWE-78 regression test: run_cmd must never invoke a shell."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_cmd(["git", "status"], cwd="/tmp")
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0], ["git", "status"])
        self.assertFalse(kwargs.get("shell"))


class TestLineCountViolations(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detects_files_over_limit(self):
        (self.root / "big.py").write_text("\n".join(f"line {i}" for i in range(10)))
        (self.root / "small.py").write_text("line 1\n")

        results = _line_count_violations(self.root, "*.py", limit=5)
        names = [name for _, name in results]
        self.assertIn("big.py", names)
        self.assertNotIn("small.py", names)

    def test_excludes_node_modules_and_similar_dirs(self):
        excluded = self.root / "node_modules" / "pkg"
        excluded.mkdir(parents=True)
        (excluded / "big.js").write_text("\n".join(str(i) for i in range(50)))

        results = _line_count_violations(self.root, "*.js", limit=5)
        self.assertEqual(results, [])

    def test_caps_at_20_and_sorts_descending(self):
        for i in range(25):
            (self.root / f"f{i}.py").write_text("\n".join(str(n) for n in range(i + 10)))

        results = _line_count_violations(self.root, "*.py", limit=5)
        self.assertLessEqual(len(results), 20)
        locs = [loc for loc, _ in results]
        self.assertEqual(locs, sorted(locs, reverse=True))

    def test_skips_files_over_size_bound(self):
        """CWE-400 regression test: a file over the size bound is skipped
        entirely (never counted as a violation), regardless of line count."""
        import workstream.verify as verify_module
        big = self.root / "big.py"
        big.write_text("x\n" * 100)  # well over the line limit, small on disk

        original_bound = verify_module._LINE_COUNT_MAX_BYTES
        verify_module._LINE_COUNT_MAX_BYTES = 10  # shrink well below big.py's real size
        try:
            results = _line_count_violations(self.root, "*.py", limit=1)
        finally:
            verify_module._LINE_COUNT_MAX_BYTES = original_bound
        self.assertEqual(results, [])


class TestFilterOut(unittest.TestCase):
    def test_filters_multiple_excludes(self):
        lines = ["src/a.py:1:import x", "node_modules/b.js:1:x", "vendor/target/c:1:x"]
        result = _filter_out(lines, "node_modules", "target/")
        self.assertEqual(result, ["src/a.py:1:import x"])


class GitFixtureTestCase(unittest.TestCase):
    """Real git repo fixture — mirrors test_integration.py's setUp pattern."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        subprocess.run(["git", "init"], cwd=str(self.root), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"],
                        cwd=str(self.root), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"],
                        cwd=str(self.root), capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _commit(self, message="initial"):
        subprocess.run(["git", "add", "."], cwd=str(self.root), capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=str(self.root), capture_output=True)


class TestModePreflight(GitFixtureTestCase):
    def test_clean_tree_proceeds(self):
        (self.root / "a.py").write_text("print(1)\n")
        self._commit()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mode_preflight(str(self.root), limit=125)
        self.assertEqual(rc, 0)
        self.assertIn("CLEAN", buf.getvalue())
        self.assertIn("DECISION: PROCEED", buf.getvalue())

    def test_detects_line_limit_violation(self):
        (self.root / "big.py").write_text("\n".join(f"x = {i}" for i in range(200)))
        self._commit()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mode_preflight(str(self.root), limit=10)
        self.assertIn("big.py", buf.getvalue())


class TestModeDiffOracle(GitFixtureTestCase):
    def test_handles_root_commit_fallback(self):
        """Root commit has no parent, so `<hash>^..HEAD` fails and must fall back
        to `<hash>..HEAD` — this is the `||` in the original shell command."""
        (self.root / "a.py").write_text("print(1)\n")
        self._commit("first")
        (self.root / "a.py").write_text("print(2)\n")
        self._commit("second")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mode_diff_oracle(str(self.root), since="1970-01-01")
        self.assertEqual(rc, 0)
        self.assertIn("a.py", buf.getvalue())

    def test_since_with_shell_metacharacters_does_not_crash_or_inject(self):
        """Regression test: --since previously reached a shell unsanitized
        (f'git log --oneline --since="{since}"'). Now passed as a single argv
        element, so it can never break out into shell execution."""
        (self.root / "a.py").write_text("print(1)\n")
        self._commit()
        canary = self.root / "canary.txt"

        malicious_since = '"; touch ' + str(canary) + ' ; echo "'
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mode_diff_oracle(str(self.root), since=malicious_since)

        self.assertEqual(rc, 0)
        self.assertFalse(canary.exists(), "since value must never reach a shell")


class TestModeDependency(GitFixtureTestCase):
    def test_finds_importer_and_excludes_node_modules(self):
        (self.root / "target.py").write_text("x = 1\n")
        (self.root / "caller.py").write_text("from target import x\n")
        excluded = self.root / "node_modules"
        excluded.mkdir()
        (excluded / "also_imports.py").write_text("from target import x\n")
        self._commit()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mode_dependency(str(self.root), ["target.py"])
        output = buf.getvalue()
        self.assertIn("caller.py", output)
        self.assertNotIn("also_imports.py", output)


class TestModeCallers(GitFixtureTestCase):
    def test_builds_caller_map(self):
        (self.root / "target.py").write_text("x = 1\n")
        (self.root / "caller.py").write_text("from target import x\n")
        (self.root / "target_spec.py").write_text("from target import x\n")
        self._commit()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mode_callers(str(self.root), "target.py")
        output = buf.getvalue()
        self.assertIn("caller.py", output)
        self.assertIn("target_spec.py", output)

    def test_does_not_drop_caller_whose_name_contains_target_basename(self):
        """Regression test: a caller file ending in the target's own basename
        (e.g. test_target.py against target target.py) must not be excluded —
        the exclusion is meant to drop the target's self-reference only, via
        an exact basename match, not a substring match across the whole line."""
        (self.root / "target.py").write_text("x = 1\n")
        (self.root / "test_target.py").write_text("from target import x\n")
        self._commit()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mode_callers(str(self.root), "target.py")
        output = buf.getvalue()
        self.assertIn("test_target.py", output)
        self.assertNotIn("No callers found", output)


if __name__ == '__main__':
    unittest.main()
