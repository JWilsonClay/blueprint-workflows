# Helpdesk Ticket: Ghost Dependency — /secretary Hard-Codes Monolithic /document Path

**To**: Senior Architect of Workflows
**From**: Sovereign Depreciate + Investigate Joint Audit Agent
**Date**: 2026-05-12
**Subject**: /secretary contains a path reference to /document that will silently break when /document is migrated to Pointer/Payload architecture.
**Urgency**: MEDIUM

---

## 1. Executive Summary

`/secretary` Phase 2 triggers `/document` by reading `document.md` directly. A deprecation note is embedded in the payload acknowledging this is a structural debt item. As long as `document.md` remains a monolithic file under 12,000 characters, the call is safe. However, the path reference is hard-coded to the root monolithic file — when `/document` is eventually migrated to Pointer/Payload architecture (as all large workflows should be), the `view_file` call in `/secretary/core.md` Line 132 will silently reference the pointer, not the payload, breaking the document trigger or receiving a truncated workflow. Because `/secretary` does not emit an error when sub-workflows fail unexpectedly, this failure mode is invisible to the user.

## 2. Root Cause Analysis: "Ghost Dependency Path"

**Failure class**: Structural Debt / Future Breaking Change

- **The How**: `/secretary` Phase 2 issues `view_file /home/jwils/.gemini/antigravity/global_workflows/document.md` — a hard-coded path to the root monolithic file. When `/document` is migrated, `document.md` will become a 15-line pointer. The secretary will then read the pointer (not the full protocol), receive incomplete workflow instructions, and proceed silently.
- **The Why**: The `/secretary` workflow did not adopt the pattern of referencing payloads via sub-directory `core.md` paths for its triggered sub-workflows. Phase 2 was written when `/document` was monolithic, and the fix was deferred with an inline comment rather than resolved structurally. The workflow lacks a pre-flight check that verifies the target file is a payload (not a pointer) before executing it.

## 3. Forensic Evidence

- **[Ghost dependency declaration]**: [secretary/core.md:L132](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L132)
  *Evidence: `view_file /home/jwils/.gemini/antigravity/global_workflows/document.md` — the call targets the root file, not a payload path. This line will return a 15-line pointer when /document is migrated.*

- **[Embedded debt note acknowledging the gap]**: [secretary/core.md:L147](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L147)
  *Evidence: "Dependency note: /document is currently a monolithic workflow (Structured grade). This call is safe as long as /document.md is under 12,000 characters. When /document is converted to Pointer/Payload architecture, update the view_file path here to reference document/core.md." — The architect acknowledged the future break but did not create a tracking mechanism to ensure the fix happens at migration time.*

- **[/secretary STRICT RULE 10 — sub-workflow failure tolerance]**: [secretary/core.md:L299](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L299)
  *Evidence: "If any Phase fails... log the failure in the Secretary Receipt and continue." — The secretary's own failure tolerance means the broken /document call would be swallowed silently rather than surfaced as a blocking error.*

## 4. Remediation: Migrate /secretary Phase 2 to Payload-Aware Path

The remediation has two components:

1. **When /document is migrated to Pointer/Payload**: Update [secretary/core.md:L132](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L132) from `view_file document.md` to `view_file document/core.md`. Update the dependency note at L147 to reflect the completed migration.
2. **Now (pre-migration guard)**: Inject a pre-flight size check into /secretary Phase 2 that warns if `document.md` exceeds 10,000 bytes, alerting the architect that migration is overdue before the silent failure occurs.
3. **Structural rule**: Add to /secretary STRICT RULES: "Phase 2 view_file path must always target a payload (`core.md`), not a pointer root file. Before invoking /document, verify the path ends in `/core.md` or the file is confirmed monolithic and under 10,000 bytes."

## 5. Recommendation to Senior Architect

The suite-wide pattern of hard-coding sub-workflow paths without a payload-awareness check will repeat this failure for every workflow that calls another workflow directly via `view_file`. A governance rule should be established: any workflow that triggers another workflow via `view_file` must reference the **payload** path (`/name/core.md`), not the pointer root. This prevents the entire class of ghost-dependency breaks during future Pointer/Payload migrations and should be codified as a STRICT RULE in `/harden-workflow`.

---
**Status**: **OPEN**
**Verification**: Resolved when /document is migrated and secretary/core.md:L132 is updated to `view_file /home/jwils/.gemini/antigravity/global_workflows/document/core.md`, confirmed by reading the updated line.

---
*Signed,*
**Sovereign Depreciate + Investigate Joint Audit Agent**
*(Forensic Audit — global_workflows substrate, 2026-05-12)*

---

## Addendum A — CONTRA-A: Phase 4 Overwrites HANDOFF.md Without Reading Prior Content
**Added**: 2026-05-12 | **Urgency elevation**: MEDIUM → HIGH | **Audit**: /investigate + /depreciate joint lens

**Finding**: STRICT RULE 3 states "Prior content is NOT archived unless it contains anomalies not in ANOMALY_LOG.md." This conditional requires reading the prior HANDOFF.md before overwriting. Phase 4 contains no such read step — it issues the overwrite unconditionally. The conditional in the STRICT RULE is structurally unenforceable: the data needed to evaluate the exception is destroyed in the act of overwriting.

**Forensic citations**:
- [secretary/core.md:L208](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L208) — Phase 4 overwrite note: "The prior HANDOFF is not archived unless it contains anomalies not yet in ANOMALY_LOG.md."
- [secretary/core.md:L292-L293](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L292-L293) — STRICT RULE 3: "HANDOFF.md is overwritten each session. Prior content is NOT archived unless it contains anomalies not in ANOMALY_LOG.md."

**Remediation**: Insert a Phase 4 pre-flight step: read prior HANDOFF.md, scan for any anomaly language (STRICT RULE override, MISMATCH accepted, workflow skipped) not present in ANOMALY_LOG.md. If found, append to ANOMALY_LOG.md first. Then overwrite. Alternative: adopt HANDOFF Archive pattern (Divergence D2 — see below).

---

## Addendum B — CONTRA-B: Suite Health Score Is Architecturally Stale in Phase 7
**Added**: 2026-05-12 | **Urgency**: MEDIUM | **Audit**: /depreciate lens

**Finding**: STRICT RULE 9 mandates the Suite Health Score be calculated from "actual live file reads." WORKFLOW_MANIFEST.md is read in Phase 1. The Secretary Receipt emitting the score is Phase 7 — six phases and potentially significant execution time later. If any workflow was hardened during the same session after Phase 1 ran, the emitted score reflects pre-hardening state. The rule is unenforceable without re-reading the manifest in Phase 7 immediately before emitting the receipt.

**Forensic citations**:
- [secretary/core.md:L298](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L298) — STRICT RULE 9 live read requirement.
- [secretary/core.md:L280](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L280) — Suite Health Score field in Phase 7 receipt.

**Remediation**: Add a Phase 7 sub-step: "Re-read WORKFLOW_MANIFEST.md Suite Health block immediately before emitting the receipt. Do not use the Phase 1 cached value."

---

## Addendum C — CONTRA-C: WORKFLOW_MANIFEST.md Existence Check Has No Fail-Safe Gate
**Added**: 2026-05-12 | **Urgency**: HIGH | **Audit**: /investigate + /depreciate lens

**Finding**: Phase 1 has three conditional branches for WORKFLOW_MANIFEST.md: (1) exists at correct path → targeted edit; (2) does not exist → write_to_file create; (3) exists at old path → migrate. There is no validation step between the existence check and the write decision. An agent that misidentifies the branch (fails to detect the file at the old path, or fails to read the manifest/ directory) will execute write_to_file against an existing file — silently discarding the entire workflow grade history. STRICT RULE 15 prohibits this but is enforced only by its own text.

**Forensic citations**:
- [secretary/core.md:L117-L121](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L117-L121) — Three-branch existence logic in Phase 1.
- [secretary/core.md:L303-L304](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L303-L304) — STRICT RULE 15 prohibition on full write_to_file.

**Remediation**: Add an explicit verification gate between existence check and write decision: run `ls /home/jwils/.gemini/antigravity/global_workflows/manifest/WORKFLOW_MANIFEST.md` and `ls /home/jwils/.gemini/antigravity/global_workflows/WORKFLOW_MANIFEST.md` as shell commands. Use exit codes to determine branch — not agent inference. Only proceed to write_to_file create if BOTH return non-zero (file absent at both paths).

---

## Addendum D — CONTRA-D: ANOMALY_LOG.md Missing Atomic-Append Enforcement
**Added**: 2026-05-12 | **Urgency**: HIGH | **Audit**: /investigate lens

**Finding**: STRICT RULE 4 declares ANOMALY_LOG.md append-only. Phase 5 says "Append entries (or create the file if absent)." But Phase 5 contains NO atomic-append mandate — no `cat >>` requirement, no prohibition on write_to_file Overwrite:true. This is the identical failure mode that burned /retrospective's PROCESS_LEARNINGS.md (documented in retrospective/core.md STRICT RULE 9 and its Change Log entry 2). The retrospective's append-safety hardening was applied only to that workflow and was never backported to /secretary's ANOMALY_LOG.md despite the same structural risk.

**Forensic citations**:
- [secretary/core.md:L294](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L294) — STRICT RULE 4: "ANOMALY_LOG.md is append-only. Never rewrite or remove entries."
- [retrospective/core.md:L210](file:///home/jwils/.gemini/antigravity/global_workflows/retrospective/core.md#L210) — The atomic-append mandate that /secretary is missing: "Use shell-level redirection (cat >>) via run_command for all appends — never use write_to_file with Overwrite: true."
- [retrospective/core.md:L252](file:///home/jwils/.gemini/antigravity/global_workflows/retrospective/core.md#L252) — Change Log entry documenting the exact failure mode this rule was built to prevent.

**Remediation**: Inject into Phase 5 of /secretary/core.md: "Use shell-level redirection (`cat >>`) via run_command for all appends to ANOMALY_LOG.md. Never use write_to_file with Overwrite:true for this file. Add as STRICT RULE 16." Mirror the exact language from retrospective/core.md STRICT RULE 9.

---

## Addendum E — Phase 6 Sub-Workflow Confirmation Has No Machine-Readable Enforcement
**Added**: 2026-05-12 | **Urgency**: MEDIUM | **Audit**: /investigate lens

**Finding**: Phase 6 requires "confirmation that the append succeeded" before proceeding to Phase 7. The confirmation mechanism is prose-based — the agent reads /retrospective's chat output and decides. STRICT RULE 13 mandates all six phases be confirmed before the receipt is emitted, but the confirmation mechanism for Phase 6 is behavioral, not structural. Under context pressure or if /retrospective's output is partial, the agent may declare confirmation received incorrectly, producing a Secretary Receipt that claims a complete /retrospective entry when none exists.

**Forensic citations**:
- [secretary/core.md:L253](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L253) — "Receive confirmation that the append succeeded."
- [secretary/core.md:L302](file:///home/jwils/.gemini/antigravity/global_workflows/secretary/core.md#L302) — STRICT RULE 13: all phases confirmed before receipt.

**Remediation**: After /retrospective Phase 5 appends to PROCESS_LEARNINGS.md, /secretary should run an independent verification: `tail -n 10 /home/jwils/.gemini/antigravity/global_workflows/process_learnings/PROCESS_LEARNINGS.md` and confirm the new entry date matches the current session date. This replaces prose-based confirmation with a deterministic file verification.

---

## Divergence Surface — Orthogonal Improvement Vectors
**Added**: 2026-05-12 | **Audit**: /divergence lens

Five ideas orthogonal to the current failure frame (none are remediation items — they are architectural opportunities):

- **D1 — Zero-Input Mode**: Derive session scope autonomously from prior HANDOFF.md + git log + conversation context. Eliminates Phase 0 ambiguity loop.
- **D2 — HANDOFF Rolling Archive**: `HANDOFF_ARCHIVE/HANDOFF_YYYYMMDD.md` preserves every session's handoff. Eliminates CONTRA-A entirely. The live HANDOFF.md is always current; nothing is ever destroyed.
- **D3 — Sub-Workflow Fidelity Tokens**: Each triggered sub-workflow emits a machine-readable `SECRETARY_TOKEN: COMPLETE|phase=N|...` as its final line. /secretary parses deterministically instead of relying on prose output.
- **D4 — Incremental Manifest Diff**: Scan only workflows modified since last /secretary run (checksum or mtime comparison). Eliminates full-scan overhead and the three-branch existence problem.
- **D5 — Anomaly Severity Escalation**: Tier ANOMALY_LOG.md entries (LOW/MEDIUM/HIGH/CRITICAL). Auto-file /helpdesk-tickets when CRITICAL anomaly is logged. Closes the loop between anomaly detection and formal incident response.

---
**Updated Status**: **OPEN** — 6 findings total (1 original + 5 addenda). Urgency elevated to HIGH due to ANOMALY_LOG.md overwrite risk (Addendum D) and WORKFLOW_MANIFEST.md fail-safe gap (Addendum C).
**Next action for /harden-workflow --ticket**: Consume all addenda in sequence. Addendum D (atomic-append) is the highest-urgency injection — it mirrors an already-solved problem in /retrospective and is a copy-paste hardening.

---
**Status**: **REMEDIATED**
**Closed**: 2026-05-15
**Changes Made**:
- Phase 1: Addendum C — shell `ls` exit-code gate replaces inference-based WORKFLOW_MANIFEST.md branch decision.
- Phase 4: Addendum A — grep-based pre-flight scan of prior HANDOFF.md before overwrite. Unlogged anomaly language rescued to ANOMALY_LOG.md before HANDOFF is superseded.
- Phase 5: Addendum D — all ANOMALY_LOG.md writes converted to `cat >>` atomic-append via run_command. write_to_file Overwrite:true explicitly prohibited.
- Phase 6: Addendum E — `tail -n 10` of PROCESS_LEARNINGS.md with session-date match check replaces prose-based /retrospective confirmation.
- Phase 7: Addendum B — `tail -n 30` of WORKFLOW_MANIFEST.md re-read gate injected immediately before Suite Health Score is emitted. Eliminates Phase 1 cache staleness.
- STRICT RULE 17: Added atomic-append mandate for ANOMALY_LOG.md, mirroring retrospective/core.md STRICT RULE 9.
- Change Log entry 5 appended.
- Divergences D1-D5 deferred (architectural improvements, not correctness fixes).
