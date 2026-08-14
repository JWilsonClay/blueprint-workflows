# Helpdesk Ticket: Multi-Agent Close Semantics — Five Deferred Items Re-homed at the `--context` Ticket's Closure, So the Live Peer-Overwrite Pathway and the HANDOFF_ARCHIVE Contradiction Stay Visible

**To**: Senior Architect of Workflows
**From**: Claude Fable 5 — `blueprint-workflows` Senior Architect session
**Date**: 2026-08-13
**Subject**: `CLOSED_20260728_secretary_workflow.md` closed 2026-08-13 by explicit user approval at its built scope (`--context` MODE GATE — its items 1–4 and 6). Its five deferred items — two of them live defects — would otherwise lose their only session-start-visible tracking home once the closed file archives. This ticket is that home. Full forensics live in the parent; this file deliberately does not restate them.
**Urgency**: HIGH (item 7 is reproducible from protocol text on every tandem close, and `.workflow_state/` is untracked by git, so the overwrite it permits is unrecoverable)
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING
**Prior occurrence**: PREVIOUSLY DOCUMENTED — parent: `CLOSED_20260728_secretary_workflow.md`. Distinct from the open meta ticket `20260813_secretary_workflow.md` (Antigravity Restoration Cluster — delivery surfaces), which shares only the faulting workflow; the two do not overlap in scope.

---

## 1. Executive Summary

The `--context` mode is built, closed, and in production — that matter is finished. What remains are the parent ticket's openly-deferred items: `/secretary` Phase 4 still mandates an unconditional `HANDOFF.md` overwrite with no peer-detection (correct tandem behavior currently depends on an agent improvising *against* STRICT RULE 3, exactly once observed); the GLOSSARY still promises a `HANDOFF_ARCHIVE.md` that STRICT RULE 3 denies and that has never existed on disk; `--context` checkpoints are write-only until Phase 4 consumes the ledger; and two suite-level gaps (a machine-readable session index; active-`.workflow_state/` discovery in multi-rooted repositories) remain unspecified.

## 2. Root Cause Analysis: "Solo-Agent Assumption" (candidate pattern — carried from the parent, still not promoted)

- **The How**: `/secretary` Phase 4 has no representation of a peer agent — no detection, no attribution field, no merge step — while STRICT RULE 3 mandates overwrite. The one observed tandem close survived only because the second agent improvised a merge the protocol never instructed, and logged `NO ANOMALIES` while doing it.
- **The Why**: the parent ticket's remediation deliberately scoped itself to the checkpoint mode (items 1–4, 6) and deferred the Phase 4 surface entirely. The deferral was correct discipline against scope creep; this ticket exists so the deferral does not decay into silence. Full mechanism, filesystem evidence, and the parent's own two named self-corrections: see the parent — restating them here is the bloat `20260707_workflow-architectural-bloat_workflow.md` (open, CRITICAL) warns against.

## 3. Forensic Evidence

- **The five items, as deferred at closure**: [parent — Remaining deferred items](file:///home/jwils/blueprint-workflows/helpdesk-tickets/CLOSED_20260728_secretary_workflow.md#L189-L193)
  *Evidence: items 5, 7, 8, 9 enumerated with item 7 explicitly named "the live destruction pathway."*
- **Item 10, added by the parent's own correction pass**: [parent — deferred item 10](file:///home/jwils/blueprint-workflows/helpdesk-tickets/CLOSED_20260728_secretary_workflow.md#L218-L218)
  *Evidence: no workflow defines how to locate the active `.workflow_state/` when a repository contains more than one; an agent invoked from the repo root would have checkpointed into the dormant directory.*
- **The overwrite mandate, still live in v8**: [secretary.md STRICT RULE 3](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L633-L633)
  *Evidence: "HANDOFF.md is overwritten each session… Prior content is NOT archived unless it contains anomalies" — unchanged by the `--context` build, which deliberately did not touch Phase 4.*
- **The promised archive that has never existed**: [secretary.md GLOSSARY, HANDOFF.md row](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L67-L67)
  *Evidence: "(prior content preserved in HANDOFF_ARCHIVE.md if needed)" — directly contradicts STRICT RULE 3; the file exists in no known workspace.*

## 4. Remediation: The Five Items, Priority-Ordered

1. **Item 7 — Phase 4 peer-detection + attributed merge.** If the existing `HANDOFF.md` names a different generating agent for the same session date, merge under attributed headings — codifying the 2026-07-16 improvisation. This is the live pathway and goes first.
2. **Item 8 — resolve the `HANDOFF_ARCHIVE.md` contradiction** in the same Phase 4 edit, per `/nodelete`'s Contradiction Protocol: implement the archive the GLOSSARY promises, or correct the GLOSSARY to match STRICT RULE 3. (Items 7+8 are one surface — one edit session.)
3. **Item 5 — Phase 4 consumes `CONTEXT_LEDGER.md`** entries recorded since the last close into `HANDOFF.md`, marking them consumed. Until then, checkpoints are write-only.
4. **Item 9 — one-line-per-session structured ledger** written via `scripts/ledger/` (the denominator problem: 40 recorded sessions vs. 77 tickets vs. 46 retrospectives, an impossible inversion). Ordering: downstream of item 5 — build the collection layer before the reporting layer.
5. **Item 10 — specify active-`.workflow_state/` discovery** for multi-rooted repositories; check whether `/sentinel`'s `.doorway/substrate_index.json` already holds the needed facts before designing anything new.

**Sequencing constraint**: `secretary.md` currently carries the uncommitted v8 working-tree state. Any edit for items 7/8/5 should land after that state is committed, so the changes remain separable in history.

## 5. Recommendation to Senior Architect

Carried forward from the parent, still open, and still the right structural frame: **audit every Sovereign workflow that produces a single-author, overwrite-semantics artifact for the same assumption** — an artifact that overwrites must either carry agent attribution and merge semantics, or be paired with an append-only companion that cannot be clobbered. That audit is also the natural decision point on promoting "Solo-Agent Assumption" into `role.md` Section IV: this is the pattern's second-sighting-carried-forward, and promotion was deliberately withheld at n=2 per the role's own restraint precedent.

---
**Status**: **OPEN**
**Verification**: PENDING — each item verifies per its own scope (item 7/8: protocol text + a live tandem close leaving both agents' briefings attributed and intact; item 5: a consumed-and-marked ledger entry appearing in the next `HANDOFF.md`; items 9/10: design approved, then built and tested). Ticket closes via Remediation Record when the set is delivered or explicitly re-scoped by the user.

---
*Signed,*
**Claude Fable 5**
*(Senior Architect of Workflows — `blueprint-workflows` session, 2026-08-13)*
