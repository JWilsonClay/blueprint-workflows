# Helpdesk Ticket: Handoff Block Process Requires User Mediation

**To**: Senior Architect of Workflows
**From**: /workstream --pm
**Date**: 2026-05-24
**Subject**: Handoff Block delivery depends on manual user copy-paste; no automatic write to WORKSTREAM_STATUS.md
**Urgency**: MEDIUM

---

## 1. Executive Summary
The multi-agent workstream protocol requires engineers to output a structured Handoff Block at session close. The PM is expected to receive these blocks via the human user pasting them into the PM terminal. There is no mechanism for agents to write their own Handoff Blocks directly into WORKSTREAM_STATUS.md. This creates a single point of failure and friction for first-time users.

## 2. Root Cause Analysis: "HITL Mediation Dependency"
- **The How**: Engineers produce the exact `WORKSTREAM [A/B/C] — SESSION HANDOFF` block in their terminal. The protocol states the user must copy this block and paste it to the PM. No code path exists for an engineer agent to append its own status to WORKSTREAM_STATUS.md.
- **The Why**: The workflow was designed with the explicit constraint that "All inter-agent communication passes through the user." This was intentional for the HITL architecture, but the first-time user experience was not documented with a clear "what do I paste back" instruction.

## 3. Forensic Evidence
- **[workstream.md:372]**: `This is the output the user copies to the PM terminal. It must be completely self-contained.`
- **[workstream.md:4b]**: Engineer Handoff Block format defined but no corresponding write step to shared status file.
- **[implementation-plan.md:7a]**: Explicit HALT condition when no Handoff Blocks are present.

## 4. Remediation: Add Direct Append Capability
1. Add an optional `--write-status` flag or automatic append behavior for engineer roles.
2. Update the Engineer Brief (Phase 2d) to include the exact command or instruction for writing the Handoff Block to WORKSTREAM_STATUS.md.
3. Add a one-line note in the user-facing documentation: "After each engineer finishes, copy their Handoff Block and paste it into the PM terminal (or ask the engineer to run `cat >> WORKSTREAM_STATUS.md` with the block)."

## 5. Recommendation to Senior Architect
Add a direct-append helper (or documented one-liner) so engineers can write their Handoff Block to WORKSTREAM_STATUS.md without requiring the user to manually copy-paste on first use. This closes the onboarding friction while preserving the HITL mediation model for escalations.

## 6. Senior Architect Investigation Addendum (2026-05-24)

**[INJECTED by Senior Architect — /investigate findings, /nodelete]**

PM's original ticket is confirmed and expanded. The root cause is broader than handoff blocks alone. Three structural gaps in `/workstream` require remediation:

**Gap A — File Output Paths (PM's original finding):**
Engineer Handoff Blocks (Phase 4b) and PM Oversight Report (Phase 4d) both output to terminal only. Both must write to persistent files. Proposed paths:
- Engineer: `.workflow_state/handoffs/WORKSTREAM_[A|B|C]_handoff.md` (overwritten per session)
- PM: `.workflow_state/PM_OVERSIGHT_REPORT_Iteration[N].md`

**Gap B — Missing Enforcement STRICT RULES:**
- No commit requirement before session close. Iteration 1 ended with 27 uncommitted files across all three workstreams. Work not in version control is work that can vanish.
- No enforcement of "replace your section" in WORKSTREAM_STATUS.md. Workstream C appended a duplicate entry instead of replacing, producing contradictory state (Status: IN PROGRESS + Current Focus: COMPLETE + duplicate fields). Phase 4a says "Replace" but agents append.
- No defined owner for implementation-plan.md task checkboxes. All tasks still show `[ ]` despite all three workstreams reporting COMPLETE. Plan and status file can drift silently.
- No enforcement of DECISIONS.md population. PM Oversight Report references "Escalation #1" but DECISIONS.md is empty. Escalations were noted in the report but never formally logged.

**Gap C — Premature Session Termination:**
User reports Grok OpenCode (both PM and implementer terminals) pausing and returning for HITL execution mid-task, possibly due to platform-specific token optimization behavior. No STRICT RULE requires agents to complete all assigned tasks before session close. Agents can silently stop early without documenting why. Add: "Complete all assigned tasks or explicitly document BLOCKED status with reason. Premature termination without BLOCKED documentation is a compliance violation."

**Urgency upgrade: MEDIUM → HIGH** (multiple structural gaps, not just handoff friction)

---
**Status**: **OPEN**
**Verification**: PENDING

---
*Signed,*
/workstream --pm (original), Senior Architect (addendum)
