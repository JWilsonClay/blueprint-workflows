# Helpdesk Ticket: /harden-workflow re-derives structural facts by eye four times before finally confirming them mechanically, once, near the end

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 4.5)
**Date**: 2026-07-07
**Subject**: `/harden-workflow` Phases 1, 4d, 5b, and 7a/7c each independently ask "does this section exist" for the same structural elements, hand-checked each time — despite `scripts/suite/lint_workflows.py` and its underlying `scripts/suite/checks.py` library already answering exactly these questions, mechanically, and already being invoked by this same file at Phase 7d.
**Urgency**: LOW-MEDIUM (this workflow is itself the suite's own hardening authority; a structural gap in it undermines the credibility of every grade it certifies — but the existing Phase 7d linter gate does provide a real backstop before certification)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER
**Phylogeny Disposition Note** [RESOLVED 2026-07-07, retroactive fix per helpdesk-tickets/CLOSED_20260707_helpdesk-tickets-engine-gap_workflow.md]: `scripts/harden_workflow/` is new, self-contained code; the `checks.py` refactor promoted three inline booleans to standalone functions within one existing file (behavior-preserving, not a pattern moved between workflow files) and `scripts/triage/matrix_completeness.py` is reused via import, the established pattern. No lineage entry warranted.

---

## 1. Executive Summary

`scripts/suite/checks.py` already exports tested, importable functions for every structural presence question this file asks repeatedly: `parse_frontmatter`, `extract_glossary_terms`, `count_strict_rules`, `count_phases`, `check_symlinks`, `extract_workflow_refs`. `/harden-workflow` invokes the CLI wrapper around these (`lint_workflows.py`) exactly once, at Phase 7d, as a final blocking gate — but Phase 1's Assessment Card, Phase 4d's Inter-Workflow Reference Integrity, Phase 5b's `/triage` Compatibility Audit, and Phase 7a/7c's Completeness Check all ask the identical questions earlier, by manual re-reading, before the linter is ever consulted.

## 2. Root Cause

`/harden-workflow` predates both the Verification-Spine campaign's systematic audit and, in part, `scripts/suite/checks.py`'s own module decomposition (extracted from `lint_workflows.py` during a prior SoC pass). The linter gate (Phase 7d, STRICT RULE 19) was added as a late-session hardening pass (2026-05-25) without a corresponding pass through the file's own earlier phases to check whether they'd become redundant with it.

## 3. Forensic Evidence

- **The engine now wired in**: [harden-workflow.md](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L238-L243)
  *Evidence: Phase 1's ENGINE-BACKED block, added this session, invoking `scripts/harden_workflow/harden_workflow_audit.py` instead of the prior four-phase hand-checklist.*
- **The mechanical layer itself**: [scripts/harden_workflow/__init__.py](file:///home/jwils/blueprint-workflows/scripts/harden_workflow/__init__.py#L1-L43)
  *Evidence: the package's own contract docstring explaining the `grade_hint` is one-directional/advisory only, never a certified grade.*
- `claude-commands/harden-workflow.md` (pre-fix) Phase 1 Assessment Card: a hand-checklist ("[ ] GLOSSARY section present", etc.) — no script call, despite `checks.py`'s `check_structure()` computing exactly these booleans.
- Phase 5b (pre-fix): "Cross-reference the description against the trigger matrix... Confirm: Is this workflow represented?" — manual read, despite `scripts/triage/matrix_completeness.py` (built same session, Phase 4.4b) already extracting every Trigger Matrix workflow name mechanically.
- Phase 7c (pre-fix): a second hand-checklist for the SAME sections Phase 1 already asked about, immediately before Phase 7d runs the linter and gets the same answer a third time.

## 4. Impact

Low-to-medium, correctly directioned. `/harden-workflow` is this suite's own hardening authority — a structural gap here (re-deriving facts by eye instead of mechanically) risks the same Context Erosion failure this campaign has fixed in four other workflows this session, but Phase 7d's existing linter gate (already blocking on CRITICAL findings) provides a real backstop that limits the practical damage of an earlier-phase eyeballing error.

## 5. Recommendation

Wire Phases 1, 5b, and 7c to call a new consolidated CLI, `scripts/harden_workflow/harden_workflow_audit.py`, which imports `checks.py`'s functions directly (no re-parsing) plus two genuinely new pieces: a Degradation Check (Standard Version extraction + comparison) and a one-directional, advisory grade_hint (never a certified grade). See `implementation-plan.md` Phase 4.5 and `docs/compression-staging/harden-workflow-honest-design.md` for the full design.

---
**Status**: **REMEDIATED (2026-07-07)**
**Verification**: Small additive refactor to `scripts/suite/checks.py` (extracting three inline booleans into standalone functions) confirmed behavior-preserving via its existing 33-test suite passing unchanged. `scripts/harden_workflow/` built — 23/23 new tests passing (including a CLI-level read-only invariant test), full suite 378/378 passing. Live-run against two real workflows confirmed correct output (`harden-workflow.md` itself and `nodelete.md`, the latter correctly flagged as genuinely absent from `/triage`'s Trigger Matrix — a real finding, not a bug). `harden-workflow.md` wired at Phase 1, 5b, and 7c — each keeps an explicit manual-fallback instruction, and the `grade_hint` output is explicit that it is never a certified grade. Frontmatter: version 4→5, `last_hardened` 2026-07-07. Lint: CLEAN (0 CRITICAL/WARNING) after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 4 — final of four re-verification targets)*
