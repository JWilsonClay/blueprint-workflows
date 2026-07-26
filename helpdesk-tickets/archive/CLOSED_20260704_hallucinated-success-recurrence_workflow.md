# Helpdesk Ticket: Hallucinated Success Is the Suite's Single Largest Recurring Failure Pattern, Never Investigated as a Cross-Workflow Signal

**To**: Senior Architect of Workflows
**From**: Claude (session agent — surfaced while acting on the Suite Learning Registry's REVIEW verdict)
**Date**: 2026-07-04
**Subject**: `manifest/CONTRADICTION_REGISTRY.md` shows Hallucinated Success as the most frequent named failure pattern in the suite's history, recurring across at least six distinct workflows — this has never been reviewed as an aggregate signal because the registry itself had never been reviewed once, at any threshold crossing, since it was built.
**Urgency**: MEDIUM
**Root Cause Type**: SUBSTANTIVE-LOGIC — **[CONFIRMED 2026-07-05]** the investigation's real remediation (`/receipt-check` engine build) required new code, not just documentation.
**Phylogeny Disposition**: CONFIRMED — lineage entry added: `manifest/SUITE_PHYLOGENY.md`, "Lineage Entry — 2026-07-05 — `phase_status.parse_tasks_md` transfers to a second engine (focus-plan → receipt-check)"

---

## 1. Executive Summary

This is an **investigation-needed ticket, not a diagnosed-and-fixed one.** While clearing the Registry backlog for `helpdesk-tickets/CLOSED_20260704_registry-phylogeny-gap_workflow.md`, the aggregate came back with a REVIEW verdict (36 events, threshold 10) that had never actually been reviewed — not at this crossing, not at the original 2026-06-12 crossing either. Hallucinated Success is the largest named category by a clear margin and appears against at least six different workflows, not one. Nobody has looked at this signal as a signal; every occurrence was investigated only in isolation, ticket by ticket. This ticket exists to make sure that look happens, deliberately, rather than continuing to pass a REVIEW verdict through unexamined.

## 2. Root Cause Analysis: "Hallucinated Success" (pending confirmation — this ticket documents a statistical signal, not yet a mechanism)

- **The How**: `manifest/CONTRADICTION_REGISTRY.md`'s Event Log currently shows Hallucinated Success tagged against `/receipt-check`, `/implementation-plan` (twice, separately dated), `/workstream`, `/focus-plan`, `/harden`, `/iterate-test`, and `/contradiction-registry` — six-to-seven distinct faulting workflows across a two-month span, not a cluster in one place.
- **The Why**: Unknown. This is exactly what an investigation would need to determine — whether these are independent, unrelated instances of a generically hard problem (an LLM self-reporting completion it didn't actually verify), or whether they share a common structural gap the suite hasn't named yet (e.g., a missing verification-before-claiming-done step that several workflows independently lack). **Do not assume the second without checking** — this ticket deliberately stops at "the aggregate is suspicious," not "here is the shared mechanism," because asserting a mechanism without checking each instance would itself risk being an act of Hallucinated Success about Hallucinated Success.

**A caveat on the evidence itself, found while assembling it**: the registry's event count is not fully deduplicated. `registry.py` keys each event to the ticket's filename, and a ticket's filename changes on closure (`YYYYMMDD_x_workflow.md` → `CLOSED_YYYYMMDD_x_workflow.md`). A ticket scanned once while open and again after a later run finds it closed is recorded **twice** — confirmed directly: `20260612_contradiction-registry_engine.md` (patterns: Hallucinated Success, Ghost Logic) appears at both its pre-close and post-close filename in the current Event Log. Corrected count: **~34 distinct events, ~6 distinct Hallucinated Success occurrences**, not 36/7. This doesn't change the conclusion (still the largest category by margin) but the raw registry output should not be quoted without this correction. This dedup gap is itself worth a ticket — not filed here, since it's a third thing found while investigating the two the user asked about; flagged for a decision on whether it warrants its own filing.

## 3. Forensic Evidence

- **Registry aggregate, current run**: [manifest/CONTRADICTION_REGISTRY.md#L7-L11](file:///home/jwils/blueprint-workflows/manifest/CONTRADICTION_REGISTRY.md#L7-L11)
  *Evidence: "By failure pattern: Hallucinated Success: 7... verdict: REVIEW (threshold 10)" — largest category, and the verdict has been REVIEW since at least 2026-06-12 with zero `[REVIEWED YYYY-MM-DD]` markers ever appended.*
- **Six-plus distinct faulting workflows, not a cluster**: [manifest/CONTRADICTION_REGISTRY.md#L23,L30,L32,L36-L38,L40](file:///home/jwils/blueprint-workflows/manifest/CONTRADICTION_REGISTRY.md#L23)
  *Evidence: Hallucinated Success tagged against `/receipt-check` (L23), `/implementation-plan` (L30), `/workstream` (L32), `/focus-plan` (L36), `/harden` (L37), `/iterate-test` (L38), `/contradiction-registry` (L40, but see dedup caveat above).*
- **The verdict has never been actioned**: [harden-workflow.md#L208-L212](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L208-L212)
  *Evidence: "on REVIEW the agent ingests and may file a /helpdesk-tickets entry" — this is the first time that instruction is being followed since the registry existed.*

## 4. Remediation: Not Yet Determined — This Ticket's Job Is to Force the Investigation, Not Skip It

No fix is proposed here. The recommended next action is a dedicated investigation pass (candidate: `/investigate`, or a manual read of each of the six-plus source tickets in full) asking specifically: do these instances share a structural gap common to several workflows, or are they independent? Only that answer determines whether this ticket forks into a real STRUCTURAL/SUBSTANTIVE-LOGIC fix, a documentation note that this is an irreducible LLM tendency worth a standing mitigation, or a "not actually a pattern, just a common label" closure.

## 5. Recommendation to Senior Architect

Beyond this specific instance: the registry's REVIEW verdict should not be allowed to sit unexamined across multiple threshold crossings again. Consider whether `/secretary`'s new unconditional Registry pass (Step 1.0.5, added this session) needs a stronger prompt than "ingest and judge" — perhaps an explicit refusal to let two consecutive REVIEW verdicts pass without at least a recorded "reviewed, no action" note, distinct from the dedicated `[REVIEWED YYYY-MM-DD]` reset.

---
**Status**: **REMEDIATED (investigation completed; two stale ticket bodies corrected; /receipt-check engine-backed via scripts/receipt/, closing Verification-Spine Campaign QUEUE #11; a linter robustness fix discovered and applied along the way)**
**Verification**: See Remediation Record below.

---
*Signed,*
**Claude**
*(Session Agent — Senior Architect of Workflows role)*

---

## REMEDIATION RECORD

```
REMEDIATION RECORD
  Ticket:            20260704_hallucinated-success-recurrence_workflow.md
  Faulting workflow: /receipt-check (the one real, still-open gap the
                     investigation confirmed); two archived tickets with
                     stale paperwork (not live gaps); no single faulting
                     workflow for the investigation itself.
  Root cause fixed:  The investigation (deferred at filing time) is complete.
                     Three distinct clusters, not one undifferentiated
                     pattern:
                       Cluster A — instructional enforcement of a
                       verification guarantee (/focus-plan, /harden,
                       /iterate-test) — already fixed via the pre-existing
                       Verification-Spine Campaign (root implementation-plan.md
                       QUEUE), confirmed still in progress with 10 workflows
                       PENDING at investigation time.
                       Cluster B — self-assessment corrupted by a visible
                       target (/implementation-plan's calibration-band
                       gaming) — already fixed (STRICT RULE 17 supersedes
                       the calibration guidance); ticket paperwork was stale.
                       Cluster C — platform-specific context decay (Grok
                       OpenCode bulk-loading) — already fixed (31 pointer
                       files, bulk-loader retired); ticket paperwork was
                       stale, and the runtime itself was independently
                       retired by the user mid-session (see below).
  Changes made:      (1) Corrected Status/Verification on
                     CLOSED_20260524_implementation-plan_workflow.md and
                     CLOSED_20260524_workstream_opencode_pointer_workflow.md
                     from stale OPEN/PENDING to REMEDIATED, with verification
                     notes citing current substrate.
                     (2) Built scripts/receipt/ (coverage.py + reporter.py +
                     receipt_audit.py CLI + _utils.py, 15 tests) — the one
                     PENDING QUEUE row explicitly tagged Hallucinated Success
                     most directly. Reuses focus.phase_status.parse_tasks_md
                     directly (second engine to do so — SUITE_PHYLOGENY.md
                     entry). Matches BUILD/VALIDATION receipts by phase name,
                     HARDEN by a disclosed file-mention heuristic, reports
                     DOCUMENTED as existence-only (its real Phase/Stage value
                     is a fixed constant, confirmed against the live file —
                     no per-phase key exists), wires Quality-Process via a
                     direct quality_audit.py subprocess call. Reuses
                     /focus-plan v4's PENDING-is-not-a-gap distinction rather
                     than regressing it.
                     (3) Re-hardened receipt-check.md v2->v3 (Hardened->
                     Sovereign): EXECUTION MODEL section makes the engine
                     primary; original five-phase procedure preserved
                     verbatim as Manual Fallback Mode; STRICT RULES 9-11
                     added.
                     (4) Updated the Verification-Spine QUEUE (/receipt-check
                     row 11 -> DONE) and manifest/SUITE_HEALTH.md
                     (Sovereign 19->20, Hardened 13->12, live-recounted from
                     the table, not assumed).
                     (5) Mid-verification, discovered the user had
                     independently uninstalled Grok OpenCode (replaced by
                     x.ai's official Grok Build, not yet in active use) —
                     unrelated to this ticket's own scope, but it surfaced
                     via this ticket's re-verification pass. Filed
                     helpdesk-tickets/20260705_opencode-to-grok-build-
                     transition_workflow.md (left OPEN, tracking an external
                     adoption in progress, not a bug) and fixed a genuine,
                     general linter defect it exposed: scripts/suite/
                     checks.py's check_symlinks warned once per file (32
                     near-identical lines) when a runtime directory was
                     wholly absent, rather than recognizing "the whole
                     runtime is gone" as one fact distinct from "one file's
                     pointer is missing." Added check_runtime_availability
                     (one INFO-level note per scan) and gated the per-file
                     check on directory existence; added addendum to
                     CLOSED_20260524_workstream_opencode_pointer_workflow.md
                     noting its verified fix is now moot, not wrong.
  Tests:             21 new (15 scripts/tests/test_receipt.py, 6
                     scripts/tests/test_suite_checks.py). Full suite:
                     207/207 passed (186 pre-existing + 21 new), 0
                     regressions.
  Linter:            lint_workflows.py --workspace ~/blueprint-workflows:
                     0 CRITICAL, 19 WARNING — identical to the pre-existing
                     baseline; the transient 31-line OpenCode pointer noise
                     is now a single INFO note, confirmed by direct
                     before/after comparison, not assumed clean.
  Deferred:          The registry dedup artifact noted in Section 2
                     (a ticket scanned pre- and post-close counts twice) —
                     flagged there as a third thing found while
                     investigating, explicitly not filed as its own ticket
                     yet; still an open decision, not forgotten.
                     Everything the new OpenCode/Grok Build ticket itself
                     defers (Grok-Build-specific tooling, /workstream's
                     Grok framing) — deliberately not touched here; that
                     ticket's own scope, not this one's.
```
