# Archival Ledger — implementation-plan.md

This file contains archived, completed phases from `implementation-plan.md` per the `/nodelete --archive` workflow.

---

## Phase 1 — Quick Wins
<!-- Marker slot: leave blank until /implementation-plan --audit confirms it. -->

### Detailed Requirements

`.changelogs/` externalization (see tasks.md for the per-file checklist) and the `lint_workflows.py --fix-hashes --write` mode. The latter is **already built and tested this session** (`scripts/suite/lint_workflows.py`, `scripts/tests/test_lint_workflows_write.py`, 6/6 passing) — resolves `helpdesk-tickets/CLOSED_20260704_lint-fix-hashes-gap_workflow.md`.

---

## Phase 2 — Instruction Density Compression

### Detailed Requirements

Apply the compression test above to STRICT RULES and Phase control-flow sections across the suite. Do not touch GLOSSARY, motivational prose, or Change Log narrative. Candidate high-value targets (highest STRICT RULES word-share per `docs/workflow_length_analysis.html`): `secretary.md`, `nodelete.md`, `harden-workflow.md`, `workstream.md`. Each file's compression is a self-contained, `/nodelete`-compliant edit (supersede prose with denser notation; the Change Log entry documents the change).

---

## Phase 4 — Verification-Spine Re-Verification

### Detailed Requirements

Before building engines for `/execute-build`, `/secretary`, `/triage`, `/harden-workflow`, re-run Honest-Design Discipline against their *current* content (all four were hardened to Sovereign by other means since the original seed design was written — see governing ticket §2.2). Then execute the ten-step recipe. `/execute-build` first, per the Dependencies note above.

---

## Phase 5 — Verification-Spine Engine Extraction (remaining 5)

### Detailed Requirements

Standard ten-step recipe per workflow, seed designs preserved in the archive file. `/harden-workflow` is covered by Phase 4 (already re-verified there), not repeated here.

---

## Phase 6 — Handoff Mechanism
**SUPERSEDED [QUARANTINE:2026-07-07]** (reason: over-engineered a problem that doesn't exist — see the corrected Phase 6 note earlier in this file, under "Execution-Readiness Per Phase." `/execute-build`, already generic and already pointer-available to Antigravity, is the handoff mechanism. No new `/workstream` extension is needed. Preserved here per `/nodelete` rather than deleted.)

### Detailed Requirements (superseded, preserved for record)

~~Extend `/workstream` Phase 0a and `/implementation-plan` Phase 6 to accept a workstream design with only Workstream B (Gemini) populated, A and C explicitly DORMANT. Reuse Pre-Flight Manifest, Engineer Brief, Handoff Block verbatim. Skip rotation formula, cross-workstream conflict scan, PM/Architect ceremony (all assume 3 simultaneous agents). Bound every delegation to one phase/slice — never an open-ended "build the whole plan" handoff.~~ The one substantively correct point carried forward: **bound every delegation to one phase/slice — never an open-ended "build the whole plan" handoff.** That safety principle is not superseded, only the mechanism it was attached to.

---

## Phase 7 — User Training Guide

### Detailed Requirements

`docs/GEMINI_EXECUTE_BUILD_GUIDE.md` (renamed from the superseded `GEMINI_WORKSTREAM_GUIDE.md`): exactly how to open an Antigravity session and invoke `/execute-build` against this workspace, what a Phase Build Receipt round-trip looks like, and a worked example drawn from Phase 8's first real pilot. Exists specifically so the mechanism isn't built and then forgotten a second time — direct response to the user's own 2026-07-07 observation.

---

## Phase 8 — First Live Delegation Pilot

### Detailed Requirements

Run Phase 1 (Quick Wins) through Gemini via `/execute-build`, invoked in an Antigravity session — the one phase already verified execution-ready (see "Execution-Readiness Per Phase" above). Do not use the doorway `substrate_index.json` work as the first pilot despite it being well-specified elsewhere — it hasn't been checked against `/execute-build` Phase 2's observability bar the way Phase 1 has, and a first pilot should not carry that unverified risk. Claude runs a Coverage Ledger-style audit of the result before accepting it.

---

## Phase 9 — Session Close (this session's own authorized cleanup)

### Detailed Requirements
Retroactive cleanup, closing tickets, and verifying test suite execution for the first delegation session.

---

## Phase 10 — Next Gemini Delegation Candidate

### Detailed Requirements
Identify and stage the next candidate tasks for Gemini execution.


### Archived Meta-Data (Handoff, Readiness, & Concept Notes)

### User Approval (2026-07-07)

**Recorded here because `/execute-build.md` STRICT RULE 15 ("Discussion Is Not Authorization") requires confirmation that a plan reflects genuine approval before building starts — and a fresh Gemini session, with zero memory of the Claude Code conversation this plan was produced in, has no way to see that approval unless it's written down here.** User's own words, 2026-07-07: *"I have read them and approve them."* This satisfies STRICT RULE 15 for `implementation-plan.md` and `tasks.md` as they stood at this date. Any phase substantively re-scoped after this date needs its own confirmation before `/execute-build` treats it as pre-approved — do not assume this blanket approval extends to content added later without a new, equally explicit statement.

### Execution-Readiness Per Phase (added 2026-07-07 — direct answer to "is this ready for handoff")

**Verified against `/execute-build.md` Phase 2's own gate** ("Criteria must be observable... a phase where some tasks lack acceptance criteria is underspecified... HALT and ask the user to clarify before building") — not asserted, checked:

| Phase | Ready for Gemini today? | Why |
|---|---|---|
| 1 (Quick Wins) | **YES** | 1.1 already done. 1.2/1.3 have observable, mechanical criteria (a named file list, a naming convention, a directional metric check). |
| 2 (Instruction Density Compression) | **PARTIAL — 2a YES, 2b NO** | Per-rule judgment now done for `secretary.md` (8/20 rules compressed, evidence in `tasks.md` 2.1) and `nodelete.md` (0/14 — file already at the density floor, a real verified finding, `tasks.md` 2.2). 2a's mechanical apply (`tasks.md` 2.5a) is genuinely execution-ready, same recipe shape as Phase 1.2. `harden-workflow.md` (22 rules), `workstream.md` (24 rules), and Phase control-flow sections across all 4 files remain unassessed — deferred as 2b rather than rushed; still requires the same per-rule Claude pass before handoff. |
| 3 (Doorway/README) | Already done natively | — |
| 4-5 (Verification-Spine builds) | **NO** | These explicitly require running Honest-Design Discipline — the campaign's own named "mandatory judgment step." Asking Gemini to perform it contradicts the "not thinking, just execution" model directly. Needs Claude to pre-resolve each workflow's seed design first. |
| 6 (Handoff mechanism) | **RESOLVED 2026-07-07** | See below — simpler than originally designed, no new construction needed. |
| 7 (Training guide) | Blocked on 6 | Now unblocked; scope corrected below. |
| 8 (First pilot) | **NO — candidate not yet locked** | "Select... or confirm a different candidate" is itself a decision. Needs Claude to pick one and pre-resolve its open judgment calls before handoff. |

**Recommendation**: hand off Phase 1 as the real first Gemini invocation. Do not hand off Phase 2, 4, 5, or 8 until each gets its own Claude design-tightening pass — the same "one upgrade at a time, honestly" discipline the original Verification-Spine campaign was built on, now applied to *designing for* delegation rather than building natively.

### Phase 6 — Handoff Mechanism, Corrected (2026-07-07)

**The original Phase 6 (below) over-engineered this.** Direct re-check: Antigravity already holds pointer files for all 33 current workflows, including `/execute-build`, which is already generic (project-agnostic persona, `<IMPL_PLAN>`/`<TASKS_FILE>` discovery, no Claude-Code-specific tool assumptions found on a full re-read) and already consumes exactly the `implementation-plan.md` + `tasks.md` format this plan uses. **The handoff mechanism is: open an Antigravity session, invoke `/execute-build`, point it at this workspace.** No new single-engineer `/workstream` mode needs to be built. The original Phase 6 tasks (extending `/workstream`'s Phase 0a, DORMANT-role markers, etc.) solved a problem that doesn't exist — struck through in `tasks.md`, not deleted, per `/nodelete`.

---

## THE CONCEPT (carried forward verbatim from the archived format — still governs Phases 4-5)

The suite's verification workflows historically enforced their core guarantees by **instruction** — they *asked* the agent to gather evidence and *trusted* it did. That is the weakest enforcement model; a capable model routes around the ceremony, and the guarantee (that a check actually happened) rests on nothing structural. The fix, proven five times now (`/focus-plan`, `/quality`, `/harden`, `/iterate-test`, `/receipt-check`):

- **Split each workflow into a deterministic half and a judgment half.**
- **Build the deterministic half as a read-only Python "engine"** under `scripts/<name>/`, modeled on `scripts/doorway/`. It reads the substrate, emits a structured JSON evidence report, and **writes nothing** to the workspace.
- **Reduce the workflow `.md` to a thin "verification rail"** that runs the engine and reasons over its output — keeping every judgment step intact.
- Because a *script* produced the evidence, the agent **cannot hallucinate it.**

## HONEST-DESIGN DISCIPLINE (mandatory before building any Phase 4/5 engine)

1. **What is mechanically verifiable here?** → the engine.
2. **What is irreducible judgment?** → stays in the model, untouched.
3. **The Mock-Trap test:** if your proposed engine would have to *judge* (2) to produce its result, STOP — redesign it to verify (1) only, and make any heuristic signal one-directional and advisory.

Full END-TO-END UPGRADE RECIPE (steps A-J) and per-workflow seed designs for the four re-verify targets: see `.history/archive/implementation-plan-verification-spine-queue-format.md.ledger.md` — preserved verbatim, still the operative recipe, just relocated so this live file stays lean.

## Instruction Density Compression — the test (governs Phase 2)

Per-rule test before compressing a STRICT RULE or Phase control-flow block into pseudocode notation: **does this change what's being asked, or only how densely it's phrased?** If only the latter, compress it. If compression would require inventing a function that secretly performs judgment (e.g. `is_this_design_excellent()`), that is a Mock Trap wearing code-shaped clothes — do not write it, in prose or pseudocode. Full reasoning: governing ticket §3.3 item 3.
