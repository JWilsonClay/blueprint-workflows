"""Temp-repo tests for the suite gate installer.

Fixture history uses --no-verify. The installer and the product commits do not.
"""

import io
import json
import os
import shutil
import stat
import subprocess
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from hooks import hook_text, install_gates
from hooks.install_gates import SUITE_ROOT, install, main


# Exact stdout. git 2.34.1 forwards pre-commit stdout onto the commit's stderr.
LOUD = (
    "SUITE GATES SKIPPED — SUITE_GATES_SKIP is set for this commit only. "
    "The length and complexity gates did not run. This value is not stored."
)
FAIL_PYTHON = "SUITE GATES FAILED CLOSED — python3 is not on PATH."
MARKER = "# suite-hook:set-hooks-path"

REPORT_KEYS = (
    "loc_action",
    "complexity_action",
    "config_action",
    "hooks_path_action",
    "chain",
    "wrote",
    "length_runs",
    "loc_reject",
    "loc_maintain",
    "loc_aim",
    "cognitive",
    "max_args",
    "ceilings_source",
)

CONFIG_BODY = """\
# suite-gates.cfg — created by scripts/hooks/install_gates.py because the file was absent.
# The integers below are the defaults. A later edit is the live ceiling for
# suite-installed sections only. Constraints, or the hook fails closed:
# reject > 200, reject > maintain > aim >= 0, cognitive >= 0, max_args >= 0.
# A whitespace-only file is malformed. It is not "missing, use defaults."
# This file does not retune a length hook this installer did not write.
# The installer does not git add this file.

[loc]
reject = 500
maintain = 200
aim = 150

[complexity]
cognitive = 15
max_args = 5
"""


def _git(ws, *args, check=True):
    proc = subprocess.run(
        ["git", "-C", str(ws), *args],
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {args} -> {proc.returncode}\n{proc.stderr}")
    return proc


def _statements(count):
    return "\n".join(["x = 1"] * count) + "\n"


def _ifs(count, name="keep"):
    lines = [f"def {name}(a):"]
    lines += ["    if a: return 1"] * count
    return "\n".join(lines) + "\n"


def commit_hook_output(proc):
    """git 2.34.1 forwards pre-commit stdout to the commit's stderr."""
    return proc.stderr


def product_revert_preflight(ws, rev="HEAD"):
    """Stop before revert unless the index and the rev's paths are clean.

    Pass is empty ``git ls-files --others`` output. That command exits 0
    even when it prints a path, and it does not take --exclude-standard.
    An empty diff-tree must not call ls-files with no paths: that lists
    every untracked path.
    """
    cached = _git(ws, "diff", "--cached", "--quiet", check=False)
    if cached.returncode != 0:
        return False
    listed = _git(
        ws, "diff-tree", "--no-commit-id", "--name-only", "-r", rev, check=False,
    )
    paths = [line for line in listed.stdout.splitlines() if line]
    if not paths:
        return True
    dirty = _git(ws, "diff", "--quiet", "--", *paths, check=False)
    if dirty.returncode != 0:
        return False
    others = _git(ws, "ls-files", "--others", "--", *paths, check=False)
    return others.stdout.strip() == ""


class Repo(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        self.extra = []
        self.link = None
        _git(self.ws, "init", "-q")
        _git(self.ws, "config", "user.email", "test@example.com")
        _git(self.ws, "config", "user.name", "Test")
        _git(self.ws, "config", "commit.gpgsign", "false")
        _git(self.ws, "config", "diff.renames", "false")

    def tearDown(self):
        if self.link is not None:
            subprocess.run(
                ["git", "-C", str(self.ws), "worktree", "remove", "--force", str(self.link)],
                capture_output=True,
                text=True,
            )
            shutil.rmtree(self.link, ignore_errors=True)
        for path in self.extra:
            shutil.rmtree(path, ignore_errors=True)
        shutil.rmtree(self.ws, ignore_errors=True)

    def keep(self, path):
        self.extra.append(path)
        return path

    def write(self, name, text, mode=None):
        path = self.ws / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text)
        if mode is not None:
            path.chmod(mode)
        return path

    def write_exec(self, name, text, mode=0o755):
        return self.write(name, text, mode)

    def add(self, *names):
        _git(self.ws, "add", "--", *names)

    def commit(self, msg="fixture"):
        _git(self.ws, "commit", "--no-verify", "-m", msg)

    def product_commit(self, msg, paths=None, *, skip=False, path_env=None):
        # Product path. No --no-verify. The prefix lives only on this command.
        env = os.environ.copy()
        env.pop("SUITE_GATES_SKIP", None)
        if skip:
            env["SUITE_GATES_SKIP"] = "1"
        if path_env is not None:
            env["PATH"] = path_env
        cmd = ["git", "-C", str(self.ws), "commit", "-m", msg]
        if paths is not None:
            cmd.extend(["--", *paths])
        return subprocess.run(cmd, capture_output=True, text=True, env=env)

    def revert(self, rev="HEAD"):
        env = os.environ.copy()
        env.pop("SUITE_GATES_SKIP", None)
        self.assertNotIn("SUITE_GATES_SKIP", env)
        return subprocess.run(
            ["git", "-C", str(self.ws), "revert", "--no-edit", rev],
            capture_output=True,
            text=True,
            env=env,
        )

    def cli(self, args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def confirmed(self):
        return install(self.ws, confirmed=True)

    def hooks_path(self):
        proc = _git(self.ws, "config", "--get", "core.hooksPath", check=False)
        if proc.returncode != 0:
            return None
        return proc.stdout.strip()

    def rev(self):
        proc = _git(self.ws, "rev-parse", "HEAD", check=False)
        if proc.returncode != 0:
            return None
        return proc.stdout.strip()

    def subject(self):
        return _git(self.ws, "log", "-1", "--format=%s").stdout.strip()

    def show_names(self):
        return _git(self.ws, "show", "--name-only", "--format=").stdout

    def assert_default_ceilings(self, report, source="default"):
        self.assertEqual(report["loc_reject"], 500)
        self.assertEqual(report["loc_maintain"], 200)
        self.assertEqual(report["loc_aim"], 150)
        self.assertEqual(report["cognitive"], 15)
        self.assertEqual(report["max_args"], 5)
        self.assertEqual(report["ceilings_source"], source)

    def assert_rejected_ceilings(self, report):
        self.assertEqual(report["config_action"], "left-existing")
        self.assertEqual(report["ceilings_source"], "rejected")
        builtins = {
            "loc_reject": 500,
            "loc_maintain": 200,
            "loc_aim": 150,
            "cognitive": 15,
            "max_args": 5,
        }
        for key, builtin in builtins.items():
            self.assertEqual(report[key], "rejected")
            self.assertIsNotNone(report[key])
            self.assertNotEqual(report[key], builtin)
        line = install_gates._format_human(report)
        self.assertIn("ceilings_source=rejected", line)
        self.assertIn("loc_reject=rejected", line)
        self.assertNotIn("loc_reject=null", line)
        self.assertNotIn("loc_reject=500", line)
        self.assertNotIn("loc_maintain=200", line)
        self.assertNotIn("loc_aim=150", line)
        self.assertNotIn("cognitive=15", line)
        self.assertNotIn("max_args=5", line)

    def assert_hook_rejects_config(self, name="ok.py"):
        self.write(name, "x = 1\n")
        self.add(name)
        proc = self.product_commit("small file", [name])
        self.assertEqual(proc.returncode, 1)
        stream = commit_hook_output(proc)
        self.assertIn("suite-gates.cfg rejected:", stream)
        self.assertNotIn("loc ", stream)
        self.assertIsNone(self.rev())
        return stream

    def assert_noop(self, report):
        self.assertEqual(report["loc_action"], "noop")
        self.assertEqual(report["complexity_action"], "noop")
        self.assertEqual(report["config_action"], "not-needed")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertEqual(report["chain"], "none")
        self.assertIs(report["wrote"], False)

    def seed_config(self, text):
        path = self.write(".githooks/suite-gates.cfg", text)
        past = time.time() - 10_000
        os.utime(path, (past, past))
        return path

    def install_refusing_config(self, hook_path):
        """git config --local core.hooksPath fails. Other git commands pass through."""
        witness_dir = self.keep(Path(tempfile.mkdtemp()))
        witness = witness_dir / "witness"
        bindir = self.keep(Path(tempfile.mkdtemp()))
        script = (
            "#!/bin/sh\n"
            "flat=\" $* \"\n"
            "case \"$flat\" in\n"
            "  *\" config --local core.hooksPath .githooks \"*)\n"
            f"    cp {hook_text.shell_quote(str(hook_path))} "
            f"{hook_text.shell_quote(str(witness))} 2>/dev/null || true\n"
            "    echo refusing hooksPath write >&2\n"
            "    exit 1\n"
            "    ;;\n"
            "esac\n"
            "exec /usr/bin/git \"$@\"\n"
        )
        fake = bindir / "git"
        fake.write_text(script)
        fake.chmod(0o755)
        old = os.environ["PATH"]
        os.environ["PATH"] = str(bindir) + os.pathsep + old
        try:
            code, out, err = self.cli(
                ["--workspace", str(self.ws), "--workspace-confirmed", "--output-json"]
            )
        finally:
            os.environ["PATH"] = old
        return code, json.loads(out), err, witness


class TestHookText(unittest.TestCase):
    def test_stdout_strings_and_shell_quote(self):
        self.assertEqual(hook_text.LOUD_LINE, LOUD)
        self.assertEqual(hook_text.FAIL_PYTHON, FAIL_PYTHON)
        self.assertEqual(hook_text.MARKER_LINE, MARKER)
        self.assertEqual(hook_text.CONFIG_TEXT, CONFIG_BODY)
        self.assertEqual(hook_text.shell_quote("a'b"), "'a'\\''b'")

    def test_sources_record_this_tree(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("hook_text.py", "install_gates.py"):
            text = (root / "scripts" / "hooks" / name).read_text()
            self.assertNotIn("/home/", text)
            self.assertNotIn("jwils", text)
        self.assertEqual(SUITE_ROOT, root)
        self.assertEqual(SUITE_ROOT, Path(install_gates.__file__).resolve().parents[2])

    def test_from_scratch_skip_is_first_and_has_no_marker(self):
        text = hook_text.render("/suite", preserved=False, length=True, complexity=True)
        self.assertNotIn("pre-commit.suite-preserved", text)
        self.assertNotIn(MARKER, text)
        self.assertLess(text.index("SUITE_GATES_SKIP"), text.index("command -v python3"))
        self.assertIn('python3 "$_loc" --staged', text)
        self.assertIn('python3 "$_cog" --staged', text)
        self.assertNotIn("\nexec ", text)

    def test_case_4_listing_shape(self):
        text = hook_text.render("/suite", preserved=True, length=True, complexity=True)
        self.assertIn(
            '_preserved=$(CDPATH= cd -- "$(dirname "$0")" && pwd)/pre-commit.suite-preserved',
            text,
        )
        self.assertIn('"$_preserved" "$@"', text)
        self.assertNotIn("\nexec ", text)
        self.assertNotIn("sh \"$_preserved\"", text)
        self.assertIn(LOUD, text)
        self.assertIn(FAIL_PYTHON, text)
        self.assertIn("not a file", text)
        self.assertIn("LOC-EXEMPT", text)
        self.assertNotIn(MARKER, text)
        self.assertTrue(text.endswith('exit "$_suite_gate_status"\n'))

    def test_complexity_only_omits_the_length_call(self):
        text = hook_text.render("/suite", preserved=True, length=False, complexity=True)
        self.assertIn("# suite-hook:loc-existing", text)
        self.assertNotIn("loc_gate.py", text)
        self.assertNotIn("suite-hook:loc-gate", text)
        self.assertNotIn("LOC-EXEMPT", text)
        self.assertIn("suite-hook:complexity-gate", text)

    def test_length_only_omits_the_complexity_block(self):
        text = hook_text.render("/suite", preserved=True, length=True, complexity=False)
        self.assertIn("loc_gate.py", text)
        self.assertIn("LOC-EXEMPT", text)
        self.assertNotIn("suite-hook:complexity-gate", text)
        self.assertNotIn("complexity_gate.py", text)

    def test_splice_inserts_before_the_last_exit(self):
        text = "#!/bin/sh\nexit 0\necho after\nexit 1\n"
        out = hook_text.splice(text, [hook_text.complexity_block()])
        lines = out.splitlines()
        self.assertEqual(lines[-1], "exit 1")
        self.assertEqual(lines[-2], "# <<< suite-hook:complexity-gate <<<")
        self.assertLess(lines.index("exit 0"), lines.index("# >>> suite-hook:complexity-gate >>>"))

    def test_splice_without_exit_returns_none(self):
        self.assertIsNone(hook_text.splice("#!/bin/sh\necho done\n", [hook_text.loc_block()]))


class TestUsage(Repo):
    def test_missing_workspace_exits_2(self):
        code, out, err = self.cli([])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("--workspace", err)

    def test_not_a_directory_exits_2(self):
        path = self.write("a-file", "x\n")
        code, out, err = self.cli(["--workspace", str(path), "--workspace-confirmed"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("not an existing directory", err)

    def test_not_a_repository_exits_2(self):
        other = self.keep(Path(tempfile.mkdtemp()))
        code, out, err = self.cli(["--workspace", str(other), "--workspace-confirmed"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("not a git repository", err)
        self.assertFalse((other / ".githooks").exists())

    def test_subdirectory_is_not_the_toplevel(self):
        sub = self.ws / "sub"
        sub.mkdir()
        code, out, err = self.cli(["--workspace", str(sub), "--workspace-confirmed"])
        self.assertEqual(code, 2)
        self.assertIn("not the git toplevel", err)
        self.assertFalse((sub / ".githooks").exists())

    def test_filesystem_root_and_home_root_are_refused(self):
        root_hook = Path("/.githooks/pre-commit")
        root_existed = root_hook.exists()
        code, out, err = self.cli(["--workspace", "/", "--workspace-confirmed"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("refusing filesystem root", err)
        self.assertEqual(root_hook.exists(), root_existed)

        home = Path.home().resolve()
        home_hook = home / ".githooks" / "pre-commit"
        before = home_hook.read_bytes() if home_hook.exists() else None
        code, out, err = self.cli(["--workspace", str(home), "--workspace-confirmed"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("refusing home root", err)
        after = home_hook.read_bytes() if home_hook.exists() else None
        self.assertEqual(before, after)

    def test_linked_worktree_exits_2(self):
        self.write("base.txt", "base\n")
        self.add("base.txt")
        self.commit("base")
        link = Path(tempfile.mkdtemp())
        link.rmdir()
        self.link = link
        _git(self.ws, "worktree", "add", "--detach", str(link))
        self.assertTrue((link / ".git").is_file())
        code, out, err = self.cli(["--workspace", str(link), "--workspace-confirmed"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("not a normal repository", err)
        self.assertFalse((link / ".githooks").exists())
        self.assertFalse((self.ws / ".githooks").exists())


class TestInstall(Repo):
    def test_dry_run_writes_nothing(self):
        report = install(self.ws, confirmed=False)
        self.assertEqual(report["loc_action"], "would-install")
        self.assertEqual(report["complexity_action"], "would-install")
        self.assertEqual(report["config_action"], "would-create")
        self.assertEqual(report["hooks_path_action"], "set:.githooks")
        self.assertEqual(report["chain"], "created")
        self.assertIs(report["wrote"], False)
        self.assertIs(report["length_runs"], False)
        self.assertFalse((self.ws / ".githooks").exists())
        self.assertIsNone(self.hooks_path())
        code, out, _err = self.cli(["--workspace", str(self.ws)])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("suite-gates: "))
        keys = [part.split("=", 1)[0] for part in out.strip()[len("suite-gates: "):].split(" ")]
        self.assertEqual(keys, list(REPORT_KEYS))

    def test_case_1a_sets_hooks_path_only_after_config(self):
        note = self.write(".git/hooks/notes.txt", "not a hook\n")
        sample = self.ws / ".git" / "hooks" / "pre-commit.sample"
        self.assertTrue(sample.is_file())
        names_before = sorted(p.name for p in (self.ws / ".git" / "hooks").iterdir())
        git_path = _git(self.ws, "rev-parse", "--git-path", "hooks")
        self.assertEqual(git_path.stdout.strip(), ".git/hooks")

        code, out, err = self.cli(
            ["--workspace", str(self.ws), "--workspace-confirmed"]
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("suite-gates: "))
        self.assertIn("loc_action=installed", out)
        self.assertIn("complexity_action=installed", out)
        self.assertIn("config_action=created", out)
        self.assertIn("hooks_path_action=set:.githooks", out)
        self.assertIn("chain=created", out)
        self.assertIn("wrote=true", out)
        self.assertIn("length_runs=true", out)
        self.assertIn("ceilings_source=default", out)

        hook = self.ws / ".githooks" / "pre-commit"
        text = hook.read_text()
        self.assertEqual(text.splitlines()[1], MARKER)
        self.assertEqual(stat.S_IMODE(hook.stat().st_mode), 0o755)
        self.assertIn(f"_suite_gates_root={hook_text.shell_quote(str(SUITE_ROOT))}", text)
        self.assertNotIn("pre-commit.suite-preserved", text)
        self.assertFalse((self.ws / ".git" / "hooks" / "pre-commit").exists())
        self.assertEqual(self.hooks_path(), ".githooks")
        self.assertEqual((self.ws / ".githooks" / "suite-gates.cfg").read_text(), CONFIG_BODY)
        self.assertEqual(note.read_text(), "not a hook\n")
        names_after = sorted(p.name for p in (self.ws / ".git" / "hooks").iterdir())
        self.assertEqual(names_before, names_after)

        before = hook.read_bytes()
        report = self.confirmed()
        self.assert_noop(report)
        self.assertIs(report["length_runs"], True)
        self.assertEqual(hook.read_bytes(), before)
        self.assertEqual(self.hooks_path(), ".githooks")

        code, out, err = self.cli(
            ["--workspace", str(self.ws), "--workspace-confirmed", "--output-json"]
        )
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(list(data), list(REPORT_KEYS))
        self.assertIs(data["wrote"], False)
        self.assertNotIn("suite-gates:", out)

    def test_case_1a_failed_config_leaves_the_marker_absent(self):
        hook = self.ws / ".githooks" / "pre-commit"
        code, data, err, witness = self.install_refusing_config(hook)
        self.assertEqual(code, 0, err)
        self.assertIn("refusing hooksPath write", err)
        self.assertIs(data["wrote"], True)
        self.assertEqual(data["loc_action"], "installed")
        self.assertEqual(data["complexity_action"], "installed")
        self.assertEqual(data["config_action"], "not-needed")
        self.assertEqual(data["hooks_path_action"], "unchanged")
        self.assertEqual(data["chain"], "created")
        self.assertIs(data["length_runs"], False)
        self.assertIsNone(self.hooks_path())
        self.assertNotIn(MARKER, hook.read_text())
        self.assertIn("suite-hook:chain", witness.read_text())
        self.assertNotIn(MARKER, witness.read_text())
        self.assertFalse((self.ws / ".githooks" / "suite-gates.cfg").exists())
        self.assertFalse((self.ws / ".git" / "hooks" / "pre-commit").exists())

        report = self.confirmed()
        self.assertEqual(report["loc_action"], "noop")
        self.assertEqual(report["complexity_action"], "noop")
        self.assertEqual(report["hooks_path_action"], "set:.githooks")
        self.assertEqual(report["chain"], "none")
        self.assertIs(report["wrote"], True)
        self.assertIs(report["length_runs"], True)
        self.assertEqual(report["config_action"], "created")
        self.assertEqual(hook.read_text().splitlines()[1], MARKER)
        self.assertFalse((hook.parent / "pre-commit.suite-preserved").exists())
        self.assertEqual(self.hooks_path(), ".githooks")

    def test_zero_byte_pre_commit_is_not_case_4(self):
        empty = self.write(".git/hooks/pre-commit", b"")
        report = self.confirmed()
        self.assertEqual(report["hooks_path_action"], "set:.githooks")
        self.assertEqual(report["chain"], "created")
        self.assertEqual(empty.read_bytes(), b"")
        self.assertTrue((self.ws / ".githooks" / "pre-commit").is_file())
        self.assertEqual(self.hooks_path(), ".githooks")

    def test_case_1b_leaves_pre_push_and_hooks_path(self):
        original = "#!/bin/sh\necho push\nexit 0\n"
        pre_push = self.write_exec(".git/hooks/pre-push", original)
        report = self.confirmed()
        self.assertEqual(pre_push.read_text(), original)
        created = self.ws / ".git" / "hooks" / "pre-commit"
        self.assertTrue(created.is_file())
        self.assertEqual(stat.S_IMODE(created.stat().st_mode), 0o755)
        self.assertIn("loc_gate.py", created.read_text())
        self.assertIn("complexity_gate.py", created.read_text())
        self.assertNotIn(MARKER, created.read_text())
        self.assertFalse((self.ws / ".githooks" / "pre-commit").exists())
        self.assertTrue((self.ws / ".githooks" / "suite-gates.cfg").is_file())
        self.assertIsNone(self.hooks_path())
        self.assertEqual(report["chain"], "created")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertEqual(report["loc_action"], "installed")
        self.assertEqual(report["complexity_action"], "installed")
        self.assertIs(report["length_runs"], True)

    def test_case_1c_creates_pre_commit_in_the_effective_directory(self):
        self.write("repo-hooks/.keep", "")
        _git(self.ws, "config", "core.hooksPath", "repo-hooks")
        report = self.confirmed()
        created = self.ws / "repo-hooks" / "pre-commit"
        self.assertTrue(created.is_file())
        self.assertEqual(stat.S_IMODE(created.stat().st_mode), 0o755)
        self.assertIn("loc_gate.py", created.read_text())
        self.assertNotIn(MARKER, created.read_text())
        self.assertEqual(self.hooks_path(), "repo-hooks")
        self.assertEqual(report["chain"], "created")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertFalse((self.ws / ".githooks" / "pre-commit").exists())
        self.assertFalse((self.ws / ".git" / "hooks" / "pre-commit").exists())

    def test_case_2a_loc_exempt_preserves_the_length_checker(self):
        original = "#!/bin/sh\n# LOC-EXEMPT: legacy checker\necho legacy-length\nexit 0\n"
        live = self.write_exec(".githooks/pre-commit", original)
        _git(self.ws, "config", "core.hooksPath", ".githooks")
        report = self.confirmed()
        preserved = self.ws / ".githooks" / "pre-commit.suite-preserved"
        self.assertEqual(preserved.read_text(), original)
        text = live.read_text()
        self.assertNotIn("loc_gate.py", text)
        self.assertNotIn("suite-hook:loc-gate", text)
        self.assertIn("# suite-hook:loc-existing", text)
        self.assertIn("complexity_gate.py", text)
        self.assertNotIn(MARKER, text)
        self.assertEqual(report["loc_action"], "left-existing")
        self.assertEqual(report["complexity_action"], "installed")
        self.assertEqual(report["chain"], "wrapped")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertIs(report["length_runs"], True)
        self.assertEqual(self.hooks_path(), ".githooks")
        before = live.read_bytes()
        self.assert_noop(self.confirmed())
        self.assertEqual(live.read_bytes(), before)

    def test_case_2a_splice_before_the_last_exit(self):
        original = (
            "#!/bin/sh\n"
            "# suite-hook:chain\n"
            "# >>> suite-hook:loc-gate >>>\n"
            "echo loc-ran\n"
            "# <<< suite-hook:loc-gate <<<\n"
            "echo mid\n"
            "exit 0\n"
            "echo after\n"
            "exit 1\n"
        )
        live = self.write_exec(".githooks/pre-commit", original)
        _git(self.ws, "config", "core.hooksPath", ".githooks")
        report = self.confirmed()
        lines = live.read_text().splitlines()
        self.assertEqual(report["chain"], "spliced")
        self.assertEqual(report["loc_action"], "left-existing")
        self.assertEqual(report["complexity_action"], "installed")
        self.assertEqual(lines[-1], "exit 1")
        self.assertEqual(lines[-2], "# <<< suite-hook:complexity-gate <<<")
        self.assertEqual(lines.count("# >>> suite-hook:complexity-gate >>>"), 1)
        self.assertIn("echo loc-ran", lines)
        self.assertLess(lines.index("exit 0"), lines.index("# >>> suite-hook:complexity-gate >>>"))
        self.assertFalse((live.parent / "pre-commit.suite-preserved").exists())
        self.assertEqual(self.hooks_path(), ".githooks")

    def test_splice_without_exit_writes_nothing(self):
        original = (
            "#!/bin/sh\n"
            "# suite-hook:chain\n"
            "# >>> suite-hook:loc-gate >>>\n"
            "echo loc-ran\n"
            "# <<< suite-hook:loc-gate <<<\n"
            "echo done\n"
        )
        live = self.write_exec(".githooks/pre-commit", original)
        _git(self.ws, "config", "core.hooksPath", ".githooks")
        code, out, err = self.cli(
            ["--workspace", str(self.ws), "--workspace-confirmed", "--output-json"]
        )
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["loc_action"], "refused")
        self.assertEqual(data["complexity_action"], "refused")
        self.assertIs(data["wrote"], False)
        self.assertEqual(data["chain"], "none")
        self.assertIn("no exit line to splice before", err)
        self.assertEqual(live.read_text(), original)
        self.assertFalse((self.ws / ".githooks" / "suite-gates.cfg").exists())

    def test_case_2b_does_not_copy_a_dormant_length_checker(self):
        dormant_text = "#!/bin/sh\n# LOC-EXEMPT: dormant\necho DORMANT\nexit 0\n"
        dormant = self.write_exec(".githooks/pre-commit", dormant_text)
        active_text = "#!/bin/sh\necho ACTIVE\nexit 0\n"
        active = self.write_exec("repo-hooks/pre-commit", active_text)
        _git(self.ws, "config", "core.hooksPath", "repo-hooks")
        report = self.confirmed()
        self.assertEqual(dormant.read_text(), dormant_text)
        live = active.read_text()
        self.assertNotIn("loc_gate.py", live)
        self.assertNotIn("LOC-EXEMPT", live)
        self.assertIn("complexity_gate.py", live)
        self.assertIn("# suite-hook:loc-existing", live)
        self.assertIs(report["length_runs"], False)
        self.assertEqual(report["loc_action"], "left-existing")
        self.assertEqual(report["complexity_action"], "installed")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertEqual(self.hooks_path(), "repo-hooks")

    def test_case_2b_trampoline_runs_the_dormant_file_first(self):
        pre_push = self.write_exec(".git/hooks/pre-push", "#!/bin/sh\necho push\nexit 0\n")
        push_bytes = pre_push.read_bytes()
        dormant_text = "#!/bin/sh\n# LOC-EXEMPT: dormant\necho DORMANT-RAN\nexit 3\n"
        dormant = self.write_exec(".githooks/pre-commit", dormant_text)
        report = self.confirmed()
        hook = self.ws / ".git" / "hooks" / "pre-commit"
        text = hook.read_text()
        self.assertEqual(dormant.read_text(), dormant_text)
        self.assertEqual(pre_push.read_bytes(), push_bytes)
        self.assertLess(text.index(str(dormant.resolve())), text.index("complexity_gate.py"))
        self.assertIn('"$_preserved" "$@"', text)
        self.assertNotIn("loc_gate.py", text)
        self.assertNotIn(MARKER, text)
        self.assertIsNone(self.hooks_path())
        self.assertEqual(report["chain"], "trampoline")
        self.assertEqual(report["loc_action"], "left-existing")
        self.assertEqual(report["complexity_action"], "installed")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertIs(report["length_runs"], True)
        proc = subprocess.run([str(hook)], cwd=self.ws, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("DORMANT-RAN", proc.stdout)
        self.assertNotIn("complexity", proc.stdout)
        self.assertNotIn("SUITE GATES", proc.stdout)

    def test_trampoline_length_runs_when_the_workspace_path_has_a_quote(self):
        parent = self.keep(Path(tempfile.mkdtemp()))
        ws = parent / "a'b"
        ws.mkdir()
        _git(ws, "init", "-q")
        _git(ws, "config", "user.email", "test@example.com")
        _git(ws, "config", "user.name", "Test")
        dormant = ws / ".githooks" / "pre-commit"
        dormant.parent.mkdir()
        dormant.write_text("#!/bin/sh\n# LOC-EXEMPT: dormant\nexit 0\n")
        dormant.chmod(0o755)
        pre_push = ws / ".git" / "hooks" / "pre-push"
        pre_push.write_text("#!/bin/sh\nexit 0\n")
        pre_push.chmod(0o755)
        report = install(ws, confirmed=True)
        hook = ws / ".git" / "hooks" / "pre-commit"
        text = hook.read_text()
        quoted = hook_text.shell_quote(str(dormant.resolve()))
        self.assertNotIn(str(dormant.resolve()), text)
        self.assertIn(quoted, text)
        self.assertNotIn("loc_gate.py", text)
        self.assertEqual(report["chain"], "trampoline")
        self.assertIs(report["length_runs"], True)
        before = hook.read_bytes()
        again = install(ws, confirmed=True)
        self.assertEqual(again["loc_action"], "noop")
        self.assertEqual(again["complexity_action"], "noop")
        self.assertIs(again["length_runs"], True)
        self.assertIs(again["wrote"], False)
        self.assertEqual(again["chain"], "none")
        self.assertEqual(hook.read_bytes(), before)

    def test_case_2b_dormant_not_executable_refuses(self):
        dormant = self.write(".githooks/pre-commit", "#!/bin/sh\n# LOC-EXEMPT\nexit 0\n", 0o644)
        code, out, err = self.cli(
            ["--workspace", str(self.ws), "--workspace-confirmed", "--output-json"]
        )
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["loc_action"], "refused")
        self.assertEqual(data["hooks_path_action"], "unchanged")
        self.assertIs(data["wrote"], False)
        self.assertEqual(stat.S_IMODE(dormant.stat().st_mode), 0o644)
        self.assertIsNone(self.hooks_path())
        self.assertIn("not executable", err)
        self.assertFalse((self.ws / ".git" / "hooks" / "pre-commit").exists())

    def test_case_2b_both_checkers_activates_without_wrapping(self):
        body = (
            "#!/bin/sh\n"
            "# LOC-EXEMPT: present\n"
            "# >>> suite-hook:complexity-gate >>>\n"
            "echo cog\n"
            "# <<< suite-hook:complexity-gate <<<\n"
            "exit 0\n"
        )
        hook = self.write_exec(".githooks/pre-commit", body)
        report = self.confirmed()
        self.assertEqual(report["loc_action"], "noop")
        self.assertEqual(report["complexity_action"], "noop")
        self.assertEqual(report["hooks_path_action"], "set:.githooks")
        self.assertEqual(report["chain"], "none")
        self.assertIs(report["wrote"], True)
        self.assertEqual(report["config_action"], "created")
        self.assertNotEqual(
            (report["loc_action"], report["wrote"], report["hooks_path_action"]),
            ("noop", False, "unchanged"),
        )
        self.assertEqual(hook.read_text(), hook_text.insert_marker(body))
        self.assertEqual(hook.read_text().splitlines()[1], MARKER)
        self.assertFalse((hook.parent / "pre-commit.suite-preserved").exists())
        self.assertEqual(self.hooks_path(), ".githooks")
        self.assert_default_ceilings(report)

    def test_case_2b_activation_failed_config_leaves_the_marker_absent(self):
        body = (
            "#!/bin/sh\n"
            "# LOC-EXEMPT: present\n"
            "# >>> suite-hook:complexity-gate >>>\n"
            "echo cog\n"
            "# <<< suite-hook:complexity-gate <<<\n"
            "exit 0\n"
        )
        hook = self.write_exec(".githooks/pre-commit", body)
        code, data, err, witness = self.install_refusing_config(hook)
        self.assertEqual(code, 0, err)
        self.assertEqual(data["loc_action"], "left-existing")
        self.assertEqual(data["complexity_action"], "left-existing")
        self.assertIs(data["wrote"], False)
        self.assertEqual(data["hooks_path_action"], "unchanged")
        self.assertEqual(data["chain"], "none")
        self.assertIs(data["length_runs"], False)
        self.assertNotEqual(
            (data["loc_action"], data["wrote"], data["hooks_path_action"]),
            ("noop", False, "unchanged"),
        )
        self.assertNotEqual(
            (data["loc_action"], data["wrote"], data["hooks_path_action"]),
            ("noop", True, "set:.githooks"),
        )
        self.assertFalse((self.ws / ".githooks" / "suite-gates.cfg").exists())
        self.assertEqual(hook.read_text(), body)
        self.assertNotIn(MARKER, witness.read_text())
        self.assertIsNone(self.hooks_path())
        self.assertFalse((hook.parent / "pre-commit.suite-preserved").exists())

    def test_case_2b_missing_section_marks_the_wrapper_only_after_config(self):
        original = "#!/bin/sh\n# LOC-EXEMPT: legacy\necho legacy\nexit 0\n"
        hook = self.write_exec(".githooks/pre-commit", original)
        report = self.confirmed()
        preserved = hook.parent / "pre-commit.suite-preserved"
        self.assertEqual(preserved.read_text(), original)
        self.assertNotIn(MARKER, preserved.read_text())
        text = hook.read_text()
        self.assertEqual(text.splitlines()[1], MARKER)
        self.assertNotIn("loc_gate.py", text)
        self.assertIn("complexity_gate.py", text)
        self.assertIn("# suite-hook:loc-existing", text)
        self.assertEqual(report["chain"], "wrapped")
        self.assertEqual(report["hooks_path_action"], "set:.githooks")
        self.assertEqual(report["loc_action"], "left-existing")
        self.assertEqual(report["complexity_action"], "installed")
        self.assertIs(report["wrote"], True)
        self.assertEqual(self.hooks_path(), ".githooks")
        self.assertEqual(stat.S_IMODE(preserved.stat().st_mode), 0o755)

    def test_case_2b_missing_section_failed_config_does_not_mark_or_clobber(self):
        original = "#!/bin/sh\n# LOC-EXEMPT: legacy\necho legacy\nexit 0\n"
        hook = self.write_exec(".githooks/pre-commit", original)
        code, data, err, witness = self.install_refusing_config(hook)
        self.assertEqual(code, 0, err)
        preserved = hook.parent / "pre-commit.suite-preserved"
        self.assertEqual(preserved.read_bytes(), original.encode())
        self.assertNotIn(MARKER, preserved.read_text())
        self.assertIn("complexity_gate.py", hook.read_text())
        self.assertNotIn(MARKER, hook.read_text())
        self.assertIn("complexity_gate.py", witness.read_text())
        self.assertNotIn(MARKER, witness.read_text())
        self.assertIsNone(self.hooks_path())
        self.assertIs(data["wrote"], True)
        self.assertEqual(data["chain"], "wrapped")
        self.assertEqual(data["config_action"], "not-needed")

        report = self.confirmed()
        self.assertEqual(preserved.read_bytes(), original.encode())
        self.assertNotIn(MARKER, preserved.read_text())
        self.assertEqual(hook.read_text().splitlines()[1], MARKER)
        self.assertEqual(report["hooks_path_action"], "set:.githooks")
        self.assertEqual(report["chain"], "none")
        self.assertEqual(self.hooks_path(), ".githooks")

    def test_case_3_wraps_the_effective_hook_and_does_not_silence_dotgit(self):
        original_push = "#!/bin/sh\necho push\nexit 0\n"
        pre_push = self.write_exec(".git/hooks/pre-push", original_push)
        active_text = "#!/bin/sh\necho ACTIVE\nexit 0\n"
        active = self.write_exec("repo-hooks/pre-commit", active_text, 0o750)
        _git(self.ws, "config", "core.hooksPath", "repo-hooks")
        report = self.confirmed()
        preserved = active.parent / "pre-commit.suite-preserved"
        self.assertEqual(preserved.read_text(), active_text)
        self.assertEqual(stat.S_IMODE(preserved.stat().st_mode), 0o750)
        self.assertEqual(stat.S_IMODE(active.stat().st_mode), 0o755)
        self.assertIn("loc_gate.py", active.read_text())
        self.assertIn("complexity_gate.py", active.read_text())
        self.assertNotIn(MARKER, active.read_text())
        self.assertEqual(pre_push.read_text(), original_push)
        self.assertFalse((self.ws / ".git" / "hooks" / "pre-commit").exists())
        self.assertEqual(self.hooks_path(), "repo-hooks")
        self.assertEqual(report["chain"], "wrapped")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertIs(report["length_runs"], True)

    def test_case_3_leftover_dotgit_pre_commit_stays_byte_identical(self):
        leftover_text = "#!/bin/sh\necho LEFTOVER\nexit 0\n"
        leftover = self.write_exec(".git/hooks/pre-commit", leftover_text, 0o700)
        active_text = "#!/bin/sh\necho ACTIVE\nexit 0\n"
        active = self.write_exec("repo-hooks/pre-commit", active_text)
        _git(self.ws, "config", "core.hooksPath", "repo-hooks")
        self.confirmed()
        self.assertEqual(leftover.read_text(), leftover_text)
        self.assertEqual(stat.S_IMODE(leftover.stat().st_mode), 0o700)
        self.assertNotIn("LEFTOVER", active.read_text())
        self.assertIn("complexity_gate.py", active.read_text())
        self.assertEqual(self.hooks_path(), "repo-hooks")
        self.assertFalse((self.ws / ".git" / "hooks" / "pre-commit.suite-preserved").exists())

    def test_case_4_wraps_preserves_mode_and_rejects_over_ceiling(self):
        original = "#!/bin/sh\necho PRESERVED-OK\nexit 0\n"
        live = self.write_exec(".git/hooks/pre-commit", original, 0o700)
        report = self.confirmed()
        preserved = live.parent / "pre-commit.suite-preserved"
        self.assertEqual(preserved.read_text(), original)
        self.assertEqual(stat.S_IMODE(preserved.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(live.stat().st_mode), 0o755)
        text = live.read_text()
        self.assertNotIn(MARKER, text)
        self.assertIn('"$_preserved" "$@"', text)
        self.assertIn("loc_gate.py", text)
        self.assertIn("complexity_gate.py", text)
        self.assertIsNone(self.hooks_path())
        self.assertEqual(report["chain"], "wrapped")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertIs(report["length_runs"], True)
        self.assertEqual(report["config_action"], "created")
        before = live.read_bytes()
        self.assert_noop(self.confirmed())
        self.assertEqual(live.read_bytes(), before)

        self.write("wide.py", _statements(500))
        self.add("wide.py")
        proc = self.product_commit("over ceiling", ["wide.py"])
        self.assertEqual(proc.returncode, 1)
        stream = commit_hook_output(proc)
        self.assertIn("PRESERVED-OK", stream)
        self.assertIn("loc ", stream)
        self.assertIn("band=reject", stream)
        self.assertLess(stream.index("PRESERVED-OK"), stream.index("band=reject"))
        self.assertIsNone(self.rev())

    def test_case_4_preserved_failure_does_not_run_the_gates(self):
        self.write_exec(
            ".git/hooks/pre-commit",
            "#!/bin/sh\necho PRESERVED-STOP\nexit 9\n",
        )
        self.confirmed()
        self.write("god.py", _statements(500))
        self.add("god.py")
        proc = self.product_commit("stopped", ["god.py"])
        self.assertNotEqual(proc.returncode, 0)
        stream = commit_hook_output(proc)
        self.assertIn("PRESERVED-STOP", stream)
        self.assertNotIn("band=reject", stream)
        self.assertIsNone(self.rev())

    def test_case_4_when_hooks_path_resolves_to_dotgit(self):
        original = "#!/bin/sh\necho HERE\nexit 0\n"
        live = self.write_exec(".git/hooks/pre-commit", original)
        absolute = str((self.ws / ".git" / "hooks").resolve())
        _git(self.ws, "config", "core.hooksPath", absolute)
        report = self.confirmed()
        self.assertEqual(self.hooks_path(), absolute)
        self.assertEqual(report["chain"], "wrapped")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertNotIn(MARKER, live.read_text())
        self.assertEqual(
            (live.parent / "pre-commit.suite-preserved").read_text(),
            original,
        )

    def test_case_4_absent_pre_commit_is_created_without_changing_config(self):
        _git(self.ws, "config", "core.hooksPath", ".git/hooks")
        report = self.confirmed()
        created = self.ws / ".git" / "hooks" / "pre-commit"
        self.assertTrue(created.is_file())
        self.assertNotIn(MARKER, created.read_text())
        self.assertIn("loc_gate.py", created.read_text())
        self.assertEqual(self.hooks_path(), ".git/hooks")
        self.assertEqual(report["chain"], "created")
        self.assertEqual(report["hooks_path_action"], "unchanged")
        self.assertFalse((created.parent / "pre-commit.suite-preserved").exists())

    def test_cognitive_word_is_not_a_complexity_checker(self):
        self.write_exec(
            ".git/hooks/pre-commit",
            "#!/bin/sh\n# cognitive is not a detection\nexit 0\n",
        )
        report = self.confirmed()
        text = (self.ws / ".git" / "hooks" / "pre-commit").read_text()
        self.assertEqual(report["complexity_action"], "installed")
        self.assertIn("complexity_gate.py", text)

    def test_hooks_path_outside_the_workspace_refuses(self):
        outside = self.keep(Path(tempfile.mkdtemp()))
        _git(self.ws, "config", "core.hooksPath", str(outside))
        code, out, err = self.cli(
            ["--workspace", str(self.ws), "--workspace-confirmed", "--output-json"]
        )
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["hooks_path_action"], "refused")
        self.assertEqual(data["loc_action"], "refused")
        self.assertEqual(data["complexity_action"], "refused")
        self.assertIs(data["wrote"], False)
        self.assertFalse((outside / "pre-commit").exists())
        self.assertEqual(self.hooks_path(), str(outside))
        self.assertIn("outside the workspace", err)

    def test_non_executable_pre_commit_refuses(self):
        original = "#!/bin/sh\n# LOC-EXEMPT: off\necho stay\nexit 0\n"
        live = self.write(".git/hooks/pre-commit", original, 0o644)
        code, out, err = self.cli(
            ["--workspace", str(self.ws), "--workspace-confirmed", "--output-json"]
        )
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["loc_action"], "refused")
        self.assertEqual(data["complexity_action"], "refused")
        self.assertEqual(data["hooks_path_action"], "unchanged")
        self.assertIs(data["wrote"], False)
        self.assertIs(data["length_runs"], False)
        self.assertEqual(live.read_text(), original)
        self.assertEqual(stat.S_IMODE(live.stat().st_mode), 0o644)
        self.assertFalse((live.parent / "pre-commit.suite-preserved").exists())
        self.assertIsNone(self.hooks_path())
        self.assertIn("not executable", err)

    def test_interrupted_wrap_refuses_without_touching_either_file(self):
        live_text = "#!/bin/sh\necho LIVE-ORIGINAL\nexit 0\n"
        preserved_text = "#!/bin/sh\necho PRESERVED-ORIGINAL\nexit 0\n"
        live = self.write_exec(".git/hooks/pre-commit", live_text)
        preserved = self.write(".git/hooks/pre-commit.suite-preserved", preserved_text, 0o700)
        code, out, err = self.cli(
            ["--workspace", str(self.ws), "--workspace-confirmed", "--output-json"]
        )
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["loc_action"], "refused")
        self.assertIs(data["wrote"], False)
        self.assertEqual(live.read_text(), live_text)
        self.assertEqual(preserved.read_text(), preserved_text)
        self.assertTrue(live.exists())
        self.assertTrue(preserved.exists())
        self.assertIn("not a chain", err)

    def test_preseeded_config_is_not_rewritten(self):
        body = (
            "[loc]\n"
            "reject = 600\n"
            "maintain = 300\n"
            "aim = 100\n"
            "\n"
            "[complexity]\n"
            "cognitive = 20\n"
            "max_args = 7\n"
        )
        path = self.seed_config(body)
        before = path.stat().st_mtime_ns
        report = self.confirmed()
        self.assertEqual(path.read_text(), body)
        self.assertEqual(path.stat().st_mtime_ns, before)
        self.assertEqual(report["config_action"], "left-existing")
        self.assertEqual(report["loc_reject"], 600)
        self.assertEqual(report["loc_maintain"], 300)
        self.assertEqual(report["loc_aim"], 100)
        self.assertEqual(report["cognitive"], 20)
        self.assertEqual(report["max_args"], 7)
        self.assertEqual(report["ceilings_source"], "config")

    def test_empty_config_stays_byte_identical(self):
        path = self.seed_config("")
        before = path.stat().st_mtime_ns
        report = self.confirmed()
        self.assertEqual(path.read_bytes(), b"")
        self.assertEqual(path.stat().st_mtime_ns, before)
        self.assert_rejected_ceilings(report)
        stream = self.assert_hook_rejects_config("empty_cfg.py")
        self.assertIn("suite-gates.cfg rejected: whitespace-only", stream)

    def test_unparsable_config_stays_byte_identical(self):
        path = self.seed_config("[[[broken\n")
        before = path.read_bytes()
        stamp = path.stat().st_mtime_ns
        report = self.confirmed()
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, stamp)
        self.assert_rejected_ceilings(report)
        self.assert_hook_rejects_config("bad_cfg.py")


class TestHookRuntime(Repo):
    def _git_only_path(self):
        bindir = self.keep(Path(tempfile.mkdtemp()))
        os.symlink("/usr/bin/git", bindir / "git")
        return str(bindir)

    def test_missing_python3_fails_closed_before_either_section(self):
        self.confirmed()
        self.write("ok.py", "x = 1\n")
        self.add("ok.py")
        proc = self.product_commit("needs python", ["ok.py"], path_env=self._git_only_path())
        self.assertEqual(proc.returncode, 1)
        stream = commit_hook_output(proc)
        self.assertIn(FAIL_PYTHON, stream)
        self.assertNotIn("not a file", stream)
        self.assertNotIn("band=", stream)
        self.assertIsNone(self.rev())

    def test_one_missing_script_still_runs_the_other_section(self):
        fake = self.keep(Path(tempfile.mkdtemp()))
        hooks = fake / "scripts" / "hooks"
        hooks.mkdir(parents=True)
        os.symlink(
            Path(install_gates.__file__).resolve().parent / "complexity_gate.py",
            hooks / "complexity_gate.py",
        )
        missing = hooks / "loc_gate.py"
        self.assertFalse(missing.exists())
        text = hook_text.render(str(fake), preserved=False, length=True, complexity=True)
        self.write_exec(".git/hooks/pre-commit", text)
        self.write("c.py", _ifs(16))
        self.add("c.py")
        proc = self.product_commit("one missing", ["c.py"])
        self.assertEqual(proc.returncode, 1)
        stream = commit_hook_output(proc)
        self.assertIn(
            f"SUITE GATES FAILED CLOSED — cannot start {missing}: not a file",
            stream,
        )
        self.assertIn("complexity ", stream)

    def test_campaign_skip_is_not_exported(self):
        self.confirmed()
        self.write("god.py", _statements(500))
        self.add("god.py")
        parent_skip = os.environ.get("SUITE_GATES_SKIP")
        failed = self.product_commit("refactor: extract concern to god.py", ["god.py"])
        self.assertNotEqual(failed.returncode, 0)
        stream = commit_hook_output(failed)
        self.assertIn("loc ", stream)
        self.assertIn("band=reject", stream)
        self.assertIsNone(self.rev())

        skipped = self.product_commit(
            "refactor: extract concern to god.py",
            ["god.py"],
            skip=True,
        )
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertIn(LOUD, commit_hook_output(skipped))
        self.assertEqual(os.environ.get("SUITE_GATES_SKIP"), parent_skip)
        stored = _git(self.ws, "config", "--get-regexp", "SUITE_GATES", check=False)
        self.assertNotEqual(stored.returncode, 0)
        self.assertEqual(stored.stdout.strip(), "")
        landed = self.rev()
        self.assertIsNotNone(landed)

        self.write("wide.py", _statements(500))
        self.add("wide.py")
        again = self.product_commit("refactor: extract concern to wide.py", ["wide.py"])
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("band=reject", commit_hook_output(again))
        self.assertEqual(self.rev(), landed)

    def test_one_line_shim_on_a_500_line_file_already_in_head(self):
        self.confirmed()
        self.write("god.py", _statements(500))
        self.add("god.py")
        self.commit("fixture 500")
        landed = self.rev()
        path = self.ws / "god.py"
        path.write_text(path.read_text() + "shim = 1\n")
        self.add("god.py")
        failed = self.product_commit("refactor: extract concern to god.py", ["god.py"])
        self.assertNotEqual(failed.returncode, 0)
        stream = commit_hook_output(failed)
        self.assertIn("loc ", stream)
        self.assertIn("band=reject", stream)
        self.assertEqual(self.rev(), landed)
        skipped = self.product_commit(
            "refactor: extract concern to god.py",
            ["god.py"],
            skip=True,
        )
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertIn(LOUD, commit_hook_output(skipped))
        self.assertNotEqual(self.rev(), landed)

    def test_path_limited_skip_leaves_the_syntax_error_staged(self):
        self.write("base.txt", "base\n")
        self.add("base.txt")
        self.commit("base")
        self.confirmed()
        self.write("bad.py", "def (\n")
        self.add("bad.py")
        self.write("god.py", _statements(500))
        self.add("god.py")
        skipped = self.product_commit(
            "refactor: extract concern to god.py",
            ["god.py"],
            skip=True,
        )
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertIn(LOUD, commit_hook_output(skipped))
        names = self.show_names()
        self.assertIn("god.py", names)
        self.assertNotIn("bad.py", names)
        cached = _git(self.ws, "diff", "--cached", "--name-only").stdout
        self.assertIn("bad.py", cached)
        self.assertNotIn("god.py", cached)
        failed = self.product_commit("keep the syntax error", ["bad.py"])
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("syntax error in bad.py", commit_hook_output(failed))
        self.assertNotIn(LOUD, commit_hook_output(failed))

    def test_untracked_pathspec_does_not_run_the_hook(self):
        self.write("base.txt", "base\n")
        self.add("base.txt")
        self.commit("base")
        self.write_exec(".git/hooks/pre-commit", "#!/bin/sh\necho HOOK-RAN\nexit 0\n")
        self.confirmed()
        self.write("new_module.py", "x = 1\n")
        head = self.rev()
        failed = self.product_commit(
            "refactor: extract concern to new_module.py",
            ["new_module.py"],
        )
        self.assertEqual(failed.returncode, 1)
        self.assertIn("did not match any file(s) known to git", failed.stderr)
        self.assertNotIn("HOOK-RAN", failed.stdout)
        self.assertNotIn("HOOK-RAN", failed.stderr)
        self.assertNotIn(LOUD, failed.stderr)
        self.assertEqual(self.rev(), head)
        self.add("new_module.py")
        skipped = self.product_commit(
            "refactor: extract concern to new_module.py",
            ["new_module.py"],
            skip=True,
        )
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        stream = commit_hook_output(skipped)
        self.assertIn("HOOK-RAN", stream)
        self.assertIn(LOUD, stream)
        self.assertLess(stream.index("HOOK-RAN"), stream.index(LOUD))
        self.assertNotEqual(self.rev(), head)
        self.assertIn("new_module.py", self.show_names())

    def test_ignored_receipt_is_not_added_or_committed(self):
        self.write(".gitignore", ".workflow_state/\n")
        self.write("SOC_MANIFEST.md", "tracked\n")
        self.add(".gitignore", "SOC_MANIFEST.md")
        self.commit("base")
        self.confirmed()
        manifest = self.ws / "SOC_MANIFEST.md"
        manifest.write_text(manifest.read_text() + "dirty\n")
        self.write(".workflow_state/receipts/SOC_RECEIPTS.md", "receipt\n")
        added = _git(
            self.ws,
            "add",
            "--",
            "SOC_MANIFEST.md",
            ".workflow_state/receipts/SOC_RECEIPTS.md",
            check=False,
        )
        self.assertEqual(added.returncode, 1)
        self.assertIn("ignored by one of your .gitignore files", added.stderr)
        cached = _git(self.ws, "diff", "--cached", "--name-only").stdout
        self.assertIn("SOC_MANIFEST.md", cached)
        self.assertNotIn("SOC_RECEIPTS", cached)
        head = self.rev()
        committed = self.product_commit(
            "chore: soc complete for module -- receipt filed",
            ["SOC_MANIFEST.md", ".workflow_state/receipts/SOC_RECEIPTS.md"],
            skip=True,
        )
        self.assertEqual(committed.returncode, 1)
        self.assertIn("did not match any file(s) known to git", committed.stderr)
        self.assertEqual(self.rev(), head)
        _git(self.ws, "reset", "-q")
        self.add("SOC_MANIFEST.md")
        landed = self.product_commit(
            "chore: soc complete for module -- receipt filed",
            ["SOC_MANIFEST.md"],
            skip=True,
        )
        self.assertEqual(landed.returncode, 0, landed.stderr)
        self.assertIn(LOUD, commit_hook_output(landed))
        names = self.show_names()
        self.assertIn("SOC_MANIFEST.md", names)
        self.assertNotIn("SOC_RECEIPTS", names)
        self.assertNotIn(".workflow_state", names)
        ignored = _git(
            self.ws, "check-ignore", "--", ".workflow_state/receipts/SOC_RECEIPTS.md",
        )
        self.assertIn("SOC_RECEIPTS.md", ignored.stdout)
        self.assertTrue((self.ws / ".workflow_state" / "receipts" / "SOC_RECEIPTS.md").is_file())


class TestRevertPreflight(Repo):
    def test_clean_revert_does_not_run_the_commit_hook(self):
        self.write("base.txt", "base\n")
        self.add("base.txt")
        self.commit("base")
        self.write_exec(".git/hooks/pre-commit", "#!/bin/sh\necho ran >> hook.log\nexit 0\n")
        self.write("tracked.py", "x = 1\n")
        self.add("tracked.py")
        made = self.product_commit("add tracked", ["tracked.py"])
        self.assertEqual(made.returncode, 0, made.stderr)
        log = self.ws / "hook.log"
        self.assertIn("ran", log.read_text())
        before = log.read_text()
        self.assertTrue(product_revert_preflight(self.ws))
        proc = self.revert()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(log.read_text(), before)
        self.assertTrue(self.subject().startswith("Revert "))
        self.assertNotIn("SUITE_GATES_SKIP", proc.args)

    def test_staged_change_stops_the_product_and_revert_exits_128(self):
        self.write("a.txt", "a\n")
        self.add("a.txt")
        self.commit("base")
        self.write("a.txt", "a2\n")
        self.add("a.txt")
        self.commit("change")
        self.write("other.txt", "staged\n")
        self.add("other.txt")
        cached = _git(self.ws, "diff", "--cached", "--quiet", check=False)
        self.assertEqual(cached.returncode, 1)
        self.assertFalse(product_revert_preflight(self.ws))
        head = self.rev()
        proc = self.revert()
        self.assertEqual(proc.returncode, 128)
        self.assertIn("your local changes would be overwritten by revert", proc.stderr)
        self.assertEqual(self.rev(), head)

    def test_unstaged_edit_of_a_reverted_path_stops(self):
        self.write("f.txt", "v1\n")
        self.add("f.txt")
        self.commit("v1")
        self.write("f.txt", "v2\n")
        self.add("f.txt")
        self.commit("v2")
        self.write("f.txt", "v3\n")
        cached = _git(self.ws, "diff", "--cached", "--quiet", check=False)
        self.assertEqual(cached.returncode, 0)
        listed = _git(self.ws, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
        self.assertIn("f.txt", listed.stdout.splitlines())
        dirty = _git(self.ws, "diff", "--quiet", "--", "f.txt", check=False)
        self.assertEqual(dirty.returncode, 1)
        self.assertFalse(product_revert_preflight(self.ws))
        head = self.rev()
        proc = self.revert()
        self.assertEqual(proc.returncode, 128)
        self.assertIn("overwritten by merge", proc.stderr)
        self.assertEqual(self.rev(), head)
        self.assertEqual((self.ws / "f.txt").read_text(), "v3\n")

    def test_unrelated_dirt_does_not_refuse_the_revert(self):
        self.write("a.txt", "a\n")
        self.write("b.txt", "b\n")
        self.write(".gitignore", "d.txt\n")
        self.add("a.txt", "b.txt", ".gitignore")
        self.commit("base")
        self.write("a.txt", "a2\n")
        self.add("a.txt")
        self.commit("change a")
        self.write("b.txt", "b-dirty\n")
        self.write("c.txt", "untracked\n")
        self.write("d.txt", "ignored\n")
        self.assertTrue(product_revert_preflight(self.ws))
        proc = self.revert()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.subject(), 'Revert "change a"')
        self.assertEqual((self.ws / "b.txt").read_text(), "b-dirty\n")
        self.assertEqual((self.ws / "c.txt").read_text(), "untracked\n")
        self.assertEqual((self.ws / "d.txt").read_text(), "ignored\n")

    def test_empty_diff_tree_does_not_list_every_untracked_path(self):
        self.write("base.txt", "base\n")
        self.add("base.txt")
        self.commit("base")
        _git(self.ws, "commit", "--allow-empty", "--no-verify", "-m", "empty")
        listed = _git(self.ws, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
        self.assertEqual(listed.stdout.strip(), "")
        self.write("junk.txt", "junk\n")
        bare = _git(self.ws, "ls-files", "--others", "--")
        self.assertIn("junk.txt", bare.stdout)
        self.assertTrue(product_revert_preflight(self.ws))

    def test_content_conflict_aborts_without_continue(self):
        self.write("line.txt", "base\n")
        self.add("line.txt")
        self.commit("base")
        self.write("line.txt", "a-line\n")
        self.add("line.txt")
        self.commit("A")
        sha_a = self.rev()
        self.write("line.txt", "b-line\n")
        self.add("line.txt")
        self.commit("B")
        sha_b = self.rev()
        cached = _git(self.ws, "diff", "--cached", "--quiet", check=False)
        quiet = _git(self.ws, "diff", "--quiet", "--", "line.txt", check=False)
        self.assertEqual(cached.returncode, 0)
        self.assertEqual(quiet.returncode, 0)
        others = _git(self.ws, "ls-files", "--others", "--", "line.txt")
        self.assertEqual(others.stdout.strip(), "")
        self.assertTrue(product_revert_preflight(self.ws, sha_a))
        proc = self.revert(sha_a)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("CONFLICT (content)", proc.stdout)
        status = _git(self.ws, "status", "--short").stdout.strip()
        self.assertTrue(status.startswith("UU"))
        self.assertIn("line.txt", status)
        self.assertTrue((self.ws / ".git" / "REVERT_HEAD").exists())
        self.assertEqual(self.rev(), sha_b)
        aborted = _git(self.ws, "revert", "--abort")
        self.assertEqual(aborted.returncode, 0)
        self.assertFalse((self.ws / ".git" / "REVERT_HEAD").exists())
        self.assertEqual(_git(self.ws, "status", "--short").stdout.strip(), "")
        self.assertEqual((self.ws / "line.txt").read_text(), "b-line\n")
        self.assertEqual(self.rev(), sha_b)

    def test_non_ignored_untracked_occupant_stops_and_revert_keeps_bytes(self):
        self.write("gone.py", "original\n")
        self.add("gone.py")
        self.commit("add")
        _git(self.ws, "rm", "-q", "--", "gone.py")
        self.commit("delete")
        self.write("gone.py", "keep-me\n")
        cached = _git(self.ws, "diff", "--cached", "--quiet", check=False)
        quiet = _git(self.ws, "diff", "--quiet", "--", "gone.py", check=False)
        self.assertEqual(cached.returncode, 0)
        self.assertEqual(quiet.returncode, 0)
        others = _git(self.ws, "ls-files", "--others", "--", "gone.py", check=False)
        self.assertEqual(others.returncode, 0)
        self.assertEqual(others.stdout.strip(), "gone.py")
        self.assertFalse(product_revert_preflight(self.ws))
        self.assertEqual((self.ws / "gone.py").read_text(), "keep-me\n")
        proc = self.revert()
        self.assertEqual(proc.returncode, 128)
        self.assertIn(
            "untracked working tree files would be overwritten by merge",
            proc.stderr,
        )
        self.assertFalse((self.ws / ".git" / "REVERT_HEAD").exists())
        self.assertEqual((self.ws / "gone.py").read_text(), "keep-me\n")

    def test_ignored_untracked_occupant_is_not_deleted(self):
        self.write("gone.py", "original\n")
        self.add("gone.py")
        self.commit("add")
        self.write(".gitignore", "gone.py\n")
        self.add(".gitignore")
        self.commit("ignore")
        _git(self.ws, "rm", "-q", "--", "gone.py")
        self.commit("delete")
        self.write("gone.py", "ignored-keep\n")
        cached = _git(self.ws, "diff", "--cached", "--quiet", check=False)
        quiet = _git(self.ws, "diff", "--quiet", "--", "gone.py", check=False)
        self.assertEqual(cached.returncode, 0)
        self.assertEqual(quiet.returncode, 0)
        hidden = _git(
            self.ws, "ls-files", "--others", "--exclude-standard", "--", "gone.py", check=False,
        )
        self.assertEqual(hidden.returncode, 0)
        self.assertEqual(hidden.stdout.strip(), "")
        shown = _git(self.ws, "ls-files", "--others", "--", "gone.py", check=False)
        self.assertEqual(shown.returncode, 0)
        self.assertEqual(shown.stdout.strip(), "gone.py")
        self.assertFalse(product_revert_preflight(self.ws))
        self.assertEqual((self.ws / "gone.py").read_text(), "ignored-keep\n")
        proc = self.revert()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.subject(), 'Revert "delete"')
        self.assertFalse((self.ws / ".git" / "REVERT_HEAD").exists())
        self.assertEqual((self.ws / "gone.py").read_text(), "original\n")

    def test_ignored_directory_occupant_is_the_same_overwrite(self):
        self.write("sub/gone.py", "original\n")
        self.add("sub/gone.py")
        self.commit("add")
        self.write(".gitignore", "sub/\n")
        self.add(".gitignore")
        self.commit("ignore")
        _git(self.ws, "rm", "-q", "--", "sub/gone.py")
        self.commit("delete")
        self.write("sub/gone.py", "ignored-keep\n")
        shown = _git(self.ws, "ls-files", "--others", "--", "sub/gone.py", check=False)
        self.assertEqual(shown.returncode, 0)
        self.assertEqual(shown.stdout.strip(), "sub/gone.py")
        hidden = _git(
            self.ws,
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            "sub/gone.py",
            check=False,
        )
        self.assertEqual(hidden.stdout.strip(), "")
        self.assertFalse(product_revert_preflight(self.ws))
        self.assertEqual((self.ws / "sub" / "gone.py").read_text(), "ignored-keep\n")
        proc = self.revert()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.subject(), 'Revert "delete"')
        self.assertFalse((self.ws / ".git" / "REVERT_HEAD").exists())
        self.assertEqual((self.ws / "sub" / "gone.py").read_text(), "original\n")


if __name__ == "__main__":
    unittest.main()
