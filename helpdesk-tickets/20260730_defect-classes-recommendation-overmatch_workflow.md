# Helpdesk Ticket: `defect_classes.py` Over-Matches Bulleted Lines Inside An Audit's "Recommendations" Section, Inflating The Finding Count

**To**: Senior Architect of Workflows
**From**: Claude Code session (`research/proforma` workspace, Phase 67 / Fix 258)
**Date**: 2026-07-30
**Subject**: `defect_classes.py` enumerated 9 findings (`MED-01`…`MED-09`) against a report carrying 3, the six extras being bullet lines from the "Recommendations for Future Plans" section — a section that is advisory, not a findings ledger
**Urgency**: MEDIUM
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

Running the Defect-Class Preflight against `20260730-1310-proforma-phase64.md`, the two enumeration engines disagreed:

| Engine | Findings enumerated |
|---|---|
| `remediation_ledger.py` | **3** (the report's actual count) |
| `defect_classes.py` | **9** (`MED-01`…`MED-09`) |

The six extras are bullet lines inside **"Recommendations for Future Plans"**. Recommendations are explicitly *not* findings — they carry no severity, no deduction, and no 1:1 remediation obligation. Treating them as Medium findings inflates the ledger a remediating phase must account for, and invites a phase to either pad its Fix list with un-scored items or appear to have silently dropped findings it never had.

**No acceptance criterion has yet been affected**, because `/implementation-plan` Phase 8b names `remediation_ledger.py` as the authority and the discrepancy was caught by comparing the two. That is the mitigation working; it is not a reason the defect is harmless.

## 2. Root Cause Analysis: "Section-Blind Bullet Matching"

- **The How**: `defect_classes.py` matches finding-shaped bullet lines without constraining the match to the Findings sections (`## Critical Weaknesses`, `## Medium/Lesser Weaknesses`). Any `- ` line elsewhere in the report that resembles a finding is enumerated as one.
- **The Why**: the report's own section structure carries the semantics — "this list is findings, that list is advice" — and the matcher does not consult it. It is a whole-document regex sweep where a section-scoped one is required.
- **Confirmation that it is a real engine defect and not a one-report artifact**: against `20260730-1642-proforma-phase65.md` the over-match **did not fire** — solely because that report's Recommendations are written as a *numbered* list rather than a bulleted one. Against `20260730-1620-proforma-phase66.md` it again did not fire, for the same reason. **The engine defect is real and merely did not have bullets to match.** Whether the Preflight is correct is currently a function of an audit author's incidental choice of list marker.

## 3. Forensic Evidence

- **The disagreement, measured**: `20260730-1310-proforma-phase64.md` — `remediation_ledger.py` → 3 findings; `defect_classes.py` → 9 (`MED-01`…`MED-09`), six of which resolve to Recommendation bullets.
  *Recorded in `research/proforma/tasks.md`, Phase 65 Findings Ledger tooling note.*
- **Localisation to the Recommendations section**: performed by the Phase 66 session's engine-agreement note; the six extras map one-to-one onto that section's bullets.
- **Non-recurrence explained rather than assumed**: Phase 66's and Phase 67's engine-agreement notes both record `defect_classes.py` matching the correct count against reports whose Recommendations are numbered. The variable is the list marker, not the engine.
- **Not masked by a missing registry**: in this workspace `project_classes_loaded: 0` (no `PROCESS_LEARNINGS.md`), so the Preflight runs against the suite-global registry only. The over-match is in enumeration, upstream of class matching, and is unaffected by that.

## 4. Remediation: Scope Enumeration To The Findings Sections

Not applied — this workflow does not fix failures. Recommendation:

1. **Constrain enumeration to the Findings sections.** Parse `## Critical Weaknesses` and `## Medium/Lesser Weaknesses` (and their recognised variants), and enumerate only within them. This matches what `remediation_ledger.py` already does and would make the two engines agree by construction rather than by coincidence.
2. **Alternatively/additionally, explicitly exclude advisory sections** (`## Recommendations for Future Plans`, `## Honest Assessment`, `## Strengths`) from enumeration. Weaker — an allowlist of findings sections is safer than a denylist of everything else, since a future section name would default to being counted.
3. **Consider a cheap agreement assertion**: where both engines run, disagreement on count could be surfaced rather than left for a session to notice. Three consecutive project phases have now had to hand-compare them.

## 5. Cross-References

- Project-local record: `research/proforma/implementation-plan.md`, outstanding-work table row **`U5`** — declined for that workspace deliberately and correctly, since the fix lives in `~/blueprint-workflows/scripts/plan/defect_classes.py` and affects every consuming project.
- Recommendation 6 of `20260730-1642-proforma-phase65.md` raises the same item.
- Sibling tickets filed the same day by the same Fix: `20260730_remediation-ledger-unparseable-findings_workflow.md`, `20260730_phase-status-found-incomplete-conflation_workflow.md`, `20260730_continuous-verify-anchor-false-absent_workflow.md`.
- **Nothing under `~/blueprint-workflows/` was edited to file this ticket.**
