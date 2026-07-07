# Helpdesk Ticket: /execute-build has no deterministic engine backing its mechanical steps

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 4.1-4.2)
**Date**: 2026-07-07
**Subject**: `/execute-build` still relies on "read the file and extract by eye" for Phase Map construction, receipt-presence checking, the Step 5d Completeness Scan, and the Step 5f Scope Compliance Check — all four are mechanical facts an agent could get wrong or skip under Context Erosion, matching the same failure shape the Verification-Spine campaign already fixed for `/focus-plan`, `/quality`, `/harden`, `/iterate-test`, and `/receipt-check`.
**Urgency**: MEDIUM (this workflow drives every phase of every build in this suite; the gap is latent, not actively causing failures, but the enforcement model — instruction, not structure — is the weakest available)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER
**Phylogeny Disposition Note** [RESOLVED 2026-07-07, retroactive fix per helpdesk-tickets/CLOSED_20260707_helpdesk-tickets-engine-gap_workflow.md]: `scripts/build/` reuses `scripts/focus/phase_status.py` via direct Python import — the established reuse pattern this whole campaign follows (e.g. `/harden-workflow` importing `scripts/triage/matrix_completeness.py`), not a structural pattern (STRICT RULE template, decision scaffold) transferred between workflow **files**. No lineage entry warranted.

---

## 1. Executive Summary

`/execute-build`'s Step 0b ("Read <TASKS_FILE> in full. Extract...") and Step 6's receipt logic were instructional-only, despite `scripts/focus/phase_status.py` already existing and already answering the exact same questions for `/focus-plan` and `/nodelete`. Steps 5d (Completeness Scan) and 5f (Scope Compliance Check) asked the agent to both perform a mechanical search (grep for TODO/FIXME/etc., diff touched files against declared scope) *and* attest that it did so — the weakest enforcement model this suite's own THE CONCEPT section names explicitly.

## 2. Root Cause

The 2026-06-02 Verification-Spine queue scan classified `/execute-build` as "Medium fit" and deferred it, noting its engine "would mostly reuse /focus-plan + /continuous-verify rather than add new substance." That assessment undervalued two things: (a) `phase_status.py` was built four weeks later and never wired back into the workflow that motivated its Phase-Map/receipt-cross-reference design in the first place; (b) Steps 5d/5f's searches are genuinely mechanical and were never covered by any existing engine.

## 3. Forensic Evidence

- **The engine now wired in**: [execute-build.md](file:///home/jwils/blueprint-workflows/claude-commands/execute-build.md#L89-L94)
  *Evidence: Step 0b's ENGINE-BACKED block, added this session, invoking `scripts/build/build_audit.py` instead of the prior "read and extract by eye" instruction.*
- **The mechanical layer itself**: [scripts/build/__init__.py](file:///home/jwils/blueprint-workflows/scripts/build/__init__.py#L1-L29)
  *Evidence: the package's own contract docstring — reuses `scripts/focus/phase_status.py` directly (not duplicated) for Phase Map/receipt status, and adds the two genuinely new pieces (completeness scan, scope diff) named in Section 5's recommendation below.*
- `claude-commands/execute-build.md` (pre-fix, v5) Step 0b: "Read <TASKS_FILE> in full. Extract: Every phase... Every task... current completion state" — no script invocation.
- `scripts/focus/phase_status.py`: already parses `tasks.md` into exactly this shape (`Phase` dataclass: title, checkboxes, status, receipt_status) — built 2026-06-30, extended 2026-07-04, used by `focus.py` and `nodelete`'s Archival Mode, never imported by anything under `execute-build.md`.
- `claude-commands/execute-build.md` (pre-fix) Step 5d/5f: pure prose instructions to search for markers / compare file lists — no engine, no test coverage, no structural guarantee the search actually ran.

## 4. Impact

Low-to-medium, correctly directioned (a false-negative risk — a skipped or sloppy manual check under Context Erosion — not a false-positive). Every `/execute-build` run since this workflow's creation has relied on the agent actually performing these mechanical steps faithfully; nothing structural verified that it did.

## 5. Recommendation

Build `scripts/build/` (read-only, mirrors `scripts/doorway/`/`scripts/focus/`): wrap `phase_status.py`'s existing report for Step 0b/0d/6, and add two new narrow modules for Step 5d (completeness marker scan) and 5f (scope diff via `git status`). Wire both into `execute-build.md` as verification rails, keeping every judgment call (acceptance criteria completeness, marker justification, scope-deviation warrant, the Regression Guard's semantic check) explicitly with the model. See `implementation-plan.md` Phase 4.1-4.2 and `docs/compression-staging/execute-build-honest-design.md` for the full design.

---
**Status**: **REMEDIATED (2026-07-07)**
**Verification**: `scripts/build/` built — 15/15 new tests passing (including an explicit read-only invariant test), 318/318 full suite passing, live-run confirmed against this actual workspace (correctly flagged a real out-of-scope file during its own build, evidence in `implementation-plan.md` Phase 4.2 work). `execute-build.md` wired at Steps 0b/5d/5f with explicit manual-fallback instructions if the engine is unavailable, per the established recipe. Frontmatter: version 5→6, `last_hardened` 2026-07-07. Lint: CLEAN (0 CRITICAL/WARNING), confirmed after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 4)*
