# Helpdesk Ticket: /triage hand-duplicates two existing engines and has no structural completeness check for its own most-repeated STRICT RULE

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 4.4-4.5)
**Date**: 2026-07-07
**Subject**: `/triage` Phase 0b (task/phase state) and Phase 0c (receipt state) hand-count/hand-check facts that `scripts/focus/phase_status.py` and `scripts/receipt/coverage.py` already compute for other workflows, and nothing mechanically confirms the report actually mentions every Trigger Matrix workflow — despite STRICT RULES 3 and 9 and Phase 1's own injected text each independently naming that exact guarantee.
**Urgency**: LOW-MEDIUM (a real gap, but `/triage`'s own STRICT RULE 1 — cite specific evidence — and the human-in-the-loop review of every report provide some existing mitigation; still, a mechanical backstop is the correct fix per this campaign's own standard)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

`/triage` already sets a real precedent for engine reuse — three Trigger Matrix rows (`/harden`, `/iterate-test`, `/quality`) already call existing engines directly. Two of its own Phase 0 steps do not follow that precedent: 0b hand-counts `tasks.md` checkboxes (duplicating `phase_status.py`) and 0c hand-checks receipt files (duplicating `coverage.py`). Separately, this file states the same completeness guarantee three times in prose (STRICT RULE 3, STRICT RULE 9, Phase 1's injected "Completeness requirement") with no structural check that a workflow was never silently dropped from the emitted report.

## 2. Root Cause

`/triage` predates both `phase_status.py` (built 2026-06-30) and the Verification-Spine campaign's own systematic per-workflow audit — it was hardened multiple times (entries 1-12 in its Change Log) for content additions (new Trigger Matrix rows) but never received a fresh Honest-Design Discipline pass checking whether its own Phase 0 mechanics had accumulated duplication as sibling engines were built for other workflows.

## 3. Forensic Evidence

- `claude-commands/triage.md` (pre-fix) Phase 0b: "Read it fully... Count tasks by state" — no script call, despite `phase_status.py` existing and doing exactly this since 2026-06-30.
- `claude-commands/triage.md` (pre-fix) Phase 0c: "Are Build Receipts present?... Harden Grades?..." — no script call, despite `coverage.py` existing and doing exactly this for `/receipt-check`.
- STRICT RULE 3, STRICT RULE 9, and the Phase 1 "Completeness requirement" injection all independently state "every workflow must appear in the report" with no shared mechanical enforcement.

## 4. Impact

Low-to-medium. `/triage` is read-only and advisory (STRICT RULE 7: "does not execute any workflow"), so a Hallucinated-Success-shaped omission here degrades trust in the recommendation, not workspace state directly. Still, per this campaign's own standard, a repeatedly-stated guarantee with zero structural backing is exactly the pattern targeted for conversion.

## 5. Recommendation

Wire Phase 0b/0c to call `scripts/focus/phase_status.py` and `scripts/receipt/coverage.py` directly (no new parsing code needed). Build a small new completeness check (`scripts/triage/matrix_completeness.py`) that parses `triage.md`'s own Trigger Matrix headers and reports which are absent from a given report's text — a pure set-difference, explicitly NOT a proxy for evaluation rigor. See `implementation-plan.md` Phase 4.4-4.5 and `docs/compression-staging/triage-honest-design.md` for the full design.

---
**Status**: **REMEDIATED (2026-07-07)**
**Verification**: `scripts/triage/` built — 13/13 new tests passing (including a read-only invariant test), full suite 355/355 passing. Live-run against this actual `triage.md` correctly extracted all 25 distinct Trigger Matrix entries. A real regex bug (annotated headers like `/quality`'s "(audit trigger)" sit inside the same bold span as the name, so the closing `**` doesn't immediately follow the name) was caught and fixed during test-writing, before the live-run, not after. `triage.md` wired at Phase 0b/0c (direct engine calls) and a new Phase 2 Trigger Matrix Completeness Gate — each keeps an explicit manual-fallback instruction and an explicit statement of what the gate does NOT verify (name presence is not proof of evaluation rigor). Frontmatter: version 3→4, `last_hardened` 2026-07-07. Lint: CLEAN (0 CRITICAL/WARNING) after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 4)*
