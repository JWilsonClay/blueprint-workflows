"""
test_iterate.py — Test suite for the iterate Mock-Trap Detector engine.

Covers: AST extraction of imports (production vs test-infra split), patch targets
(plain patch, patch.object, mocker.patch, monkeypatch.setattr), per-symbol
mock-vs-live classification, the critical FALSE-POSITIVE guard (mocking an
infrastructure dependency while the SUBJECT is called live must NOT flag the
subject), the hardcoded-assertion tautology and its one-directional contract
(distinct/trivial values are NOT flagged), the bridge classifier's one-directional
signal (a clean LIVE result is NOT a certification), the end-to-end auditor with
walk + single-file modes, the path-traversal / non-Python guards, and the
architectural read-only invariant (the auditor must never write to the workspace).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from iterate.bridge_classifier import classify_file
from iterate.iterate_audit import IterateAuditor
from iterate.mock_analyzer import MockTrapAnalyzer


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _all_paths(root: Path) -> set:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


# The `@patch` / `MagicMock` tokens below live inside triple-quoted SOURCE strings
# the analyzer parses — they are not patches in THIS file's own AST, so the engine
# never self-flags test_iterate.py during a workspace walk.
def _analyze(src, subject=None):
    return classify_file(MockTrapAnalyzer().analyze("tests/test_subject.py", src, subject))


def _sym(report, name):
    return next((s for s in report["symbols"] if s["name"] == name), None)


# ---------------------------------------------------------------------------
# Analyzer — imports, patches, symbols
# ---------------------------------------------------------------------------
class TestMockAnalyzer(unittest.TestCase):
    def setUp(self):
        self.A = MockTrapAnalyzer()

    def test_imports_split_infra_vs_production(self):
        src = ("import unittest\n"
               "from unittest.mock import patch, MagicMock\n"
               "from app.core import governor\n"
               "import app.http\n")
        r = self.A.analyze("tests/test_x.py", src)
        prod = {i["local_name"] for i in r["imports"]["production_candidates"]}
        infra = {i["local_name"] for i in r["imports"]["test_infra"]}
        # `import app.http` binds the name `app` (Python import semantics); the
        # qualified source is recorded separately for patch-target matching.
        self.assertEqual(prod, {"governor", "app"})
        self.assertEqual(
            {i["qualified_name"] for i in r["imports"]["production_candidates"]},
            {"app.core.governor", "app.http"},
        )
        self.assertEqual(infra, {"unittest", "patch", "MagicMock"})

    def test_patched_subject_is_mock_trap_candidate(self):
        src = ("from unittest.mock import patch\n"
               "from app.governor import run\n"
               "@patch('app.governor.run')\n"
               "def test_it(m):\n"
               "    run('x')\n")
        r = self.A.analyze("tests/test_x.py", src)
        s = _sym(r, "run")
        self.assertTrue(s["patched"])
        self.assertEqual(s["fidelity"], "MOCK_TRAP_CANDIDATE")
        self.assertEqual(s["patch_how"]["target"], "app.governor.run")

    def test_live_call_not_flagged(self):
        src = ("from app.governor import run\n"
               "def test_it():\n"
               "    out = run('hello')\n"
               "    assert out\n")
        r = self.A.analyze("tests/test_x.py", src)
        s = _sym(r, "run")
        self.assertFalse(s["patched"])
        self.assertEqual(s["fidelity"], "CALLED_LIVE")
        self.assertGreaterEqual(s["call_count"], 1)

    def test_infra_mock_does_not_flag_live_subject(self):
        # THE false-positive guard: mocking an infrastructure dependency while the
        # SUBJECT is imported and called live must NOT flag the subject.
        src = ("from unittest.mock import patch\n"
               "from app.governor import Governor\n"
               "@patch('app.http.Client')\n"
               "def test_it(m):\n"
               "    g = Governor()\n"
               "    g.handle('hi')\n")
        r = self.A.analyze("tests/test_x.py", src, subject="app.governor.Governor")
        s = _sym(r, "Governor")
        self.assertFalse(s["patched"])
        self.assertEqual(s["fidelity"], "CALLED_LIVE")

    def test_patch_object_target_resolved(self):
        src = ("from unittest.mock import patch\n"
               "from app import mod\n"
               "@patch.object(mod, 'run')\n"
               "def test_it(m):\n"
               "    pass\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertTrue(any(p["target"] == "mod.run" for p in r["patches"]))

    def test_mocker_patch_detected(self):
        src = ("from app.governor import run\n"
               "def test_it(mocker):\n"
               "    mocker.patch('app.governor.run')\n"
               "    run('x')\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertEqual(_sym(r, "run")["fidelity"], "MOCK_TRAP_CANDIDATE")

    def test_monkeypatch_setattr_detected(self):
        src = ("from app.governor import run\n"
               "def test_it(monkeypatch):\n"
               "    monkeypatch.setattr('app.governor.run', lambda x: 1)\n"
               "    run('x')\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertEqual(_sym(r, "run")["fidelity"], "MOCK_TRAP_CANDIDATE")

    def test_imported_unused_symbol(self):
        src = "from app.governor import helper\nimport unittest\n"
        r = self.A.analyze("tests/test_x.py", src)
        self.assertEqual(_sym(r, "helper")["fidelity"], "IMPORTED_UNUSED")

    def test_parse_error_graceful(self):
        r = self.A.analyze("tests/test_x.py", "def broken(:\n  pass\n")
        self.assertTrue(r["parse_error"])
        self.assertEqual(r["symbols"], [])

    def test_mock_construction_canned_flag(self):
        src = ("from unittest.mock import MagicMock\n"
               "m = MagicMock(return_value='canned reply here')\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertTrue(any(mc["canned_output"] for mc in r["mock_constructions"]))


# ---------------------------------------------------------------------------
# Analyzer — hardcoded-assertion tautology (one-directional)
# ---------------------------------------------------------------------------
class TestTautology(unittest.TestCase):
    def setUp(self):
        self.A = MockTrapAnalyzer()

    def test_return_value_echoed_in_assert_flagged(self):
        src = ("from unittest.mock import MagicMock\n"
               "def test_it():\n"
               "    m = MagicMock()\n"
               "    m.return_value = 'I can help you today friend'\n"
               "    assert call(m) == 'I can help you today friend'\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertEqual(len(r["hardcoded_assertions"]), 1)

    def test_assertEqual_canned_value_flagged(self):
        src = ("from unittest.mock import MagicMock\n"
               "import unittest\n"
               "class T(unittest.TestCase):\n"
               "    def test_it(self):\n"
               "        m = MagicMock(return_value='the canned answer string')\n"
               "        self.assertEqual(run(m), 'the canned answer string')\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertEqual(len(r["hardcoded_assertions"]), 1)

    def test_distinct_values_not_flagged(self):
        # Canned X but assert Y — not a tautology.
        src = ("from unittest.mock import MagicMock\n"
               "def test_it():\n"
               "    m = MagicMock()\n"
               "    m.return_value = 'canned value alpha'\n"
               "    assert run(m) == 'a different expected beta'\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertEqual(r["hardcoded_assertions"], [])

    def test_trivial_literal_not_flagged(self):
        # Short/boolean values recur legitimately — one-directional skip.
        src = ("from unittest.mock import MagicMock\n"
               "def test_it():\n"
               "    m = MagicMock()\n"
               "    m.return_value = True\n"
               "    assert run(m) == True\n")
        r = self.A.analyze("tests/test_x.py", src)
        self.assertEqual(r["hardcoded_assertions"], [])


# ---------------------------------------------------------------------------
# Bridge classifier — one-directional signal
# ---------------------------------------------------------------------------
class TestBridgeClassifier(unittest.TestCase):
    def setUp(self):
        self.A = MockTrapAnalyzer()

    def _sig(self, src, subject=None):
        return classify_file(self.A.analyze("tests/test_x.py", src, subject))

    def test_mock_trap_candidate_signal(self):
        src = ("from unittest.mock import patch\n"
               "from app.gov import run\n"
               "@patch('app.gov.run')\n"
               "def test_it(m):\n    run('x')\n")
        self.assertEqual(self._sig(src)["file_signal"], "MOCK_TRAP_CANDIDATE")

    def test_live_signal_is_not_a_certification(self):
        src = ("from app.gov import run\n"
               "def test_it():\n    assert run('x')\n")
        r = self._sig(src)
        self.assertEqual(r["file_signal"], "LIVE")
        # The basis must loudly disclaim certification (the Mock-Trap guard).
        self.assertIn("NOT A FIDELITY CERTIFICATION", r["signal_basis"])

    def test_no_production_import_signal(self):
        src = ("import unittest\n"
               "from unittest.mock import MagicMock\n"
               "def test_it():\n    assert MagicMock()\n")
        self.assertEqual(self._sig(src)["file_signal"], "NO_PRODUCTION_IMPORT")

    def test_parse_error_signal(self):
        self.assertEqual(self._sig("def broken(:\n pass")["file_signal"], "PARSE_ERROR")


# ---------------------------------------------------------------------------
# Auditor — discovery, modes, guards, read-only invariant
# ---------------------------------------------------------------------------
class TestIterateAuditor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "tests" / "test_trap.py",
               "from unittest.mock import patch\n"
               "from app.gov import run\n"
               "@patch('app.gov.run')\n"
               "def test_it(m):\n    run('x')\n")
        _write(self.tmp / "app" / "gov.py", "def run(x):\n    return x\n")  # production

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_walk_discovers_test_files_only(self):
        report = IterateAuditor(self.tmp).run()
        scanned = {f["path"] for f in report["files"]}
        self.assertIn("tests/test_trap.py", scanned)
        self.assertNotIn("app/gov.py", scanned)  # production file is not a test

    def test_init_py_package_marker_excluded(self):
        # Regression: an __init__.py under a tests/ dir is a package marker, not a
        # test-case module — it must not be analyzed (live-run false-positive fix).
        _write(self.tmp / "tests" / "__init__.py", '"""test package marker"""\n')
        report = IterateAuditor(self.tmp).run()
        scanned = {f["path"] for f in report["files"]}
        self.assertNotIn("tests/__init__.py", scanned)

    def test_end_to_end_trap_flagged(self):
        report = IterateAuditor(self.tmp).run()
        self.assertEqual(report["summary"]["verdict_hint"], "FINDINGS")
        self.assertEqual(report["summary"]["mock_trap_candidate_files"], 1)

    def test_single_test_mode(self):
        report = IterateAuditor(self.tmp, test_override="tests/test_trap.py").run()
        self.assertEqual(report["summary"]["tests_scanned"], 1)
        self.assertEqual(report["files"][0]["path"], "tests/test_trap.py")

    def test_subject_flag_marks_symbol(self):
        report = IterateAuditor(self.tmp, test_override="tests/test_trap.py",
                                subject="app.gov.run").run()
        s = _sym(report["files"][0], "run")
        self.assertTrue(s["is_subject"])

    def test_non_python_test_rejected(self):
        _write(self.tmp / "tests" / "test_x.js", "describe('x', () => {})\n")
        report = IterateAuditor(self.tmp, test_override="tests/test_x.js").run()
        self.assertEqual(report["summary"]["tests_scanned"], 0)
        self.assertTrue(report["notes"])

    def test_path_traversal_rejected(self):
        report = IterateAuditor(self.tmp, test_override="../../etc/passwd").run()
        self.assertEqual(report["summary"]["tests_scanned"], 0)
        self.assertTrue(report["notes"])

    def test_no_findings_verdict_on_live_suite(self):
        # A workspace whose only test exercises production live → NO_FINDINGS
        # (which the advisory explicitly says is NOT a certification).
        clean = Path(tempfile.mkdtemp())
        try:
            _write(clean / "tests" / "test_live.py",
                   "from app.gov import run\n"
                   "def test_it():\n    assert run('x') == compute_expected()\n")
            report = IterateAuditor(clean).run()
            self.assertEqual(report["summary"]["verdict_hint"], "NO_FINDINGS")
            self.assertIn("Mock Trap", report["summary"]["advisory"])
        finally:
            shutil.rmtree(clean, ignore_errors=True)

    def test_auditor_is_read_only(self):
        # The architectural guarantee: analysis must not mutate the workspace.
        before = _all_paths(self.tmp)
        IterateAuditor(self.tmp).run()
        IterateAuditor(self.tmp, test_override="tests/test_trap.py",
                       subject="app.gov.run").run()
        after = _all_paths(self.tmp)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
