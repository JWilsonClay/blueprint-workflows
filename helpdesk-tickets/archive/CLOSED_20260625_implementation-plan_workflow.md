# Helpdesk Ticket: Arbitrary Cap and Count Constraints on Adversarial Audit Mode

**To**: Senior Architect of Workflows
**From**: Antigravity Gemini / helpdesk-tickets
**Date**: 2026-06-25
**Subject**: Inflexible issue counts in `/implementation-plan --audit` mode distort report fidelity and mask critical failures.
**Urgency**: CRITICAL (Architectural)

---

## 1. Executive Summary
The `/implementation-plan --audit` mode mandates listing "at least 4 specific, genuine weaknesses" and associates a heavy comparative score deduction (7-15 points) with each one. In practice, this hard count requirement forces the auditing model to artificially elevate minor/medium observations to "Critical Weaknesses" to meet the quota when fewer than 4 critical issues exist, or to prematurely halt and omit critical vulnerabilities once the 4-issue quota is reached. The audit should instead report all discovered critical vulnerabilities without artificial limits, while capping minor/medium/lesser issues to a maximum of 4 to prevent LLM context drift.

## 2. Root Cause Analysis: "Structural Gap"
- **The How**: The auditor model is constrained by strict templates demanding a minimum of 4 "Critical Weaknesses" with associated score deductions. During evaluations of small or high-quality phases, the model must either invent minor issues and treat them as critical, or split a single issue into multiple redundant parts. Conversely, during evaluations of large-scale refactorings, the model stops cataloging issues after reaching the target number, leaving other files and modules completely unaudited.
- **The Why**: The faulting workflow `/implementation-plan.md` does not distinguish between severity classes of findings (Critical vs. Medium/Lesser). In [implementation-plan.md L188](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L188) and [L213](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L213), the workflow hardcodes a minimum requirement of "at least 4 specific, genuine weaknesses" and applies a flat deduction penalty of 7-15 points to every reported item, regardless of its actual severity or real-world impact.

## 3. Forensic Evidence
- **Audit Count Constraint**: [implementation-plan.md#L188](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L188)
  *Evidence: Instructions mandate that the Auditor "must find and clearly articulate at least 4 specific, genuine weaknesses".*
- **Audit Section Format**: [implementation-plan.md#L213-L214](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L213-L214)
  *Evidence: The output template enforces "Critical Weaknesses (Minimum 4 Required; each weakness MUST reduce comparitive score between 7-15 points for each weakness)".*

## 4. Remediation: Reclassify Finding Severities and Remove Arbitrary Limits
The `/implementation-plan --audit` mode needs to be updated to restructure how findings are categorized, counted, and scored:
1. **Differentiate Severity Levels**: Split findings into "Critical Weaknesses" (severe architectural failures, regressions, or bypasses) and "Medium/Lesser Weaknesses" (minor design, naming, style, or documentation issues).
2. **Dynamic Severity-Based Quotas**:
   - Surface **every** critical weakness found across the entire changeset, with no minimum or maximum cap (bounded only by logical context limits before drift sets in).
   - If no critical weaknesses are present, the auditor is allowed to report 0 critical weaknesses.
   - Limit "Medium/Lesser Weaknesses" to a maximum cap of 4 to keep the audit concise and prevent focus drift.
3. **Calibrate Deductions**: Apply a larger comparative score deduction to Critical Weaknesses (e.g., 10-20 points) and a much smaller deduction to Medium/Lesser Weaknesses (e.g., 2-5 points) to ensure the final score realistically reflects the implementation's quality.

## 5. Recommendation to Senior Architect
Update the audit phase rules in `/implementation-plan` to replace the rigid "Minimum 4 Critical Weaknesses" constraint with a tiered severity system. The auditor should be instructed to exhaustively audit all modified files for critical vulnerabilities, while capping the reporting of lesser concerns to at most 4 items. The scoring framework must reflect these severities proportionally.

---
**Status**: **REMEDIATED (Coverage Ledger model replaces the fixed minimum-count quota — mechanical changeset enumeration + mandatory per-file verdict, in place of "find at least N weaknesses"; Critical Weaknesses uncapped 10-20pts, Medium/Lesser capped at 4 for 2-10pts, applied identically to both the standalone `--audit` and `--audit --workstreams` paths)**
**Verification**: This ticket's own Section 4 proposal (pure removal of the minimum, severity tiering) was refined after discussion with the user: naive removal would have reopened the exact rubber-stamp risk the original "minimum 4" was — imperfectly — protecting against. The user supplied context this ticket didn't have: the quota was a deliberate two-fold forcing function (judge plan quality AND judge audit rigor from a guaranteed non-empty sample), not an arbitrary number, and had already been identified as "prone to gaming" and removed once before (2026-05-13, Change Log entry 3) before silently reappearing by 2026-05-25 (STRICT RULE 23). Final design: mechanical coverage enumeration (`git diff --stat`) + mandatory per-file verdict replaces the count as the anti-rubber-stamp mechanism, without capping how many real Critical Weaknesses can be reported (0 to however many are genuine). Halt-on-incomplete-coverage replaces halt-on-self-assessed-effort, since an LLM cannot reliably self-detect its own under-effort as a gate condition. `claude-commands/implementation-plan.md` v3→v4: GLOSSARY (Coverage Ledger added), Phase 5 + Phase 6/7d + PM Oversight Report template all rewritten consistently (previously inconsistent at "min 4" vs "min 2" with no stated rationale), STRICT RULE 23 updated in place with superseding note, STRICT RULES 24-25 added (23→25), frontmatter version 3→4. This also resolves a standing internal contradiction: STRICT RULE 9 already said "do not use fixed numeric targets" — the Phase 5/6 templates had been violating that rule since before this ticket was filed. `lint_workflows.py --file implementation-plan.md` → 0 CRITICAL, 0 WARNING, hash genuinely recomputed. No engine exists for this workflow (plan/audit generation is confirmed-irreducible judgment per the root `implementation-plan.md` campaign doc's own engine-scoring table), so verification here is structural/textual, not test-suite-backed the way the `/focus-plan` ticket's fix was. See Change Log entry 10 for the full record.

---
*Signed,*
**Antigravity Gemini** (ticket) / **Claude, Sonnet 5** (remediation)
*(Sovereign Helpdesk Analyst / Senior Architect of Workflows)*
