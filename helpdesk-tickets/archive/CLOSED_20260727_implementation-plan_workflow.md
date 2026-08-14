# Helpdesk Ticket: --audit's Coverage Ledger Assumes a Clean Commit Boundary That Nothing Enforces

**To**: Senior Architect of Workflows
**From**: Claude Code Session (research/proforma, lsshreveport project)
**Date**: 2026-07-27
**Subject**: `/implementation-plan`'s Phase 5 Coverage Ledger is built entirely around `git diff --stat` producing a clean, single-phase changeset, but nothing in Phase 5 (or elsewhere in the suite's build cycle) ensures a commit happens between build phases — so a user who forgets to commit gets multiple phases squashed into one commit, degrading the next audit to a manual-reconstruction fallback.
**Urgency**: HIGH
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary
The Coverage Ledger (`/implementation-plan` Phase 5) enumerates a changeset via `git diff --stat` against "the base this plan was executed from," treating that as authoritative unless git is unavailable entirely. It has no notion of a *messy* git history — one where a user's forgotten commit lets a second build phase's work land on top of an uncommitted first phase's work, so a later `git diff --stat` mixes both phases together with no clean boundary between them. This happened today: between the Phase 37 audit and the Phase 38 audit in this session, no commit occurred, so Phase 38's own `/execute-build` run committed Phase 37's remaining changes and Phase 38's new changes together in one commit, with an orphan commit in between containing only one unrelated file deletion. The Phase 38 audit had to fall back to the receipt's self-declared file list plus a manual cell-level diff against a checkpoint file to isolate Phase 38's actual impact — a real, working fallback, but a degraded one, and exactly the kind of self-report-as-fact risk the Coverage Ledger's own `git diff --stat` requirement exists to avoid.

## 2. Root Cause Analysis: "Structural Gap — No Commit-Boundary Discipline Between Build Phases"
- **The How**: A user runs `/execute-build` for phase N, then (without committing) runs `/execute-build` again for phase N+1, then invokes `/implementation-plan --audit`. Git's history now shows phase N+1's commit containing both phases' diffs. The audit's `git diff --stat` against the pre-phase-N base returns a changeset spanning two phases, not one — the Ledger's core assumption (one commit = one phase = one clean boundary) is silently false, and nothing in the workflow detected or prevented it.
- **The Why**: Phase 5's Coverage Ledger protocol (`implementation-plan.md:204-208`) specifies *how* to enumerate a changeset once you have one, and STRICT RULE 24 (`implementation-plan.md:955`) makes the enumeration mandatory — but neither step, nor `/execute-build`'s own Phase 6/7 receipt-writing steps, ever checks whether a commit boundary actually separates the phase being built from the phase before it. The workflow that writes the changeset (`/execute-build`) and the workflow that audits it (`/implementation-plan --audit`) have no shared discipline ensuring a commit happens between them.

## 3. Forensic Evidence
- **Coverage Ledger protocol — treats `git diff --stat` as the authority with no commit-boundary check**: [Coverage Ledger steps 1 and 4](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L204-L208)
  *Evidence: Step 1 says "enumerate the actual changeset mechanically: `git diff --stat` against the base this plan was executed from" — it assumes that base-to-HEAD diff corresponds to exactly one phase's work, with no verification of that assumption.*
- **STRICT RULE 24 — makes the enumeration mandatory but not the commit boundary it depends on**: [STRICT RULE 24](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L955)
  *Evidence: "Both the standalone audit (Phase 5) and the per-workstream audit (Phase 7d) MUST enumerate the actual changeset mechanically (`git diff --stat`...)" — the rule's only stated degradation path is "if git is unavailable," not "if the changeset spans more than the phase being audited."*
- **The Phase 38 audit's own scoping note, demonstrating the fallback live**: [Coverage Ledger scoping note](file:///home/jwils/blueprint-workflows/implementation-plan/audits/20260727-1735-proforma.md#L6)
  *Evidence: "`git diff --stat` cannot cleanly isolate Phase 38's changeset — Phase 37's remaining uncommitted work and Phase 38's work were both committed together in `0d3628f`... this Ledger is scoped to the receipt's own declared Files Modified list... plus a direct cell-level diff against `checkpoint_Phase37.xlsx`" — a real, working degradation, but not the Ledger's designed path.*
- **The git log itself, showing the squashed boundary**: `git log --oneline -5 -- research/proforma/` in `/home/jwils/.prebuild.temp/lsshreveport` shows `0d3628f` ("remediate audit findings... magnitude-aware currency formatting, automated workbook jargon scanning, and cleaning internal audit disclosures") sitting directly on `e7d556b` ("implement automated workbook jargon scanning, harden sanitization logic, and remediate Phase 37-38 audit findings") — both commit messages describe work spanning Phase 37 *and* Phase 38, confirming the phases were never cleanly separated by a commit.

## 4. Remediation: Not Yet Applied — Recommendation Only
This ticket does not propose a specific fix mechanism. The reporting session's own Phase 38 audit worked around the gap successfully (receipt file list + checkpoint diff), so there is no urgent breakage to patch — but the pattern will recur for any user of this suite who forgets to commit between `/execute-build` cycles, and the right mechanism is a judgment call the architect should make, not one this ticket should presuppose:
1. **Option A — hard gate in `/implementation-plan --audit`**: before Step 1 of the Coverage Ledger, check whether `git status --short` shows uncommitted changes, or whether the git log between the audit's base and HEAD contains more than one phase's own receipt-writing commit; if so, HALT and prompt the user to commit (or explicitly accept degraded, multi-phase coverage) before scoring.
2. **Option B — soft warning, same check**: proceed with the audit using the best-available fallback (as happened today), but surface a visible warning in the audit's own output that the Coverage Ledger's `git diff --stat` boundary is not trustworthy this run, rather than leaving that discovery to the auditor's own judgment mid-Ledger.
3. **Option C — the gate belongs in `/execute-build`, not `/implementation-plan`**: require `/execute-build`'s own Phase 6/7 (Phase Build Receipt / Final Build Receipt) to prompt for or perform a commit at phase boundaries, so the problem never reaches `--audit` at all.
Each option has a different cost/friction tradeoff (auto-committing on the user's behalf is a meaningfully different posture than halting to ask, and this suite's own git-safety norms elsewhere lean toward asking rather than acting) — flagged explicitly rather than assumed.

## 5. Recommendation to Senior Architect
Investigate whether Phase 5's Coverage Ledger should verify its own foundational assumption — that the `git diff --stat` boundary it enumerates against actually corresponds to one phase's work — before treating that diff as authoritative, and choose the right mechanism (hard gate, soft warning, or moving the check upstream into `/execute-build`'s own phase-boundary handling) rather than defaulting to the first option considered. This is a workflow-level gap: any project using this suite's `/execute-build` → `/implementation-plan --audit` cycle across multiple phases without an intervening commit will hit the same degraded fallback, not just this session's project.

---
**Status**: **OPEN**
**Verification**: PENDING — awaiting Senior Architect review.

---
*Signed,*
**Claude Code (Sovereign Helpdesk Analyst mode)**
*(Creating Agent — research/proforma session, lsshreveport project)*

---
## Addendum — 2026-07-27, /secretary session close

**Finding**: This ticket was found renamed to `CLOSED_20260727_implementation-plan_workflow.md` at session close, by an actor not identifiable in this session's own conversation history. The rename carried **zero content change** — no closure record, no Phylogeny Disposition resolution, no Hardening Certificate or Remediation Record — and the ticket's own internal `**Status**: **OPEN**` line was left untouched, directly contradicting the `CLOSED_` filename. Independently re-verified: `implementation-plan.md` contains no commit-boundary check of any kind (`grep` for "commit boundary", "uncommitted changes.*halt", "git status --short.*audit" returns zero matches). This is a false closure — the underlying finding was never remediated.

**Action taken**: Reverted the rename, restoring the ticket to open state, consistent with its own internal Status field and the actual (unremediated) state of `implementation-plan.md`. No other ticket content altered, per `/nodelete`.

**Contrast noted**: The sibling ticket filed the same session, `20260727_personality_workflow.md`, was also found closed at session start — but that closure *is* substantively genuine (a real, well-scoped `Suite Workflow Exemption` was added to `personality.md` Section 6 and mirrored to `CLAUDE.md`, verified by direct diff) — see that ticket's own closure record. This ticket's false closure is not evidence of a systemic problem with ticket closures generally; it appears to be an isolated incomplete action, but is exactly the failure shape this project's own audit history has repeatedly named: a closure claimed without corresponding proof. Logged to `ANOMALY_LOG.md`.

---
## Addendum 2 — 2026-07-27, /secretary session close (corrects Addendum 1 above)

**Correction**: Addendum 1's conclusion — "the underlying finding was never remediated" — was reached by grepping only `implementation-plan.md`. That was incomplete. The actual remediation landed in a sibling workflow instead, matching **Option C** this ticket's own Section 4 proposed ("the gate belongs in `/execute-build`, not `/implementation-plan`"). Independently re-verified, this session:

- `execute-build.md` frontmatter: `version: 8`, `strict_rule_count: 22`.
- GLOSSARY term **Phase Boundary Auto-Commit** present (`execute-build.md:72`), citing this ticket by filename.
- Step 6b present in the Phase 6 body (`execute-build.md:470`) and STRICT RULE 22 present (`execute-build.md:585`), both citing this ticket.
- `scripts/core/git_ops.py` and `scripts/git/auto_commit.py` both exist on disk and were exercised directly: `python3 -m unittest tests.test_git_ops -v` → **13 tests, all passing** (matches the SUITE_HEALTH.md narrative's claim exactly, independently reproduced, not taken on trust).

**Genuinely still missing** (not fabricated, but real gaps in the closure *process*, independent of the fix's own substance):
1. This ticket file itself never received a closure record before being renamed `CLOSED_` — its own `**Status**` line still read `OPEN` internally, contradicting the filename. That contradiction is what triggered Addendum 1 in the first place.
2. `manifest/SUITE_PHYLOGENY.md` has no lineage entry for this remediation, despite `execute-build.md`'s Step 6b existing specifically to serve `/implementation-plan --audit`'s Coverage Ledger — a real cross-workflow structural relationship that the Phylogeny Disposition Gate (STRICT RULE 12) exists to capture. See the proper closure record below, which resolves this.
3. `manifest/SUITE_HEALTH.md`'s own 2026-07-27 narrative bullet claims "`/implementation-plan` (Phase 5 Coverage Ledger Pre-check)" was also added — independently checked, `implementation-plan.md` contains no such addition (`grep -c "Coverage Ledger Pre-check"` → 0). That specific sub-claim is inaccurate; the `execute-build.md` half of the same bullet is accurate. Corrected via a new dated bullet in `SUITE_HEALTH.md`, not by silently editing the existing one.

**Reverting Addendum 1's rename decision was itself premature** — recorded here rather than silently un-done, per the same evidentiary discipline this whole session has applied to every other claim.

## CLOSURE RECORD

**Status**: **REMEDIATED (Phase Boundary Auto-Commit added to `/execute-build`)**
**Root Cause Type — corrected**: STRUCTURAL → **SUBSTANTIVE-LOGIC**. The delivered fix required new decision logic (Step 6b's judgment about when/how to auto-commit) and new supporting code (`scripts/core/git_ops.py`, `scripts/git/auto_commit.py`) — the exact SUBSTANTIVE-LOGIC signature this suite's own `helpdesk-tickets.md` Change Log entry 3 and `execute-build.md` Change Log entry 12 already document as commonly misclassified STRUCTURAL at filing time. Closed via direct remediation (the SUBSTANTIVE-LOGIC path), not `/harden-workflow --ticket` — consistent with `execute-build.md` being `grade: Sovereign` (that tool halts without modification on an already-Sovereign file per its own Phase 1).

**Remediation Record**:
```
Ticket:            20260727_implementation-plan_workflow.md
Faulting workflow: /implementation-plan (fix delivered in /execute-build instead — Option C)
Root cause fixed:  No commit-boundary discipline between /execute-build phases, degrading
                   /implementation-plan --audit's Coverage Ledger to a manual-reconstruction
                   fallback when a user forgets to commit between build cycles.
Changes made:      execute-build.md v7→v8 — new Step 6b (Phase Boundary Auto-Commit) + STRICT
                   RULE 22 + GLOSSARY entry, all citing this ticket. New scripts/core/git_ops.py
                   (run_cmd, run_gate, auto_commit) + scripts/git/auto_commit.py CLI wrapper.
Tests:             13/13 passing — independently re-run this session via
                   `python3 -m unittest tests.test_git_ops -v`, not taken from the narrative on trust.
Linter:            0 CRITICAL / 22 WARNING (suite-wide, this session's own reading — see Secretary Receipt)
Deferred:          NONE for this ticket's own scope. Separately outstanding: this Phylogeny
                   entry itself (being written now) and the SUITE_HEALTH.md narrative correction
                   (added as a new dated bullet, not an edit to the existing one).
```

**Phylogeny Disposition**: `[lineage entry added — see manifest/SUITE_PHYLOGENY.md, "Phase Boundary Auto-Commit — a new gate spanning /execute-build and /implementation-plan's Coverage Ledger", 2026-07-27]` — a genuine cross-workflow structural relationship: `execute-build.md`'s new Step 6b exists specifically so `/implementation-plan --audit`'s Phase 5 Coverage Ledger has a clean `git diff --stat` boundary to enumerate against. Not `NO TRANSFER`.

---
**Status**: **REMEDIATED (Phase Boundary Auto-Commit added to `/execute-build`, Option C)**
**Verification**: 13/13 tests independently re-run and passing this session; `execute-build.md` v8 content independently read and confirmed (Step 6b, STRICT RULE 22, GLOSSARY entry, all present and citing this ticket).

---
*Re-closed by:*
**Claude Code (Sovereign Helpdesk Analyst mode, /secretary session close)**
