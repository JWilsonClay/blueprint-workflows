# Helpdesk Ticket: /triage's Trigger Matrix has no block for /investigate, despite /investigate documenting 7 explicit /triage trigger conditions

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, found while surveying next-step candidates after the Verification-Spine campaign)
**Date**: 2026-07-07
**Subject**: `investigate.md`'s own INTEGRATION section names 7 specific `/triage triggers` ("Something is broken and I don't know why" → `/investigate`, etc.), but `triage.md`'s Trigger Matrix — the authoritative table `/triage` actually evaluates — has no `/investigate` block at all. The link is one-directional and broken on the authoritative side.
**Urgency**: LOW (a real, live gap, but `/investigate` is still directly user-invocable regardless of `/triage` routing it — the failure mode is a missed recommendation, not a blocked capability)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER — a Trigger Matrix row addition local to `triage.md`, not a reusable engine or pattern.

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

## 6. Remediation Record — 2026-07-07

Added a `/investigate` block to `triage.md`'s Trigger Matrix (after `/redteam`), translating the 7 declared `/triage triggers` conditions from `investigate.md`'s own INTEGRATION section into 4 trigger rows using this suite's existing style: 2 mechanical (`<FAILURE_SIGNALS>` unexplained-behavior evidence at P2; journal/commit evidence of an unresolved error at P2) and 2 intent-driven (general "something's broken"/"walk me through" phrasing at P1; the explicit "treat this like a crime scene" invocation phrase at P0, matching `/investigate`'s own stated explicit-invocation semantics). This required judgment about priority levels and intent-modifier phrasing, per this ticket's own §5 — not mechanical, so it was filed rather than auto-fixed, and is now resolved by a Claude judgment pass rather than an engine.

**Verified**: [triage.md](file:///home/jwils/blueprint-workflows/claude-commands/triage.md#L315-L321) — new block present. `scripts/triage/matrix_completeness.py`'s `extract_matrix_workflows()` re-run against the live file confirms `/investigate` now appears (26 distinct entries, up from 25 at filing time). 463/463 suite tests pass, no regressions. Frontmatter: version 4→5, content_hash recomputed via `lint_workflows.py --fix-hashes --write`, last_hardened 2026-07-07. Change Log entry 14 appended to `triage.md`.

---
**Status**: **REMEDIATED**
**Verification**: CONFIRMED — engine re-run confirms the row is present and correctly parsed; full suite green.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster — post-campaign survey)*
*(Remediated by: Claude Code, Sovereign Scaling Cluster, blueprint-workflows main session, 2026-07-07)*
