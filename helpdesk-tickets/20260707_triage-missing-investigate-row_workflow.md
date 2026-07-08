# Helpdesk Ticket: /triage's Trigger Matrix has no block for /investigate, despite /investigate documenting 7 explicit /triage trigger conditions

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, found while surveying next-step candidates after the Verification-Spine campaign)
**Date**: 2026-07-07
**Subject**: `investigate.md`'s own INTEGRATION section names 7 specific `/triage triggers` ("Something is broken and I don't know why" → `/investigate`, etc.), but `triage.md`'s Trigger Matrix — the authoritative table `/triage` actually evaluates — has no `/investigate` block at all. The link is one-directional and broken on the authoritative side.
**Urgency**: LOW (a real, live gap, but `/investigate` is still directly user-invocable regardless of `/triage` routing it — the failure mode is a missed recommendation, not a blocked capability)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

Every workflow's INTEGRATION section documents its own expected `/triage triggers` as a form of self-declared routing intent, but `/triage`'s Trigger Matrix is the actual authority `/triage` Phase 1 evaluates — a workflow's own claim about how it should be triggered does nothing unless a corresponding row exists in `triage.md` itself. `/investigate` documents 7 such conditions; none of them exist as rows in `triage.md`'s Trigger Matrix, discovered by running `scripts/triage/triage_audit.py`'s underlying `extract_matrix_workflows()` against `triage.md` and comparing the result against `/investigate`'s own declared triggers.

## 2. Root Cause

`/investigate`'s INTEGRATION section was written (2026-05-09/12 hardening passes) with its own `/triage triggers` list as a matter of self-documentation convention, matching every other workflow's INTEGRATION section — but no corresponding hardening pass ever added the reciprocal row to `triage.md` itself. This is a one-directional documentation gap: `/investigate` believes it is triage-routed; `/triage` has never actually been taught to route to it.

## 3. Forensic Evidence

- **`/investigate`'s own declared triggers**: [investigate.md](file:///home/jwils/blueprint-workflows/claude-commands/investigate.md#L417-L424)
  *Evidence: 7 explicit `/triage triggers` lines, none of which have a corresponding Trigger Matrix row in `triage.md`.*
- **`triage.md`'s Trigger Matrix, confirmed to have no `/investigate` block**: [triage.md](file:///home/jwils/blueprint-workflows/claude-commands/triage.md#L166-L169)
  *Evidence: the Trigger Matrix section header and its first block (`/harden`) — `/investigate` never appears anywhere in this section, confirmed via `scripts/triage/matrix_completeness.py`'s `extract_matrix_workflows()` against the live file (25 workflows extracted, `/investigate` not among them).*

Note: `/sentinel` is also absent from the Trigger Matrix, but this is correctly intentional — `sentinel.md`'s own INTEGRATION section explicitly states "`/sentinel` and `/triage` are architecturally distinct... sentinel is proactive (session-init), triage is reactive (on-demand)" — no `/triage triggers` list is claimed for `/sentinel` at all. Only `/investigate` has the mismatch.

## 4. Impact

Low. `/investigate` remains directly user-invocable; the gap only means `/triage` will never proactively surface it as a recommendation for a described symptom that should route there, even though `/investigate`'s own text promises exactly that routing.

## 5. Recommendation

Add a `/investigate` block to `triage.md`'s Trigger Matrix, using `investigate.md`'s own 7 documented conditions as the source triggers (e.g. "Failure signals detected with no clear cause" → P2, intent-driven elevation on phrases like "walk me through what happened"). This requires judgment about priority levels and intent-modifier phrasing (matching every other Trigger Matrix block's own style) — not mechanical, so it is being filed rather than auto-fixed in this pass.

---
**Status**: **OPEN**
**Verification**: PENDING

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster — post-campaign survey)*
