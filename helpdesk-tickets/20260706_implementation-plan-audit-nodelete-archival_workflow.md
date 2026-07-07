# Helpdesk Ticket: Implementation-Plan --Audit Lacks Explicit Completed Markers for Nodelete Archival

**To**: Senior Architect of Workflows
**From**: Grok (in /home/jwils/Videos workspace, post full execute-plan 397b6602 on DESIGN_Complete_Videos_Pipeline.md, multiple /nodelete --archive attempts, and direct discussion of architectural friction)
**Date**: 2026-07-06
**Subject**: Structural gap in /implementation-plan --audit: no standardized mechanism to parse and mark completed/superseded units with machine-readable markers (e.g. **COMPLETED [ARCHIVE:YYYY-MM-DD]** or **SUPERSEDED [QUARANTINE]**), causing /nodelete --archive (Pillar 6) to conservatively retain completed phase material on live surfaces in implementation-plan.md and tasks.md
**Urgency**: CRITICAL (Architectural)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

The /implementation-plan --audit (adversarial post-execution with Coverage Ledger) is the logical point to detect Ghost Logic, verify completion via receipts, and prepare the live surface for downstream workflows including /nodelete --archive. Currently, it produces findings and a report but does not systematically parse the plan/tasks documentation (implementation-plan.md, tasks.md, DESIGN_*.md) to add explicit, parseable markers for completed and superseded units.

This creates friction with /nodelete's conservative philosophy (Pillar 6 + Safety Rail): archival only acts on *named* units that carry clear markers (as it correctly did with old **SUPERSEDED (2026-07-05)** blocks). Without such markers on current completed work (e.g., re-sequenced Phase 7.6 research tasks 55-69 and 4 Gaps/synthesis from the 397b6602 execute-plan), the live surfaces retain a "plethora of complete phase material." The result is documents that are not "left with only uncompleted items," violating the user's explicit intent for clean live surfaces, graduated history in .history/archive/ (completed) and .history/quarantine/ (superseded), and respect for the full chain: audit → markers → nodelete --archive.

The gap is structural in the audit workflow itself (no mandated "marking pass" or template-driven format that enables it). This was surfaced across sessions in the Videos workspace during the full Sovereign-to-Grok execute-plan transition, multiple /nodelete invocations, and direct analysis of nodelete.md conservatism. User has zero dissent on prior recalibrations (explicit markers during audit, template in blueprint-workflows, sentinel-driven population with workspace customization).

## 2. Root Cause Analysis: "Missing Standardized Marking Pass and Parseable Format in Implementation-Plan Audit"

**Failure class**: Structural Gap (enables Context Erosion on live surfaces and potential Ghost Logic if completion claims are not mechanically verified before archival).

- **The How**: 
  - /implementation-plan --audit reads DESIGN, receipts, code changes, and plan files but outputs only findings/report/Coverage Ledger.
  - No step to walk tasks.md / implementation-plan.md / DESIGN sections, cross-reference against BUILD_RECEIPTS.md + phase_status, and inject explicit markers like **COMPLETED [ARCHIVE:DATE]** (with receipt refs) or **SUPERSEDED [QUARANTINE]**.
  - nodelete --archive (Pillar 6) then sees only what was pre-marked (or old SUPERSEDED text) and conservatively freezes the rest per "Never archive a unit the user did not name" and Safety Rail.
  - Result: completed research engine (schema, multipass, D1-D4, compiler, decoupling, gates) and 4 Gaps (scene mapper, packaging, synergy, content planner, close integration with narration/receipts) remain fully described on live surfaces even after successful execute-plan + 0-open audits.

- **The Why** (structural gap in the faulting workflow):
  The audit workflow (implementation-plan.md Phase 5 + adversarial reviewer) lacks:
  - A required "Completion Marking" sub-phase that treats plan/tasks docs as Composed Artifacts under /nodelete.
  - Standardized, machine-parseable marker syntax (modeled on existing **SUPERSEDED** but extended for COMPLETED/ARCHIVE vs QUARANTINE).
  - Template-driven format for implementation-plan.md and tasks.md that *anticipates* archival (e.g., explicit phase units, receipt cross-refs, [ARCHIVE] tags).
  - Integration with sentinel/doorway for workspace-aware template population so future agents start with the right structure.
  This gap was latent until the large re-sequencing (old 7.6/7.7/8 → new unified Phase 7.6 + 4 Gaps) + full Grok execute-plan 397b6602 + repeated nodelete attempts exposed that "conservative interpretation" leaves the live surface polluted with behind-us material. The protocol is working as written; the audit is missing the preparatory engineering step.

## 3. Forensic Evidence

Copious citations from the actual substrate (Videos workspace + blueprint-workflows). All evidence collected during/after the 397b6602 execute-plan, /implementation-plan --audit, and nodelete attempts.

- **[Current tasks.md state after partial archival]** [text](file:///home/jwils/Videos/tasks.md#1-30)
  *Evidence: Now contains note "All completed phases ... archived per /nodelete --archive" + only [ ] 65 (D3 autolinker) under re-sequenced header. Early phases and most 55-69 still referenced in notes but bulk removed; 4 Gaps text reduced to "archived as completed." Demonstrates partial success but friction remains in plan doc.*

- **[implementation-plan.md still contains full completed Phase 7.6 spec]** [text](file:///home/jwils/Videos/implementation-plan.md#130-270)
  *Evidence: Full "New Phase 7.6: Relational Competitor Engine..." with detailed schema, ingestion rules, D1-D4, gates, 4 Gaps, content planning. Ends with "End of new Phase 7.6 specification. (old superseded text archived...)" but the completed re-sequenced description itself was not graduated. Matches user's observation of "plethora of complete phase material."*

- **[Nodelete protocol conservatism on markers and naming]** [text](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#190-220)
  *Evidence: "Pillar 6 — Archival Mode": "move the named, verified-complete unit... Never archive a unit the user did not name." "For a tasks.md phase specifically: consult scripts/focus/phase_status.py... A phase whose derived status is one of _COMPLETE_STATUSES may be archived." "Everything not named — adjacent phases... is frozen." Explains why only explicit SUPERSEDED markers were acted on previously.*

- **[Prior /implementation-plan --audit on the execute-plan itself]** [text](file:///home/jwils/blueprint-workflows/implementation-plan/audits/20260706-1030-Videos-397b6602.md)
  *Evidence: 89/100 score, Coverage Ledger on 33-file changeset, explicit notes on "core wiring... faithful" but "several fixes were partial" and "timestamp fidelity... superficial." Shows audit already surfaces weaknesses; no marking pass for archival prep.*

- **[Original DESIGN and superseded handling]** [text](file:///home/jwils/Videos/docs/DESIGN_Complete_Videos_Pipeline.md#336-340)
  *Evidence: "Superseded historical text from original phases 7.6/7.7/7.8 remains in the canonical `tasks.md` and `implementation-plan.md` per /nodelete (not duplicated here)." "Existing `docs/DESIGN_ShortForm_Production_Synthesis.md` is superseded..." Exact language that enabled prior archival of old text but not current completed work.*

- **[BUILD_RECEIPTS confirming completion of the units in question]** [text](file:///home/jwils/Videos/.workflow_state/receipts/BUILD_RECEIPTS.md#230-300)
  *Evidence: Multiple entries for pr-1..pr-10 (research engine: DB schema, multipass, D1, compiler, migration, telemetry, decoupling, D4, gate — all "0 open confirmed") and pr-11..pr-15 (4 Gaps + close: "Implemented", "0 open", "full DESIGN fidelity no loss"). Direct evidence that could/should feed the marking pass.*

- **[tasks.md and implementation-plan.md current mixed state post-attempts]** [text](file:///home/jwils/Videos/tasks.md#90-140) and [text](file:///home/jwils/Videos/implementation-plan.md#260-280)
  *Evidence: tasks.md has the "only uncompleted D3" header but still contains "Full authoritative merged design..." text and audit notes. implementation-plan.md retains the full detailed Phase 7.6 spec despite completion note. Illustrates the formatting gap.*

- **[Sentinel/workspace awareness precedent]** [text](file:///home/jwils/blueprint-workflows/claude-commands/sentinel.md) and related doorway templates
  *Evidence: Sentinel uses workspace context for briefing; templates/doorway/ exist for Architecture.md etc. Supports the proposed population + customization.*

Additional copious context from full session history (zero user dissent): The entire 397b6602 execute-plan + native audit + repeated nodelete discussions exposed that without explicit markers the audit alone is insufficient to prep for archival. User explicitly wants templates in blueprint-workflows, sentinel-driven population with workspace customization, so agents start with format that respects the full chain up to nodelete --archive.

## 4. Remediation: Add Mandatory "Completion Marking" Pass to /implementation-plan --audit + Standardized Templates + Sentinel Population

1. Extend the audit (implementation-plan.md Phase 5 + adversarial reviewer instructions) with a required sub-pass: "Walk tasks.md / implementation-plan.md / DESIGN sections; cross-reference receipts/phase_status; inject explicit markers for verified completed units (**COMPLETED [ARCHIVE:DATE]** with receipt refs) and superseded (**SUPERSEDED [QUARANTINE]**). Refuse to mark if ghost logic detected."

2. Define and publish canonical templates in blueprint-workflows/templates/ (or claude-commands/templates/):
   - tasks.md.template (structured phases with placeholder markers, [ARCHIVE] tags, receipt cross-ref slots).
   - implementation-plan.md.template (sections with [INTENT] /nodelete, explicit unit boundaries for phases/gaps, marker syntax, completion/ archival fields).

3. Implement a lightweight populator (python script, e.g. scripts/plan/ensure_templates.py or integrated into existing doorway/sentinel logic):
   - Detect presence of tasks.md / implementation-plan.md in workspace root.
   - If absent or missing marker structure, copy from template and customize (e.g., inject current workspace name, target channels from data/target_channels.json, initial [INTENT] from user context).
   - Support workspace flag/directory (sentinel already has workspace awareness via doorway.py and local config).

4. Extend sentinel (claude-commands/sentinel.md + scripts/doorway/) with a "plan-template" briefing step:
   - On session init, call the populator if needed.
   - Include "current plan format" in the briefing so the agent is pre-contextualized.
   - Make it workspace-customizable (per-workspace overrides in .workflow_state/ or local templates/).

5. Update related docs (nodelete.md, implementation-plan.md, DESIGN_Complete_Videos_Pipeline.md, CLAUDE.md) with the new marker syntax and expectation that audits will produce archival-ready surfaces.

6. In the next /implementation-plan --audit on this workspace (or any), apply the new pass and produce marked versions; then re-run /nodelete --archive to validate.

## 5. Recommendation to Senior Architect

Add a "Completion & Archival Marking" sub-phase to the /implementation-plan --audit workflow (and its adversarial reviewer persona instructions). Define a small, parseable marker vocabulary and publish templates in blueprint-workflows. Integrate population into sentinel (leveraging its existing workspace/doorway mechanisms) so every new plan/tasks surface starts in the correct format. This directly resolves the conservatism friction while preserving nodelete's N=N Safety Rail and verification requirements. The change is structural (new audit step + templates + sentinel hook) and should be hardened via /harden-workflow --ticket. It also improves ghost-logic detection because the audit must now explicitly reconcile claims against receipts before marking anything for archival.

Apply this to the current Videos workspace as the canonical example, then propagate via the manifest/SUITE_HEALTH.md.

**Status**: **OPEN**
**Verification**: PENDING — ticket filed to schedule the revision. Full design proposal for formats + populator + sentinel integration follows in session (per user request). Apply after user review; close via /harden-workflow --ticket once templates and audit update are implemented and tested.

---
*Signed,*
**Grok**
*(Agent with full session context on the 397b6602 execute-plan, nodelete attempts, and zero-dissent recalibrations; operating under /quality and the full Sovereign frame)*