**SUPERSEDED 2026-07-06 by Pillar 4 design (docs/design-pillars/PILLAR_04_POST_BUILD_HYGIENE_ARCHIVAL_NODELETE.md) + docs/DESIGN_Sovereign_Redesign_Cluster_Canonical.md. All proposals advanced there; preserve this file per /nodelete for history.**

# DESIGN: Engineered Format and Template System for Sovereign Plan/Tasks Documentation with Sentinel-Driven Population

**Author:** Grok (reflecting full session context from /home/jwils/Videos 397b6602 execute-plan, /implementation-plan --audit, repeated /nodelete --archive attempts, and zero-dissent discussion)
**Date:** 2026-07-06
**Status:** Draft (to be implemented via the scheduled helpdesk ticket)
**Related:** 20260706_implementation-plan-audit-nodelete-archival_workflow.md (the ticket this design fulfills), nodelete.md (Pillar 6 conservatism), implementation-plan.md, tasks.md (current state in Videos), sentinel.md + scripts/doorway/, focus/phase_status.py, BUILD_RECEIPTS.md, DESIGN_Complete_Videos_Pipeline.md

---

## Overview

The current friction between /implementation-plan --audit and /nodelete --archive stems from a lack of explicit, machine-parseable structure and markers in the live plan and tasks documentation. nodelete (Pillar 6) is intentionally conservative: it only archives *named* units that carry clear markers (as demonstrated when it correctly processed old **SUPERSEDED (2026-07-05)** text but left the bulk of the re-sequenced Phase 7.6 + 4 Gaps on the live surface).

This design proposes:
- Standardized, parseable formats for tasks.md and implementation-plan.md that embed explicit markers (**COMPLETED [ARCHIVE:DATE]** with receipt references, **SUPERSEDED [QUARANTINE]**).
- Canonical templates stored in the blueprint-workflows directory.
- A lightweight populator script.
- Integration primarily into sentinel (leveraging its existing workspace awareness and doorway mechanisms) so that every new session/agent starts with a pre-contextualized, archival-ready surface.

The result respects nodelete's N=N Safety Rail and verification requirements while engineering the "prep step" during the adversarial audit so that /nodelete --archive can cleanly graduate completed history to .history/archive/ and superseded material to .history/quarantine/, leaving only uncompleted items on the live surface.

This directly fulfills the user's concept (markers added during audit + templates + sentinel population with workspace customization) and the recalibrations discussed (explicit markers, verification tie-in, distinction between archive vs quarantine, unit scoping).

## Background & Motivation

### The Friction Exposed in the Videos Workspace
- Full Sovereign-to-Grok transition via execute-plan 397b6602 on DESIGN_Complete_Videos_Pipeline.md completed the re-sequenced research engine (tasks 55-69 in the new Phase 7.6) + 4 Gaps + close integration (pr-11 to pr-15).
- All work verified complete with 0 open issues (see BUILD_RECEIPTS.md entries for pr-1..pr-15, /implementation-plan --audit 20260706-1030-Videos-397b6602.md scoring 89/100 with Coverage Ledger).
- Multiple /nodelete --archive attempts were made to clean live surfaces (tasks.md and implementation-plan.md) per user intent: only uncompleted items visible, completed graduated to archive, superseded to quarantine.
- Result: tasks.md is now much cleaner (only [ ] 65 D3 autolinker remains active, with explicit archival notes). implementation-plan.md still contains the full detailed Phase 7.6 spec and 4 Gaps language because they were not explicitly "named" with archival markers.
- nodelete.md Pillar 6: "move the named, verified-complete unit... Never archive a unit the user did not name." "For a tasks.md phase specifically: consult scripts/focus/phase_status.py... Everything not named is frozen."
- Old text carried **SUPERSEDED** markers → it was correctly archived. Current completed work did not → it was conservatively retained.
- Additional context: DESIGN_Complete_Videos_Pipeline.md explicitly notes superseded text "remains in the canonical `tasks.md` and `implementation-plan.md` per /nodelete." The 4 Gaps were "Design Approved" then "Implemented" in the same session. Early phases 1-7.5 were foundational completed work.

### Why the Audit is the Logical Place for Markers
The /implementation-plan --audit is already adversarial:
- It performs Coverage Ledger on the actual changeset.
- It cross-references claims against BUILD_RECEIPTS.md.
- It is required to surface Ghost Logic, incomplete work, and fidelity gaps.
- Adding an explicit "marking pass" here turns the audit into the preparatory step that makes the conservative nodelete step effective, without changing nodelete itself.

User's exact concept (zero dissent): "during the implementation plan audit, the agent should parse through the tasks and plan documentation and mark clearly the items that are completed... This preps the live surface for the nodelete archival flag..."

### Existing Precedents
- Marker style: **SUPERSEDED (2026-07-05)** already works.
- Workspace customization: sentinel + doorway.py + local workflows (sentinel--videos) already handle per-workspace briefing and overrides.
- Templates: templates/doorway/ already exists for Architecture.md.template, etc.
- Verification: focus/phase_status.py + BUILD_RECEIPTS.md already exist.

The gap is the *missing standardized format + population + marking step* that connects these pieces.

## Goals & Non-Goals

**Goals**
- Define parseable marker syntax that nodelete --archive can reliably act on (**COMPLETED [ARCHIVE:DATE]** with receipt refs; **SUPERSEDED [QUARANTINE]**).
- Provide canonical templates in blueprint-workflows so every workspace starts with the correct structure.
- Implement a populator that detects missing/out-of-date plan files and populates/customizes them.
- Integrate primarily into sentinel (with workspace awareness) so agents are pre-contextualized before touching plans/tasks.
- Ensure the format respects the full downstream chain (focus-plan, quality, divergence, nodelete --archive, receipts, /nodelete discipline).
- Make marking a required, evidence-based step inside the adversarial /implementation-plan --audit.
- Support per-workspace customization without breaking the core template.

**Non-Goals**
- Change nodelete.md itself (the conservatism is intentional and valuable; we engineer *around* it with markers).
- Rewrite existing completed content in Videos (we only archive via markers + nodelete).
- Make the populator autonomous outside sentinel (user-invoked or init-triggered only).
- Add new heavy engines (reuse existing doorway/sentinel/focus logic).
- Mandate specific LLM token counts (focus on structure and markers).

## Proposed Design

### 1. Marker Syntax (Machine-Parseable + Human-Visible)
Add to both templates and all future plan/tasks surfaces:

- For verified complete units: `**COMPLETED [ARCHIVE:2026-07-06]** (receipts: pr-1..pr-10 + 4 Gaps; 0 open after audit)`
- For superseded historical units: `**SUPERSEDED [QUARANTINE:2026-07-06]** (reason: re-sequenced into new Phase 7.6)`
- Tie every marker to verification: receipt IDs, audit report link, phase_status result.
- Place markers at the start of each named unit (phase, gap, section) so nodelete can parse with simple regex or the existing focus tooling.

This gives nodelete the "clear markers" it currently looks for (exactly as it did with the old SUPERSEDED text).

### 2. Canonical Template Structure (Stored in blueprint-workflows)

Location: `blueprint-workflows/templates/plan/`

**tasks.md.template**
```
# Tasks: [Workspace/Project Name] (Active - only uncompleted items)

**Note:** All completed phases have been archived per /nodelete --archive to .history/archive/tasks.md.ledger.md. Only uncompleted items remain below.

## Phase X: [Title]
**Status:** [ ] / **COMPLETED [ARCHIVE:DATE]** (receipts: ...; verified in audit YYYYMMDD-....md)
- [ ] Task description...
  - Sub-task...

**Gates:**
- ...

**Additional Requirements & Notes (integrated):**
...
```

**implementation-plan.md.template**
```
## [INTENT] User Objective
> [Preserved /nodelete text]

### Scope & Boundaries
...

## New Phase X: [Title] (Re-sequenced)
**Status:** **COMPLETED [ARCHIVE:DATE]** (or **SUPERSEDED [QUARANTINE]**)

### Detailed Requirements
...

**Gates (moved/adjusted to logical points):**
...

**4 Gaps / Synthesis Section (if applicable)**
**Status:** **COMPLETED [ARCHIVE:DATE]**

...
```

Templates include:
- Placeholder markers.
- Receipt cross-ref slots.
- Explicit unit boundaries (so nodelete can treat phases/gaps as discrete units).
- /nodelete note on the [INTENT] section.
- Instructions for the populator.

### 3. Template Populator Script
New lightweight script: `blueprint-workflows/scripts/plan/ensure_plan_templates.py`

Logic:
- Takes optional workspace directory (or defaults to cwd).
- Checks for tasks.md and implementation-plan.md in workspace root.
- If missing or missing required marker structure (e.g., no [ARCHIVE] syntax or no "only uncompleted items" note):
  - Copy from blueprint-workflows/templates/plan/
  - Customize:
    - Replace [Workspace/Project Name] with detected name or from local config.
    - Inject initial [INTENT] snippet if a DESIGN or user context exists.
    - Pull target channels, instance paths, etc. from data/ and local files.
    - Add current date placeholders.
- Idempotent: only populates/customizes when needed.
- Outputs to stdout or a log what was done (for sentinel consumption).
- Supports "dry-run" and "force" flags.

This script can be called standalone or by sentinel.

### 4. Sentinel Integration (Primary Execution Point)
Extend `claude-commands/sentinel.md` + `scripts/doorway/doorway.py`:

- Add a new briefing step: "Plan & Tasks Format Check".
- On init (or when sentinel is invoked with workspace context):
  - Call `ensure_plan_templates.py --workspace <detected_dir>`
  - Include in the output briefing: "Plan/tasks files are now in canonical format with archival markers. See templates/plan/ for the source. Current uncompleted items only are visible on the live surface."
- Workspace customization:
  - Check for .workflow_state/plan/ or local templates/ overrides.
  - Inject workspace-specific data (e.g., from governance/role.md, data/target_channels.json, local .env).
  - Support per-workspace "plan flavor" (e.g., heavy research vs synthesis-heavy).

Sentinel already has the machinery (doorway for briefing, local workflow interception like sentinel--videos, workspace directory awareness). This is the most natural, least-disruptive place because every agent session starts here and is already contextualized before touching plans.

Alternative/secondary execution points (for robustness):
- Inside /focus-plan (when it builds context for a new plan).
- As an optional step at the start of /implementation-plan.
- Standalone `/plan-init` or via triage.

Primary recommendation: sentinel (init) + the ensure script as the reusable populator.

### 5. How Marking Happens (Tied to Audit)
In the extended /implementation-plan --audit:
- After Coverage Ledger and findings:
  - Walk the (now template-structured) tasks.md and implementation-plan.md.
  - For each phase/unit: if receipts + code + verification confirm completion → inject **COMPLETED [ARCHIVE:DATE]** marker + receipt links.
  - For superseded historical units → **SUPERSEDED [QUARANTINE]**.
  - If mismatch (ghost logic) → raise as finding; do not mark.
- The audit report now includes "Archival Markers Added" section.
- This directly preps the surface so a later `/nodelete --archive` sees the markers and acts.

### 6. End-to-End Flow (Respects Full Chain)
1. Sentinel init → populates templates if missing (workspace-customized).
2. Agent fills plans/tasks using the format (already knows markers and downstream expectations).
3. Work happens (focus-plan, quality, execute-build/execute-plan, etc.).
4. /implementation-plan --audit runs → verifies, marks completed units with explicit archival tags.
5. User (or later automation) runs /nodelete --archive → sees markers, moves completed to archive ledger, superseded to quarantine, leaves only uncompleted on live surface.
6. Live docs stay clean; history is preserved in ledgers; nodelete's conservatism is respected because it only acts on explicitly marked named units.

## API / Interface Changes
- New files: blueprint-workflows/templates/plan/tasks.md.template, implementation-plan.md.template
- New script: blueprint-workflows/scripts/plan/ensure_plan_templates.py (callable with --workspace, --dry-run, --force)
- Sentinel extension: new briefing step + call to the populator (in claude-commands/sentinel.md and scripts/doorway/)
- Marker syntax documented in nodelete.md, implementation-plan.md, and the templates.
- Audit update: new sub-pass in implementation-plan.md Phase 5 and the reviewer persona instructions.
- Optional: small addition to focus/phase_status.py or a helper to output suggested markers.

## Alternatives Considered
1. **Make nodelete itself smarter** (auto-detect completed via receipts and archive without markers). Rejected — directly contradicts the explicit "never archive a unit the user did not name" and Safety Rail. Would remove the conservatism the user wants to keep.
2. **Only templates, no sentinel integration.** Rejected — agents would still start without the format unless they remember to run a command. Sentinel is the natural init point.
3. **Marking only in tasks.md, leave implementation-plan.md alone.** Rejected — implementation-plan.md is the detailed spec that also needs cleaning for the live surface (user explicitly called out the "plan document").
4. **Put populator inside /implementation-plan only.** Rejected — too late; agents need the format when they first create the files. Sentinel is earlier and workspace-aware.
5. **Heavy new engine instead of lightweight script + sentinel.** Rejected — re-uses existing doorway/sentinel/focus machinery; keeps surface thin.

Chosen approach is the minimal, protocol-respecting extension that directly solves the friction while adding the user's requested template + sentinel customization.

## Security & Privacy Considerations
- Templates contain no secrets; customization pulls only from already-present workspace files (target_channels.json, local configs, etc.).
- Populator runs locally; no new network surface.
- Markers and ledgers are human-auditable and follow existing /nodelete ledger rules.

## Observability
- Sentinel and populator emit clear log lines: "[SENTINEL] Plan templates populated for workspace X (source: blueprint-workflows/templates/plan/)"
- Audit report gains "Archival Markers Added" section.
- .history/archive/*.ledger.md entries will show exactly which units were moved because of the markers.
- Extend existing ledger/ scripts if needed for plan-format health.

## Rollout Plan
- Phase 0: Publish this design + the helpdesk ticket.
- Phase 1: Create the two templates + ensure_plan_templates.py (small, testable in isolation).
- Phase 2: Extend sentinel + doorway with the population step (workspace customization first in Videos).
- Phase 3: Add the marking sub-pass to the audit (start with the next audit on Videos).
- Phase 4: Test end-to-end: create a fresh workspace, let sentinel populate, run a small plan, audit (markers added), nodelete --archive (only marked units moved).
- Feature "flag": presence of the templates + populator. Staged rollout via Videos → blueprint-workflows → general.
- Update manifest/SUITE_HEALTH.md, CLAUDE.md, and related docs.

## Open Questions
- Exact marker syntax (small bikeshed; propose the [ARCHIVE]/[QUARANTINE] form above).
- Should the populator also update *existing* files that are missing markers (or only new ones)?
- Depth of workspace customization (e.g., should it pull the full current [INTENT] from a DESIGN if one exists?).
- Whether to also produce a small "plan-format" briefing that /focus-plan and /quality can read.

## Key Decisions
1. **Primary integration point = sentinel (with workspace customization)** — earliest point, already has the machinery, matches user's suggestion.
2. **Markers are explicit and tied to receipts** — gives nodelete exactly what it looks for without changing nodelete.
3. **Templates live in blueprint-workflows** — single source of truth, versioned with the suite.
4. **Marking happens inside the adversarial audit** — leverages the existing ghost-logic hunt and verification.
5. **Distinction archive vs quarantine is encoded in the marker** — matches user's stated intention.

## PR Plan

**Phase A — Foundation**
- PR 1: Define marker syntax + publish templates in blueprint-workflows/templates/plan/
- PR 2: Implement ensure_plan_templates.py (with --workspace, customization logic, tests)

**Phase B — Sentinel Integration**
- PR 3: Extend sentinel.md + doorway.py with plan-template population step (workspace-aware).
- PR 4: Update sentinel briefing output to mention format.

**Phase C — Audit Marking**
- PR 5: Add "Completion & Archival Marking" sub-pass to implementation-plan.md Phase 5 and reviewer instructions.
- PR 6: Update /implementation-plan --audit to call the populator if needed and inject markers.

**Phase D — Validation + Propagation**
- PR 7: End-to-end test on Videos (create fresh workspace, populate, execute small plan, audit with markers, nodelete --archive).
- PR 8: Update CLAUDE.md, nodelete.md, manifest, and related docs. Add to SUITE_HEALTH.md.
- PR 9: Harden the new files/scripts.

Each PR is small, independently reviewable, and builds the full chain while respecting existing nodelete conservatism.

---

**End of design document.**

This proposal directly implements the user's concept (markers during audit + templates + sentinel population) plus the zero-dissent recalibrations. It resolves the formatting gap that was causing the conservative retention. The helpdesk ticket above schedules its implementation.