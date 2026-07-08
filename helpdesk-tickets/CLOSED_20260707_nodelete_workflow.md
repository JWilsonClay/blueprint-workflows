# Helpdesk Ticket: Archival Mode Fails to Execute Dual-Surface Plan/Task Cleanup

**To**: Senior Architect of Workflows
**From**: Antigravity Gemini
**Date**: 2026-07-07
**Subject**: /nodelete's Archival Mode treats implementation-plan.md as a generic document without receipt infrastructure, preventing completed phases from being cleared out concurrently with tasks.md.
**Urgency**: HIGH
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER — remediated as part of `helpdesk-tickets/CLOSED_20260708_plan-archive-pipeline-design_workflow.md`'s Sibling D fix, not a reusable pattern transferred from elsewhere.

---

## 1. Executive Summary
The user operates as a "vibe coder" who relies on active documents being fiercely forward-looking, meaning once a phase is built, its corresponding plan and task checklist should both be removed from the active workspace to prevent bloat. However, `/nodelete --archive` currently only formally clears `tasks.md` using the receipt infrastructure. It treats `implementation-plan.md` as a generic composed artifact lacking receipts, failing to recognize that the two documents share an identical 1:1 phase nomenclature. This structural gap causes completed architectural plans to linger in the active workspace, forcing the user to manually manage document bloat.

## 2. Root Cause Analysis: "Structural Gap"
- **The How**: When a user attempts to archive a completed phase, `/nodelete` will cleanly strip the phase from `tasks.md` and append it to `.history/archive/tasks.md.ledger.md`, but it refuses to apply this exact same receipt-verified archival logic to `implementation-plan.md`.
- **The Why**: Pillar 6 of the `/nodelete` workflow explicitly hardcodes the `phase_status.py` receipt verification strictly to `tasks.md` phases. It explicitly demotes all other composed artifacts (including `implementation-plan.md`) to a fragile fallback check (looking for `TODO` markers), completely missing the opportunity to leverage the shared phase nomenclature.

## 3. Forensic Evidence
- **[tasks.md Hardcoding]**: [nodelete.md](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L206)
  *Evidence: The verification gate explicitly restricts `phase_status.py` cross-referencing to "For a tasks.md phase specifically", creating an artificial boundary.*
- **[Plan Demotion]**: [nodelete.md](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L207)
  *Evidence: The workflow defines `implementation-plan.md` as a generic composed artifact with no receipt infrastructure, ignoring its 1:1 mapping with `tasks.md`.*

## 4. Remediation: Introduce Dual-Surface Receipt Verification
1. Update Pillar 6 to formally recognize `implementation-plan.md` (and any document sharing the phase nomenclature) as part of the receipt-verified infrastructure.
2. Modify the Archival Mode logic so that when a phase is declared `COMPLETE` by `phase_status.py`, the archival sweep targets the phase across ALL paired documents concurrently.
3. Upon `/nodelete --archive Phase X`, the workflow must simultaneously strip Phase X from both `tasks.md` and `implementation-plan.md` and append them verbatim to `.history/archive/tasks.md.ledger.md` and `.history/archive/implementation-plan.md.ledger.md` respectively.

## 5. Recommendation to Senior Architect
Redesign Pillar 6 of the `/nodelete` protocol to support "Dual-Surface Archival". The workflow must be upgraded to understand that a Phase is a cross-document entity. When the `phase_status.py` gate confirms a phase is complete, Archival Mode should aggressively clear that phase from both the execution checklist (`tasks.md`) and the architectural blueprint (`implementation-plan.md`), preserving the user's forward-looking "vibe coder" flow without sacrificing byte-for-byte historical accuracy in the ledgers.

## 6. User Escalation & Frustration Log (Added 2026-07-07)
**Critical Note from the User**: Due to the severe friction and ongoing failures of the current archival system failing to properly remove completed metadata and artifacts from the active workspace surfaces, the user reached a point of extreme frustration and *purposefully deleted* the plan and tasks files outright. The user explicitly authorized this deletion because they were "tired of trying to figure it out." This highlights a critical usability breakdown: when the automated archival engine fails to keep the active workspace fiercely forward-looking, the resulting bloat actively antagonizes the user's workflow to the point of manual, destructive override. This must be prioritized as a Tier 1 usability failure for the Senior Architect.

---

## 7. Remediation Record — 2026-07-08

Resolved by `helpdesk-tickets/CLOSED_20260708_plan-archive-pipeline-design_workflow.md`'s **Sibling D** fix (filed after this ticket, by a different session, as one of four coordinated fixes for the same class of gap — that ticket's own §2 secondary root cause is this ticket verbatim). `nodelete.md` Pillar 6 and STRICT RULE 14 now require **Dual-Surface Archival**: once `phase_status.py` verifies a `tasks.md` phase complete, the matching phase in the workspace's planning document (`implementation-plan.md`) is archived concurrently, into its own `.history/archive/implementation-plan.md.ledger.md` — verified present at [nodelete.md#L207-L210](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L207-L210) and STRICT RULE 14 at [nodelete.md#L269](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L269). Confirmed exercised for real in this workspace: `.history/archive/tasks.md.ledger.md` and `.history/archive/implementation-plan.md.ledger.md` both exist with full archived phase content (157 and 125 lines respectively). Frontmatter: `nodelete.md` version 6→8 across the two remediation sessions, `strict_rule_count` unchanged at 14 (an existing rule updated, not a new one added). Full suite: 466/466 tests pass.

**Related, not resolved by this closure**: §6's user escalation describes the *consequence* of this gap (manual, destructive deletion of `tasks.md`/`implementation-plan.md` in `~/blueprint-workflows` itself, done out of frustration before this fix landed) — the fix arrived after the workaround, not before it. Both files are gone from the active workspace (confirmed absent, user reports them in the OS recycling bin, not restored as part of this closure) but their content is not lost: the archive ledgers already contain what had been verified complete. A fresh `tasks.md`/`implementation-plan.md` pair will need to be generated via `/implementation-plan` the next time a plan is needed — this closure does not do that, since no plan was requested here.

---
**Status**: **REMEDIATED**
**Verification**: CONFIRMED — Dual-Surface Archival rule present and exercised in this workspace; 466/466 tests pass.

---
*Signed,*
**Antigravity Gemini**
*(Sovereign Helpdesk Analyst)*
*(Remediated by: Claude Code, Sovereign Scaling Cluster, blueprint-workflows main session, 2026-07-08 — via a sibling session's coordinated fix, cross-referenced and verified here)*
