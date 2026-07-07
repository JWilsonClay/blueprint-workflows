# Helpdesk Ticket: Unbuilt Item Alarm Fatigue (The Pending vs. Unverifiable Gap)

**To**: Senior Architect of Workflows
**From**: Antigravity / Hebrews 6 Reader Session
**Date**: 2026-06-30
**Subject**: /focus-plan currently halts and throws alarms for unbuilt future items, conflating "pending work" with "unverifiable risk".
**Urgency**: CRITICAL (Architectural)

---

## 1. Executive Summary
The `/focus-plan` workflow is designed as a pre-build planning gate, prioritizing the "Negative Space Scan" to catch forgotten details before execution. However, the workflow's Sovereign Gate logic classifies legitimately unbuilt, forward-looking plan items as `UNVERIFIABLE` (a YELLOW risk that halts the pipeline). In a new project, this creates a massive volume of false alarms, burying the actual Negative Space findings under a panic response to missing substrate files that shouldn't exist yet.

## 2. Root Cause Analysis: "Structural Gap (Psychological Flaw)"
- **The How**: When the agent (or the focus.py engine) detects that an anchor is `ABSENT`, the agent follows the workflow rules to classify it as `UNVERIFIABLE`, which is defined as a failure/halt condition. The agent then expends massive cognitive effort trying to justify why it cannot pass the gate, causing friction and context erosion.
- **The Why**: The workflow did not differentiate between "Phase 1 is complete but missing a file" (Ghost Logic) and "Phase 5 hasn't started yet" (Pending). It lumps forward-looking implementation plans into the `UNVERIFIABLE` bucket alongside LOW-confidence intent, forcing a HALT condition where a GREEN (Pending) condition is appropriate.

## 3. Forensic Evidence
- **[Gate Definition]**: [focus-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L47)
  *Evidence: Defines UNVERIFIABLE as a HALT state and explicitly includes "feature not yet implemented" in this definition.*
- **[Adjudication Logic]**: [focus-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L118)
  *Evidence: Instructs the agent that "not-yet-built" items result in "UNVERIFIABLE (defer)" instead of a neutral/pending state.*
- **[Sovereign Gate HALT Rule]**: [focus-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L142)
  *Evidence: Explicitly instructs the agent to HALT the gate for any "not-yet-built item that blocks the plan", treating unbuilt future features as pipeline blockers rather than expected future tasks.*

## 4. Remediation: [Re-Classifying "Pending" as a Green State]
1. Update `/focus-plan` to introduce a new gate state: `PENDING`.
2. Define `PENDING` as: "The item is documented in the plan, but belongs to the active or a future execution phase. It is unbuilt, but expectedly so. This is a GREEN condition. Do not halt."
3. Reserve `UNVERIFIABLE` strictly for LOW-confidence Intent, and reserve `MISMATCH (Ghost Logic)` strictly for items that belong to *past, completed* phases but are absent from the substrate.

## 5. Recommendation to Senior Architect
Restructure Phase 4 (The Sovereign Gate) in `/focus-plan` to decouple "Not-Yet-Built" from the `UNVERIFIABLE` risk category. By introducing a GREEN `PENDING` state, the workflow will stop punishing the pipeline for having a forward-looking plan, and will free up the agent's cognitive bandwidth to focus entirely on the Negative Space Scan instead of apologizing for missing code.

---
**Status**: **REMEDIATED (Sovereign Gate gains a fourth outcome, the `PENDING` state this ticket named — GREEN, does not halt — for absent anchors whose phase is not yet complete; `UNVERIFIABLE` narrowed to LOW-confidence Intent/Plan only; `MISMATCH` for absences now strictly requires a complete phase, i.e. real Ghost Logic)**
**Verification**: Built `scripts/focus/phase_status.py` (new engine module, 18 unit tests in `scripts/tests/test_phase_status.py`) parsing `tasks.md` phase checkboxes + cross-referencing `.workflow_state/receipts/BUILD_RECEIPTS.md`, surfaced as Evidence Report field `tasks_md` (schema 1.0→1.1). `claude-commands/focus-plan.md` v3→v4: GLOSSARY (PENDING + Phase Status Report added, MISMATCH/UNVERIFIABLE/Sovereign Gate narrowed), PHASE 2 adjudication rewritten to consult `tasks_md` before defaulting to UNVERIFIABLE, PHASE 4 gains the PENDING outcome and explicitly reverses its own prior "not-yet-built → YELLOW" guidance, Final Review + STRICT RULES (18, was 17) + Manual Fallback Mode updated to match. Full suite 169/169 green (151 pre-existing + 18 new). Live end-to-end run against a synthetic workspace confirmed the exact discrimination this ticket asked for: a claimed-done-but-missing anchor (phase `complete` + matching receipt) → MISMATCH-eligible; a genuinely future anchor (phase `not_started`) → PENDING — from the same raw `absent_anchors` signal that previously couldn't tell them apart. `lint_workflows.py` CLEAN, hash recomputed. See `claude-commands/focus-plan.md` Change Log entry 5 and `manifest/WORKFLOW_MANIFEST.md` for the full record.

---
*Signed,*
**Antigravity**
*(Sovereign Helpdesk Analyst)*
