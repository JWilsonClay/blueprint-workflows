# Helpdesk Ticket: `remediation_ledger.py` Cannot Distinguish "No Findings" From "Found A Findings Section But Could Not Read Any Items" — And Reports The Latter As The Former

**To**: Senior Architect of Workflows
**From**: Claude Code session (`research/proforma` workspace, Phase 67 / Fix 258)
**Date**: 2026-07-30
**Subject**: `scripts/plan/findings.py:_parse_items` returns an empty item list for a Findings section written in the `**CRIT-NN — claim**` declared-paragraph shape, and `remediation_ledger.py` reports that as `status: ok`, `exit 0`, `total: 0` — indistinguishable from a genuine zero-findings audit
**Urgency**: HIGH
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

`remediation_ledger.py` returned `status: ok`, **exit 0**, `total: 0`, `total_deduction: null` against an audit report carrying **1 Critical and 3 Medium** findings. Both Findings sections were located (`sections: {critical: true, medium: true}`); only the *items inside them* failed to parse.

The severity is not the parse failure. It is what `/implementation-plan` Phase 8b instructs a session to do with that output: a `total` of 0 with `status: ok` *"is a genuine zero-findings audit; report that plainly and stop."* **A session following the documented protocol would have reported "nothing to remediate" against a Critical finding and stopped.** That is the exact Hallucinated Success shape STRICT RULE 29 exists to prevent, arriving wearing the engine's own green output.

Compounding it: the unparseable shape is a **declared `CRIT-NN` ID paragraph** — the very ID convention STRICT RULE 31 and the Finding ID glossary mandate.

It was caught only because the reading session refused to believe a zero against a report it had just read, and treated it as a parse failure per STRICT RULE 29. That is a human-judgment catch, not a mechanical one, and it is not repeatable at scale.

## 2. Root Cause Analysis: "Section Located, Items Unread, Reported As Success"

- **The How**: `~/blueprint-workflows/scripts/plan/findings.py:_parse_items` selects among four item conventions — sub-heading, `- ` list item, `**C1 —` labelled, or none. A **declared `**CRIT-NN — claim**` paragraph matches none of them.** `_DECLARED_ID` does extract the ID, but it is never treated as an item boundary, so it cannot rescue the parse.
- **The Why**: the failure state has no distinct exit code. Exit `2` (`no_findings_section`) fires only when the *section heading* is missing. Here the headings were found and the items were not, and nothing in the return shape distinguishes "this audit found nothing" from "I found the section and could not read a single thing in it." The gap is between *section located* and *items parsed*, and it is unreported.

## 3. Forensic Evidence

Both runs below are against the **same report content** — identical findings, identical IDs, identical deductions. Only the item shape differs. The report is `~/blueprint-workflows/implementation-plan/audits/20260730-1620-proforma-phase66.md`; the failing shape was reconstructed on a **copy** by reverting only the item formatting, so the persisted report was not modified to produce this evidence.

**FAILING — the declared-paragraph shape (`**CRIT-01 — claim** — citations`):**

```json
{
  "audit_name": "u12_paragraph_form.md",
  "status": "ok",
  "id_source": "none",
  "sections": { "critical": true, "medium": true },
  "summary": { "critical": 0, "medium": 0, "total": 0, "total_deduction": null },
  "errors": []
}
```
Exit code: **0**. Findings parsed: **0**. `errors` is empty — nothing anywhere signals a problem.

**CORRECT — the canonical list shape (`- CRIT-01 — **claim** — citations`):**

```json
{
  "audit_name": "20260730-1620-proforma-phase66.md",
  "status": "ok",
  "id_source": "declared",
  "sections": { "critical": true, "medium": true },
  "summary": { "critical": 1, "medium": 3, "total": 4, "total_deduction": 20 },
  "errors": []
}
```
Exit code: **0**. Findings parsed: **4** — `CRIT-01`, `MED-01`, `MED-02`, `MED-03`. `total_deduction: 20` independently reproduces the report's own `100 − 20 = 80`.

Note that `status`, `sections` and `errors` are **identical across both runs**. The only distinguishing fields are `id_source` (`none` vs `declared`) and the summary counts — and a consumer that trusts `status: ok` never looks at either.

- **The selector**: [`_parse_items`](file:///home/jwils/blueprint-workflows/scripts/plan/findings.py)
  *Evidence: four conventions, none matching a declared-ID bold paragraph.*
- **The instruction that turns it into a false report**: `/implementation-plan` Phase 8b — a `total` of 0 with `status: ok` "is a genuine zero-findings audit; report that plainly and stop."

## 4. Remediation: A Distinct Status For "Section Found, Zero Items Parsed"

Not applied — this workflow does not fix failures. Recommendation, in preference order:

1. **Minimum, and the one this ticket argues for**: return a **distinct non-zero status** (e.g. `findings_section_unparsed`) whenever a Findings section is located but yields zero items. This is the structural fix: a parser that cannot distinguish "no findings" from "found nothing I could read" will keep producing this failure in some other shape, whatever item conventions are added. Fixing only the shape leaves the class open.
2. **Additionally**: treat `_DECLARED_ID` as a fourth item-boundary convention, so the `CRIT-NN` paragraph shape parses. This is worth doing on its own merits — STRICT RULE 31 mandates that ID convention, so the engine currently cannot read a shape the suite requires — but it is a *symptom* fix and should not substitute for (1).
3. **Consider**: have `remediation_ledger.py` cross-check its own `total: 0` against a cheap independent signal (e.g. a count of `CRIT-`/`MED-` ID occurrences anywhere in the file) and escalate on disagreement. Cheap, and it converts a silent zero into a loud one.

## 5. Cross-References

- Project-local record: `research/proforma/implementation-plan.md`, outstanding-work table row **`U12`** (the engine defect) and **`U11`** (the format correction applied to the affected report, content and IDs unchanged, recorded inside the report itself).
- Sibling tickets filed the same day by the same Fix: `20260730_defect-classes-recommendation-overmatch_workflow.md`, `20260730_phase-status-found-incomplete-conflation_workflow.md`, `20260730_continuous-verify-anchor-false-absent_workflow.md`.
- **Nothing under `~/blueprint-workflows/` was edited to file this ticket.** The reproduction was performed on a copy in a session scratchpad.
