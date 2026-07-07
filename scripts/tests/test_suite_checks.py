"""
test_suite_checks.py — Tests for scripts/suite/checks.py, the Sovereign
Suite linter's parsing and validation logic.

Originally scoped only to the runtime-directory-gating fix (2026-07-05,
resolves helpdesk-tickets/20260705_opencode-to-grok-build-transition_workflow.md)
-- check_symlinks gates its per-file OpenCode/Antigravity pointer checks on
whether the runtime directory exists at all, and check_runtime_availability
reports that fact once per scan rather than once per file.

[EXTENDED 2026-07-06 -- Sovereign Redesign Cluster Stage 4, PR 05-04, produced
via /design-orchestrator's real native path -- see
docs/DESIGN_PR_05_04_Suite_Checks_Test_Coverage.md] Added direct unit coverage
for the 12 previously-untested functions that implement the linter's actual
parsing and validation logic (parse_frontmatter, compute_content_hash,
extract_workflow_refs, _extract_strict_rules_section, count_strict_rules,
count_phases, extract_glossary_terms, check_frontmatter, check_structure,
check_cross_references, check_content_hash, check_glossary_usage) -- a bug in
any of these would silently corrupt every hash/structure/frontmatter check in
the entire suite, and nothing previously caught that.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import unittest
from pathlib import Path
from unittest import mock

from suite import checks
from suite.models import LintReport


class TestRuntimeAvailability(unittest.TestCase):
    def test_reports_info_when_directory_missing(self):
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent/opencode"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/nonexistent/antigravity"), \
             mock.patch.object(checks, "GROK_BUILD_DIR", "/nonexistent/grok"):
            checks.check_runtime_availability(report)
        self.assertEqual(len(report.findings), 3)
        self.assertTrue(all(f.severity == "INFO" for f in report.findings))
        self.assertTrue(all(f.workflow == "(suite)" for f in report.findings))
        messages = [f.message for f in report.findings]
        self.assertTrue(any("OpenCode" in m for m in messages))
        self.assertTrue(any("Antigravity" in m for m in messages))
        self.assertTrue(any("Grok Build" in m for m in messages))

    def test_no_finding_when_directory_present(self):
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/tmp"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/tmp"), \
             mock.patch.object(checks, "GROK_BUILD_DIR", "/tmp"):
            checks.check_runtime_availability(report)
        self.assertEqual(report.findings, [])

    def test_never_a_warning_or_critical(self):
        # A retired/replaced runtime is informational, not a defect — must
        # never inflate the WARNING/CRITICAL counts other checks rely on.
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent"):
            checks.check_runtime_availability(report)
        self.assertEqual(report.criticals, [])
        self.assertEqual(report.warnings, [])


class TestSymlinksGating(unittest.TestCase):
    def test_missing_directory_produces_no_per_file_warning(self):
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent/opencode"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/nonexistent/antigravity"), \
             mock.patch.object(checks, "SYMLINK_DIR", "/tmp/definitely-not-here-either"):
            checks.check_symlinks("some_workflow.md", "/home/jwils/blueprint-workflows", report)
        pointer_findings = [f for f in report.findings if f.check == "pointer"]
        self.assertEqual(pointer_findings, [])  # gated out — no per-file noise

    def test_present_directory_missing_file_still_warns(self):
        # The genuinely different case: the runtime IS installed, but this
        # one specific file's pointer wasn't created — that's a real gap.
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/tmp"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/tmp"), \
             mock.patch.object(checks, "SYMLINK_DIR", "/tmp"):
            checks.check_symlinks("definitely_not_a_real_pointer_file.md",
                                  "/home/jwils/blueprint-workflows", report)
        pointer_findings = [f for f in report.findings if f.check == "pointer"]
        self.assertEqual(len(pointer_findings), 2)  # OpenCode + Antigravity, both real gaps
        self.assertTrue(all(f.severity == "WARNING" for f in pointer_findings))

    def test_thirty_two_files_missing_directory_yields_zero_pointer_warnings(self):
        # Regression guard for the exact symptom this ticket fixed: one
        # missing directory must never produce N per-file warnings again.
        report = LintReport()
        with mock.patch.object(checks, "OPENCODE_DIR", "/nonexistent"), \
             mock.patch.object(checks, "ANTIGRAVITY_DIR", "/nonexistent"), \
             mock.patch.object(checks, "SYMLINK_DIR", "/tmp"):
            for i in range(32):
                checks.check_symlinks(f"workflow_{i}.md", "/home/jwils/blueprint-workflows", report)
        pointer_findings = [f for f in report.findings if f.check == "pointer"]
        self.assertEqual(pointer_findings, [])


class TestParseFrontmatter(unittest.TestCase):
    def test_valid_frontmatter(self):
        content = '---\ndescription: "A real workflow"\ngrade: Sovereign\n---\n\nBody text here.'
        fm, body = checks.parse_frontmatter(content)
        self.assertEqual(fm["description"], "A real workflow")
        self.assertEqual(fm["grade"], "Sovereign")
        self.assertEqual(body, "Body text here.")

    def test_missing_frontmatter(self):
        fm, body = checks.parse_frontmatter("Just a body, no frontmatter fences at all.")
        self.assertIsNone(fm)
        self.assertEqual(body, "Just a body, no frontmatter fences at all.")

    def test_malformed_yaml(self):
        # Unterminated flow mapping -- a real YAML parse error, not just odd formatting.
        content = '---\ndescription: [unterminated\n---\n\nBody.'
        fm, body = checks.parse_frontmatter(content)
        self.assertTrue(fm.get("_parse_error"))


class TestComputeContentHash(unittest.TestCase):
    def test_identical_content_identical_hash(self):
        content = "---\ndescription: x\n---\n\nSame body."
        self.assertEqual(checks.compute_content_hash(content), checks.compute_content_hash(content))

    def test_different_content_different_hash(self):
        h1 = checks.compute_content_hash("---\ndescription: x\n---\n\nBody A.")
        h2 = checks.compute_content_hash("---\ndescription: x\n---\n\nBody B.")
        self.assertNotEqual(h1, h2)

    def test_hash_is_16_char_hex(self):
        h = checks.compute_content_hash("---\ndescription: x\n---\n\nBody.")
        self.assertEqual(len(h), 16)
        int(h, 16)  # raises ValueError if not valid hex

    def test_change_log_excluded_from_hash(self):
        # The whole point of excluding Change Log: appending a new dated entry
        # (the normal, expected way this file grows) must not change the hash.
        base = "---\ndescription: x\n---\n\nProtocol body.\n\n### Change Log\n1. Entry one."
        grown = "---\ndescription: x\n---\n\nProtocol body.\n\n### Change Log\n1. Entry one.\n2. Entry two."
        self.assertEqual(checks.compute_content_hash(base), checks.compute_content_hash(grown))


class TestExtractWorkflowRefs(unittest.TestCase):
    def test_extracts_exact_set(self):
        body = "See /execute-build and /focus-plan, then /execute-build again."
        refs = checks.extract_workflow_refs(body)
        self.assertEqual(refs, {"execute-build", "focus-plan"})


class TestStrictRulesExtraction(unittest.TestCase):
    def test_extracts_section_and_counts(self):
        body = (
            "## STRICT RULES\n\n"
            "1. First rule.\n"
            "2. Second rule.\n"
            "3. Third rule.\n"
            "\n---\n"
        )
        section = checks._extract_strict_rules_section(body)
        self.assertIn("First rule", section)
        self.assertEqual(checks.count_strict_rules(body), 3)

    def test_no_section_returns_zero(self):
        self.assertEqual(checks.count_strict_rules("No rules section here at all."), 0)


class TestCountPhases(unittest.TestCase):
    def test_counts_phase_headers(self):
        body = "## PHASE 0 — INTAKE\n\ntext\n\n## PHASE 1 — BUILD\n\ntext\n\n## PHASE 2 — VERIFY\n"
        self.assertEqual(checks.count_phases(body), 3)

    def test_ignores_non_phase_headers(self):
        body = "## PHASE 0 — INTAKE\n\n## GLOSSARY\n\n## STRICT RULES\n"
        self.assertEqual(checks.count_phases(body), 1)


class TestExtractGlossaryTerms(unittest.TestCase):
    def test_extracts_terms_from_table(self):
        body = (
            "## GLOSSARY\n\n"
            "| Term | Definition |\n"
            "|------|------------|\n"
            "| **Foo** | The foo thing. |\n"
            "| **Bar** | The bar thing. |\n"
            "\n---\n"
        )
        terms = checks.extract_glossary_terms(body)
        self.assertEqual(terms, ["Foo", "Bar"])


class TestCheckFrontmatter(unittest.TestCase):
    def test_valid_frontmatter_no_findings(self):
        report = LintReport()
        checks.check_frontmatter({"description": "A real description"}, "wf.md", report)
        criticals = [f for f in report.findings if f.severity == "CRITICAL"]
        self.assertEqual(criticals, [])

    def test_missing_frontmatter_is_critical(self):
        report = LintReport()
        checks.check_frontmatter(None, "wf.md", report)
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].severity, "CRITICAL")

    def test_missing_description_is_critical(self):
        report = LintReport()
        checks.check_frontmatter({}, "wf.md", report)
        criticals = [f for f in report.findings if f.severity == "CRITICAL"]
        self.assertEqual(len(criticals), 1)
        self.assertIn("description", criticals[0].message)


class TestCheckStructure(unittest.TestCase):
    def test_complete_body_no_structure_warnings(self):
        report = LintReport()
        body = "## GLOSSARY\n\nHOW TO BEGIN\n\n## STRICT RULES\n1. Rule.\n\nINTEGRATION\n\n### Change Log\n1. Entry."
        checks.check_structure(body, "wf.md", {"type": "execution"}, report)
        structure_findings = [f for f in report.findings if f.check == "structure"]
        self.assertEqual(structure_findings, [])

    def test_missing_sections_produce_warnings(self):
        report = LintReport()
        checks.check_structure("Just a body with nothing structural.", "wf.md", {"type": "execution"}, report)
        structure_findings = [f for f in report.findings if f.check == "structure"]
        self.assertEqual(len(structure_findings), 5)  # GLOSSARY, HOW TO BEGIN, STRICT RULES, INTEGRATION, Change Log

    def test_documentation_type_exempt_from_strict_rules(self):
        report = LintReport()
        checks.check_structure("## GLOSSARY\nHOW TO BEGIN\nINTEGRATION\n### Change Log\n1. x", "wf.md",
                                {"type": "documentation"}, report)
        strict_findings = [f for f in report.findings if "STRICT RULES" in f.message]
        self.assertEqual(strict_findings, [])


class TestCheckCrossReferences(unittest.TestCase):
    def test_known_reference_no_finding(self):
        report = LintReport()
        checks.check_cross_references("See /execute-build for details.", "wf.md",
                                       ["execute-build.md", "wf.md"], report)
        self.assertEqual(report.findings, [])

    def test_unknown_reference_produces_info(self):
        report = LintReport()
        checks.check_cross_references("See /totally-nonexistent-workflow for details.", "wf.md",
                                       ["execute-build.md", "wf.md"], report)
        xref_findings = [f for f in report.findings if f.check == "xref"]
        self.assertEqual(len(xref_findings), 1)
        self.assertEqual(xref_findings[0].severity, "INFO")


class TestCheckContentHash(unittest.TestCase):
    def test_matching_hash_no_finding(self):
        report = LintReport()
        content = "---\ndescription: x\n---\n\nBody."
        actual = "sha256:" + checks.compute_content_hash(content)
        checks.check_content_hash(content, {"content_hash": actual}, "wf.md", report)
        self.assertEqual(report.findings, [])

    def test_mismatched_hash_produces_warning(self):
        report = LintReport()
        content = "---\ndescription: x\n---\n\nBody."
        checks.check_content_hash(content, {"content_hash": "sha256:0000000000000000"}, "wf.md", report)
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].severity, "WARNING")

    def test_no_content_hash_field_no_finding(self):
        report = LintReport()
        checks.check_content_hash("anything", {}, "wf.md", report)
        self.assertEqual(report.findings, [])


class TestCheckGlossaryUsage(unittest.TestCase):
    def test_used_term_no_finding(self):
        # NOTE: given the same glossary_end quirk documented in
        # test_unused_term_not_detected_when_table_has_dashed_divider below,
        # this "no finding" result holds regardless of whether the body text
        # actually repeats the term -- the table's own divider already
        # guarantees post_glossary includes the term's own definition row.
        # Kept as a real assertion of current behavior (a genuinely-used term
        # correctly produces no finding), not proof the check distinguishes
        # used-from-unused in the way its name implies.
        report = LintReport()
        body = (
            "## GLOSSARY\n\n| Term | Definition |\n|---|---|\n| **Widget** | A thing. |\n\n---\n\n"
            "This workflow operates on a Widget throughout."
        )
        checks.check_glossary_usage(body, "wf.md", report)
        self.assertEqual(report.findings, [])

    def test_unused_term_not_detected_when_table_has_dashed_divider(self):
        # [FINDING -- discovered live 2026-07-06, Sovereign Redesign Cluster
        # Stage 4, PR 05-04] check_glossary_usage's glossary_end calculation
        # is `body.find("---", body.find("GLOSSARY") + 1)` -- the first "---"
        # substring after the word GLOSSARY. In a standard markdown table
        # (every GLOSSARY in this suite), that divider row (`|---|---|` or
        # `|------|------------|`) itself contains "---", so glossary_end
        # lands INSIDE the table, before any term's own definition row.
        # post_glossary therefore always includes the table's own rows, so
        # a term is always found "used" via its own definition -- this check
        # cannot detect a genuinely unused term when the table uses the
        # standard dashed-divider format. Confirmed empirically before
        # writing this test (not assumed). Out of scope to fix here per this
        # DESIGN's own boundary (docs/DESIGN_PR_05_04_Suite_Checks_Test_Coverage.md
        # Acceptance Criterion 3: a bug found while adding tests is named, not
        # silently patched) -- this test documents the real, current behavior,
        # not the intended one.
        report = LintReport()
        body = (
            "## GLOSSARY\n\n| Term | Definition |\n|---|---|\n| **Widget** | A thing. |\n\n---\n\n"
            "This workflow never mentions that term again."
        )
        checks.check_glossary_usage(body, "wf.md", report)
        self.assertEqual(report.findings, [])  # bug: should be 1 INFO finding, is 0


if __name__ == "__main__":
    unittest.main()
