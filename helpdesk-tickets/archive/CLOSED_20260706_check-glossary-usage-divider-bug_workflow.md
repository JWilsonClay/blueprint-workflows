# Helpdesk Ticket: check_glossary_usage never detects an unused GLOSSARY term

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Redesign Cluster, Stage 4 Task 4.4)
**Date**: 2026-07-06
**Subject**: `scripts/suite/checks.py`'s `check_glossary_usage` function cannot detect a genuinely-unused GLOSSARY term when the table uses a standard markdown dashed-divider row — which is every GLOSSARY table in this suite. Found via direct unit testing, not observed as a live symptom.
**Urgency**: LOW (INFO-severity check only; does not affect CRITICAL/WARNING findings, hash verification, structural checks, or any gating behavior)
**Root Cause Type**: SUBSTANTIVE-LOGIC (a code logic defect in `scripts/suite/checks.py`, not a workflow `.md` structural gap — `/harden-workflow` cannot remediate this per its own opening line and STRICT RULE 3)
**Phylogeny Disposition**: `NO TRANSFER` — a self-contained parsing-logic fix in one function; no structural pattern moved between workflow files.
**Status**: **REMEDIATED**
**Verification**: See Section 7, Remediation Record, below.

---

## 1. Executive Summary

While adding direct unit test coverage for `scripts/suite/checks.py`'s previously-untested functions (Sovereign Redesign Cluster Stage 4, Task 4.4 — see `docs/DESIGN_PR_05_04_Suite_Checks_Test_Coverage.md`), a genuine test for `check_glossary_usage`'s "unused term" path failed. Investigation confirmed a real, latent defect in the function itself, not a test-authoring error.

## 2. Root Cause

`check_glossary_usage` (`scripts/suite/checks.py:235-243`) computes the end of the GLOSSARY section as:
```python
glossary_end = body.find("---", body.find("GLOSSARY") + 1) if "GLOSSARY" in body else 0
```
This finds the *first* `"---"` substring after the word "GLOSSARY" anywhere in the body. In a standard markdown table — the format every GLOSSARY section in this suite actually uses — the header divider row (`|---|---|` or `|------|------------|`) itself contains three-or-more consecutive dashes, which `str.find("---", ...)` matches before ever reaching the table's data rows. `glossary_end` therefore lands *inside* the table, before any term's own definition row.

Consequence: `post_glossary` (the text searched for term usage) always includes the table's own rows, so every term is trivially "found" via its own definition — the check can never report a term as unused when the table uses this format. Confirmed empirically:
```python
body = ('## GLOSSARY\n\n| Term | Definition |\n|---|---|\n| **Widget** | A thing. |\n\n---\n\n'
        'This workflow never mentions that term again.')
# body.find("GLOSSARY") -> 3; body.find("---", 4) -> 36 (inside "|---|---|", before the Widget row)
```

## 3. Evidence

- `scripts/tests/test_suite_checks.py::TestCheckGlossaryUsage::test_unused_term_not_detected_when_table_has_dashed_divider` — direct, passing test documenting the real (buggy) behavior.
- `scripts/tests/test_suite_checks.py::TestCheckGlossaryUsage::test_used_term_no_finding` — the adjacent "positive" test, annotated to note it passes for the same structural reason, not because the check genuinely distinguishes used from unused terms.
- Every GLOSSARY table in this suite (`execute-build.md`, `focus-plan.md`, `implementation-plan.md`, `design-orchestrator.md`, etc.) uses a dashed-divider table, so this check has almost certainly never fired correctly across the suite's history — an absence of observed symptoms is not evidence of correctness here, just evidence nobody looked (this ticket is the first time it was tested directly).

## 4. Impact

Low. This is an INFO-severity, advisory-only check (`report.add("INFO", ...)`) — it does not gate CRITICAL/WARNING counts, hash verification, or any certification decision. Its failure mode is silent under-reporting of a hygiene signal (an unused GLOSSARY term going unflagged), not a false positive or a security/correctness issue.

## 5. Recommendation

Fix `glossary_end`'s calculation to find the end of the table itself (e.g., search for the first blank line or the first line not starting with `|` after the GLOSSARY header, rather than the first bare `"---"` substring), then re-verify against the two existing tests (updating their assertions to reflect corrected behavior) plus a new true-positive case. Direct, quality-verified remediation per `role.md`'s "On code authority" (SUBSTANTIVE-LOGIC path) — not a `/harden-workflow` pass, since this is code logic, not workflow-file structure.

## 6. References

- `scripts/suite/checks.py:235-243` (the function).
- `scripts/tests/test_suite_checks.py` (the two tests documenting current behavior).
- `docs/DESIGN_PR_05_04_Suite_Checks_Test_Coverage.md` (the DESIGN whose Independent Critique and Acceptance Criterion 3 explicitly anticipated "a test reveals a real bug, name it, don't silently patch it").
- `implementation-plan/sovereign-redesign-cluster/tasks.md` Stage 4 Task 4.4 (the end-to-end verification this finding emerged from).

## 7. Remediation Record ([ADDED] 2026-07-07, by Claude Code)

```
REMEDIATION RECORD
  Ticket:            20260706_check-glossary-usage-divider-bug_workflow.md
  Faulting workflow: N/A (SUBSTANTIVE-LOGIC — scripts/suite/checks.py code, not a workflow .md file)
  Root cause fixed:  glossary_end computed via body.find("---", ...), which matched inside a
                     standard table's own |---|---| divider row before any term's definition
                     row. Replaced with _find_glossary_section_end(): walks line-by-line past
                     every `|`-prefixed row starting from the GLOSSARY heading, returning the
                     position of the first line after the table structurally ends -- no longer
                     dependent on matching a specific divider character sequence.
  Changes made:      scripts/suite/checks.py: new _find_glossary_section_end() helper;
                     check_glossary_usage() calls it instead of the inline body.find("---", ...).
                     scripts/tests/test_suite_checks.py: test_unused_term_not_detected_when_
                     table_has_dashed_divider renamed to test_unused_term_produces_info_finding,
                     assertion flipped from "documents the bug" (0 findings) to "verifies the
                     fix" (1 INFO finding, correct term named); test_used_term_no_finding's
                     comment corrected (no longer explains away a coincidental pass); new test
                     test_discriminates_used_from_unused_within_same_multi_term_table added --
                     a realistic multi-term GLOSSARY proving per-term discrimination, not just
                     aggregate pass/fail.
  Tests:             3/3 in TestCheckGlossaryUsage passing (was 2, one asserting buggy
                     behavior). Full suite: 295/295, 0 regressions.
  Verified against real data, not just synthetic tests: ran _find_glossary_section_end()
                     directly against design-orchestrator.md's real GLOSSARY table (8 real
                     terms) -- confirmed glossary_end lands exactly at the table's true end,
                     not inside it. Full suite-wide lint run: 0 INFO findings across all 33
                     real workflow files -- checked this isn't a silent false-clean (the fix
                     could theoretically still be broken in a way that produces 0 findings
                     universally); the direct real-file trace above rules that out, and 0
                     unused terms suite-wide is a credible, not suspicious, result for a suite
                     whose GLOSSARY tables have been actively maintained throughout this session.
  Linter:            0 CRITICAL, unchanged WARNING baseline (19, all pre-existing structural
                     gaps in unrelated files).
  Deferred:          NONE. This ticket's full scope (fix + both existing tests updated + one
                     new true-positive test, per the ticket's own Section 5 Recommendation) is
                     complete.
```

**Phylogeny Disposition**: `NO TRANSFER` (confirmed at closure — see header).

---
*Closed by Claude Code, 2026-07-07.*
