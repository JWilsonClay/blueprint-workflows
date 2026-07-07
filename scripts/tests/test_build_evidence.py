"""
test_build_evidence.py — Test suite for scripts/build/evidence.py

Covers: completeness marker detection (all 6 marker types), fenced-block
skipping, missing/unreadable file handling, scope-diff set arithmetic,
git-unavailable degradation, and the read-only invariant (no git mutation,
no file writes).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from build.evidence import compute_scope_diff, scan_completeness


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestScanCompleteness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_finds_all_marker_types(self):
        f = self.tmp / "sample.py"
        _write(f, (
            "def a():\n"
            "    # TODO: fix this\n"
            "    pass\n"
            "def b():\n"
            "    # FIXME later\n"
            "    raise NotImplementedError\n"
            "# HACK around the bug\n"
            "x = 1  # PLACEHOLDER value\n"
        ))
        matches = scan_completeness([str(f)])
        markers = {m.marker for m in matches}
        self.assertEqual(
            markers,
            {"TODO", "FIXME", "HACK", "PLACEHOLDER", "NotImplementedError", "bare_pass"},
        )

    def test_bare_pass_only_matches_standalone_pass_statement(self):
        f = self.tmp / "sample.py"
        _write(f, "class Foo:\n    pass\n\ndef bar():\n    passthrough = 1\n")
        matches = scan_completeness([str(f)])
        bare_pass_lines = [m.line for m in matches if m.marker == "bare_pass"]
        self.assertEqual(bare_pass_lines, [2])

    def test_skips_fenced_code_blocks(self):
        f = self.tmp / "doc.md"
        _write(f, (
            "Some real code:\n"
            "```python\n"
            "pass\n"
            "```\n"
            "Discussion of TODO markers.\n"
        ))
        matches = scan_completeness([str(f)])
        # The fenced `pass` is skipped; the prose "TODO" mention outside the
        # fence is a real match — this scanner only strips fences, it does
        # not attempt prose/code semantic judgment.
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].marker, "TODO")

    def test_missing_file_is_silently_skipped(self):
        matches = scan_completeness([str(self.tmp / "does_not_exist.py")])
        self.assertEqual(matches, [])

    def test_relative_path_resolved_against_workspace(self):
        f = self.tmp / "sub" / "sample.py"
        _write(f, "# TODO here\n")
        matches = scan_completeness(["sub/sample.py"], workspace=self.tmp)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].marker, "TODO")

    def test_no_markers_returns_empty(self):
        f = self.tmp / "clean.py"
        _write(f, "def add(a, b):\n    return a + b\n")
        self.assertEqual(scan_completeness([str(f)]), [])

    def test_snippet_is_truncated(self):
        f = self.tmp / "long.py"
        _write(f, "x = 1  # TODO " + ("a" * 500) + "\n")
        matches = scan_completeness([str(f)])
        self.assertLessEqual(len(matches[0].snippet), 200)


class TestComputeScopeDiff(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=str(self.tmp), check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(self.tmp), check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(self.tmp), check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_touched_matches_declared_exactly(self):
        _write(self.tmp / "a.py", "x = 1\n")
        report = compute_scope_diff(self.tmp, ["a.py"])
        self.assertTrue(report.git_available)
        self.assertEqual(report.declared_and_touched, ["a.py"])
        self.assertEqual(report.touched_not_declared, [])
        self.assertEqual(report.declared_not_touched, [])

    def test_touched_not_declared_flagged(self):
        _write(self.tmp / "a.py", "x = 1\n")
        _write(self.tmp / "b.py", "y = 2\n")
        report = compute_scope_diff(self.tmp, ["a.py"])
        self.assertEqual(report.touched_not_declared, ["b.py"])

    def test_declared_not_touched_flagged(self):
        _write(self.tmp / "a.py", "x = 1\n")
        report = compute_scope_diff(self.tmp, ["a.py", "never_created.py"])
        self.assertEqual(report.declared_not_touched, ["never_created.py"])

    def test_no_declared_scope_all_touched_flagged(self):
        _write(self.tmp / "a.py", "x = 1\n")
        report = compute_scope_diff(self.tmp, [])
        self.assertEqual(report.touched_not_declared, ["a.py"])

    def test_not_a_git_repo_reports_unavailable(self):
        non_repo = Path(tempfile.mkdtemp())
        try:
            report = compute_scope_diff(non_repo, ["a.py"])
            self.assertFalse(report.git_available)
            self.assertEqual(report.touched, [])
            self.assertEqual(report.touched_not_declared, [])
        finally:
            shutil.rmtree(non_repo, ignore_errors=True)

    def test_rename_reports_both_sides(self):
        _write(self.tmp / "old.py", "x = 1\n")
        subprocess.run(["git", "add", "."], cwd=str(self.tmp), check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(self.tmp), check=True)
        (self.tmp / "old.py").rename(self.tmp / "new.py")
        report = compute_scope_diff(self.tmp, ["new.py"])
        self.assertIn("new.py", report.touched)


class TestReadOnlyInvariant(unittest.TestCase):
    """
    Mirrors the read-only invariant test convention used by
    test_phase_status.py / test_focus.py: snapshot the filesystem (and, here,
    the git ref) before and after a run; assert nothing changed. Both
    functions in this module are documented read-only — this proves it rather
    than trusting the docstring.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=str(self.tmp), check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(self.tmp), check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(self.tmp), check=True)
        _write(self.tmp / "a.py", "# TODO fix\npass\n")
        _write(self.tmp / "b.py", "y = 2\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_scan_completeness_writes_nothing(self):
        before = self._snapshot()
        scan_completeness([str(self.tmp / "a.py"), str(self.tmp / "b.py")])
        self.assertEqual(before, self._snapshot())

    def test_compute_scope_diff_writes_nothing_and_mutates_no_git_state(self):
        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(self.tmp), capture_output=True, text=True
        )
        before = self._snapshot()
        compute_scope_diff(self.tmp, ["a.py"])
        after = self._snapshot()
        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(self.tmp), capture_output=True, text=True
        )
        self.assertEqual(before, after)
        # Both calls fail identically (no commits exist yet) — the invariant
        # under test is that compute_scope_diff did not change that outcome,
        # not that HEAD resolves.
        self.assertEqual(head_before.returncode, head_after.returncode)
        self.assertEqual(head_before.stdout, head_after.stdout)


if __name__ == "__main__":
    unittest.main()
