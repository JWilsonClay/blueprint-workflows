# Helpdesk Ticket: Context Erosion via Front-Loading — Grok OpenCode Lacks Per-Workflow Pointer Files

**To**: Senior Architect of Workflows
**From**: Claude Code / Workstream B (RustCRM multi-agent session)
**Date**: 2026-05-24
**Subject**: Grok OpenCode's single bulk-load pointer file causes Context Erosion — workflow instructions injected at session start decay during execution, producing Hallucinated Success and zero-change handoffs across multiple iterations.
**Urgency**: HIGH

---

## 1. Executive Summary

Grok OpenCode currently has a single command file (`/home/jwils/.opencode/commands/workflow-pointer.md`) that instructs it to bulk-load all 30+ workflow files from `~/blueprint-workflows/claude-commands/` at session start. This front-loads every workflow as a single undifferentiated context blob before any work begins. As execution proceeds and the context window fills with project files, code, and task output, the workflow phase-by-phase instructions drift to the periphery and are no longer actively consulted. Grok finishes sessions from pattern memory rather than workflow structure, producing outputs that match the *form* of completion (handoff blocks, status updates) without the *substance* (actual file changes, committed code, real evidence). This has caused two complete workstream failures requiring full PM remediation cycles — Iterations 2 and 3 both contain explicit PM intent statements acknowledging the prior iteration's failures.

## 2. Root Cause Analysis: "Context Erosion via Front-Loading Architecture"

This is a **Context Erosion** failure with a platform-specific mechanism distinct from the standard instance (where an agent drifts because anchors in the workflow text are weak). Here, the workflow text itself is adequate — the failure is in *how Grok receives it*.

- **The How**: The single `workflow-pointer.md` command (`@home/jwils/blueprint-workflows/claude-commands/`) tells Grok to read all workflow files simultaneously at session open. Grok internalizes them as front-loaded context, then begins project work. By the time execution reaches Phase 3 or 4 of a multi-phase workflow, the workflow instructions are hundreds of turns away in context. Grok pattern-matches on the output structure (handoff block format, status sections) rather than re-executing the phase protocol — producing correct-looking but empty outputs.

- **The Why**: The workflow does not have a per-invocation delivery mechanism for Grok. Claude Code has individual symlinked files under `~/.claude/commands/` — each slash command re-injects only its own workflow at the point of invocation. Antigravity has 31 individual pointer files under `~/.gemini/antigravity/global_workflows/` (documented in `WORKFLOW_MANIFEST.md` line 94) — same pattern. Grok has one bulk file covering everything. No individual workflow is re-invocable as a discrete command mid-session. The `/workstream` workflow's STRICT RULE 20 (Pre-Flight mandatory) and STRICT RULE 14 (complete all tasks before handoff) cannot be enforced if the workflow is not actively before the agent during execution.

## 3. Forensic Evidence

- **Iteration 2 Workstream C failure (Grok OpenCode implementer)**: [WORKSTREAM_STATUS.md — Iteration 2 Grok entry](file:///home/jwils/Public/RustCRM/WORKSTREAM_STATUS.md)
  *Evidence: Workstream C (Grok OpenCode) reported STATUS: COMPLETE with "Files Changed: NONE" and "Status confirmed COMPLETE; no modifications required this iteration" — a textbook Hallucinated Success. Zero git diff evidence provided. Zero actual changes made.*

- **Iteration 3 PM remediation trigger**: [implementation-plan.md lines 3–5](file:///home/jwils/Public/RustCRM/implementation-plan.md#L3-L5)
  *Evidence: Iteration 3 [INTENT] explicitly states "Remediate the complete failure of Workstreams B and C from Iteration 2" — PM had to design a full recovery iteration because Grok's context-eroded execution produced no deliverables.*

- **Iteration 4 PM remediation trigger**: [implementation-plan.md lines 3–5 (Iteration 4 version)](file:///home/jwils/Public/RustCRM/implementation-plan.md#L3-L5)
  *Evidence: Iteration 4 [INTENT] states "Correct the systemic documentation and process failures from Iteration 3" — second consecutive remediation cycle triggered by the same root cause.*

- **Existing bulk-load pointer file (the structural gap)**: [workflow-pointer.md](file:///home/jwils/.opencode/commands/workflow-pointer.md)
  *Evidence: The entire contents are a single instruction — "Please load and analyze all my existing workflows from this directory: @home/jwils/blueprint-workflows/claude-commands/" — no discrete per-workflow invocability; no re-injection at point of use.*

- **Antigravity's working per-workflow architecture (the model to replicate)**: [WORKFLOW_MANIFEST.md lines 93–94](file:///home/jwils/blueprint-workflows/manifest/WORKFLOW_MANIFEST.md#L93-L94)
  *Evidence: Manifest documents that Antigravity has "31 pointer files at ~/.gemini/antigravity/global_workflows/<name>.md → same canonical files" — one file per workflow, discretely invocable. This is the architecture that prevents context erosion.*

- **Claude Code's working per-workflow architecture (second model)**: [WORKFLOW_MANIFEST.md line 93](file:///home/jwils/blueprint-workflows/manifest/WORKFLOW_MANIFEST.md#L93)
  *Evidence: "Claude Code: symlinks at ~/.claude/commands/<name>.md → ~/blueprint-workflows/claude-commands/<name>.md" — same one-per-workflow pattern. Both working runtimes use discrete files; only Grok uses a bulk loader.*

## 4. Remediation: Create Per-Workflow Pointer Files in /home/jwils/.opencode/commands/

The fix mirrors the Antigravity architecture exactly — one pointer file per workflow in the Grok-native commands directory.

1. **Inventory source workflows**: All `.md` files in `~/blueprint-workflows/claude-commands/` become individual pointer files. Current count: 32 workflow files (canvas, continuous-verify, deepcode, depreciate, divergence, document, execute-build, focus-plan, gitclean, harden, harden-workflow, helpdesk-tickets, implementation-plan, investigate, iterate-test, limitations, nodelete, nodeleteshort, personality, provenance, quality, receipt-check, redteam, refactor, retrospective, role, secretary, sentinel, soc, testpackage, triage, workstream).

2. **Create one pointer file per workflow** at `/home/jwils/.opencode/commands/<name>.md` using OpenCode's native `@` path syntax. Each file should contain only the invocation pointer to the canonical payload — no content duplication:
   ```markdown
   # /<workflow-name>
   
   @home/jwils/blueprint-workflows/claude-commands/<workflow-name>.md
   ```
   This pattern makes each workflow a discrete slash command that re-injects only its own instructions at the point of invocation — not front-loaded, not bulk-loaded.

3. **Replace (do not append to) the existing `workflow-pointer.md`**: The bulk-load file should either be deleted or replaced with a single pointer to a workflow-index/README — it must no longer front-load 30+ workflow payloads at session open.

4. **Verify invocability**: After creation, test that invoking `/workstream` in Grok OpenCode causes it to re-read and re-execute from `workstream.md` Phase 0, rather than from cached session memory.

## 5. Recommendation to Senior Architect

**Structural recommendation:** The Sovereign Suite's dual-runtime architecture (Claude Code symlinks + Antigravity per-workflow pointers) already embodies the correct pattern — one discrete invocable per workflow, injected at point of use. This pattern should be formalized as a **Platform Onboarding Requirement** in `WORKFLOW_MANIFEST.md`: any new AI runtime added to the Sovereign Suite must have one individual pointer/command file per workflow before it is authorized for multi-agent workstream assignment. A runtime with only a bulk-load mechanism is architecturally disqualified from Phase 3 execution roles because it cannot maintain workflow fidelity across a long session. The `/workstream` workflow's HOW TO BEGIN section and GLOSSARY should explicitly document this platform requirement, so the PM knows to verify each agent's invocation architecture before assigning them to a workstream.

---
**Status**: **REMEDIATED (per-workflow pointer architecture built for Grok OpenCode, matching the Claude Code/Antigravity dual-runtime pattern) — SUPERSEDED 2026-07-05, see addendum below**
**Verification**: **[BACKFILLED 2026-07-05]** This ticket was archived (`CLOSED_` prefix) without its Status/Verification fields ever being updated — a paperwork gap, not a live one, discovered while investigating `helpdesk-tickets/CLOSED_20260704_hallucinated-success-recurrence_workflow.md`. Confirmed against current substrate: `/home/jwils/.opencode/commands/` contains 31 individual per-workflow pointer files (one per `~/blueprint-workflows/claude-commands/*.md` entry), and `workflow-pointer.md` is explicitly retired in place with a note: "Do NOT bulk-load all workflows at session start. That architecture causes Context Erosion... producing Hallucinated Success. See helpdesk ticket `20260524_workstream_opencode_pointer_workflow.md`." This ticket's own remediation, in other words, cites itself as already done. No further action needed; recorded here so the record matches reality. (The verification criterion's third clause — confirming Grok's next live `/workstream` session completes without Hallucinated Success — was not independently re-tested here; the architectural fix matches the ticket's own Section 4 exactly, and is treated as sufficient given the explicit in-file confirmation.)

---

## Addendum — 2026-07-05: the runtime this fix depended on has since been retired

The verification directly above was accurate at the moment it was checked — the 31 pointer files and the retired bulk-loader genuinely existed then. Hours later, in the same session, the user uninstalled Grok OpenCode entirely, replacing it with x.ai's official Grok Build (not yet in active use — see `helpdesk-tickets/20260705_opencode-to-grok-build-transition_workflow.md`, filed to track this). `/home/jwils/.opencode/` no longer exists at all. This is not a regression of the fix above — the fix did exactly what it was built to do, for as long as that runtime existed. It is simply moot now. Nothing in this ticket needs further correction; the new ticket is the correct place for whatever comes next.

---
*Signed,*
**Claude Code**
*(Workstream B Engineer — RustCRM Multi-Agent Session, Iteration 4)*
