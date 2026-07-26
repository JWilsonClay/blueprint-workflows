# Helpdesk Ticket: Missing User-Invoked Archival Mode for Completed History

**To**: Senior Architect of Workflows
**From**: antigravity / Outlier Tracker Module Session
**Date**: 2026-07-04
**Subject**: The /nodelete protocol lacks a documented Archival Mode — no procedure exists for a user explicitly invoking /nodelete to move completed, non-contradicted history to .history/ ledgers and clean the active surface.
**Urgency**: MEDIUM
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: CONFIRMED — lineage entry added: `manifest/SUITE_PHYLOGENY.md`, "Lineage Entry — 2026-07-04 — 'verify-before-trusting-appearance' gate pattern, third occurrence (focus-plan.md → helpdesk-tickets.md → nodelete.md)"

---

## 1. Executive Summary
During the Outlier Tracker Module build session, the user invoked `/nodelete` with the clear intent to archive completed Phase 1 tasks out of the active `tasks.md` surface — not because those tasks contradict anything, but to clean the live document so only forward-looking work remains visible. The workflow contains no procedure for this scenario. The agent was left guessing the user's intent with no defined path to execute it, resulting in a confused exchange. The failure was not a behavioral error by the agent — it was a documentation gap in the workflow itself.

## 2. Root Cause Analysis: "Missing Archival Mode"
- **The How**: When the user invoked `/nodelete` against a planning document to archive completed phases, the agent had no documented procedure to follow. The workflow defines two mechanisms: scope discipline for ongoing edits, and the Quarantined Change Ledger for removed contradictions. It defines no mechanism for user-directed archival of non-contradicted completed history. The agent was forced to interpret intent without a protocol anchor, which caused the confusion.
- **The Why**: The workflow did not define an **Archival Mode** — a named, human-invoked procedure that moves completed, non-contradicted tasks and phases out of the active surface and into `.history/` ledger files. The concept of "completed work is finished, archive it for focus" is entirely absent from the protocol. The Safety Rail in Pillar 1 ("never delete a unit the user did not name and that does not directly contradict the change") does not distinguish between unmentioned/uncontradicted content and content the user is explicitly directing to be archived, leaving the agent with no path forward when the user invokes archival of completed items.

## 3. Forensic Evidence
- **Safety Rail (Pillar 1)**: [nodelete.md L89](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L89)
  *Evidence: States "never delete a unit the user did not name and that does not directly contradict the change." This rule is correct for the contradiction-cleanup use case but provides no carve-out for user-explicitly-invoked archival of completed history, creating an ambiguity the agent cannot safely resolve.*
- **Quarantined Change Ledger scope (Pillar 3)**: [nodelete.md L140-L148](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L140-L148)
  *Evidence: Defines the `.history/` ledger exclusively as a repository for removed contradictory values, stating "reading it would re-introduce the deleted contradiction." No mention of completed, non-contradicted history as a valid ledger resident, leaving the agent with no documented home for completed tasks the user wants archived.*

## 4. Remediation: Add a Formal Archival Mode to /nodelete
1. Add a clearly named **Archival Mode** section to the `/nodelete` protocol defining the following procedure: when a user explicitly invokes `/nodelete` against a planning document with the intent to archive completed phases, the agent moves those completed items into `.history/archive/[filename].ledger.md` and strips the active surface clean, leaving only forward-looking, active work visible.
2. **[User suggestion — 2026-07-04]** Split the `.history/` directory into two named subdirectories with parallel naming conventions, maintaining a clear separation of purpose:
   - `.history/quarantine/[filename].ledger.md` — the existing Quarantined Change Ledger. Receives contradicted or superseded values removed from active surfaces. Write-only at runtime; ingestion-banned per existing Pillar 3 rules.
   - `.history/archive/[filename].ledger.md` — the new Archival Ledger. Receives completed, non-contradicted history moved off the active surface by explicit user invocation. Readable for reference; not ingestion-banned (no contradiction risk).
   Both subdirectories use the same file naming convention (`[filename].ledger.md`) to ensure discoverability and consistency across both use cases.
3. Add a note clarifying that Archival Mode is **strictly user-invoked**: the agent never autonomously archives completed tasks. The trigger must be an explicit user instruction. This preserves the Safety Rail's intent while opening the path for the archival action.
4. Update the `HOW TO BEGIN` section to reference Archival Mode as a distinct invocation path alongside the standard scope-and-contradiction use.

## 5. Recommendation to Senior Architect
Add a formal **Archival Mode** to `/nodelete` — a named, human-invoked procedure covering the movement of completed, non-contradicted history from active planning surfaces to `.history/` ledger files. The current protocol is complete for contradiction cleanup but completely silent on the equally legitimate and common use case of deliberate archival for surface hygiene. Without this, any agent receiving this instruction will be forced to guess intent, generating the exact confusion that occurred here.

---
**Status**: **REMEDIATED (Pillar 6 — Archival Mode — added to /nodelete: /nodelete --archive invocation, phase_status.py-backed verification gate, .history/ split into quarantine/ + archive/, all cross-file references retargeted, registry aggregator fixed to match)**
**Verification**: See Remediation Record below.

---
*Signed,*
**Claude**
*(Session Agent — Senior Architect of Workflows role)*

---

## REMEDIATION RECORD

```
REMEDIATION RECORD
  Ticket:            20260704_nodelete_workflow.md
  Faulting workflow: /nodelete (missing protocol section — the actual gap);
                     scripts/registry/aggregator.py (dependency, would have silently
                     broken on the .history/ split without its own fix)
  Root cause fixed:  /nodelete had no procedure for user-invoked archival of
                     completed, non-contradicted history — every existing pillar
                     governed contradictions only. Routing archival through the
                     Quarantined Change Ledger would have been a category error.
  Changes made:      nodelete.md v4->v5 — new Pillar 6 (Archival Mode): explicit
                     `/nodelete --archive` invocation (never inferred); verification
                     gate via scripts/focus/phase_status.py's receipt-cross-referenced
                     status before archiving a tasks.md phase (Intent-Mismatch Gate
                     fires on anything short of confirmed-complete); .history/ split
                     into quarantine/ (existing Quarantined Change Ledger, relocated)
                     and archive/ (new Archival Ledger, Append-Only, not
                     ingestion-banned). GLOSSARY +2, STRICT RULE 14 added (13->14),
                     HOW TO BEGIN documents both invocation paths, INTEGRATION gains
                     an /execute-build line and clears a stale "to be refined"
                     parenthetical about /depreciate (the refinement had already
                     happened — Remediation on Contact catch, not a new decision).
                     One-time migration: .history/depreciate.md.ledger.md moved to
                     .history/quarantine/depreciate.md.ledger.md (the only real file
                     affected) — by hand, not scripted, a one-time action.
                     scripts/registry/aggregator.py: collect_history_events call
                     retargeted from .history to .history/quarantine — its flat,
                     non-recursive glob would otherwise silently stop finding any
                     quarantine ledger post-split, undercounting the registry with
                     no error (the exact shape of failure this suite calls Ghost
                     Logic).
                     Cross-file reference sweep (forward-looking text only —
                     historical Change Log entries left untouched, they correctly
                     describe state at the time): depreciate.md (9 sites + Change
                     Log entry 7, also explicitly disambiguated the new
                     .history/quarantine/ from the pre-existing, unrelated bare
                     quarantine/ staging dir), harden-workflow.md (Step TM-6, Change
                     Log entry 12), divergence.md (Context Bloat destination,
                     RECOMMENDED ACTION template, STRICT RULE 13, Change Log entry
                     5), execute-build.md (Step 5h.3, Change Log entry 7).
                     sentinel.md and .gitignore needed no change — the bare
                     .history/ trailing-slash pattern already covers both new
                     subdirectories recursively (verified, not assumed).
  Tests:             3 new (scripts/tests/test_registry.py,
                     TestQuarantineArchiveSplit): quarantine ledger found at the new
                     path, archive/ content excluded from contradiction aggregation
                     (proven with identical ledger content, not just absence),
                     pre-split flat path confirmed no longer scanned. 2 pre-existing
                     fixtures in the same file updated to the new path (would have
                     otherwise failed). Full suite: 186/186 passed (183 pre-existing
                     + 3 new), 0 regressions.
  Linter:            lint_workflows.py --workspace ~/blueprint-workflows: 0
                     CRITICAL, 19 WARNING (identical pre-existing baseline; every
                     file touched this pass is hash-clean).
  Deferred:          NONE. Phylogeny Disposition: CONFIRMED — this ticket's own fix
                     is recorded in manifest/SUITE_PHYLOGENY.md as the third
                     occurrence of a now-named recurring pattern (the
                     Verified-Completion Gate: focus-plan.md -> helpdesk-tickets.md
                     -> nodelete.md), with a recommended-transfer note for future
                     candidates (/execute-build, /receipt-check).
```
