# Helpdesk Ticket: /harden — Grade Computed by Judgment, Not from Findings (Grade Fraud, Structural)

**To**: Senior Architect of Workflows
**From**: /implementation-plan session (Opus 4.8) — Verification-Spine Campaign, /harden upgrade (QUEUE #1)
**Date**: 2026-06-02
**Subject**: /harden's Hardening Grade is *defined* as a deterministic function of finding-severity counts, but is *rendered by agent judgment* with no mechanical detection of the signatures that define it. A grade so produced can be asserted without the scan that would cap it — the textbook Grade Fraud surface. The same deterministic checklist items (dynamic exec, the `shell`-True kwarg, hardcoded secrets, disabled TLS, unsafe deserialization, world-writable perms) are enforced by "state PASS/FINDING/N/A" prose only.
**Urgency**: HIGH

---

## 1. Executive Summary

`/harden` is a security workflow whose threat modeling, exploitability adjudication, and Sound-Effect-Execution reasoning are irreducible judgment and must stay in the model. But its terminal artifact — the **Hardening Grade** (Diamond/Gold/Silver/Bronze) that `/receipt-check` reads as the project's security-coverage signal — is *explicitly defined as a computation over finding counts* (`harden.md:196–203`): Diamond requires 0 CRITICAL/HIGH/MEDIUM; Gold ≤2 MEDIUM; Silver ≤2 HIGH; Bronze = CRITICAL resolved. A function with a closed-form definition is being evaluated by hand. Nothing in the workflow mechanically detects the very signatures that determine the grade, and nothing prevents an agent from certifying **Diamond** over a file that still contains a `shell`-True subprocess call. Certifying a grade whose structural criteria were never mechanically verified is the named pattern **Grade Fraud** (role.md:124).

## 2. Root Cause Analysis: "Instructional Enforcement of a Computable Grade (Grade Fraud surface)"

**Failure class:** Grade Fraud, with latent Hallucinated Success (a grade asserted without the scan that backs it) and Sound Effect Execution exposure (a security control present but never confirmed reached).

- **The How**: Phase 2c instructs the agent to run a 19-item checklist and "explicitly state PASS / FINDING / N/A" for each (`harden.md:123`), then Phase 2f maps remaining finding severities to a grade (`:196–203`). Both the detection *and* the grade are produced by prose instruction. The Phase-0 credential scan is specified as a shell `grep` the agent is told to run and "note every match" (`:79–86`) — with nothing verifying it executed (Hallucinated Success exposure, identical in class to /focus-plan's pre-v3 SEARCH EVIDENCE).
- **The Why**: The workflow never externalized the *deterministic half* of its checklist into a tool, even though many items are exact regex signatures and STRICT RULES 7–8 already treat two of them as absolutes ("never disable SSL/TLS verification," `:300`; "never use the `shell`-True kwarg ... always flag as CRITICAL," `:301`). The suite's own Mute Witness principle (architectural enforcement > instructional), already realized in `scripts/focus/` and `scripts/quality/`, was not applied to its highest-stakes security artifact.

## 3. Forensic Evidence

- **A computable grade evaluated by hand**: [Phase 2f grade table](file:///home/jwils/blueprint-workflows/claude-commands/harden.md#L196)
  *Evidence: the grade is a pure function of CRITICAL/HIGH/MEDIUM counts (`:198–203`), yet it is assigned by the agent with no deterministic finding tally backing it.*
- **Deterministic detection enforced by prose**: [Phase 2c checklist](file:///home/jwils/blueprint-workflows/claude-commands/harden.md#L123)
  *Evidence: "For each category, explicitly state PASS / FINDING / N/A" — the dynamic-exec, secrets, TLS, deserialization, and world-writable items all have exact machine signatures but are checked by instruction.*
- **Absolute rules with regex signatures, instruction-only**: [STRICT RULES 7–8](file:///home/jwils/blueprint-workflows/claude-commands/harden.md#L300)
  *Evidence: SSL-verification-disabled and the `shell`-True kwarg are declared absolute/always-CRITICAL — both are one-line regex matches, neither is mechanically gated.*
- **Unverified Phase-0 credential scan**: [Cross-Workspace Credential Scan](file:///home/jwils/blueprint-workflows/claude-commands/harden.md#L79)
  *Evidence: a `grep` the agent is told to run and "note every match"; nothing confirms execution or completeness (Hallucinated Success surface).*
- **The suite's own proven pattern, not yet applied here**: [focus-plan v3 EXECUTION MODEL](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L86)
  *Evidence: a read-only engine gathers the mechanical evidence so the agent cannot hallucinate it; /harden's grade has no such backing.*

## 4. Remediation: "Script-Backed Hardening Evidence Engine + Deterministic Grade Ceiling"

Applied in the same session (Verification-Spine Campaign recipe):

1. Build `scripts/harden/` — a **read-only** Hardening Evidence Engine (doorway/focus/quality-modeled): a **CWE Scanner** (deterministic signatures for dynamic exec, the `shell`-True kwarg, `os.system`, hardcoded secrets, unsafe deserialization, disabled TLS, weak crypto, world-writable perms, insecure temp files), a heuristic **Threat Classifier** (advisory only), and a **Grade Computer** that computes a deterministic **grade *ceiling*** from real findings. It detects the mechanical items and **caps** the grade; it never certifies a positive grade and never assesses excellence — that stays the agent's judgment.
2. The **one-directional honesty boundary** (the anti-Mock-Trap / anti-Grade-Fraud core): a CRITICAL signature *forbids* Diamond/Gold/Silver; but a clean scan (`ceiling = Diamond`) says **nothing** about whether the file deserves Diamond. The agent still runs the threat model, exploitability adjudication, and Sound-Effect-Execution check, and assigns the final grade **at or below** the engine's ceiling. Reading a clean ceiling as a Diamond certification *is* the Grade Fraud — disclaimed loudly in code, schema, and the workflow.
3. Re-harden `harden.md` to v3: a thin engine-backed EXECUTION MODEL consuming the report; the deterministic checklist items gated by the scanner; the grade computed-then-adjudicated; every judgment step (threat model, iterative fixing, regression check, /nodelete fixing discipline) preserved verbatim per /nodelete.
4. Wire the deterministic signal into `/triage` (a real `harden_audit.py` call mirroring the existing `lint_workflows.py --quiet` P0 precedent — CRITICAL/HIGH findings in scripts lacking a current grade promote the /harden recommendation from receipt-existence to actual-finding evidence).
5. Add `scripts/tests/test_harden.py` (unittest) incl. a read-only invariant, CWE-detection cases, grade-ceiling cases, and a documentation-mention negative control; verify via `run_tests.sh` + live run + CLEAN lint.

## 5. Recommendation to Senior Architect

Extend the campaign principle established by the /focus-plan and /quality tickets — **prescribe the evidence standard and verify it structurally, not by instruction** — with the corollary this ticket proves: **where a workflow's terminal artifact is a grade with a closed-form definition over findings, the findings and the grade computation must be deterministic; the engine computes the *ceiling*, the model adjudicates beneath it. Never let a clean scan read as a positive certification — that is Grade Fraud wearing the mask of a passing test.** Register "instructional enforcement of a computable grade" alongside "instructional enforcement of a verification/anti-trust artifact" in `/harden-workflow`.

---
**Status**: **REMEDIATED (Hardening Evidence Engine + deterministic Grade Ceiling + v3 engine-backed EXECUTION MODEL + /triage deterministic-call wiring)**
**Verification**: `scripts/harden/` passes 33/33 unittests (incl. the read-only invariant, the grade-ceiling one-directional contract, and the documentation-mention / test-path / placeholder-secret false-positive guards); the full suite shows only the known unrelated `test_core.test_import_patterns_python` failure; the live run flagged 2 genuine `shell`-True CRITICALs (`scripts/workstream/verify.py:54`, `scripts/core/git_ops.py:110`) — files prior instruction-based hardening had left — now correctly capped at UNGRADED, with zero false positives, and confirmed read-only (clean `git status`); `harden.md` and `triage.md` both lint CLEAN (0 CRITICAL, 0 WARNING). The Grade-Fraud surface is closed: the grade now carries a deterministic ceiling the agent cannot certify above, while the judgment core (threat model, Sound-Effect-Execution, iterative fixing, regression check) is preserved verbatim per /nodelete. Same-session closure by the creating agent per /helpdesk-tickets Phase 4.

---
*Signed,*
**Sovereign Implementation Architect (Opus 4.8)**
*(/implementation-plan session, acting as Senior Architect of Workflows)*
