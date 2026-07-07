"""
test_harden_workflow_evidence.py — Test suite for scripts/harden_workflow/

Covers: Standard Version extraction (last-mention wins), degradation
comparison in both directions, the grade_hint decision ladder across all
four grades and the unknown-structured-output cap, the checks.py refactor's
three new standalone section-presence functions (behavior-preserving), and
the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harden_workflow.degradation_check import check_degradation, extract_standard_version
from harden_workflow.grade_hint import compute_grade_hint
from suite.checks import (
    has_changelog_section,
    has_glossary_section,
    has_how_to_begin_section,
    has_integration_section,
    has_strict_rules_section,
)


class TestExtractStandardVersion(unittest.TestCase):
    def test_finds_single_mention(self):
        self.assertEqual(extract_standard_version("Standard Version: 3"), 3)

    def test_takes_last_mention_not_first(self):
        text = "Standard Version: 2\nsome text\nStandard Version: 3\n"
        self.assertEqual(extract_standard_version(text), 3)

    def test_no_mention_returns_none(self):
        self.assertIsNone(extract_standard_version("no version info here"))


class TestCheckDegradation(unittest.TestCase):
    def test_behind_current_is_degraded(self):
        result = check_degradation(certified_version=2, current_version=3)
        self.assertTrue(result.degraded)

    def test_current_is_not_degraded(self):
        result = check_degradation(certified_version=3, current_version=3)
        self.assertFalse(result.degraded)

    def test_ahead_of_current_is_not_degraded(self):
        # Should not happen in practice, but the comparison must not
        # misreport a newer stamp as degraded.
        result = check_degradation(certified_version=4, current_version=3)
        self.assertFalse(result.degraded)

    def test_no_certified_version_is_not_degraded(self):
        result = check_degradation(certified_version=None, current_version=3)
        self.assertFalse(result.degraded)
        self.assertIsNone(result.certified_version)


class TestComputeGradeHint(unittest.TestCase):
    def _all_present(self, **overrides):
        base = dict(
            command_file_correct=True,
            symlink_present=True,
            frontmatter_present=True,
            glossary_present=True,
            how_to_begin_present=True,
            strict_rules_present=True,
            changelog_present=True,
            structured_output_present=True,
        )
        base.update(overrides)
        return base

    def test_all_present_yields_sovereign(self):
        result = compute_grade_hint(**self._all_present())
        self.assertEqual(result.grade_hint, "Sovereign")
        self.assertEqual(result.missing_criteria, [])

    def test_missing_frontmatter_yields_legacy(self):
        result = compute_grade_hint(**self._all_present(frontmatter_present=False))
        self.assertEqual(result.grade_hint, "Legacy")

    def test_missing_how_to_begin_yields_legacy(self):
        result = compute_grade_hint(**self._all_present(how_to_begin_present=False))
        self.assertEqual(result.grade_hint, "Legacy")

    def test_missing_symlink_yields_legacy(self):
        result = compute_grade_hint(**self._all_present(symlink_present=False))
        self.assertEqual(result.grade_hint, "Legacy")

    def test_missing_strict_rules_yields_structured(self):
        result = compute_grade_hint(**self._all_present(strict_rules_present=False))
        self.assertEqual(result.grade_hint, "Structured")

    def test_missing_changelog_only_yields_hardened(self):
        result = compute_grade_hint(**self._all_present(changelog_present=False))
        self.assertEqual(result.grade_hint, "Hardened")
        self.assertIn("changelog", result.missing_criteria)

    def test_missing_structured_output_only_yields_hardened(self):
        result = compute_grade_hint(**self._all_present(structured_output_present=False))
        self.assertEqual(result.grade_hint, "Hardened")
        self.assertIn("structured_output", result.missing_criteria)

    def test_missing_glossary_only_yields_hardened_not_sovereign(self):
        result = compute_grade_hint(**self._all_present(glossary_present=False))
        self.assertEqual(result.grade_hint, "Hardened")

    def test_unknown_structured_output_caps_at_hardened(self):
        result = compute_grade_hint(**self._all_present(structured_output_present=None))
        self.assertEqual(result.grade_hint, "Hardened")
        self.assertTrue(result.structured_output_unknown)
        self.assertNotIn("structured_output", result.missing_criteria)

    def test_advisory_present_in_every_result(self):
        result = compute_grade_hint(**self._all_present())
        self.assertIn("NEVER that the workflow's content is good", result.advisory)


class TestChecksRefactorPreservesBehavior(unittest.TestCase):
    """
    Confirms the additive refactor to suite/checks.py (extracting the three
    inline booleans into standalone functions) is genuinely behavior-
    preserving — same regex, same results, now also independently
    importable for scripts/harden_workflow/.
    """

    def test_has_glossary_section(self):
        self.assertTrue(has_glossary_section("## GLOSSARY\n..."))
        self.assertFalse(has_glossary_section("no such section"))

    def test_has_how_to_begin_section(self):
        self.assertTrue(has_how_to_begin_section("HOW TO BEGIN\n..."))
        self.assertFalse(has_how_to_begin_section("nothing here"))

    def test_has_strict_rules_section(self):
        self.assertTrue(has_strict_rules_section("## STRICT RULES\n1. x"))
        self.assertFalse(has_strict_rules_section("nothing here"))

    def test_has_integration_section(self):
        self.assertTrue(has_integration_section("INTEGRATION WITH OTHER WORKFLOWS"))
        self.assertFalse(has_integration_section("nothing here"))

    def test_has_changelog_section(self):
        self.assertTrue(has_changelog_section("### Change Log\n1. x"))
        self.assertFalse(has_changelog_section("nothing here"))


_SAMPLE_WORKFLOW = """\
---
description: "A sample workflow for read-only invariant testing."
---

## GLOSSARY

| Term | Def |
|---|---|
| X | Y |

## STRICT RULES

1. Do the thing.

────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
Begin.

### Change Log
1. Created. Standard Version: 3
"""

_SAMPLE_TRIAGE_MD = """\
### Trigger Matrix

**`/sample-workflow`**
| Trigger | Priority |
|---|---|
| row | P1 |
"""


class TestCliReadOnlyInvariant(unittest.TestCase):
    """
    Mirrors the read-only invariant convention used throughout
    scripts/tests/ (test_build_evidence.py, test_secretary_evidence.py):
    snapshot the target workspace before/after a full CLI run; assert
    nothing changed. The engine's own docstring claims read-only — this
    proves it rather than trusting the claim.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "claude-commands").mkdir()
        (self.tmp / "claude-commands" / "sample-workflow.md").write_text(
            _SAMPLE_WORKFLOW, encoding="utf-8"
        )
        (self.tmp / "claude-commands" / "triage.md").write_text(
            _SAMPLE_TRIAGE_MD, encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_cli_run_writes_nothing(self):
        before = self._snapshot()
        here = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [
                sys.executable,
                str(here / "harden_workflow" / "harden_workflow_audit.py"),
                "--workflow-name", "sample-workflow",
                "--workspace", str(self.tmp),
                "--triage-md", str(self.tmp / "claude-commands" / "triage.md"),
                "--output-json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"grade_hint"', result.stdout)
        self.assertIn('"integration_present": false', result.stdout)
        self.assertEqual(before, self._snapshot())


if __name__ == "__main__":
    unittest.main()
