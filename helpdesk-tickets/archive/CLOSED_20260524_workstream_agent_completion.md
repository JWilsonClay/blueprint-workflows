# Helpdesk Ticket: Agent Premature Termination and Possible Token Optimization Interference

**To**: Senior Architect of Workflows
**From**: Senior Architect (filed on behalf of user observation)
**Date**: 2026-05-24
**Subject**: Grok OpenCode terminates sessions before completing all workstream tasks; possible platform-level token optimization interfering with task completion
**Urgency**: MEDIUM — requires audit in next iteration; no hard evidence yet

---

## 1. Executive Summary
During Iteration 1, Grok OpenCode (both PM and implementer terminals) exhibited a pattern of pausing and returning to the user for HITL execution before completing all assigned tasks. The user suspects a possible prompt injection or platform-level behavior that instructs the agent to limit token usage, causing premature termination. No direct evidence exists yet, but the pattern is consistent enough to warrant a formal audit point and a structural mitigation in `/workstream`.

## 2. Root Cause Analysis: "Silent Early Exit"
- **The How**: The agent stops working mid-task and returns control to the user without documenting why. No BLOCKED status is set. No escalation is logged. The session simply ends.
- **The Why (hypothesized)**: Platform-level token optimization may be instructing the agent to minimize output. This would conflict with `/workstream`'s requirement for comprehensive task completion and structured handoff blocks. Alternatively, the agent may be interpreting the HITL architecture as permission to return after each sub-task rather than completing the full workstream.
- **Structural gap**: `/workstream` has no STRICT RULE requiring agents to complete all assigned tasks before session close or to explicitly document why they stopped early.

## 3. Forensic Evidence
- User observation (2026-05-24): "opencode is pausing and returning with me for HITL execution"
- User observation: "there may be a possible prompt injection telling grok to limit the token usage as much as possible"
- No BLOCKED entries in WORKSTREAM_STATUS.md despite premature returns
- No escalations logged in DECISIONS.md
- Pattern observed in BOTH PM terminal and implementer terminal

## 4. Remediation
1. **Structural fix in /workstream**: Add STRICT RULE requiring task completion or explicit BLOCKED documentation. Add language encouraging agents to proceed until all tasks are done: "You are expected to complete ALL assigned tasks in your workstream before producing the Handoff Block. If you cannot complete a task, set status to BLOCKED with a specific reason. Returning to the user without completing tasks and without BLOCKED documentation is a compliance violation."
2. **Audit point for next iteration**: Include in the PM's oversight checklist: "Did any agent terminate before completing all tasks? If yes, was BLOCKED status documented? If no documentation, flag as premature termination."
3. **Platform investigation**: If the pattern persists after the structural fix, consider moving the PM role to a separate Claude Code terminal window for more intentional execution.

## 5. Recommendation to Senior Architect
This ticket has two layers: a structural fix (add STRICT RULES now) and an observational audit (monitor next iteration). The structural fix is actionable immediately. The platform investigation depends on whether the pattern persists. File this as an audit point in the next iteration's implementation plan.

---
**Status**: **OPEN**
**Verification**: PENDING — requires next iteration observation

---
*Signed,*
Senior Architect of Workflows
