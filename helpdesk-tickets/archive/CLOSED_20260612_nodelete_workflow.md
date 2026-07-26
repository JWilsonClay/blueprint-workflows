# Helpdesk Ticket: Ambiguity Resolution Gap in /nodelete Workflow Causing Unintended Spec Rewrites and Contradiction Accumulation

**To**: Senior Architect of Workflows
**From**: Antigravity / Session c4c2fbf9-4ff9-4b3f-bf03-1aef0583eb18
**Date**: 2026-06-12
**Subject**: /nodelete lacks a clear protocol for resolving user-communicated corrections, leading to speculative rewrites and stale configuration accumulation.
**Urgency**: HIGH

---

## 1. Executive Summary
There is a fundamental interface gap between the organic, apragmatic user (who communicates specific, localized corrections as they notice them) and the procedurally pragmatic LLM (which is hyper-aware of ambiguities and programmed to resolve them by making assumptions and expanding scope). 

When the user communicates a correction to a configuration variable or active rule, the LLM often fails to realize that the old instruction must be completely deleted from the active specification. Instead, due to the ambiguity in `/nodelete`, the LLM either accumulates both conflicting instructions (polluting prompt context) or attempts to be "extra helpful" by rewriting unrelated adjacent sections based on assumptions.

## 2. Root Cause Analysis: "Speculative Resolution of Ambiguity"
- **The How**: When the user rejects a specific instruction (e.g., rejecting the "truck driver" lowest-barrier proxy), the LLM detects the contradiction but also notices surrounding ambiguities. Rather than performing a minimal, surgical deletion of the rejected parameter, the LLM makes assumptions to fill in the ambiguities and rewrites adjacent rules, causing drift.
- **The Why**: The `/nodelete` workflow [nodelete.md:L61-68](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L61-68) does not explicitly mandate that:
  1. Once a contradiction in configuration or active specification text is detected, the old, rejected parameter **must always be deleted** from the active surface.
  2. The deletion must be **strictly bounded** to the exact item corrected, with a hard ban on speculative expansion (no resolving unrelated ambiguities or rewriting adjacent sections).

## 3. Forensic Evidence
- **Active Contradiction Rules**: [nodelete.md:L61-68](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L61-68)
  *Evidence: Tells the agent to keep original info and add resolution notes, which directly causes active spec contamination for LLM prompts.*
- **Preservation vs. Over-Helpfulness**: [nodelete.md:L83-88](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L83-88)
  *Evidence: The workflow bans "cleaning up" but fails to define the boundary of user-directed corrections, causing the agent to over-speculate and execute unintended adjacent changes when trying to resolve user feedback.*

## 4. Remediation: Bounded Deletion & Ambiguity Quarantine Protocol
1. **Mandate Deletion of Rejected Parameters**: Update the workflow to dictate that when a user correction or specification change is received, the rejected parameter/configuration is **deleted** immediately from the active surface, rather than annotated or preserved inline.
2. **Enforce Surgical Bounding**: Instruct the LLM that when executing a user correction, it must *only* modify the target parameter. It is strictly forbidden from "fixing" unrelated ambiguities or rewriting surrounding text to be helpful.
3. **The Ambiguity Halt**: If a user correction exposes surrounding ambiguity, the agent must NOT make assumptions to resolve it. It must either perform the minimal surgical edit or ask for clarification, rather than speculating.

## 5. Recommendation to Senior Architect
Update `/nodelete` to include a structural definition for **Tier-2 (Active Prompts/Config)** vs **Tier-1 (Decisional History)**. Mandate that Tier-2 files must enforce clean, immediate deletion of contradictory parameters upon user correction, with a strict ban on speculative adjacent rewrites.

---
**Status**: **REMEDIATED**
**Verification**: COMPLETE — Hardened 2026-06-12 via `/harden-workflow --tickets`. See the /nodelete Hardening Certificate (Standard Version 3). The **Active Surface Correction Protocol** (Tier-1 Decisional History vs Tier-2 Active Surface), surgical bounding, and the **Ambiguity Halt** were injected; the Speculative Resolution of Ambiguity failure is now named and forbidden. Structural grade corrected from declared-Sovereign / actual-Structured to genuine Sovereign (GLOSSARY, STRICT RULES, INTEGRATION, HOW TO BEGIN added). Linter: CLEAN (0 CRITICAL / 0 WARNING). **Interpretation note:** "delete from active surface" was implemented as *relocate-to-Archive* (never destroy) to preserve the /nodelete doctrine — flagged to the user for confirmation.

---
*Signed,*
**Antigravity**
*Sovereign Ghostwriter & Architect*
