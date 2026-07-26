# Helpdesk Ticket: /helpdesk-tickets's own Phase 2 checklist and STRICT RULES 7/12 have no mechanical enforcement

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 5.5)
**Date**: 2026-07-07
**Subject**: `helpdesk-tickets.md`'s Phase 2 TICKET VALIDATION checklist, STRICT RULE 7 (duplicate detection), and STRICT RULE 12 (Phylogeny/Status contradiction gate) are all currently manual/hand-checked, and a live audit of this campaign's own already-filed tickets found the exact defect STRICT RULE 12 exists to prevent.
**Urgency**: MEDIUM (this is the suite's own institutional-memory mechanism — an unenforced schema on the tickets that document every other workflow's failures undermines the whole chain)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER
**Phylogeny Disposition Note**: This engine reuses `scripts/investigate/citation_fidelity.py` directly (import, not a code pattern transferred/duplicated into a new file) — the established precedent for this campaign (e.g. `/harden-workflow` reusing `scripts/triage/matrix_completeness.py`). No structural DNA pattern (STRICT RULE template, decision scaffold) moved between workflow files as a result of this ticket; the transfer is a Python import, already the norm for this campaign's engines, not a new phylogenetic event.

---

## 1. Executive Summary

`/helpdesk-tickets`'s Phase 2 checklist asks 11 questions, most of them mechanical (filename convention, section presence, field validity, citation count) — but all are hand-checked today. STRICT RULE 7 ("check for existing open tickets against the same faulting workflow") and STRICT RULE 12 ("a ticket cannot close with Phylogeny Disposition still PENDING") are both stated as hard requirements with no structural backing. Running a new validator against this campaign's own already-CLOSED tickets from earlier this same session found real, live instances of exactly the STRICT RULE 12 violation: multiple tickets marked `REMEDIATED` while their `Phylogeny Disposition` field still read `PENDING`, plus prose-only forensic evidence sections instead of the mandated `file:///path#LN-LM` citation format.

## 2. Root Cause

Both mechanisms were specified as instructional discipline without a verification layer — the same enforcement-by-instruction gap this campaign has closed in nine prior workflows this session (five in Phase 4/one in this ticket's own file's history, four more in Phase 5 before this one).

## 3. Forensic Evidence

- **STRICT RULE 12's own text, uninforced**: [claude-commands/helpdesk-tickets.md](file:///home/jwils/blueprint-workflows/claude-commands/helpdesk-tickets.md#L272-L272)
  *Evidence: "A ticket cannot close — via either path — with Phylogeny Disposition still PENDING." No mechanism anywhere in the file checked this before Phase 4 set Status to REMEDIATED, prior to this session's fix.*
- **The contradiction-detection logic that now catches it**: [schema_validator.py](file:///home/jwils/blueprint-workflows/scripts/helpdesk_tickets/schema_validator.py#L90-L95)
  *Evidence: `phylogeny_status_contradiction` is `True` when Status starts with `REMEDIATED` and Phylogeny Disposition is still `PENDING` — the exact condition STRICT RULE 12 prohibits, now a computed boolean instead of an unenforced sentence.*
- **A real instance of the violation this check catches**, found live via this same engine against this campaign's own already-closed tickets: [CLOSED_20260707_execute-build-engine-gap_workflow.md](file:///home/jwils/blueprint-workflows/helpdesk-tickets/CLOSED_20260707_execute-build-engine-gap_workflow.md#L1-L10)
  *Evidence: header declares `Phylogeny Disposition: PENDING` while the closing block below declares `Status: REMEDIATED` — the exact contradiction, filed earlier in this same session before this ticket's own fix existed to catch it.*

## 4. Impact

Medium. This is a self-referential finding: the very tickets this campaign filed to document its OTHER workflows' gaps themselves failed the schema this workflow mandates. The impact is on institutional memory quality — a Phylogeny Disposition left PENDING after closure is exactly the "silent, undetectable loss" STRICT RULE 12's own text warns about, since it cannot be reconstructed later with the same fidelity.

## 5. Recommendation

Build `scripts/helpdesk_tickets/` to mechanically check the Phase 2 checklist, STRICT RULE 7, and STRICT RULE 12, reusing `scripts/investigate/citation_fidelity.py` directly for citation checks (same format, zero duplication). Separately — flagged here, not actioned in this ticket's own scope — this campaign's own already-closed tickets from this session should have their Phylogeny Disposition fields resolved retroactively; that is a data-cleanup task, not a structural gap in the workflow itself, and is being surfaced to the user rather than silently fixed or silently ignored.

---
**Status**: **REMEDIATED (built scripts/helpdesk_tickets/, wired into Phase 0a and Phase 2)**
**Verification**: `scripts/helpdesk_tickets/` built — 23/23 new tests passing, including a read-only invariant test and a regression test proving the Phylogeny/Status contradiction check catches a real malformed ticket. Full suite 463/463 passing. Live-run against this actual `helpdesk-tickets/` directory confirmed correct duplicate/staleness output, and against a real closed ticket from this session confirmed the exact contradiction described above. `helpdesk-tickets.md` wired at Phase 0a (duplicate + staleness) and Phase 2 (validation checklist, per-item annotated as engine-checked vs. judgment) — both keep explicit manual-fallback instructions. Frontmatter: version 5→6, `last_hardened` 2026-07-07. Lint: CLEAN (0 CRITICAL/WARNING) after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 5 — final target)*
