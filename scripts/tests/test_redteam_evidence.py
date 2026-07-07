"""
test_redteam_evidence.py — Test suite for scripts/redteam/

Covers: mock construct enumeration (all 4 construct types), non-.py file
skipping, secret-pattern detection with STRUCTURAL REDACTION (the critical
guarantee — a matched secret's actual value must never appear anywhere in
the tool's own output, including the CLI's JSON stdout), coverage-gap
parsing against coverage.py's real JSON shape (both default 80% and
surface-map 100% thresholds), malformed/missing-file degradation, and the
read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from redteam.coverage_gap import parse_coverage_json
from redteam.mock_scanner import scan_for_mocks
from redteam.secret_scanner import DEFAULT_PATTERNS, scan_for_secrets


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestScanForMocks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_finds_all_four_construct_types(self):
        f = self.tmp / "test_sample.py"
        _write(f, (
            "@patch('foo.bar')\n"
            "def test_a():\n"
            "    m = Mock()\n"
            "    mm = MagicMock()\n"
            "    monkeypatch.setattr('x', 'y')\n"
        ))
        usages = scan_for_mocks([str(f)])
        constructs = {u.construct for u in usages}
        self.assertEqual(constructs, {"patch_decorator", "Mock_call", "MagicMock_call", "monkeypatch_call"})

    def test_skips_non_python_files(self):
        f = self.tmp / "notes.md"
        _write(f, "@patch('foo.bar')\nMock()\n")
        self.assertEqual(scan_for_mocks([str(f)]), [])

    def test_missing_file_silently_skipped(self):
        self.assertEqual(scan_for_mocks([str(self.tmp / "nope.py")]), [])

    def test_no_mocks_returns_empty(self):
        f = self.tmp / "clean.py"
        _write(f, "def add(a, b):\n    return a + b\n")
        self.assertEqual(scan_for_mocks([str(f)]), [])

    def test_reports_correct_line_number(self):
        f = self.tmp / "test_sample.py"
        _write(f, "x = 1\ny = 2\nMock()\n")
        usages = scan_for_mocks([str(f)])
        self.assertEqual(usages[0].line, 3)


class TestScanForSecretsRedaction(unittest.TestCase):
    """
    The critical guarantee: a matched secret's actual VALUE must never
    appear in this scanner's output under any circumstance.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_finds_all_default_patterns(self):
        f = self.tmp / "app.log"
        _write(f, "\n".join(f"{p}=some_value_{i}" for i, p in enumerate(DEFAULT_PATTERNS)))
        hits = scan_for_secrets([str(f)])
        found_patterns = {h.pattern_matched for h in hits}
        self.assertEqual(found_patterns, set(DEFAULT_PATTERNS))

    def test_actual_secret_value_never_appears_in_hit_object(self):
        f = self.tmp / "app.log"
        # Deliberately contains none of DEFAULT_PATTERNS as a substring, so
        # exactly one hit (API_KEY) is expected -- a value that happened to
        # contain "SECRET" would legitimately also match that pattern.
        secret_value = "sk-abc123xyz-live-9f8e7d6c5b4a"
        _write(f, f"API_KEY={secret_value}\n")
        hits = scan_for_secrets([str(f)])
        self.assertEqual(len(hits), 1)
        hit_dict = hits[0].as_dict()
        serialized = json.dumps(hit_dict)
        self.assertNotIn(secret_value, serialized)
        self.assertNotIn(secret_value, str(vars(hits[0])))

    def test_hit_object_has_no_line_content_field_at_all(self):
        f = self.tmp / "app.log"
        _write(f, "PASSWORD=hunter2\n")
        hits = scan_for_secrets([str(f)])
        hit_dict = hits[0].as_dict()
        # Structural guarantee: the dict shape itself carries no field that
        # could hold line content -- not just "redacted", but ABSENT.
        self.assertEqual(set(hit_dict.keys()), {"file", "line", "pattern_matched"})

    def test_custom_patterns_override_default(self):
        f = self.tmp / "app.log"
        _write(f, "CUSTOM_MARKER=xyz\nSECRET=abc\n")
        hits = scan_for_secrets([str(f)], patterns=["CUSTOM_MARKER"])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pattern_matched, "CUSTOM_MARKER")

    def test_missing_file_silently_skipped(self):
        self.assertEqual(scan_for_secrets([str(self.tmp / "nope.log")]), [])

    def test_no_secrets_returns_empty(self):
        f = self.tmp / "clean.log"
        _write(f, "just a normal log line\n")
        self.assertEqual(scan_for_secrets([str(f)]), [])


class TestParseCoverageJson(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_coverage_json(self, files: dict) -> Path:
        f = self.tmp / "coverage.json"
        _write(f, json.dumps({"meta": {}, "files": files, "totals": {}}))
        return f

    def test_flags_below_default_threshold(self):
        f = self._write_coverage_json({
            "a.py": {"summary": {"percent_covered": 50.0}},
            "b.py": {"summary": {"percent_covered": 95.0}},
        })
        gaps = parse_coverage_json(str(f))
        below = {g.file for g in gaps if g.below_threshold}
        self.assertEqual(below, {"a.py"})

    def test_surface_map_file_gets_100_percent_threshold(self):
        f = self._write_coverage_json({
            "a.py": {"summary": {"percent_covered": 90.0}},
        })
        gaps = parse_coverage_json(str(f), surface_map_files=["a.py"])
        self.assertEqual(gaps[0].threshold_applied, 100.0)
        self.assertTrue(gaps[0].below_threshold)

    def test_non_surface_map_file_gets_default_threshold(self):
        f = self._write_coverage_json({
            "a.py": {"summary": {"percent_covered": 90.0}},
        })
        gaps = parse_coverage_json(str(f))
        self.assertEqual(gaps[0].threshold_applied, 80.0)
        self.assertFalse(gaps[0].below_threshold)

    def test_missing_file_returns_empty(self):
        self.assertEqual(parse_coverage_json(str(self.tmp / "nope.json")), [])

    def test_malformed_json_returns_empty(self):
        f = self.tmp / "bad.json"
        _write(f, "{not valid json")
        self.assertEqual(parse_coverage_json(str(f)), [])

    def test_missing_files_key_returns_empty(self):
        f = self.tmp / "weird.json"
        _write(f, json.dumps({"meta": {}}))
        self.assertEqual(parse_coverage_json(str(f)), [])


class TestReadOnlyInvariant(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "test_sample.py", "Mock()\nAPI_KEY=secret123\n")
        _write(self.tmp / "coverage.json", json.dumps({
            "meta": {}, "files": {"a.py": {"summary": {"percent_covered": 50.0}}}, "totals": {}
        }))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_all_functions_write_nothing(self):
        before = self._snapshot()
        scan_for_mocks([str(self.tmp / "test_sample.py")])
        scan_for_secrets([str(self.tmp / "test_sample.py")])
        parse_coverage_json(str(self.tmp / "coverage.json"))
        self.assertEqual(before, self._snapshot())


class TestCliRedactionEndToEnd(unittest.TestCase):
    """
    The redaction guarantee must hold at the CLI/JSON-stdout boundary too,
    not just in the Python object -- this is what an agent actually reads.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.secret_value = "sk-LIVE-SECRET-VALUE-9999"
        _write(self.tmp / "app.log", f"API_KEY={self.secret_value}\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_secret_value_absent_from_cli_json_output(self):
        here = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [
                sys.executable,
                str(here / "redteam" / "redteam_audit.py"),
                "--scan-paths", str(self.tmp / "app.log"),
                "--output-json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(self.secret_value, result.stdout)
        self.assertIn("API_KEY", result.stdout)


if __name__ == "__main__":
    unittest.main()
