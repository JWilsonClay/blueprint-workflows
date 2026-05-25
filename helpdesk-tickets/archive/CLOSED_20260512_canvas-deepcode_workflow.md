# Helpdesk Ticket: Isolation Gap — /canvas and /deepcode Are Disconnected Islands

**To**: Senior Architect of Workflows
**From**: Sovereign Depreciate + Investigate Joint Audit Agent
**Date**: 2026-05-12
**Subject**: /canvas and /deepcode have zero integration with the Sovereign Suite — not referenced by /triage, /secretary, or any other workflow, making them invisible to autonomous routing and governance.
**Urgency**: LOW

---

## 1. Executive Summary

Two workflows — `/canvas` and `/deepcode` — are functional as standalone tools but have zero integration with the rest of the suite. Neither appears in any other workflow's INTEGRATION section or triage trigger list. Both remain monolithic and at Legacy/Structured grade. As the suite's governance layer matures, these workflows become progressively harder to discover and maintain. They are not broken — they simply exist outside the ecosystem, invisible to any automated audit, routing, or coverage mechanism.

## 2. Root Cause Analysis: "Suite Orphan Pattern"

**Failure class**: Structural Gap / Integration Absence

- **The How**: `/canvas` and `/deepcode` were created as standalone utilities without integration wiring. When the rest of the suite grew INTEGRATION sections and triage trigger mappings, these two were not retrofitted.
- **The Why**: Both serve specialized, on-demand functions that were not considered part of the core Sovereign pipeline. As the suite expanded into a self-referential governance layer, the omission became increasingly structural — they cannot be discovered by `/triage`, cannot be graded correctly by WORKFLOW_MANIFEST.md without manual inspection, and cannot be measured by `/receipt-check`.

## 3. Forensic Evidence

- **[canvas.md — full file, zero INTEGRATION references, no Change Log]**: [canvas.md:L1-L52](file:///home/jwils/.gemini/antigravity/global_workflows/canvas.md#L1-L52)
  *Evidence: The complete 52-line file contains no GLOSSARY, no INTEGRATION WITH OTHER WORKFLOWS section, no HOW TO BEGIN, no STRICT RULES, no Change Log. It is a pure prompt injection, fully isolated from the suite.*

- **[deepcode.md — full file, zero INTEGRATION references, no Change Log]**: [deepcode.md:L1-L70](file:///home/jwils/.gemini/antigravity/global_workflows/deepcode.md#L1-L70)
  *Evidence: The complete 70-line file similarly contains no structural elements connecting it to the suite. No triage triggers, no INTEGRATION section.*

- **[triage/core.md — no routing entries for /canvas or /deepcode]**: [triage/core.md](file:///home/jwils/.gemini/antigravity/global_workflows/triage/core.md)
  *Evidence: Full read of the triage payload confirms neither /canvas nor /deepcode appear in any trigger condition, routing table, or recommendation path.*

## 4. Remediation: Wire /canvas and /deepcode Into the Suite

1. Add triage triggers to `/triage/core.md`: "Generate an Obsidian Canvas visualization" → `/canvas`; "Perform a deep code review of all workspace scripts" → `/deepcode`.
2. Apply `/harden-workflow` to both: YAML frontmatter, GLOSSARY, INTEGRATION WITH OTHER WORKFLOWS, HOW TO BEGIN, STRICT RULES, Change Log.
3. Evaluate both for Pointer/Payload migration after hardening increases their byte count.
4. Update WORKFLOW_MANIFEST.md with accurate pre-hardening grades.

## 5. Recommendation to Senior Architect

Any workflow added to `global_workflows/` should be required to include a triage trigger entry and an INTEGRATION section before being considered suite-integrated. Add to `/harden-workflow` Phase 0: "Check whether the target workflow is referenced in /triage. If not, adding a triage trigger is a required hardening output."

---
**Status**: **OPEN**
**Verification**: Resolved when (a) `/triage/core.md` contains trigger entries for both `/canvas` and `/deepcode`, (b) both have INTEGRATION sections at minimum, and (c) WORKFLOW_MANIFEST.md reflects accurate grades.

---
*Signed,*
**Sovereign Depreciate + Investigate Joint Audit Agent**
*(Forensic Audit — global_workflows substrate, 2026-05-12)*

---
**Status**: **REMEDIATED**
**Closed**: 2026-05-15
**Changes**:
- `triage/core.md`: /canvas Trigger Matrix block added (was completely absent). /deepcode block updated with intent-driven trigger row.
- `canvas.md`: INTEGRATION section + Change Log appended.
- `deepcode.md`: INTEGRATION section + Change Log appended. Includes full downstream routing table (/harden, /soc, /refactor, /canvas, /secretary).
- Both workflows are now suite-discoverable via /triage.
- Full /harden-workflow structural pass deferred (both files below P/P migration threshold).
