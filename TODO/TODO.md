# Workflow Suite TODO — Discussion & Deferred Items
# Location: global_workflows/TODO/TODO.md
# Purpose: Tracks divergant workflow ideas that require discussion, merger analysis, or further deliberation before building.
# Updated: 2026-05-10 (v3 — ITEM 1 resolved)

---

## ITEM 1 — /sentinel (Divergence #2)
**Status**: ✅ COMPLETE — Built 2026-05-10

**[RESOLUTION — 2026-05-10, /nodelete]**
Merger candidate identified and confirmed: the .blueprints `Doorway Protocol` (`thedoorway/dynamic_contextualizer.py`) is exactly the ambient substrate monitor the user had already built. Rather than merging /sentinel into it or duplicating it, the Doorway system was extracted, refactored to a workspace-agnostic CLI package at `scripts/doorway/doorway.py` (Diamond-hardened), and /sentinel was built as the **workflow-layer orchestrator** that calls the Doorway tool and routes findings to the appropriate workflows. The hover-train/engine metaphor from the original discussion: Doorway is the track-sensing instrument; /sentinel is the control system that reads the instrument and tells the driver what to do.

All four Discussion Points resolved:
1. **Merger candidate**: Identified as .blueprints Doorway Protocol — NOT a duplicate; /sentinel wraps and elevates it.
2. **Relationship to /triage**: Documented in sentinel/core.md — /sentinel is proactive (session-init, physical substrate evidence), /triage is reactive (on-demand, symptom-based). Complementary, not redundant. Running both gives physical + symptomatic evidence before work begins.
3. **Session init hook distinctiveness**: /sentinel's evidence source is `doorway.py --output-json` (a real-time filesystem hash scan). /triage with no arguments has no evidence — it waits for user description. Architecturally distinct.
4. **Threshold configuration**: Severity levels (HIGH/MEDIUM/LOW) defined in `recommender.py`. The ticket threshold defaults to HIGH and is configurable per-session via `--no-ticket` flag. No external config file required at this stage — thresholds live in the recommender module.

**Artifacts produced:**
- `sentinel.md` — Sovereign pointer (P/P architecture, YAML frontmatter)
- `sentinel/core.md` — Full payload: 5-phase protocol, 8 STRICT RULES, 10-term GLOSSARY, routing table, multi-workspace mode, ticket gate
**Origin**: Divergence Session, 2026-05-07

### Idea Summary
An ambient workspace monitor that detects when specific workflows should be run and surfaces the recommendation proactively, without being asked. Designed to run at the initialization of a new agentic session as a standing check.

### User Note
> "Good idea, but needs to be discussed as a potential merger candidate for something else I have already built. Could be powerful to run at the initialization of a new agentic session."

### Discussion Points
1. **Merger candidate analysis**: The user has built something in their agentic stack that may already perform a similar function. Identify the existing tool before building a duplicate.
2. **Relationship to /triage**: /sentinel (proactive, ambient, threshold-based triggers) and /triage (reactive, on-demand, evidence-based) are architecturally distinct but functionally related. Should /sentinel be a mode or scheduled variant of /triage rather than a separate workflow?
3. **Session initialization hook**: If /sentinel runs at session start, is it distinct enough from /triage invoked at session start? What does /sentinel provide that `/triage` with no arguments does not?
4. **Threshold configuration**: Sentinel requires configurable thresholds ("N days since harden"). Where do these thresholds live? Hardcoded? A config file? This is a design decision that must be made before building.

### Next Action
Schedule a discussion session. Bring the existing agentic tool to compare. Decide: merge into /triage, build as a separate workflow, or deprecate as redundant.

---

## ITEM 2 — /handoff (Divergence #4)
**Status**: ✅ COMPLETE — Absorbed into /secretary Phase 3 (2026-05-07)
**Resolution**: User reviewed the case and approved. HANDOFF.md production is now Phase 3 of the `/secretary` meta-workflow. No separate /handoff workflow was created — /secretary is the session-close orchestrator that produces HANDOFF.md as one of its three primary outputs. See `global_workflows/secretary/core.md` Phase 3.

### Idea Summary
A session-exit workflow that packages current state (in-progress tasks, open decisions, deferred risks, next recommended command) into a `HANDOFF.md` file at workspace root, enabling a subsequent session to resume without re-discovery cost.

### User's Concern
> "Antigravity has a profound context window both with the brain infrastructure and Gemini's/Claude's massive context window. A fresh session should be utilized as a fresh context window when a session context can go 'sideways'... However, I could be wrong, so dissent is welcomed."

### The Case For /handoff (User Requested)

The user's instinct about fresh sessions being valuable is correct for POISONED contexts. But /handoff addresses a different and specific failure mode:

**The Re-Discovery Tax**: When a session ends mid-work (not poisoned, just paused), the next session begins by spending 10-30 minutes reconstructing: what was being built, which tasks are actually in-progress vs. in-tasks.md-limbo, what risks were identified but not resolved, and what the next command should be. This reconstruction is done from memory + reading multiple files. It is error-prone and consumes productive session time.

**The Distinction from "Poisoned" Sessions**:
- Poisoned sessions: user correctly uses a FRESH session with zero context. /handoff is irrelevant here.
- Clean paused sessions: work was going well, session simply ended for the day. /handoff is exactly for this case.

**Specific Agentic Scenario Where /handoff Provides Non-Obvious Value**:
In /execute-build, tasks are marked `[/]` (in-progress). If a session ends with a task at `[/]`, the next agent sees this and must decide: was this actually started? How far did it get? Was it partially built? The agent has no way to know without reading the entire prior session. /handoff writes a precise state record: "task X was started, file Y was created, file Z still needs to be modified, the risk identified was A." The next agent reads this in 30 seconds instead of reconstructing it in 30 minutes.

**When NOT to use /handoff**:
- When you're starting a completely fresh topic
- When the current session went sideways (use a fresh context window instead)
- For very short sessions with minimal state to carry forward

### Discussion Points
1. Does the brain's conversation log infrastructure already provide adequate session state for the agent to reconstruct? If yes, /handoff may be redundant.
2. Should /handoff write to the workspace (`HANDOFF.md` at root) or to the brain directory for the current conversation?
3. How does /handoff interact with `/document`? They both record session output — but different aspects of it.

### Next Action
User to review the case above and decide: (a) convinced — schedule build, (b) not convinced — archive as a low-priority idea, (c) need one concrete example from their own workflow to evaluate.

---

## ITEM 3 — /continuous-verify (Divergence #7)
**Status**: ✅ COMPLETE — Built and integrated into /execute-build Step 5g (2026-05-07)
**Resolution**: User was convinced by the clarification that /continuous-verify is NOT a separate user-invoked workflow — it is an automatic gate inside /execute-build. Built as `global_workflows/continuous-verify/core.md` (Sovereign, Standard Version 2). Integrated into `/execute-build/core.md` as Step 5g, injected between Step 5f and Step 6. Three outcomes: PARITY (silent), MISMATCH (halt, block receipt), UNVERIFIABLE (advance with risk note). See `global_workflows/continuous-verify/core.md` and `global_workflows/execute-build/core.md` Step 5g.

### Idea Summary
A post-phase hook inside /execute-build that automatically runs /focus-plan's Phase 3 substrate check on the code just built, before the next phase begins. Not a separate user-invoked workflow — an automatic gate inside the build loop.

### User's Concern
> "It feels like workflow bloat. It seems it's supposed to be ran in case I forget to run /focus-plan... if I forget to run /focus-plan, I'll probably forget to run this one too."

### Clarification (Critical Distinction)
The user's reasoning would be correct if /continuous-verify were a separate workflow the user invokes. **It is not.** It is a gate INSIDE /execute-build that runs automatically at each phase boundary — the user never directly invokes it. The user doesn't need to remember it. It fires as part of the build loop.

The analogy: /continuous-verify is to /execute-build what the per-step test gates are to /soc. You don't "remember to run the test gate" — it just runs after each extraction because the workflow mandates it.

### Why It Might Still Be Unnecessary
The user's broader concern might be valid from a different angle: if /execute-build's Build Audit (Step 5) already includes acceptance criteria verification and scope compliance, /continuous-verify may be redundant. The Build Audit already checks that the built code matches the plan.

**The real question**: Is there a meaningful gap between "did this phase's code match its acceptance criteria" (Build Audit) and "does this phase's code still match the OVERALL plan's intent" (continuous-verify)? 

For small plans: probably not. For large multi-phase plans where early phases can drift from late-phase requirements: yes.

### Discussion Points
1. Is the Build Audit in /execute-build Step 5 already sufficient for plan-build alignment?
2. Should /continuous-verify be folded INTO /execute-build Step 5 as an additional sub-step rather than being a named workflow?
3. At what project complexity/phase count does /continuous-verify start adding real value vs. adding noise?

### Next Action
Consider: fold the core concept into /execute-build Step 5 as an optional "deep plan alignment check" triggered only for multi-phase projects. Retire the separate workflow concept.

---

## ITEM 4 — /pipeline (Divergence #8)
**Status**: HOLD — Deferred Until User Reaches Operational Maturity
**Origin**: Divergence Session, 2026-05-07

### Idea Summary
A meta-workflow that composes and sequences the other workflows based on project phase: focus-plan → execute-build → iterate-test → harden → soc → document. Automates the sequencing that the user currently manages manually.

### User's Assessment
> "I feel like if we build it, I won't fully know how to wield it yet. But I'm open to it."

### Agreed. Here's Why the Timing Matters.
/pipeline is the most powerful and the most dangerous workflow in the proposed suite. It automates away the human judgment calls that are currently manual — specifically: when to deviate from the standard sequence, when to skip a step, when to insert an extra /focus-plan before proceeding.

Right now, the user IS the pipeline. They've been manually learning what the right sequence is for different situations. That manual experience is exactly what /pipeline would eventually encode. Building /pipeline before the manual sequence is deeply understood risks automating the wrong sequence — or automating too rigidly, removing the flexibility that makes the manual approach valuable.

**The prerequisite**: Run the full manual pipeline (focus-plan → tasks.md → execute-build → iterate-test → harden → document) on 5-10 projects. Notice where you deviate. Notice what you skip and why. Notice what you add that's not in the standard sequence. When that pattern is clear, /pipeline encodes it.

### Discussion Points
1. After what milestone does /pipeline become appropriate? Specific criterion: "I can describe the standard pipeline from memory AND describe 3 scenarios where I would deviate from it and why."
2. Should /pipeline be project-type-aware? (A new feature has a different sequence than a refactor or a security hardening sprint.)
3. Does /triage already provide enough sequencing guidance that /pipeline is less necessary?

### Next Action
Re-visit this item after completing the Layer 2 build roadmap (Stages 1-3: /receipt-check, /retrospective, /provenance). By then, the user will have more operational experience to evaluate whether /pipeline adds value.

## ITEM 5 — WORKFLOW_DEPENDENCIES.md (Divergence #5 from /secretary session)
**Status**: DEFERRED — Approved, Awaiting Optimal Timing
**Origin**: /secretary Divergence session, 2026-05-07
**User note**: "#5 should be added to the TODO.md as a TODO item and not as a discussion item; approved, but awaiting optimal timing for implementation."

### Idea Summary
A machine-readable dependency graph at `global_workflows/WORKFLOW_DEPENDENCIES.md` documenting which workflows depend on which other workflows being configured or built first. Examples: `/receipt-check` requires Stage 1a (receipt-writing) to be operational; `/continuous-verify` requires SoC modularization of /execute-build; `/retrospective` requires `process_learnings/` to exist.

### Why It Matters
/triage and /secretary could read this file to detect "you can't run X until Y is configured" and surface actionable setup blockers before a user wastes a session attempting to use an underpowered workflow.

### Implementation Notes
- Format: simple markdown table or structured list at `global_workflows/WORKFLOW_DEPENDENCIES.md`
- Updated by: /secretary Phase 1 (auto-discovery) or manually
- Read by: /triage (for setup recommendations), /secretary (for manifest warnings)
- Complexity: LOW for the file itself; MEDIUM for /triage integration

### Next Action
Implement after the current suite stabilizes (post-Stage 1a completion and at least one full /secretary run on a real project). The dependency graph is most accurate once all receipt-writing is operational.

---

## ITEM 6 — Claude Code Migration: Destructive Cleanup
**Status**: PENDING USER CONFIRMATION
**Origin**: Claude Code port session, 2026-05-21

All 29 command files ported and symlinked. The following destructive operations were staged and presented to the user but not yet executed:

**Step 1 — Delete 17 source directories** (each contains only core.md or role.md — fully ported):
```
depreciate/ divergence/ gitclean/ harden/ harden-workflow/ investigate/ iterate-test/
personality/ provenance/ receipt-check/ redteam/ refactor/ retrospective/ role/
secretary/ sentinel/ soc/
```

**Step 2 — Partial cleanup** (preserve directory; delete only core.md):
- `helpdesk-tickets/core.md` — live ticket files remain (1 open: 20260515_soc_caller_scan_script.md)
- `implementation-plan/core.md` — `audits/` subdirectory must be preserved

**Step 3 — Delete 25 root pointer/standalone files** (all replaced by claude-commands/ single files):
```
canvas.md deepcode.md depreciate.md divergence.md document.md gitclean.md harden.md
harden-workflow.md helpdesk-tickets.md implementation-plan.md investigate.md iterate-test.md
limitations.md nodelete.md nodeleteshort.md personality.md provenance.md receipt-check.md
redteam.md refactor.md retrospective.md secretary.md sentinel.md soc.md testpackage.md
```

**Next action**: User confirms → agent executes all three steps in sequence. No design decisions needed; purely mechanical.

---

## ITEM 7 — CLAUDE.md Identity Section Modularization
**Status**: NEEDS DESIGN DECISION
**Origin**: User note surfaced during Claude Code port session, 2026-05-21

User's exact note: *"if this file is in every prompt in every workspace, then this isn't necessarily the correct role. this role is specifically ONLY for the workflows workspace, which, again, would not be in every prompt in every workspace. If true, this would need to be brought under consideration and modularized out of this global file."*

The "Senior Architect of Workflows" identity section in `~/.claude/CLAUDE.md` is workspace-specific to blueprint-workflows, but CLAUDE.md is a global file loaded in every Claude Code session across all workspaces.

**Options to discuss:**
1. Remove the Identity section from `~/.claude/CLAUDE.md` entirely; keep it only in `~/blueprint-workflows/CLAUDE.md` (project-level) and `~/blueprint-workflows/claude-commands/role.md`
2. Keep a minimal identity stub globally; full identity only in blueprint-workflows project CLAUDE.md
3. Leave as-is (accept that the architect identity bleeds into non-blueprint sessions)

**Next action**: One design conversation. No code until the approach is chosen.

---

## ARCHIVE / COMPLETED
*(Items move here when built or formally retired)*

| Item | Outcome | Date |
|------|---------|------|
| /triage (Divergence #1) | ✅ Built — `triage.md` | 2026-05-07 |
| /receipt-check (Divergence #3) | ✅ Built — `receipt-check/core.md` (Sovereign, Std. v2) | 2026-05-07 |
| /retrospective (Divergence #5) | ✅ Built — `retrospective/core.md` (Sovereign, Std. v2) | 2026-05-07 |
| /provenance (Divergence #6) | ✅ Built — `provenance/core.md` (Sovereign, Std. v2) | 2026-05-07 |
| ITEM 2 /handoff (Divergence #4) | ✅ Absorbed into /secretary Phase 3 — HANDOFF.md output | 2026-05-07 |
| ITEM 3 /continuous-verify (Divergence #7) | ✅ Built — `continuous-verify/core.md` + injected into /execute-build Step 5g | 2026-05-07 |
| ITEM 1 /sentinel (Divergence #2) | ✅ Built — `sentinel.md` + `sentinel/core.md` (Sovereign, Std. v1). Doorway Protocol extracted to `scripts/doorway/` (Diamond-hardened). | 2026-05-10 |
