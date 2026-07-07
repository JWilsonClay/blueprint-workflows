# Helpdesk Ticket: Stale Authority Boundary — Ticket-Routing Pipeline Assumes Every Fix Is Structural

**To**: Senior Architect of Workflows
**From**: Claude (Sonnet 5) — /limitations + /focus-plan remediation session
**Date**: 2026-07-04
**Subject**: `role.md`, `harden-workflow.md`, and `helpdesk-tickets.md` all still describe a workspace where the Architect never writes code and every ticket routes through `/harden-workflow` — confirmed, user-directed practice has already moved past this.
**Urgency**: HIGH

---

## 1. Executive Summary
Today's session resolved two helpdesk tickets by direct remediation — one required writing a new Python engine module (`scripts/focus/phase_status.py`) with 18 unit tests to fix a workflow's underlying classification logic. Neither ticket went through `/harden-workflow --ticket`, the path `/helpdesk-tickets` documents as standard. Investigating why revealed `/harden-workflow` explicitly excludes both protocol-logic changes and code by its own text, and `role.md` explicitly lists modifying project-level code files as out of the Architect's scope. All three documents describe a workspace that no longer matches practice. Per the user: this has caused "consistent tension" during ticket resolution before today, not just today. (Note for a future reader: `helpdesk-tickets/20260625_role_workflow.md` is also open and also touches `role.md`, but for an unrelated reason — Gemini-transition halt-boundary semantics, not authority scope. Not a duplicate of this ticket.)

## 2. Root Cause Analysis: "Stale Authority Boundary / Governance Drift"
- **The How**: `/helpdesk-tickets`' INTEGRATION section documents a single, unforked pipeline: ticket filed → `/harden-workflow --ticket` consumes it → hardening executed → ticket closed. This works when the root cause is a missing structural element (GLOSSARY, STRICT RULES, Change Log — e.g. the 2026-06-12 `/nodelete` and `/divergence` tickets). It silently fails when the root cause is a logic defect or requires code: `/harden-workflow` assesses an already-Sovereign file, finds no structural gap, and halts without modification per its own Phase 1 instruction — never touching the actual defect.
- **The Why**: `role.md` was never updated when the workspace's actual practice evolved from pure markdown-workflow authorship to include supporting Python engine work (`scripts/focus/`, `scripts/doorway/`, `scripts/registry/`, `scripts/gitignore/`, `scripts/suite/` all now exist and are actively extended). Section V still lists code-file modification as explicitly out of scope. Neither `harden-workflow.md` nor `helpdesk-tickets.md` were updated in tandem to define where logic/code-defect tickets should route once `/harden-workflow` was known to be unable to take them.

## 3. Forensic Evidence
- **Scope exclusion, still current**: [role.md](file:///home/jwils/blueprint-workflows/claude-commands/role.md) Section V — "What is explicitly out of your scope: Modifying project-level code files (Python, JS, etc.) during a workflow maintenance session" and "Closing helpdesk tickets without completing the hardening that closed them."
  *Evidence: the Architect's own identity document forbids exactly what today's session did, and implies ticket closure always follows "hardening" specifically.*
- **`/harden-workflow` structure-only mandate**: [harden-workflow.md#L45](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L45) — "This workflow does NOT harden code, scripts, or business logic. It hardens the workflow files themselves."
  *Evidence: explicit, unambiguous exclusion of the code-writing work today's `/focus-plan` ticket required.*
- **`/harden-workflow` STRICT RULE 3**: [harden-workflow.md#L716](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L716) — "Never modify a command file's protocol logic... only add missing structural elements... Content improvements belong to the specific workflow's own refinement session."
  *Evidence: explicitly excludes the PHASE 2/PHASE 4 logic rewrite today's ticket required, and names an undefined destination ("the workflow's own refinement session") for exactly this category of fix — this ticket names that session.*
- **`/harden-workflow` halts on already-Sovereign files**: [harden-workflow.md#L244-L247](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L244-L247) — "If current grade is already Sovereign... Output the Assessment Card and halt... do not modify the file."
  *Evidence: `focus-plan.md` was already Sovereign-graded before today's fix. Invoking `/harden-workflow` against it would have halted without touching the actual defect — verified by reading the file, not assumed.*
- **Unforked pipeline**: [helpdesk-tickets.md](file:///home/jwils/blueprint-workflows/claude-commands/helpdesk-tickets.md) INTEGRATION section — "Standard position in the failure response pipeline: ... 4. Senior Architect invokes /harden-workflow --ticket → ticket consumed, hardening executed."
  *Evidence: no branch exists for a ticket whose root cause is not a structural gap.*
- **Today's actual resolution path**: `scripts/focus/phase_status.py` (new file) + `scripts/tests/test_phase_status.py` (18 tests) written to resolve `helpdesk-tickets/CLOSED_20260630_focus-plan_workflow.md`; ticket closed via `/helpdesk-tickets` Phase 4's "or by the creating agent if the fix was applied in the same session" clause — a legitimate but under-advertised path, never routed through `/harden-workflow`.
  *Evidence: contemporaneous proof that practice has already diverged from the documented primary pipeline, and that a real alternate path already exists in `/helpdesk-tickets` itself.*

## 4. Remediation: Ratify the Two-Path Ticket Model
1. **Update `role.md` Section V**: replace the blanket "modifying project-level code files... out of scope" line with a bounded authority — the Architect may modify supporting code under `scripts/` when a ticket's remediation requires it, provided the change is covered by real tests and the existing suite remains green. Per /nodelete: supersede, don't silently delete, the old boundary.
2. **Update `helpdesk-tickets.md`**: add a root-cause classification step at ticket-writing time (Section 2, Root Cause Analysis) — Structural (missing scaffold element) vs. Substantive/Logic (wrong or missing judgment logic, possibly requiring code) — and fork "Standard position in the failure response pipeline" accordingly: Structural → `/harden-workflow --ticket` (unchanged); Substantive/Logic → direct refinement session under `/quality` discipline, verified by tests + linter, closed via the Phase 4 mechanism already available to the creating agent.
3. **Update `harden-workflow.md`**: no logic change needed — STRICT RULE 3 and the structure-only mandate are correct and should stay exactly as written. Add a cross-reference note pointing substantive/logic tickets to the new `helpdesk-tickets.md` fork, so a future agent reads the boundary as "there's a place for that, and it isn't here," rather than discovering the halt by trial and error.

## 5. Recommendation to Senior Architect
Formally ratify, in the governance documents rather than only in confirmed practice, that ticket remediation splits into two authorized paths — structural hardening (`/harden-workflow --ticket`, unchanged, still code-free and logic-free by design) and substantive/logic refinement (direct, quality-verified work that may include supporting code, closed via `/helpdesk-tickets`' existing "creating agent" closure clause). This is not a new workflow to build — both paths already exist in the suite's own text; they are just not currently visible to each other from the ticket-intake side.

---
**Status**: **REMEDIATED (two-path ticket model ratified across all three governance documents — this is the first ticket closed under the model it created)**
**Verification**: See Remediation Record below.

```
REMEDIATION RECORD
  Ticket:            20260704_ticket-remediation-authority_workflow.md
  Faulting workflow: /role, /harden-workflow, /helpdesk-tickets
  Root cause fixed:  All three governance documents assumed every ticket's fix was
                     structural, routing exclusively through /harden-workflow. Now
                     forked: Structural (unchanged) vs Substantive/Logic (direct,
                     quality-verified remediation, a real path that already existed
                     in /helpdesk-tickets Phase 4 but was never the documented default).
  Changes made:      role.md Section V — the original "no code" line struck through
                     and preserved (not deleted) per user directive, honoring it as
                     an expression of the role's original partnership framing rather
                     than a corrected restriction; new "On code authority" grants
                     bounded, ticket-instrumental authority to modify this repo's own
                     scripts/ (not downstream projects' application code). Third scope
                     bullet reworded to fork on Root Cause Type.
                     helpdesk-tickets.md v2→v3 — Root Cause Type (STRUCTURAL /
                     SUBSTANTIVE-LOGIC) added as a mandatory Phase 0a field and
                     Section-2 header declaration (STRICT RULE 11); forked pipeline
                     (INTEGRATION) and Phase 4 closure; new Remediation Record
                     template (this document is its first real use).
                     harden-workflow.md v3→v4 — Step TM-1.5 added: checks Root Cause
                     Type immediately after the open-ticket scan and redirects a
                     SUBSTANTIVE-LOGIC ticket explicitly, rather than letting it fall
                     through to a confusing "already Sovereign, nothing to do" halt
                     several phases later (STRICT RULE 22). STRICT RULE 3 and the
                     structure-only mandate themselves untouched — they were already
                     correct; this closes the gap in discovering when they apply.
  Tests:             No engine exists for any of the three files touched — all are
                     workflow/identity documents, not code. N/A; verification is
                     structural (linter) and textual (internal cross-reference
                     consistency across all three files), matching how the
                     `/implementation-plan` Coverage Ledger ticket was verified.
  Linter:            lint_workflows.py — role.md, helpdesk-tickets.md,
                     harden-workflow.md: 0 CRITICAL, 0 WARNING (after genuine hash
                     recomputation via --fix-hashes on all three). role.md carries
                     two pre-existing, unrelated WARNINGs (missing HOW TO BEGIN /
                     INTEGRATION) — expected, since role.md is explicitly a
                     reference document, not a slash command; not part of this
                     ticket's scope.
  Deferred:          NONE — Section 4's three remediation steps were all executed
                     in full, per the user's "proceed in full, and I will review"
                     instruction (Turn-Boundary Pause Protocol, this same session).
```

---
*Signed,*
**Claude (Sonnet 5)**
*(Senior Architect of Workflows, this session)*
