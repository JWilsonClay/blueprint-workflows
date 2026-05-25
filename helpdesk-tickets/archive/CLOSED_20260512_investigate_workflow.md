# Helpdesk Ticket: Critical Mutation Injection — /investigate Phase 4e Violates Its Own Zero-Mutation Mandate

**To**: Senior Architect of Workflows
**From**: Sovereign Investigate + Depreciate + Divergence Joint Audit Agent
**Date**: 2026-05-12
**Subject**: The 2026-05-12 Doorway hardening pass injected a write operation (Phase 4e: MRC-ORACLE.md) into a workflow whose foundational constraint is zero mutations — creating two confirmed internal contradictions and three structural gaps.
**Urgency**: CRITICAL (Architectural)

---

## 1. Executive Summary

`/investigate` is the suite's zero-mutation forensic workflow. Its foundational guarantee — "the crime scene is preserved" — is enforced by STRICT RULE 1 (zero mutations) and repeated in Phase 4's opening line ("No mutations"). The 2026-05-12 Doorway hardening pass injected Phase 4e, which explicitly writes `manifest/MRC-ORACLE.md` via `cat >>`. This single injection introduces two confirmed internal contradictions: it violates STRICT RULE 1 and contradicts Phase 4's own mutation-free declaration within the same numbered phase. Additionally, three structural gaps were identified: the Phase 4 user-confirmation gate has no enforcement mechanism, the Doorway patrol severity threshold is undefined, and the MRC handoff artifact is ephemeral (written to `/tmp`), making it unavailable to downstream workflows in subsequent sessions.

## 2. Root Cause Analysis: "Mutation Injection Into Zero-Mutation Workflow"

**Failure class**: Structural Contradiction / Injected Breaking Change

- **The How**: Phase 4e [INJECTED 2026-05-12] directs: "store it (append-only) in `manifest/MRC-ORACLE.md`." This is a `cat >>` append to a workspace file during Phase 4, which declares itself mutation-free and is governed by STRICT RULE 1.
- **The Why**: The Doorway integration pass (MRC Oracle, Autonomous Patrol, DNA Registry) was designed to extend `/investigate` with persistent memory capabilities. The MRC Oracle storage step requires persistence — which requires a write. The injection was made without reconciling the write requirement against the zero-mutation architecture. The result is a workflow that promises "crime scene preservation" but executes a write to `manifest/MRC-ORACLE.md` during every investigation that produces an MRC.

## 3. Forensic Evidence

- **[CONTRA-A: Phase 4e write vs. STRICT RULE 1]**: [investigate/core.md:L300-L302](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L300-L302)
  *Evidence: "store it (append-only) in manifest/MRC-ORACLE.md keyed by Doorway drift signature" — explicit write instruction during a zero-mutation phase.*

- **[CONTRA-A: STRICT RULE 1 prohibition]**: [investigate/core.md:L308](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L308)
  *Evidence: "No code files, config files, log files, workflow files, or any other workspace file may be modified during this workflow." — MRC-ORACLE.md is a workspace file. Direct contradiction.*

- **[CONTRA-B: Phase 4 self-declares mutation-free then writes a file]**: [investigate/core.md:L244-L245](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L244-L245)
  *Evidence: "This phase is a discussion, not an implementation. No mutations." — Phase 4e (three steps later in the same phase) writes MRC-ORACLE.md. The contradiction is self-contained within Phase 4.*

- **[F1: Phase 4 confirmation gate — behavioral not structural]**: [investigate/core.md:L233-L237](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L233-L237)
  *Evidence: Agent asks "Does this match what you were seeing?" and proceeds when it decides the answer is confirmatory. No HALT condition, no structural gate, no machine-readable confirmation token.*

- **[CONTRA-C: STRICT RULE 12 "always" + "when available" with no fallback]**: [investigate/core.md:L320](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L320)
  *Evidence: "Always consume the latest Doorway drift report when available." — 'always' and 'when available' are contradictory without a defined fallback for when Doorway data is absent.*

## 4. Remediation: Relocate MRC Oracle Write Responsibility

The MRC Oracle is valuable. The write must be relocated, not removed.

1. **Immediate (CONTRA-A/B)**: Remove the write directive from Phase 4e. Replace with: "If `/sentinel` or the invoking workflow has write access, pass the MRC to them for Oracle storage. `/investigate` itself does not write. The MRC is presented to the user for copying or forwarding to the next workflow." This preserves zero-mutation and keeps the Oracle concept.
2. **Structural (CONTRA-A/B)**: Designate `/sentinel` as the MRC Oracle writer. `/sentinel` already writes to `manifest/` and `.doorway/`. Add to `/sentinel/core.md`: "If an MRC was produced by `/investigate` in this session, append it to `manifest/MRC-ORACLE.md`."
3. **Phase 4 Gate (F1)**: Add a confirmation token protocol: after the Investigation Report, require the user to respond with `UNDERSTOOD`, `CLARIFY: [question]`, or `REDIRECT: [new scope]` before Phase 4 unlocks. Free-text confirmation remains valid; the token is an additional recognized pattern that triggers automatic gate passage.
4. **STRICT RULE 12 (CONTRA-C)**: Replace "when available" with: "If no Doorway drift report is found at `{workspace}/.doorway/`: log `DOORWAY: ABSENT — patrol mode skipped` in the Crime Scene Scope block and proceed with standard evidence collection." Explicit named fallback.
5. **F2 (Doorway paths with no HALT)**: Add HALT conditions to Phases 1d, 2d: "If `{workspace}/.doorway/` does not exist: skip this phase, log DOORWAY: ABSENT, continue to next phase."

## 5. Recommendation to Senior Architect

The zero-mutation guarantee is `/investigate`'s primary value proposition — it is what makes it safe to invoke autonomously, at scale, without human oversight. **Any injection that introduces a write operation into this workflow must be treated as a breaking architectural change**, regardless of how small the write is. A new STRICT RULE should be added to `/harden-workflow`'s injection protocol: "Before injecting into `/investigate`, verify the injection does not contain any write, append, rename, or delete operation. A mutation-containing injection into a zero-mutation workflow requires architectural review and relocation of the write to a mutation-permitted caller workflow." This prevents any future injection from repeating the CONTRA-A/B failure.

---

## Addendum — CONTRA-D: Differential Format Implies Multiple Entries But Escape Clause Permits One
**Urgency**: MEDIUM

**Finding**: Phase 2b states "generate 2–4 competing explanations" and provides a template with Hypothesis A, B, C slots. It also says "Do not fabricate hypotheses to fill the format. If there is genuinely only one plausible cause: state one hypothesis." The format implies three named slots; the escape permits one. An agent producing a one-entry Differential will leave Hypothesis B and C slots empty — creating a structurally incomplete-looking report that may be misread as an incomplete investigation.

**Forensic citations**:
- [investigate/core.md:L136-L138](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L136-L138) — "2–4 competing explanations" requirement.
- [investigate/core.md:L158](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L158) — "If genuinely only one plausible cause: state one hypothesis" escape.

**Remediation**: Update the Differential format to make the slot count dynamic: `Hypothesis [A through D as evidence supports]:` with a note that "single-hypothesis differentials are valid when alternatives are structurally impossible — state why they are impossible in a single sentence." Remove the rigid A/B/C labeling.

---

## Addendum — F3/F4/F5: Patrol Severity Undefined + Evidence Chain Scale Mismatch + Ephemeral MRC Handoff
**Urgency**: HIGH

**F3 — Patrol severity threshold undefined**: Phase 1d says "Notify user only on HIGH-severity findings" in patrol mode. HIGH-severity is defined in `/sentinel/core.md` but not in `/investigate/core.md`. Coupling to an external definition with no local fallback.

**F4 — Evidence Chain scale mismatch**: Evidence Chain is mandatory format for all investigations regardless of scope. A 2-minute single-file investigation produces the same format requirements as a multi-day cross-system audit. STRICT RULE 8 acknowledges complexity scaling for "What it is NOT" — no equivalent scaling exists for the Evidence Chain.

**F5 — Ephemeral MRC handoff**: Phase 4a MRC is "written to a scratch file" (implying `/tmp`). Scratch files are ephemeral — gone between sessions. `/iterate-test` is named as the MRC consumer, but the MRC has no durable storage path (compounded by CONTRA-A removing the MRC-ORACLE write). The investigation-to-validation handoff is session-bound.

**Forensic citations**:
- [investigate/core.md:L115](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L115) — "Notify user only on HIGH-severity findings" — no local severity definition.
- [investigate/core.md:L218-L228](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L218-L228) — Evidence Chain mandatory format block.
- [investigate/core.md:L262](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L262) — "write to a scratch file, do not modify workspace" — ephemeral.
- [investigate/core.md:L270](file:///home/jwils/.gemini/antigravity/global_workflows/investigate/core.md#L270) — "/iterate-test uses the MRC directly" — but MRC is gone next session.

**Remediation**: (F3) Add a local severity definition or explicit cross-reference to `/sentinel/core.md` severity tiers. (F4) Add a scope-tiered format note: "For QUICK investigations (single file, under 10 minutes): Evidence Chain may be abbreviated to file count only." (F5) Designate `/iterate-test` as the MRC persistence owner: "When invoked after `/investigate`, `/iterate-test` Phase 0d should ask for or receive the MRC and write it to `.workflow_state/MRC_LEDGER.md` via `cat >>`."

---

## Divergence Surface — Orthogonal Improvement Vectors
**Added**: 2026-05-12 | **Audit**: /divergence lens

- **D1 — Investigation Receipt (next-workflow writes, not /investigate)**: `/iterate-test` or `/harden-workflow` writes `INVESTIGATION_RECEIPT.md` upon receiving the Investigation Report. Keeps /investigate mutation-free while creating durable downstream artifact.
- **D2 — Scope-Tiered Format**: QUICK / STANDARD / DEEP tiers selected at Phase 0b. Evidence Chain and Differential scale with scope. Eliminates format-scope mismatch without removing structural elements.
- **D3 — MRC Oracle Ownership to /sentinel**: Sentinel already writes to `manifest/`. MRC-ORACLE becomes a Sentinel responsibility. /investigate reads it (zero-mutation preserved), Sentinel writes it.
- **D4 — Confirmation Token Protocol**: `UNDERSTOOD` / `CLARIFY: [q]` / `REDIRECT: [scope]` tokens recognized as explicit Phase 4 gate keys alongside free-text confirmation.
- **D5 — Severity Tier Governance File**: `global_workflows/governance/severity_tiers.md` shared by /sentinel and /investigate. Eliminates cross-workflow coupling for severity definitions.

---
**Status**: **OPEN**
**Urgency**: CRITICAL (Architectural) — Phase 4e mutation injection violates the workflow's zero-mutation foundational guarantee.
**Verification**: Resolved when (a) Phase 4e write directive is relocated to /sentinel, (b) STRICT RULE 1 and Phase 4 opening no longer contradict Phase 4e, (c) STRICT RULE 12 has an explicit named fallback for absent Doorway data.
**Next action for /harden-workflow --ticket**: CONTRA-A/B is a two-line fix in Phase 4e (remove the write, add "pass MRC to invoking workflow"). Highest-urgency injection in the current ticket queue — it is an active architectural violation in a currently-deployed workflow.

---
*Signed,*
**Sovereign Investigate + Depreciate + Divergence Joint Audit Agent**
*(Forensic Audit — /investigate substrate, 2026-05-12)*
