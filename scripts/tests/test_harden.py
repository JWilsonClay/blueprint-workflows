"""
test_harden.py — Test suite for the harden Hardening Evidence Engine.

Covers: deterministic CWE signature detection; the hardcoded-secret heuristic and
its one-directional contract (placeholders/env-lookups are NOT flagged); the
advisory threat classifier; the deterministic grade CEILING and its
one-directional contract (a clean scan is NOT a Diamond certification); the
end-to-end auditor; the documentation-mention / test-path / self-pattern
exclusions that keep false positives out; and the architectural read-only
invariant (the auditor must never write to the workspace).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from harden.cwe_scanner import CWEScanner, _looks_like_real_secret
from harden.grade_computer import compute_ceiling, lowest_ceiling
from harden.harden_audit import HardenAuditor
from harden.threat_classifier import ThreatClassifier


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _all_paths(root: Path) -> set:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


def _sigs(findings):
    return {f["signature"] for f in findings}


# The shell-True keyword is assembled at runtime so this test file does not
# itself contain the literal token the scanner matches.
_SHELL_TRUE = "shell" + "=True"


class TestCWEScanner(unittest.TestCase):
    def setUp(self):
        self.scan = CWEScanner()

    def _scan(self, code, ext=".py"):
        return self.scan.scan_text("x" + ext, code, ext)

    def test_detects_shell_true_critical(self):
        f = self._scan(f"subprocess.run(cmd, {_SHELL_TRUE})")
        self.assertIn("subprocess-shell-true", _sigs(f))
        self.assertEqual(f[0]["severity"], "CRITICAL")

    def test_detects_dynamic_exec_critical(self):
        f = self._scan("y = ev" + "al(user_input)\n")
        self.assertIn("dynamic-exec", _sigs(f))
        self.assertEqual([x for x in f if x["signature"] == "dynamic-exec"][0]["severity"], "CRITICAL")

    def test_detects_os_system_high(self):
        f = self._scan("import os\nos." + "system(cmd)\n")
        self.assertIn("os-system", _sigs(f))

    def test_detects_pickle_load_high(self):
        f = self._scan("import pickle\nobj = pickle." + "loads(blob)\n")
        self.assertIn("pickle-load", _sigs(f))

    def test_detects_tls_verify_disabled_critical(self):
        f = self._scan("requests.get(url, ver" + "ify=False)\n")
        self.assertIn("tls-verify-disabled", _sigs(f))

    def test_yaml_safe_load_not_flagged(self):
        # A safe loader call must NOT be reported (regression guard).
        f = self._scan("import yaml\nd = yaml.load(s, Loader=yaml.SafeLoader)\n")
        self.assertNotIn("yaml-unsafe-load", _sigs(f))

    def test_yaml_plain_load_flagged(self):
        f = self._scan("import yaml\nd = yaml." + "load(s)\n")
        self.assertIn("yaml-unsafe-load", _sigs(f))

    def test_weak_hash_is_advisory(self):
        f = [x for x in self._scan("import hashlib\nh = hashlib." + "md5(b'x')\n")
             if x["signature"] == "weak-hash"]
        self.assertTrue(f)
        self.assertTrue(f[0]["advisory"])

    def test_ext_scoping_child_process_only_js(self):
        # child_process.exec is a JS/TS signature; it must not fire on .py.
        js = self.scan.scan_text("a.js", "child_process." + "exec(cmd)\n", ".js")
        py = self.scan.scan_text("a.py", "child_process." + "exec(cmd)\n", ".py")
        self.assertIn("js-child-exec", _sigs(js))
        self.assertNotIn("js-child-exec", _sigs(py))

    def test_clean_code_zero_findings(self):
        # The one-directional contract at the scanner level: clean code => no
        # findings. That is NOT a quality or security pass — only an absence.
        f = self._scan("def add(a, b):\n    return a + b\n")
        self.assertEqual(f, [])


class TestSecretHeuristic(unittest.TestCase):
    def setUp(self):
        self.scan = CWEScanner()

    def test_real_secret_candidate_flagged_for_confirmation(self):
        f = [x for x in self.scan.scan_text("c.py", 'api_key = "AKIA1234567890ABCD"\n', ".py")
             if x["signature"] == "hardcoded-secret"]
        self.assertTrue(f)
        self.assertTrue(f[0]["requires_confirmation"])

    def test_placeholder_value_not_flagged(self):
        f = self.scan.scan_text("c.py", 'secret = "changeme"\n', ".py")
        self.assertNotIn("hardcoded-secret", _sigs(f))

    def test_env_lookup_not_flagged(self):
        f = self.scan.scan_text("c.py", 'token = os.environ["TOKEN"]\n', ".py")
        self.assertNotIn("hardcoded-secret", _sigs(f))

    def test_short_value_not_flagged(self):
        f = self.scan.scan_text("c.py", 'token = "abc"\n', ".py")
        self.assertNotIn("hardcoded-secret", _sigs(f))

    def test_looks_like_real_secret_helper(self):
        self.assertTrue(_looks_like_real_secret("AKIA1234567890ABCD"))
        self.assertFalse(_looks_like_real_secret("changeme"))
        self.assertFalse(_looks_like_real_secret("os.getenv('X')"))
        self.assertFalse(_looks_like_real_secret("abc"))


class TestThreatClassifier(unittest.TestCase):
    def setUp(self):
        self.c = ThreatClassifier()

    def test_network_facing(self):
        self.assertEqual(self.c.classify("import requests\nrequests.get(u)\n")["context"],
                         "NETWORK-FACING")

    def test_privileged(self):
        self.assertEqual(self.c.classify("import os\nos.setuid(0)\n")["context"], "PRIVILEGED")

    def test_data_handling(self):
        self.assertEqual(self.c.classify("with open('f') as fh:\n    fh.read()\n")["context"],
                         "DATA-HANDLING")

    def test_internal_only(self):
        self.assertEqual(self.c.classify("def add(a, b):\n    return a + b\n")["context"],
                         "INTERNAL-ONLY")


class TestGradeComputer(unittest.TestCase):
    @staticmethod
    def _f(sev, advisory=False, confirm=False):
        return {"severity": sev, "advisory": advisory, "requires_confirmation": confirm}

    def test_critical_forces_ungraded(self):
        self.assertEqual(compute_ceiling([self._f("CRITICAL")])["grade_ceiling"], "UNGRADED")

    def test_one_high_caps_silver(self):
        self.assertEqual(compute_ceiling([self._f("HIGH")])["grade_ceiling"], "Silver")

    def test_three_high_caps_bronze(self):
        self.assertEqual(compute_ceiling([self._f("HIGH")] * 3)["grade_ceiling"], "Bronze")

    def test_one_firm_medium_caps_gold(self):
        self.assertEqual(compute_ceiling([self._f("MEDIUM")])["grade_ceiling"], "Gold")

    def test_clean_is_diamond_ceiling_not_certification(self):
        r = compute_ceiling([])
        self.assertEqual(r["grade_ceiling"], "Diamond")
        # The basis must loudly disclaim that this is a certification (Grade-Fraud guard).
        self.assertIn("NOT A DIAMOND", r["ceiling_basis"])

    def test_advisory_finding_excluded_from_firm_ceiling(self):
        # An advisory MEDIUM does not move the firm ceiling off Diamond.
        r = compute_ceiling([self._f("MEDIUM", advisory=True)])
        self.assertEqual(r["grade_ceiling"], "Diamond")
        self.assertEqual(r["advisory_count"], 1)

    def test_confirmation_pending_excluded_from_firm_ceiling(self):
        # An unconfirmed credential candidate must not auto-penalize (FP guard).
        r = compute_ceiling([self._f("HIGH", confirm=True)])
        self.assertEqual(r["grade_ceiling"], "Diamond")
        self.assertEqual(r["confirmation_pending"], 1)

    def test_lowest_ceiling(self):
        self.assertEqual(lowest_ceiling(["Diamond", "Silver", "UNGRADED"]), "UNGRADED")
        self.assertEqual(lowest_ceiling([]), "Diamond")


class TestHardenAuditor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "danger.py", f"import subprocess\nsubprocess.run(c, {_SHELL_TRUE})\n")
        _write(self.tmp / "clean.py", "def add(a, b):\n    return a + b\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_end_to_end_detects_and_grades(self):
        report = HardenAuditor(self.tmp).run()
        self.assertEqual(report["summary"]["verdict_hint"], "BLOCKED")
        self.assertEqual(report["summary"]["lowest_ceiling"], "UNGRADED")
        by_path = {f["path"]: f for f in report["files"]}
        self.assertEqual(by_path["danger.py"]["grade_ceiling"], "UNGRADED")
        # A clean file gets a Diamond CEILING — explicitly not a certification.
        self.assertEqual(by_path["clean.py"]["grade_ceiling"], "Diamond")
        self.assertIn("Grade Fraud", report["summary"]["advisory"])

    def test_documentation_mention_not_scanned(self):
        # A .md file that *documents* a dangerous pattern is NOT a script and
        # must never be scanned — this is why harden.md never self-flags.
        _write(self.tmp / "doc.md", f"Never write subprocess.run(x, {_SHELL_TRUE}) or ev"
                                    f"al(user_input).\n")
        report = HardenAuditor(self.tmp).run()
        scanned = {f["path"] for f in report["files"]}
        self.assertNotIn("doc.md", scanned)

    def test_test_files_excluded(self):
        _write(self.tmp / "tests" / "test_thing.py",
               f"subprocess.run(c, {_SHELL_TRUE})\n")
        report = HardenAuditor(self.tmp).run()
        scanned = {f["path"] for f in report["files"]}
        self.assertNotIn("tests/test_thing.py", scanned)

    def test_single_file_mode(self):
        report = HardenAuditor(self.tmp, file_override="danger.py").run()
        self.assertEqual(report["summary"]["files_scanned"], 1)
        self.assertEqual(report["files"][0]["path"], "danger.py")

    def test_path_traversal_file_rejected(self):
        report = HardenAuditor(self.tmp, file_override="../../etc/passwd").run()
        self.assertEqual(report["summary"]["files_scanned"], 0)
        self.assertTrue(report["notes"])

    def test_auditor_is_read_only(self):
        # The architectural guarantee: a scan must not mutate the workspace.
        before = _all_paths(self.tmp)
        HardenAuditor(self.tmp).run()
        after = _all_paths(self.tmp)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
