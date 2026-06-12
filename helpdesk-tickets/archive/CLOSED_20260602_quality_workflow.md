# Helpdesk Ticket: /quality — Trust-Enforced Quality Process Receipts (Structural Gap), plus a Self-Description Contradiction

**To**: Senior Architect of Workflows
**From**: /implementation-plan session (Opus 4.8) — /quality Option-F upgrade
**Date**: 2026-06-02
**Subject**: /quality's cross-agent anti-trust mechanism (Quality Chain Tag) and its diagnostic ledger (Quality Witness) are enforced by instruction only — nothing verifies they were produced or are well-formed; HOW TO BEGIN miscounts its own STRICT RULES (11 vs 14).
**Urgency**: HIGH

---

## 1. Executive Summary

`/quality` is a behavioral modifier whose seven judgment steps cannot and should not be scripted. But it also emits two **process-evidence artifacts** — the Quality Witness log (a diagnostic ledger) and the Quality Chain Tag (a cross-agent trust token) — whose entire purpose is verification *without trusting the producing agent*. The investigation found that both are enforced **by instruction only**: the workflow tells the producing agent to emit them and tells the receiving agent it "should note" if a tag is missing, but nothing deterministic ever validates that a witness line was written, that it is well-formed, or that a chain tag is complete. An anti-trust mechanism guarded by trust is not an anti-trust mechanism. Separately, HOW TO BEGIN instructs the agent to internalize "all 11 STRICT RULES" when there are 14 — a self-description contradiction of the same class as /focus-plan's `phase_count: 0`.

## 2. Root Cause Analysis: "Instructional Enforcement of a Verification Substrate (Structural Gap)"

**Failure class:** Structural Gap, with a latent Hallucinated-Success exposure (a producer can *claim* quality protocol application that left no valid receipt) and a self-description contradiction.

- **The How**: `/quality` produces the witness log and chain tag write-side, then delegates their *verification* to prose — "the receiving agent should note that quality protocol application is UNVERIFIED" and "/triage monitors the log." No parser, no validator, no count. The producing agent must also remember to append a precisely-formatted witness line after every single output, with nothing checking compliance — maximal Context-Erosion exposure.
- **The Why**: The workflow did not externalize the deterministic half of its observability into a tool. As with /focus-plan before its v3 upgrade, the suite's own Mute Witness principle (architectural enforcement > instructional) was never applied here, even though a lower-stakes workflow (/sentinel) is already script-backed by doorway.py. The "monitors the log" integration (`quality.md:300`) names no mechanism.

## 3. Forensic Evidence

- **Anti-trust mechanism enforced by trust**: [Chain Tag purpose vs. verification](file:///home/jwils/blueprint-workflows/claude-commands/quality.md#L45)
  *Evidence: the tag exists so a receiver can "verify quality protocol application without trusting the producing agent's claim" — but verification is only "should note ... UNVERIFIED" (`:234`). Trust guarding an anti-trust device.*
- **Mandatory-but-unverified ledger append**: [STRICT RULE 14](file:///home/jwils/blueprint-workflows/claude-commands/quality.md#L266)
  *Evidence: "mandatory when the directory exists" with no validation that the line was written or well-formed; the agent must remember it every output (`:236-244`).*
- **Vague, mechanism-free monitoring**: [INTEGRATION — /triage monitors the log](file:///home/jwils/blueprint-workflows/claude-commands/quality.md#L300)
  *Evidence: "/triage Monitors `.workflow_state/quality_witness.log` for accumulated unreviewed entries (25+ → P3)" — but "unreviewed" is undefined and no parser exists.*
- **Self-description contradiction (11 vs 14)**: [HOW TO BEGIN](file:///home/jwils/blueprint-workflows/claude-commands/quality.md#L274)
  *Evidence: "Internalize all 7 steps and all 11 STRICT RULES" while the frontmatter declares `strict_rule_count: 14` (`:8`) and rules 1–14 are present.*
- **The suite's own proven pattern, never applied here**: [sentinel.md invokes doorway.py](file:///home/jwils/blueprint-workflows/claude-commands/sentinel.md#L95)
  *Evidence: deterministic, read-only script backs a lower-stakes workflow; /quality's process receipts have no such verifier.*

## 4. Remediation: "Option F — Script-Backed Quality Verification Rail + Cross-Workflow Wiring"

Applied in the same session (per HITL selection):

1. Built `scripts/quality/` — a **read-only** Quality Process Auditor (doorway-modeled): **Ledger Auditor** (parses/validates the witness log, computes `unreviewed` = entries after the last `[REVIEWED]` marker, raises the P3 trigger), **Chain-Tag Verifier** (`VALID/MALFORMED/ABSENT`), and **Anti-Pattern Smell Linter** (one-directional, advisory). It verifies the quality **process receipts and mechanical smells — never the quality itself** (that stays irreducible judgment in the model; scripting it would be a Mock Trap).
2. Re-hardened `quality.md` to v4: a thin Verification Rail consuming the engine; F4 (11→14) fixed; STRICT RULES 13/14 reframed so the tag/witness are verifiable rather than trust-only. The 7-step judgment core preserved verbatim per /nodelete.
3. Wired the engine into `/triage` (real deterministic call replacing "monitors the log") and `/receipt-check` (quality coverage dimension).
4. Added `scripts/tests/test_quality.py` (unittest) incl. a read-only invariant and the MRC fixture; verified via `run_tests.sh` + live run + CLEAN lint on all three edited workflows.

## 5. Recommendation to Senior Architect

Reaffirm the suite-wide principle from the /focus-plan ticket — **prescribe the evidence standard and verify it structurally, not by instruction** — and add its corollary discovered here: **where a guarantee is irreducible judgment (quality assessment), do NOT script the judgment; script the *process receipts* around it and keep the judgment in the model.** The anti-pattern to register in `/harden-workflow` is "instructional enforcement of a verification/anti-trust artifact." Also treat self-description fields (`strict_rule_count`, step/phase counts, "internalize all N rules" prose) as lint-checkable invariants so 11-vs-14 contradictions are caught mechanically.

---
**Status**: **REMEDIATED (Option F — Quality Process Auditor engine + v4 verification rail + /triage and /receipt-check wiring)**
**Verification**: `scripts/quality/` passes 19/19 unittests (incl. the read-only invariant and the Mock-Trap-guard assertion); live run audited the workspace witness path and validated tags/smells — a documentation-mention false-positive was caught and fixed mid-build; `quality.md`, `triage.md`, `receipt-check.md` all lint CLEAN (0 CRITICAL, 0 WARNING). The five defects (F1–F5) are addressed; the 7-step judgment core preserved per /nodelete. Same-session closure by creating agent per /helpdesk-tickets Phase 4.

---
*Signed,*
**Sovereign Implementation Architect (Opus 4.8)**
*(/implementation-plan session, acting as Senior Architect of Workflows)*
