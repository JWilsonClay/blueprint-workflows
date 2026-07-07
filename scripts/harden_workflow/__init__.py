"""
harden_workflow — Structural Assessment Evidence Engine
==========================================================
Deterministic engine (sibling of scripts/triage/, scripts/secretary/)
backing `/harden-workflow`'s Phase 1 Assessment Card, Degradation Check,
Phase 5b `/triage` Compatibility Audit, and Phase 7a/7c Completeness Check.

Named with an underscore (not a hyphen, which isn't a valid Python
identifier) to avoid collision with the existing `scripts/harden/` package,
which backs a DIFFERENT workflow — `/harden` (code security hardening), not
`/harden-workflow` (this workflow, meta-level workflow-file hardening).

`/harden-workflow` already runs `scripts/suite/lint_workflows.py` once, late,
at Phase 7d — but four earlier phases (1, 4d, 5b, 7a/7c) re-derive the exact
same structural facts by eye instead of calling the underlying, already-
exported, already-tested library functions in `scripts/suite/checks.py`
directly. This package does NOT re-parse anything `checks.py` already
parses — it imports those functions and adds exactly two genuinely new
mechanical pieces:

  1. degradation_check.py — extracts a workflow's stamped "Standard
     Version: N" and compares it to the current standard version. Pure
     text-extraction-plus-arithmetic.
  2. grade_hint.py — computes a one-directional, advisory grade suggestion
     from presence/absence booleans, implementing THE SOVEREIGN STANDARD's
     own literal decision table. Explicitly NOT a certified grade — presence
     is mechanical, but this file's own STRICT RULE 4b text shows presence
     alone does not prove a section is *complete*. A grade_hint of
     "Sovereign" means "no missing structural element was found," never
     "this workflow's content is good." Mirrors `/quality` v4's smell-linter
     precedent exactly: "no smells found says NOTHING about quality."

Also reuses `scripts/triage/matrix_completeness.py`'s
`extract_matrix_workflows()` directly for the `/triage` gap check — zero new
parsing there either.

Read-only; writes nothing.

Origin: implementation-plan.md Phase 4.5 (Sovereign Scaling Cluster),
docs/compression-staging/harden-workflow-honest-design.md.
"""

__version__ = "1.0.0"
