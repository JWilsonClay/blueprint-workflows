# Helpdesk Ticket: `phase_status.py`'s `receipt_status: found_incomplete` Conflates "Malformed Or Never Certified" With "Built, Correctly Withholding Certification Pending An External Gate"

**To**: Senior Architect of Workflows
**From**: Claude Code session (`research/proforma` workspace, Phase 67 / Fix 258)
**Date**: 2026-07-30
**Subject**: One `receipt_status` value covers two situations with opposite meanings — a defective receipt, and a correct, spec-compliant refusal to self-certify — and nothing mechanical distinguishes them
**Urgency**: MEDIUM
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

`phase_status.py` reports `receipt_status: found_incomplete` when a phase's receipt exists but its `Grade/Status:` value is not a recognised completion value. That single value currently covers two situations that mean **opposite things**:

1. **A defect** — the receipt is malformed, or the phase was genuinely never certified.
2. **Correct behaviour** — the phase is genuinely built, and is deliberately withholding certification because an acceptance criterion is explicitly *not agent-certifiable* and its external gate has not yet been discharged.

A reader — human or agent — cannot tell which they are looking at without opening the receipt and reasoning about it. The value that should be a signal is instead an ambiguity, and it appears on the exact surface (`/implementation-plan --audit`'s Completion Marking, the SR-1 dual check) where a mechanical answer is the whole point.

**Three instances in one project**, which is why this is filed rather than absorbed again:

| Phase | Situation | Why `found_incomplete` is the wrong signal |
|---|---|---|
| **17** | `Grade/Status: HALTED (recalculation completed, residual reported as required)` | The halt was **correct and spec-compliant** — the project's own plan documents it as the intended outcome. `HALTED` is the accurate record. |
| **64** | Built, 7 of 9 criteria closed; the 2 open were a Microsoft Excel human confirmation no agent may discharge | The phase was the strongest in the project's audit history and was **right** to refuse self-certification. |
| **U4 itself** | Phases 21/22 report `status: complete` with `receipt_status: not_found` | Different value, same expressibility gap — the taxonomy has no way to say "built, receipt genuinely absent" versus "never built." |

## 2. Root Cause Analysis: "One Value For Two Meanings"

- **The How**: `receipt_status` is derived by matching the receipt's `Grade/Status:` field against a set of recognised completion values. Anything unrecognised collapses to `found_incomplete`, regardless of *why* it is unrecognised.
- **The Why**: the vocabulary has no term for a **deliberate, correct withholding**. The design implicitly assumes that a receipt which does not say "complete" is a receipt with a problem. But this suite actively *requires* non-completion in two documented situations — `/execute-build` Step 6a's `RECEIPT UNVERIFIED`, and any acceptance criterion marked not-agent-certifiable — so the assumption is contradicted by the suite's own protocols.
- **Consequence**: the honest remedy for Phase 17 may be *no code change at all* — `HALTED` is the truthful record, and forcing it into a completion value to satisfy a parser would be falsifying the record to please a tool. That is precisely why this needs a vocabulary decision from the Architect rather than a local patch.

## 3. Forensic Evidence

- **Instance 1 (Phase 17)**: two receipt entries exist; `Grade/Status:` reads `HALTED (recalculation completed, residual reported as required)` → `found_incomplete`. The project's own `implementation-plan.md` closing note records this halt as the correct outcome.
- **Instance 2 (Phase 64)**: `status: in_progress` / `receipt_status: found_incomplete` while the phase was independently audited at **91/100** with **0 Critical Weaknesses** and described as "strongest single-phase build in this project's audit history." The two open checkboxes were Fix 245 AC2 (a human `F9` confirmation in Microsoft Excel) and Fix 246 AC3 (recording it).
- **Instance 3 (U4)**: Phases 21 and 22 report `status: complete` (18/18 and 4/4) with `receipt_status: not_found` — `grep -c "^- Phase/Stage: Phase 21"` returns 0 in **both** `BUILD_RECEIPTS.md` copies.
- **Declined twice before filing**: Phase 64's build session raised it as **Q6**; Phase 65 declined it as suite-level; Phase 66 re-declined it. Each decline was correct — the fix lives in `~/blueprint-workflows/scripts/focus/phase_status.py`, outside any consuming workspace.

## 4. Remediation: Give The Withholding Case Its Own Term

Not applied — this workflow does not fix failures. Recommendation:

1. **Add a distinct status for a documented, deliberate withholding** — e.g. `found_withheld` — recognised from an explicit, greppable receipt value (`HALTED`, `RECEIPT UNVERIFIED`, `HUMAN VERIFICATION GATE OPEN`, or a dedicated field). This keeps `found_incomplete` meaning "something is wrong with this receipt," which is what consumers already assume it means.
2. **Keep `found_incomplete` strictly for malformed/unrecognised receipts**, so that its appearance is once again actionable.
3. **Do not** resolve this by widening the completion-value set to swallow `HALTED`. That would mark a halted phase complete — inverting the signal rather than disambiguating it, and destroying the very record Phase 17 was right to write.
4. **Separately consider** the `not_found` half (U4): a phase that is genuinely built with a genuinely missing receipt is a third state, and back-writing a synthesised receipt to satisfy the parser would be manufacturing evidence.

## 5. Cross-References

- Project-local records: `research/proforma/implementation-plan.md`, outstanding-work rows **`U6`** (this engine defect) and **`U4`** (the project-local symptom).
- Recommendation 6 of `20260730-1642-proforma-phase65.md`.
- Sibling tickets filed the same day by the same Fix: `20260730_remediation-ledger-unparseable-findings_workflow.md`, `20260730_defect-classes-recommendation-overmatch_workflow.md`, `20260730_continuous-verify-anchor-false-absent_workflow.md`.
- **Nothing under `~/blueprint-workflows/` was edited to file this ticket.**
