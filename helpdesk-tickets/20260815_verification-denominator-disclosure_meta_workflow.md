# Helpdesk Ticket: Vacuous Pass — Verification Engines Report Success Without Disclosing What They Examined

**To**: Senior Architect of Workflows
**From**: Claude Code session (`lsshreveport` / `research/proforma` workspace, Phase 73)
**Date**: 2026-08-15
**Subject**: A suite-wide class in which a scanning engine's *effective* input set silently differs from its *intended* one, and the output is indistinguishable from a genuine clean result — plus a proposed, cheap, uniform counter-measure and the enforcement pattern built and proven against it today
**Urgency**: CRITICAL (Architectural)
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING
**Ticket Shape**: META — governs the sibling tickets named in §6. Filed as a solution proposal, at user direction, not as an incident report.

---

## 1. Executive Summary

Three suite engines have now been found reporting a clean or empty result that was produced by **examining fewer inputs than intended — sometimes none at all** — with nothing in the output disclosing it. Today's instance is the most complete: `citation_lint.py --dir` had, since the day it was written, scanned **zero files** in this workspace and printed `PASS: All checked files satisfy Citation & Heading Governance Policy.` Its exclusion filter tested every component of the *absolute* path for a leading dot, and this workspace lives under `/home/jwils/.prebuild.temp/` — so every file in it matched the exclusion, forever.

This is not the Mock Trap (which tests the wrong thing) and not Hallucinated Success (which claims work never performed). Here the code is correct, it runs, and it honestly reports what it found — across an input set that was silently emptied. **A gate that examined nothing and a gate that found nothing print the same string.** I propose naming this class **Vacuous Pass** and giving the suite one uniform, cheap counter-measure: **Denominator Disclosure** — every scanning engine reports what it examined and what it excluded, and a zero-denominator result is never a PASS.

## 2. Root Cause Analysis: "Vacuous Pass"

**Proposed vocabulary entry** (for `role.md` / global failure-pattern table, alongside Mock Trap, Ghost Logic, Hallucinated Success, Sound Effect Execution):

> **Vacuous Pass** — A verification mechanism reports success because its effective input set was empty or silently truncated, not because the property it checks holds. The code is correct and the report is honest; the *denominator* is wrong and undisclosed. Distinguished from **Mock Trap** (the check reaches a substitute for the real substrate) and **Hallucinated Success** (the work was never done). Signature: a green result whose input count nobody printed.

- **The How**: an engine applies a generic path-exclusion convention — dot-prefixed directories, a directory literally named `build`, a `_MAX_FILES` ceiling — that is correct in the average repository and wrong for the actual target. The excluded set is never counted, never printed, and never compared against expectation. The result is then consumed by a workflow that treats absence of findings as satisfaction of the criterion.
- **The Why**: **no workflow in the suite requires a verification engine to report its denominator.** Every engine reports findings; none is obliged to report *coverage of its own scan*. `/implementation-plan`'s Coverage Ledger (STRICT RULE 24) established exactly this discipline for **audits** — "a file present in the enumeration but absent from the verdict list is an incomplete audit, not a passing one" — and it was never propagated to the **engines**. The principle already exists in the suite; it simply stops at the audit layer and was never pushed down into the scripts the audit layer depends on.

## 3. Forensic Evidence

- **Total emptying, undisclosed — today's instance**: [pre-fix filter tested every part of the absolute path](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/.workflow_state/phase73/citation_lint.py.PRE_FIX296#L88-L95)
  *Evidence: `if not any(part.startswith('.') ... for part in p.parts)` — evaluated over the ABSOLUTE path. Any workspace beneath a dot-directory (this one: `.prebuild.temp`) matches on every file. Directory mode scanned 0 files and exited 0 with `PASS`. Preserved backup of the file as it stood before Phase 73.*
- **The corrected form, with the disclosure it lacked**: [relative-parts filter plus an explicit empty-set warning](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/scripts/build/citation_lint.py#L272-L296)
  *Evidence: the fix tests only parts BELOW the scan root, and — the part that matters for this ticket — prints `WARNING: no markdown files found under {root} — check --dir` when the target set is empty. Measured effect of the fix alone: 0 files scanned -> 50 files, 1,100 findings that had always been there.*
- **Silent truncation, same family, different mechanism — live in the suite now**: [`_count_matches` returns a partial total at a hard ceiling](file:///home/jwils/blueprint-workflows/scripts/investigate/search_log_verifier.py#L63-L77)
  *Evidence: `if scanned >= _MAX_FILES: return total` returns a count indistinguishable from a complete scan; `_MAX_FILES = 5000`. Nothing in the return value or the caller's report says the walk stopped early. This is the engine that verifies `/investigate`'s own Search Log claims — including this session's.*
- **Name-based pruning of a real source tree — already filed twice, independently**: [`_IGNORE_DIRS` / dot-prune convention](file:///home/jwils/blueprint-workflows/scripts/investigate/search_log_verifier.py#L32-L33)
  *Evidence: the same convention family that `20260729_focus-plan_workflow.md` and `20260730_continuous-verify-anchor-false-absent_workflow.md` each independently diagnosed, where a directory named `build` holding hand-authored production source is pruned, yielding false `ABSENT` verdicts and false Mock-Trap candidates. Three engines, three tickets, one class.*
- **The second half of the class — advertised checks that do not exist**: [docstring claimed four checks; two had no implementation](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/.workflow_state/phase73/citation_lint.py.PRE_FIX296#L1-L20)
  *Evidence: check 2 (cross-document anchor collisions) computed a set and discarded it at the call site; check 4 (broken anchor links) had no code at all. A document citing two nonexistent anchors passed clean. This is why a proposed upgrade could cite three anchors that had never been written and be reviewed as compliant — the enforcement layer could not contradict it.*
- **The engine conflict this workspace hit, needing a suite-side fix**: [`_strip_header_annotations` and `_normalize`](file:///home/jwils/blueprint-workflows/scripts/focus/phase_status.py#L122-L160)
  *Evidence: neither strips a trailing `{#id}`, so a heading anchor is folded into the receipt match key. Measured with two otherwise-identical phases carrying matching receipts: unanchored -> `found_complete`; anchored -> `not_found`. This puts a workspace citation policy requiring anchors on every heading in direct conflict with `/implementation-plan` STRICT RULE 28 for every phase header in a project.*

## 4. Remediation: What Was Built And Proven Today

Built and verified in `lsshreveport` Phase 73 (Fixes 294-299). These are offered as the **reference implementations** of the pattern, not as project-local fixes:

1. **Denominator + exemption disclosure on every run.** The linter now prints its exemption count unconditionally, worded so it cannot be read as coverage: [`Not counted as violations, and NOT evidence of coverage`](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/scripts/build/citation_lint.py#L325-L340). Empty-input now warns rather than passing silently.
2. **Refuse-by-construction, with no override flag.** The anchoring tool physically cannot produce the change that would break the receipt trail, and the reason is stated at the top of the file: [`THE LOAD-BEARING RULE`](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/scripts/build/anchor_headings.py#L1-L35). A flag would have been used exactly once, at 2am, by someone clearing a red gate.
3. **Verified citation emission — a generator that refuses to assert what it cannot prove.** The manifest generator resolves each anchor before emitting a link, and downgrades to a plain path with a stated reason when it cannot: [`_cite`](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/search_copy.py#L93-L128). This is the direct structural answer to the incident that started the phase.
4. **A gate scoped to a declared set, with every exclusion tied to a numbered routing row**: [`citation_gate.sh`](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/scripts/build/citation_gate.sh#L1-L37). Exclusions are not conveniences; each names its `U`-table row.
5. **Three-direction gate testing applied to a linter**, per that workspace's `SR-12`: reject the bad artifact, pass the good one, and — the direction nobody runs — catch a defect the check does not enumerate. Direction 3 is what proved the link checker resolved *across* files rather than only within one; a same-file-only implementation passes directions 1 and 2 and fails silently in production.

## 5. Recommendation to Senior Architect

**Adopt Denominator Disclosure as a uniform engine contract, and push the Coverage Ledger principle down from the audit layer into the engines.**

Concretely, and in ascending cost:

1. **Every read-only engine under `~/blueprint-workflows/scripts/` reports its denominator** in its JSON: `inputs_examined`, `inputs_excluded`, and `exclusion_reasons[]`. This is a handful of lines per engine and makes the class *visible* rather than *preventable* — which is the correct first move, because the exclusions themselves are usually right.
2. **A zero-denominator result is never a PASS.** An engine that examined nothing exits non-zero with an explicit message. `PASS` must mean "I looked and it was clean," never "I did not look."
3. **Path-exclusion conventions are evaluated relative to the scan root, never against the absolute path.** A one-line change per engine; the absolute-path form is a latent total-emptying bug in any workspace whose root happens to sit under a dot-directory, which is not exotic — it is this workspace.
4. **Any hard scan ceiling (`_MAX_FILES` and its kin) must surface `truncated: true`** rather than returning a partial count shaped exactly like a complete one.
5. **Add `Vacuous Pass` to the failure-pattern vocabulary** in `role.md` and the global agent frame, so the class can be *named* in future tickets rather than re-derived. Its diagnostic question is one line, and it belongs in every audit: *"How many things did this check actually examine?"*
6. **Fix `phase_status.py` to strip a trailing `{#id}` in `_strip_header_annotations`.** One line. It removes a live, suite-wide conflict between anchor-based citation governance and `/implementation-plan` STRICT RULE 28, and it retires a documented workaround in at least one workspace.

The general lesson, stated for `PROCESS_LEARNINGS.md`: **a verification result is only as trustworthy as its denominator, and no suite workflow currently obliges an engine to report one.** The Coverage Ledger already encodes this exact insight for audits (`/implementation-plan` STRICT RULE 24) — it was simply never inherited by the scripts those audits stand on.

## 6. Sibling Tickets Governed By This Meta Ticket

Each remains OPEN on its own merit and closes on its own evidence — never bulk-closed because this ticket closes (STRICT RULE 13).

- `20260729_focus-plan_workflow.md` — `IGNORE_DIRS` prunes `build/`, a real source tree. **Same class, name-based mechanism.**
- `20260730_continuous-verify-anchor-false-absent_workflow.md` — same root cause reaching `/continuous-verify`'s Null-evidence rule and Mock-Trap detection, producing false `ABSENT` and false `FOUND_TEST_ONLY`. **Same class; this ticket generalizes it rather than duplicating it.**
- `20260730_phase-status-found-incomplete-conflation_workflow.md` — `phase_status.py`, adjacent surface; §5 item 6 touches the same file and should be coordinated with it.
- `20260707_phase-status-campaign-header-scope_workflow.md` — `phase_status.py` header-parsing strictness; §5 item 6 is directly adjacent.

Filed as a distinct ticket rather than an Addendum because no existing ticket carries a **cross-engine counter-measure**; all four are correctly scoped to a single engine or workflow.

---
**Status**: **OPEN**
**Verification**: PENDING — §4 items 1-5 are built, tested and in production in the `lsshreveport` workspace (Phase 73, gate PASS, 0 receipt-trail regressions across 10 phases). §5 items 1-6 are proposals for the suite and are unimplemented.

---
*Signed,*
**Claude Code**
*(Sovereign Build Agent — `lsshreveport` / `research/proforma`, Phase 73)*
