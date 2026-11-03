"""Temp-repo tests for the staged length and complexity CLIs.

Fixture history is committed with --no-verify. The path under test is the CLI.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOC_GATE = ROOT / "scripts" / "hooks" / "loc_gate.py"
COG_GATE = ROOT / "scripts" / "hooks" / "complexity_gate.py"

_DEFAULT_CFG = """\
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


def _ifs(count, name="keep", param="a"):
    lines = [f"def {name}({param}):"]
    lines += ["    if a: return 1"] * count
    return "\n".join(lines) + "\n"


def _keep_gone(ifs=16, pad=0):
    lines = ["def keep(a):"]
    lines += ["    if a: return 1"] * ifs
    lines += ["def gone():", "    return 0"]
    lines += ["x = 1"] * pad
    return "\n".join(lines) + "\n"


def _keep_only(ifs=16, pad=0):
    lines = ["def keep(a):"]
    lines += ["    if a: return 1"] * ifs
    lines += ["x = 1"] * pad
    return "\n".join(lines) + "\n"


class RepoMixin:
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        _git(self.ws, "init", "-q")
        _git(self.ws, "config", "user.email", "test@example.com")
        _git(self.ws, "config", "user.name", "Test")
        _git(self.ws, "config", "commit.gpgsign", "false")
        _git(self.ws, "config", "diff.renames", "false")

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def write(self, name, text):
        path = self.ws / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text)
        return path

    def add(self, *names):
        _git(self.ws, "add", "--", *names)

    def commit(self, msg="fixture"):
        _git(self.ws, "commit", "--no-verify", "-m", msg)

    def plant_cfg(self, text=_DEFAULT_CFG):
        directory = self.ws / ".githooks"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "suite-gates.cfg").write_text(text)

    def gate(self, script):
        return subprocess.run(
            [sys.executable, str(script), "--staged", "--workspace", str(self.ws)],
            capture_output=True,
            text=True,
        )

    def loc(self):
        return self.gate(LOC_GATE)

    def cog(self):
        return self.gate(COG_GATE)


class TestUsage(unittest.TestCase):
    def test_staged_is_required(self):
        for script in (LOC_GATE, COG_GATE):
            proc = subprocess.run(
                [sys.executable, str(script), "--workspace", "/tmp"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2, script.name)


class TestNoPython(RepoMixin, unittest.TestCase):
    def test_no_staged_python_is_silent_even_with_a_bad_config(self):
        self.plant_cfg("   \n\t\n")
        self.write("readme.txt", "hello\n")
        self.add("readme.txt")
        for proc in (self.loc(), self.cog()):
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertNotIn("suite-gates.cfg", proc.stdout)

    def test_empty_index_is_silent(self):
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


class TestLocBands(RepoMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plant_cfg()

    def _stage_statements(self, count, name="a.py"):
        self.write(name, _statements(count))
        self.add(name)

    def test_reject_at_500(self):
        self._stage_statements(500)
        proc = self.loc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            "loc a.py executable=500 aim=150 maintain=200 reject=500 band=reject exempt=-",
            proc.stdout,
        )

    def test_499_does_not_reject(self):
        self._stage_statements(499)
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("executable=499", proc.stdout)
        self.assertIn("band=maintain", proc.stdout)
        self.assertNotIn("band=reject", proc.stdout)

    def test_maintenance_at_200(self):
        self._stage_statements(200)
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertIn(
            "loc a.py executable=200 aim=150 maintain=200 reject=500 band=maintain exempt=-",
            proc.stdout,
        )

    def test_aim_at_151_and_199(self):
        self._stage_statements(151, "low.py")
        self._stage_statements(199, "high.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("loc low.py executable=151 aim=150 maintain=200 reject=500 band=aim exempt=-", proc.stdout)
        self.assertIn("loc high.py executable=199 aim=150 maintain=200 reject=500 band=aim exempt=-", proc.stdout)

    def test_silence_at_150_and_under(self):
        self._stage_statements(150, "edge.py")
        self._stage_statements(149, "under.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_comments_and_docstring_do_not_reject(self):
        comments = "\n".join(["# note"] * 500 + ["x = 1"] * 10) + "\n"
        self.write("comments.py", comments)
        doc = ["\"\"\""] + ["prose"] * 398 + ["\"\"\""]
        self.write("doc.py", "\n".join(doc + ["x = 1"] * 10) + "\n")
        self.add("comments.py", "doc.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")
        self.assertNotIn("executable=0", proc.stdout)


class TestLocExemptions(RepoMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plant_cfg()
        self.body = _statements(500)

    def test_staged_marker_does_not_reject(self):
        self.write("a.py", "# LOC-EXEMPT: reason\n" + self.body)
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("band=exempt exempt=reason", proc.stdout)
        self.assertNotIn("band=reject", proc.stdout)

    def test_worktree_only_marker_still_rejects(self):
        self.write("a.py", self.body)
        self.add("a.py")
        self.write("a.py", "# LOC-EXEMPT: reason\n" + self.body)
        proc = self.loc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("band=reject exempt=-", proc.stdout)
        self.assertNotIn("band=exempt", proc.stdout)

    def test_string_spelling_does_not_exempt(self):
        lines = ['s = "# LOC-EXEMPT: reason"'] + ["x = 1"] * 499
        self.write("a.py", "\n".join(lines) + "\n")
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("executable=500", proc.stdout)
        self.assertIn("band=reject exempt=-", proc.stdout)

    def test_empty_reason_does_not_exempt(self):
        self.write("a.py", "# LOC-EXEMPT:\n" + self.body)
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            "loc a.py executable=500 aim=150 maintain=200 reject=500 band=reject exempt=- empty-reason=LOC-EXEMPT",
            proc.stdout,
        )

    def test_empty_then_real_reason_uses_the_non_empty_one(self):
        self.write("a.py", "# LOC-EXEMPT:\n# LOC-EXEMPT: real reason\n" + self.body)
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("band=exempt exempt=real reason", proc.stdout)
        self.assertNotIn("empty-reason", proc.stdout)

    def test_exemption_does_not_relabel_maintain(self):
        self.write("a.py", "# LOC-EXEMPT: because\n" + _statements(200))
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("band=maintain exempt=because", proc.stdout)
        self.assertNotIn("band=exempt", proc.stdout)

    def test_loc_exempt_does_not_exempt_cognitive(self):
        self.write("a.py", "# LOC-EXEMPT: reason\n" + _ifs(16, name="f"))
        self.add("a.py")
        loc = self.loc()
        cog = self.cog()
        self.assertEqual(loc.returncode, 0)
        self.assertEqual(cog.returncode, 1)
        self.assertIn("complexity a.py::f ", cog.stdout)
        self.assertIn("result=reject", cog.stdout)
        self.assertIn("failed=cognitive", cog.stdout)
        self.assertIn("exempt=-", cog.stdout)


class TestComplexity(RepoMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plant_cfg()

    def test_sixteen_ifs_reject(self):
        self.write("a.py", _ifs(16, name="f"))
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("cognitive=16", proc.stdout)
        self.assertIn("mccabe=17", proc.stdout)
        self.assertIn('mccabe_note="informational only; not a gate"', proc.stdout)
        self.assertIn("result=reject failed=cognitive exempt=-", proc.stdout)

    def test_fifteen_ifs_high_mccabe_is_silent(self):
        self.write("a.py", _ifs(15, name="wide"))
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("complexity ", proc.stdout)

    def test_cog_exempt_does_not_save_argument_count(self):
        src = (
            "def f(a, b, c, d, e, g):  # COG-EXEMPT: dispatcher\n"
            + "    if a: return 1\n" * 16
        )
        self.write("a.py", src)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("result=reject failed=args exempt=COG", proc.stdout)

    def test_args_exempt_does_not_save_cognitive(self):
        src = (
            "def f(a, b, c, d, e, g):  # ARGS-EXEMPT: dispatcher\n"
            + "    if a: return 1\n" * 16
        )
        self.write("a.py", src)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("result=reject failed=cognitive exempt=ARGS", proc.stdout)

    def test_both_markers_save_both_checks(self):
        src = (
            "def f(a, b, c, d, e, g):  # COG-EXEMPT: c\n"
            "    # ARGS-EXEMPT: a\n"
            + "    if a: return 1\n" * 16
        )
        self.write("a.py", src)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 0)
        self.assertIn("result=exempt failed=- exempt=COG,ARGS", proc.stdout)

    def test_empty_reason_does_not_exempt_either_check(self):
        src = (
            "def f(a, b, c, d, e, g):  # COG-EXEMPT:\n"
            "    # ARGS-EXEMPT:\n"
            + "    if a: return 1\n" * 16
        )
        self.write("a.py", src)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("result=reject failed=cognitive,args exempt=-", proc.stdout)
        self.assertNotIn("empty-reason", proc.stdout)

    def test_decorator_marker_does_not_attach(self):
        src = "@deco  # COG-EXEMPT: reason\n" + _ifs(16, name="f")
        self.write("a.py", src)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("a.py::f ", proc.stdout)
        self.assertIn("result=reject failed=cognitive exempt=-", proc.stdout)

    def test_marker_below_docstring_does_not_attach(self):
        src = "def f():\n    \"\"\"doc\"\"\"\n    # COG-EXEMPT: reason\n" + "    if a: return 1\n" * 16
        self.write("a.py", src)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("result=reject failed=cognitive exempt=-", proc.stdout)

    def test_argument_count_over_five_rejects_and_exactly_five_passes(self):
        self.write("over.py", "def f(a, b, c, d, e, g):\n    return a\n")
        self.write("exact.py", "def g(a, b, c, d, e):\n    return a\n")
        self.add("over.py", "exact.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("over.py::f ", proc.stdout)
        self.assertIn("args=6", proc.stdout)
        self.assertIn("failed=args", proc.stdout)
        self.assertNotIn("exact.py", proc.stdout)

    def test_leading_self_or_cls_is_dropped(self):
        self.write("mod.py", "def f(self, a, b, c, d, e):\n    return a\n")
        self.write("box.py", "class Box:\n    def make(cls, a, b, c, d, e):\n        return a\n")
        self.add("mod.py", "box.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("complexity ", proc.stdout)

    def test_self_plus_six_fails(self):
        self.write("a.py", "def f(self, a, b, c, d, e, g):\n    return a\n")
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("args=6", proc.stdout)
        self.assertIn("failed=args", proc.stdout)

    def test_keyword_only_self_is_counted(self):
        self.write("a.py", "def f(a, b, c, d, e, *, self):\n    return a\n")
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("args=6", proc.stdout)
        self.assertIn("failed=args", proc.stdout)

    def test_nested_function_over_ceiling_prints_mccabe_one(self):
        src = "def outer():\n    def inner():\n" + "        if a: return 1\n" * 16 + "    return 0\n"
        self.write("a.py", src)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("a.py::outer.inner ", proc.stdout)
        self.assertIn("cognitive=32", proc.stdout)
        self.assertIn("mccabe=1", proc.stdout)
        self.assertIn(
            'mccabe_note="nested function has no McCabe graph of its own; '
            'displayed 1 is not a measurement and is not a gate"',
            proc.stdout,
        )
        self.assertEqual(proc.stdout.count("complexity "), 1)

    def test_edit_inside_nested_function_touches_the_outer_span(self):
        outer = "def outer(a):\n" + "    if a: return 1\n" * 16
        src = outer + "    def inner():\n        return 0\n"
        self.write("a.py", src)
        self.add("a.py")
        self.commit()
        self.write("a.py", outer + "    def inner():\n        return 1\n")
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("a.py::outer ", proc.stdout)
        self.assertNotIn("::outer.inner", proc.stdout)

    def test_decorator_edit_is_a_touch(self):
        src = "def deco(fn):\n    return fn\n\n@deco\n" + _ifs(16, name="f")
        self.write("a.py", src)
        self.add("a.py")
        self.commit()
        edited = src.replace("@deco\n", "@other\n", 1)
        self.write("a.py", edited)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("a.py::f ", proc.stdout)
        self.assertNotIn("::deco", proc.stdout)


class TestGrandfather(RepoMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plant_cfg()

    def test_untouched_file_over_500_does_not_fail(self):
        self.write("big.py", _statements(500))
        self.add("big.py")
        self.commit()
        self.write("other.py", "x = 1\n")
        self.add("other.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("big.py", proc.stdout)
        self.assertNotIn("band=reject", proc.stdout)
        self.assertEqual(proc.stdout, "")

    def test_untouched_function_in_a_touched_file_is_absent(self):
        heavy = "def heavy_untouched(a):\n" + "    if a: return 1\n" * 16
        src = heavy + "\ndef light():\n    return 0\n"
        self.write("mod.py", src)
        self.add("mod.py")
        self.commit()
        self.write("mod.py", heavy + "\ndef light():\n    return 1\n")
        self.add("mod.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("heavy_untouched", proc.stdout)
        self.assertEqual(proc.stdout, "")


class TestSyntax(RepoMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plant_cfg()

    def test_syntax_error_is_not_executable_zero_and_does_not_hide_the_next_file(self):
        self.write("bad.py", "def (\n")
        self.write("also.py", "x =\n")
        self.write("big.py", _statements(500))
        self.add("bad.py", "also.py", "big.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("syntax error in bad.py", proc.stdout)
        self.assertIn("syntax error in also.py", proc.stdout)
        self.assertIn("loc big.py", proc.stdout)
        self.assertIn("band=reject", proc.stdout)
        self.assertNotIn("executable=0", proc.stdout)
        cog = self.cog()
        self.assertEqual(cog.returncode, 1)
        self.assertIn("syntax error in bad.py", cog.stdout)
        self.assertIn("syntax error in also.py", cog.stdout)

    def test_non_utf8_blob_names_the_file_and_does_not_traceback(self):
        self.write("bad.py", b"\xff\xfe")
        self.add("bad.py")
        for script in (LOC_GATE, COG_GATE):
            proc = subprocess.run(
                [sys.executable, str(script), "--staged", "--workspace", str(self.ws)],
                capture_output=True,
                text=False,
            )
            stdout = proc.stdout.decode("utf-8", "replace")
            stderr = proc.stderr.decode("utf-8", "replace")
            self.assertEqual(proc.returncode, 1, script.name)
            self.assertIn("syntax error in bad.py", stdout)
            self.assertNotIn("Traceback", stderr)
            self.assertNotIn("UnicodeDecodeError", stderr)
            self.assertNotIn("executable=0", stdout)


class TestDeletionAndRename(RepoMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plant_cfg()

    def test_inplace_deletion_of_gone_does_not_touch_keep(self):
        self.write("a.py", _keep_gone())
        self.add("a.py")
        self.commit()
        self.write("a.py", _keep_only())
        self.add("a.py")
        loc = self.loc()
        cog = self.cog()
        self.assertEqual(loc.returncode, 0)
        self.assertEqual(cog.returncode, 0)
        self.assertEqual(loc.stdout, "")
        self.assertEqual(cog.stdout, "")
        self.assertNotIn("keep", loc.stdout)
        self.assertNotIn("keep", cog.stdout)
        self.assertNotIn("gone", cog.stdout)

    def test_deletion_of_one_if_inside_keep_rejects(self):
        self.write("a.py", _ifs(17))
        self.add("a.py")
        self.commit()
        self.write("a.py", _ifs(16))
        self.add("a.py")
        loc = self.loc()
        cog = self.cog()
        self.assertEqual(loc.returncode, 0)
        self.assertEqual(loc.stdout, "")
        self.assertEqual(cog.returncode, 1)
        self.assertIn("a.py::keep ", cog.stdout)
        self.assertIn("cognitive=16", cog.stdout)
        self.assertIn("result=reject", cog.stdout)

    def test_duplicate_qualname_pure_deletion_does_not_touch_the_survivor(self):
        first = "def f():\n" + "    if a: return 1\n" * 16
        src = first + "def f():\n    return 0\n"
        self.write("a.py", src)
        self.add("a.py")
        self.commit()
        self.write("a.py", first)
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_pure_rename_of_500_lines_is_not_judged(self):
        self.write("big.py", _statements(500))
        self.add("big.py")
        self.commit()
        _git(self.ws, "mv", "big.py", "big_renamed.py")
        status = _git(
            self.ws, "-c", "diff.renames=false", "diff", "--cached", "-M", "--name-status", "-z",
        )
        self.assertIn("R100\0big.py\0big_renamed.py\0", status.stdout)
        both = _git(self.ws, "diff", "--cached", "-M", "-U0", "--", "big.py", "big_renamed.py")
        self.assertNotIn("@@", both.stdout)
        dest = _git(self.ws, "diff", "--cached", "-M", "-U0", "--", "big_renamed.py")
        self.assertIn("--- /dev/null", dest.stdout)
        missing = _git(self.ws, "show", "HEAD:big_renamed.py", check=False)
        self.assertNotEqual(missing.returncode, 0)
        loc = self.loc()
        cog = self.cog()
        self.assertEqual(loc.returncode, 0)
        self.assertEqual(cog.returncode, 0)
        self.assertEqual(loc.stdout, "")
        self.assertEqual(cog.stdout, "")
        self.assertNotIn("loc ", loc.stdout)

    def test_short_rename_plus_deletion(self):
        self.write("a.py", _keep_gone())
        self.add("a.py")
        self.commit()
        _git(self.ws, "mv", "a.py", "b.py")
        self.write("b.py", _keep_only())
        self.add("b.py")
        status = _git(
            self.ws, "-c", "diff.renames=false", "diff", "--cached", "-M", "--name-status", "-z",
        )
        self.assertIn("R092\0a.py\0b.py\0", status.stdout)
        self.assertTrue(status.stdout.startswith("R"))
        both = _git(self.ws, "diff", "--cached", "-M", "-U0", "--", "a.py", "b.py")
        self.assertIn("@@ -18,2 +17,0 @@", both.stdout)
        self.assertNotIn("--- /dev/null", both.stdout)
        loc = self.loc()
        cog = self.cog()
        self.assertEqual(loc.returncode, 0)
        self.assertEqual(cog.returncode, 0)
        self.assertNotIn("keep", loc.stdout)
        self.assertNotIn("keep", cog.stdout)
        self.assertNotIn("loc ", loc.stdout)
        self.assertNotIn("executable=", loc.stdout)

    def test_padded_rename_plus_deletion_rejects_length_not_keep(self):
        self.write("a.py", _keep_gone(pad=483))
        self.add("a.py")
        self.commit()
        _git(self.ws, "mv", "a.py", "b.py")
        self.write("b.py", _keep_only(pad=483))
        self.add("b.py")
        status = _git(
            self.ws, "-c", "diff.renames=false", "diff", "--cached", "-M", "--name-status", "-z",
        )
        self.assertIn("R099\0a.py\0b.py\0", status.stdout)
        self.assertNotIn("R092", status.stdout)
        self.assertNotIn("D\0", status.stdout)
        self.assertNotIn("A\0", status.stdout)
        both = _git(self.ws, "diff", "--cached", "-M", "-U0", "--", "a.py", "b.py")
        self.assertIn("@@ -18,2 +17,0 @@", both.stdout)
        loc = self.loc()
        cog = self.cog()
        self.assertEqual(loc.returncode, 1)
        self.assertIn("loc ", loc.stdout)
        self.assertIn("band=reject", loc.stdout)
        self.assertIn("executable=500", loc.stdout)
        self.assertNotIn("keep", loc.stdout)
        self.assertEqual(cog.returncode, 0)
        self.assertNotIn("keep", cog.stdout)


class TestConfigCli(RepoMixin, unittest.TestCase):
    def test_missing_config_prints_defaults_and_still_rejects_at_500(self):
        self.write("a.py", _statements(500))
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn(
            "suite-gates.cfg missing; using defaults "
            "(reject 500, maintain 200, aim 150, cognitive 15, max_args 5).",
            proc.stdout,
        )
        self.assertIn("band=reject", proc.stdout)
        self.assertNotIn("suite-gates.cfg rejected:", proc.stdout)

    def _rejected(self, text):
        self.plant_cfg(text)
        self.write("a.py", "x = 1\n")
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("suite-gates.cfg rejected:", proc.stdout)
        self.assertNotIn("suite-gates.cfg missing; using defaults", proc.stdout)
        self.assertNotIn("executable=", proc.stdout)
        cog = self.cog()
        self.assertEqual(cog.returncode, 1)
        self.assertIn("suite-gates.cfg rejected:", cog.stdout)
        self.assertNotIn("suite-gates.cfg missing; using defaults", cog.stdout)

    def test_whitespace_only_is_rejected(self):
        self._rejected(" \n\t\n")

    def test_parse_error_is_rejected(self):
        self._rejected("[loc\nreject = 500\n")

    def test_non_integer_is_rejected(self):
        self._rejected(
            "[loc]\nreject = abc\nmaintain = 200\naim = 150\n\n"
            "[complexity]\ncognitive = 15\nmax_args = 5\n"
        )

    def test_negative_is_rejected(self):
        self._rejected(
            "[loc]\nreject = 500\nmaintain = 200\naim = 150\n\n"
            "[complexity]\ncognitive = -1\nmax_args = 5\n"
        )

    def test_reject_200_is_rejected(self):
        self._rejected(
            "[loc]\nreject = 200\nmaintain = 100\naim = 50\n\n"
            "[complexity]\ncognitive = 15\nmax_args = 5\n"
        )

    def test_reject_not_greater_than_maintain_is_rejected(self):
        self._rejected(
            "[loc]\nreject = 400\nmaintain = 400\naim = 100\n\n"
            "[complexity]\ncognitive = 15\nmax_args = 5\n"
        )

    def test_omitted_key_uses_that_default_and_names_the_key(self):
        self.plant_cfg(
            "[loc]\nreject = 500\nmaintain = 200\naim = 150\n\n"
            "[complexity]\ncognitive = 15\n"
        )
        self.write("a.py", "def f(a, b, c, d, e, g):\n    return a\n")
        self.add("a.py")
        proc = self.cog()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("suite-gates.cfg missing key max_args; using default 5.", proc.stdout)
        self.assertIn("max_args=5", proc.stdout)
        self.assertIn("failed=args", proc.stdout)
        self.assertNotIn("suite-gates.cfg missing; using defaults", proc.stdout)
        self.assertNotIn("missing key cognitive", proc.stdout)

    def test_comment_only_file_names_missing_keys(self):
        self.plant_cfg("# ceiling notes only\n")
        self.write("a.py", "x = 1\n")
        self.add("a.py")
        proc = self.loc()
        self.assertEqual(proc.returncode, 0)
        for key, value in (
            ("reject", 500),
            ("maintain", 200),
            ("aim", 150),
            ("cognitive", 15),
            ("max_args", 5),
        ):
            self.assertIn(f"suite-gates.cfg missing key {key}; using default {value}.", proc.stdout)
        self.assertNotIn("suite-gates.cfg missing; using defaults", proc.stdout)
        self.assertNotIn("suite-gates.cfg rejected:", proc.stdout)
        self.assertNotIn("executable=", proc.stdout)

    def test_reject_600_is_the_live_reject(self):
        self.plant_cfg(
            "[loc]\nreject = 600\nmaintain = 200\naim = 150\n\n"
            "[complexity]\ncognitive = 15\nmax_args = 5\n"
        )
        self.write("under.py", _statements(599))
        self.add("under.py")
        under = self.loc()
        self.assertEqual(under.returncode, 0)
        self.assertIn("reject=600", under.stdout)
        self.assertIn("executable=599", under.stdout)
        self.assertIn("band=maintain", under.stdout)
        self.assertNotIn("band=reject", under.stdout)
        _git(self.ws, "rm", "--cached", "-q", "--", "under.py")
        self.write("over.py", _statements(600))
        self.add("over.py")
        over = self.loc()
        self.assertEqual(over.returncode, 1)
        self.assertIn(
            "loc over.py executable=600 aim=150 maintain=200 reject=600 band=reject exempt=-",
            over.stdout,
        )


if __name__ == "__main__":
    unittest.main()
