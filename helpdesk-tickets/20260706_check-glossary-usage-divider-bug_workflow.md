# Helpdesk Ticket: check_glossary_usage never detects an unused GLOSSARY term

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Redesign Cluster, Stage 4 Task 4.4)
**Date**: 2026-07-06
**Subject**: `scripts/suite/checks.py`'s `check_glossary_usage` function cannot detect a genuinely-unused GLOSSARY term when the table uses a standard markdown dashed-divider row — which is every GLOSSARY table in this suite. Found via direct unit testing, not observed as a live symptom.
**Urgency**: LOW (INFO-severity check only; does not affect CRITICAL/WARNING findings, hash verification, structural checks, or any gating behavior)
**Root Cause Type**: SUBSTANTIVE-LOGIC (a code logic defect in `scripts/suite/checks.py`, not a workflow `.md` structural gap — `/harden-workflow` cannot remediate this per its own opening line and STRICT RULE 3)
**Phylogeny Disposition**: PENDING
**Status**: OPEN
**Verification**: PENDING — a direct code fix + regression test, whenever prioritized.

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
