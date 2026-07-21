"""
test_gitignore.py — Test suite for the Sovereign Gitignore Seeder.

Covers the four ticket acceptance criteria
(20260612_gitignore-seeder_module.md §4.9):
  1. Idempotency      — two runs produce a byte-identical file, one managed block.
  2. Preservation     — existing user .gitignore entries are never touched.
  3. Path containment — dangerous targets (root, $HOME root, non-existent) refused.
  4. Detect-and-warn  — a planted ALREADY-TRACKED secret fires a warning.

Plus: create-when-absent, --report-only read-only invariant, the matcher subset,
and graceful behaviour in a non-git directory.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gitignore.config import BLOCK_END, BLOCK_START
from gitignore.matcher import find_tracked_secrets, pattern_matches
from gitignore.gitignore_seeder import GitignoreSeeder, assert_safe_target
from gitignore import gitignore_seeder


def _git(ws: Path, *args) -> None:
    subprocess.run(["git", "-C", str(ws), *args],
                   capture_output=True, check=True)


def _init_repo(ws: Path) -> None:
    _git(ws, "init", "-q")
    _git(ws, "config", "user.email", "test@example.com")
    _git(ws, "config", "user.name", "Test")


class TestSeedCreateAndIdempotency(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        self.gi = self.ws / ".gitignore"

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_creates_gitignore_when_absent(self):
        self.assertFalse(self.gi.exists())
        rep = GitignoreSeeder(self.ws).run()
        self.assertTrue(self.gi.exists())
        self.assertEqual(rep["block_action"], "created")
        self.assertTrue(rep["wrote"])
        text = self.gi.read_text()
        self.assertIn(BLOCK_START, text)
        self.assertIn(BLOCK_END, text)
        self.assertIn(".history/", text)
        self.assertIn(".env", text)

    def test_idempotent_byte_identical_single_block(self):
        GitignoreSeeder(self.ws).run()
        first = self.gi.read_text()
        rep2 = GitignoreSeeder(self.ws).run()
        second = self.gi.read_text()
        self.assertEqual(first, second)                       # byte-identical
        self.assertEqual(second.count(BLOCK_START), 1)        # no duplicate block
        self.assertEqual(second.count(BLOCK_END), 1)
        self.assertEqual(rep2["block_action"], "unchanged")
        self.assertFalse(rep2["wrote"])


class TestPreservation(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        self.gi = self.ws / ".gitignore"

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_user_entries_preserved(self):
        user = "# my personal ignores\nbespoke_dir/\nfoo.tmp\n"
        self.gi.write_text(user, encoding="utf-8")
        GitignoreSeeder(self.ws).run()
        text = self.gi.read_text()
        # Every original line survives, verbatim, ahead of the managed block.
        self.assertIn("# my personal ignores", text)
        self.assertIn("bespoke_dir/", text)
        self.assertIn("foo.tmp", text)
        self.assertLess(text.index("bespoke_dir/"), text.index(BLOCK_START))

    def test_content_outside_block_survives_rerun(self):
        GitignoreSeeder(self.ws).run()
        # Human appends a note BELOW the managed block.
        with open(self.gi, "a", encoding="utf-8") as f:
            f.write("# human-added trailing note\nlate_addition/\n")
        GitignoreSeeder(self.ws).run()
        text = self.gi.read_text()
        self.assertIn("# human-added trailing note", text)
        self.assertIn("late_addition/", text)
        self.assertEqual(text.count(BLOCK_START), 1)  # still no duplication


class TestPathContainment(unittest.TestCase):
    def test_refuses_filesystem_root(self):
        with self.assertRaises(ValueError):
            assert_safe_target(Path("/"))
        with self.assertRaises(ValueError):
            GitignoreSeeder("/")

    def test_refuses_home_root(self):
        with self.assertRaises(ValueError):
            assert_safe_target(Path.home())

    def test_refuses_nonexistent_path(self):
        missing = Path(tempfile.gettempdir()) / "no_such_seeder_ws_12345"
        with self.assertRaises(ValueError):
            GitignoreSeeder(missing)

    def test_accepts_real_subdirectory(self):
        ws = Path(tempfile.mkdtemp())
        try:
            assert_safe_target(ws)  # must NOT raise
            rep = GitignoreSeeder(ws).run()
            self.assertTrue(rep["wrote"])
        finally:
            shutil.rmtree(ws, ignore_errors=True)


class TestDetectAndWarn(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_warns_on_already_tracked_secret(self):
        _init_repo(self.ws)
        (self.ws / ".env").write_text("API_KEY=supersecret\n", encoding="utf-8")
        (self.ws / "id_rsa").write_text("PRIVATE KEY\n", encoding="utf-8")
        (self.ws / "app.py").write_text("print('hi')\n", encoding="utf-8")
        # Stage the secrets so git tracks them (the gap the warning is for).
        _git(self.ws, "add", ".env", "id_rsa", "app.py")

        rep = GitignoreSeeder(self.ws).run()
        self.assertTrue(rep["git_repo"])
        flagged = {h["path"] for h in rep["tracked_secrets"]}
        self.assertIn(".env", flagged)
        self.assertIn("id_rsa", flagged)
        self.assertNotIn("app.py", flagged)  # non-secret not flagged

    def test_no_warning_when_clean(self):
        _init_repo(self.ws)
        (self.ws / "app.py").write_text("print('hi')\n", encoding="utf-8")
        _git(self.ws, "add", "app.py")
        rep = GitignoreSeeder(self.ws).run()
        self.assertTrue(rep["git_repo"])
        self.assertEqual(rep["tracked_secrets"], [])

    def test_non_git_directory_skips_scan_gracefully(self):
        rep = GitignoreSeeder(self.ws).run()  # no git init
        self.assertFalse(rep["git_repo"])
        self.assertEqual(rep["tracked_secrets"], [])
        self.assertTrue(rep["wrote"])  # seeding still works without git


class TestReportOnly(unittest.TestCase):
    def test_report_only_writes_nothing(self):
        ws = Path(tempfile.mkdtemp())
        try:
            rep = GitignoreSeeder(ws, apply=False).run()
            self.assertFalse((ws / ".gitignore").exists())
            self.assertFalse(rep["wrote"])
            self.assertEqual(rep["block_action"], "created")  # what it WOULD do
        finally:
            shutil.rmtree(ws, ignore_errors=True)


class TestWorkspaceConfirmationGate(unittest.TestCase):
    """
    Defense-in-depth workspace-confirmation gate — resolves the follow-up (b)
    flagged in helpdesk-tickets/CLOSED_20260716_sentinel_workflow.md. An
    unconfirmed workspace is never written to; the agent-facing CLI *defaults* to
    unconfirmed; and the read-only secret scan still runs when unconfirmed (only
    the WRITE is gated, not the read).
    """

    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        self.gi = self.ws / ".gitignore"

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_class_unconfirmed_writes_nothing(self):
        rep = GitignoreSeeder(self.ws, confirmed=False).run()
        self.assertFalse(self.gi.exists())
        self.assertFalse(rep["wrote"])
        self.assertFalse(rep["confirmed"])
        self.assertEqual(rep["write_skipped_reason"], "workspace not confirmed")
        self.assertEqual(rep["block_action"], "created")  # what it WOULD do

    def test_class_default_is_confirmed(self):
        rep = GitignoreSeeder(self.ws).run()
        self.assertTrue(rep["confirmed"])
        self.assertTrue(rep["wrote"])
        self.assertTrue(self.gi.exists())

    def test_unconfirmed_still_runs_readonly_secret_scan(self):
        _init_repo(self.ws)
        (self.ws / ".env").write_text("API_KEY=supersecret\n", encoding="utf-8")
        _git(self.ws, "add", ".env")
        rep = GitignoreSeeder(self.ws, confirmed=False).run()
        self.assertFalse(self.gi.exists())               # no write
        self.assertFalse(rep["wrote"])
        self.assertTrue(rep["git_repo"])
        self.assertIn(".env", {h["path"] for h in rep["tracked_secrets"]})  # scan still ran

    def _run_cli(self, extra_args):
        argv = ["seeder.py", "--workspace", str(self.ws), "--quiet", "--output-json"] + extra_args
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            return gitignore_seeder.main()

    def test_cli_defaults_to_unconfirmed_no_write(self):
        rc = self._run_cli([])  # no --workspace-confirmed => fail safe
        self.assertEqual(rc, 0)
        self.assertFalse(self.gi.exists())

    def test_cli_writes_only_when_confirmed(self):
        rc = self._run_cli(["--workspace-confirmed"])
        self.assertEqual(rc, 0)
        self.assertTrue(self.gi.exists())


class TestMatcher(unittest.TestCase):
    def test_directory_pattern(self):
        self.assertTrue(pattern_matches("secrets/key.json", "secrets/"))
        self.assertTrue(pattern_matches("a/b/secrets/x", "secrets/"))
        self.assertTrue(pattern_matches(".aws/credentials", ".aws/"))
        self.assertFalse(pattern_matches("secrets", "secrets/"))  # file, not dir

    def test_basename_glob(self):
        self.assertTrue(pattern_matches(".env", ".env"))
        self.assertTrue(pattern_matches("config/.env", ".env"))
        self.assertTrue(pattern_matches(".env.production", ".env.*"))
        self.assertTrue(pattern_matches("server.key", "*.key"))
        self.assertTrue(pattern_matches("deep/id_rsa.pub", "id_rsa*"))
        self.assertTrue(pattern_matches("credentials-prod.json", "credentials*.json"))
        self.assertFalse(pattern_matches("readme.md", "*.key"))

    def test_find_tracked_secrets_first_pattern_wins(self):
        hits = find_tracked_secrets([".env", "main.py"], [".env", "*.key"])
        self.assertEqual(hits, [{"path": ".env", "pattern": ".env"}])


if __name__ == "__main__":
    unittest.main()
