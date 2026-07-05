# Helpdesk Ticket: Structured Outputs (PM Oversight Report) Must Be Written to Disk by Default

**To**: Senior Architect of Workflows
**From**: /implementation-plan --audit --workstreams
**Date**: 2026-05-24
**Subject**: PM Oversight Report and similar structured outputs are emitted to terminal only; user cannot copy from opencode agent output
**Urgency**: MEDIUM

---

## 1. Executive Summary
The multi-agent workflow produces a critical deliverable (PM Oversight Report) as terminal text. The user cannot reliably copy this output from the opencode interface. All final artifacts that the user must carry to another agent (Grok Web) must be written to a persistent file by default.

## 2. Root Cause Analysis: "Terminal-Only Structured Output"
- **The How**: Phase 7e of implementation-plan.md produces the full PM Oversight Report as a markdown block printed to the user. No automatic Write tool call is made to persist it.
- **The Why**: The original protocol assumed the user could copy terminal output. This assumption breaks in opencode / Claude Code where the agent output is not easily selectable for large structured reports.

## 3. Forensic Evidence
- **[implementation-plan.md:7e]**: "Produce PM Oversight Report" — no instruction to write to disk.
- User statement (2026-05-24): "I cannot copy your output in opencode, which is why I need outputs to files."

## 4. Remediation: Automatic File Persistence
1. In Phase 7e, always use the Write tool to create `PM_OVERSIGHT_REPORT_IterationN.md` in `.workflow_state/`.
2. Update the report template to include the exact file path at the top so the user knows where to find it.
3. Apply the same rule to Engineer Handoff Blocks and any other paste-ready output.

## 5. Recommendation to Senior Architect
Make file persistence the default for every structured output that the user must relay between agents. Terminal display remains for immediate visibility, but the canonical artifact must always exist on disk.

## 6. Senior Architect Investigation Addendum (2026-05-24)

**[INJECTED by Senior Architect — /investigate findings, /nodelete]**

PM's original ticket is confirmed. Additionally, a critical architectural flaw in the adversarial scoring system was identified:

**Gap A — PM Oversight Report File Output (PM's original finding):**
Confirmed. Phase 7e must write to `.workflow_state/PM_OVERSIGHT_REPORT_Iteration[N].md` by default.

**Gap B — Adversarial Scoring Calibration Causes Score Gaming (NEW — HIGH):**
Phase 7d of `/implementation-plan --audit --workstreams` includes calibration guidance visible to the scoring agent: "good work scores 55-65, above 75 means the audit was too lenient." This tells the LLM what score to produce rather than letting evidence drive the assessment.

Evidence from Iteration 1: All three workstream quality scores landed between 58-64. Integration score: 64. Every score fell neatly within the "expected" band. Meanwhile the audit missed:
- SecretsLoader.ts at 221 lines (76% over 125-line limit)
- InputSanitizer.ts at 157 lines, RateLimiter.ts at 144 lines, logs.ts at 139 lines
- 27 uncommitted files across all workstreams
- Empty DECISIONS.md despite referenced escalation
- Contradictory status data in WORKSTREAM_STATUS.md

The calibration guide caused exactly the failure it was designed to prevent. Scores looked right. Real problems went undetected. This is Hallucinated Success mediated by calibration gaming.

**Remediation:** Remove ALL scoring calibration from Phase 7d (the agent-facing instructions). The scoring agent should never know what score range is "expected." Move the calibration guidance to a separate Architect-only section in the `grok_web_architect.log` or a new `AUDIT_CALIBRATION_GUIDE.md` that only the Architect (Grok Web) reads when reviewing the PM's audit. The Architect evaluates whether the PM's scores are calibrated correctly — that's oversight of the auditor, not self-grading by the auditor.

**Urgency upgrade: MEDIUM → HIGH** (adversarial scoring system is compromised)

---
**Status**: **REMEDIATED (both gaps closed — Gap A: PM Oversight Report and similar structured outputs now persisted to disk by default; Gap B: all scoring calibration removed from Phase 7d, replaced with evidence-cited, non-trust-based scoring)**
**Verification**: **[BACKFILLED 2026-07-05]** This ticket was archived (`CLOSED_` prefix) without its Status/Verification fields ever being updated — a paperwork gap, not a live one, discovered while investigating `helpdesk-tickets/CLOSED_20260704_hallucinated-success-recurrence_workflow.md`. Confirmed against current substrate: `claude-commands/implementation-plan.md` STRICT RULE 17 explicitly states "*[Replaces original calibration guidance — see Change Log entry 9.]*" and reads "Every quality score in Phase 7d MUST cite evidence (file paths, line counts, specific observations)... do not trust self-reports" — the exact fix Gap B asked for. Gap A (file persistence) was folded into the later Coverage Ledger rework (Change Log entry 10) rather than tracked separately. No further action needed on this ticket; recorded here so its own record matches reality.

---
*Signed,*
/implementation-plan --audit --workstreams (original), Senior Architect (addendum)
