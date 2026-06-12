# Helpdesk Ticket: /focus-plan — Instructional-Only Enforcement of the Suite's Highest-Stakes Verification Gate (Structural Gap), plus Two Reproducible Decay Defects

**To**: Senior Architect of Workflows
**From**: /investigate session (Opus 4.8) — Intent/Plan/Substrate hardenability investigation
**Date**: 2026-06-02
**Subject**: /focus-plan defends its core guarantee (that verification actually happened) with its weakest available mechanism — instruction — causing capable models to bypass it; compounded by a filename mismatch that misroutes plan discovery and a STRICT RULE that mandates a file that is never created.
**Urgency**: HIGH

---

## 1. Executive Summary

`/focus-plan` is the blocking pre-gate before `/execute-build` — the most consequential verification point in the Sovereign Suite. Its entire architecture (Anchor Manifests, SEARCH EVIDENCE blocks, the per-item Triad ceremony) exists to defeat **Hallucinated Success**: an agent claiming it searched the substrate when it did not. The investigation found that this guarantee is enforced *instructionally only* — the workflow asks the agent to be honest (STRICT RULE 12) rather than making dishonesty structurally impossible. A capable model (Opus 4.8) correctly perceives the per-item ceremony as overhead it can produce natively, and routes around the workflow entirely. Two concrete decay defects make literal compliance actively misfire and reinforce the bypass instinct: (a) Phase 0's primary plan lookup names `implementation_plan.md` (underscore) while the suite's own generator and the real artifact use `implementation-plan.md` (hyphen); (b) STRICT RULE 13 mandates maintaining `manifest/FOCUS-MEMORY-LEDGER.md`, a file that has never been created.

## 2. Root Cause Analysis: "Instructional Enforcement of an Architectural Guarantee (Structural Gap)"

**Failure class:** Structural Gap, with a latent **Hallucinated Success** exposure and a self-contradiction that trains agents to ignore STRICT RULES.

- **The How**: The workflow conflates a *gate* (prove Intent/Plan/Substrate align; surface what the plan forgot) with a *ceremony* (for every item, hand-write an Anchor Manifest → SEARCH EVIDENCE block → Triad Table). The ceremony was a scaffold to force weaker models to show their work. A strong model produces the *outcome* of the ceremony without its *form*, so it skips the workflow. Meanwhile the mechanical evidence-gathering — the part most prone to Hallucinated Success — is left to the same agent the evidence is meant to police, guarded only by a sentence asking it not to fabricate (STRICT RULE 12).
- **The Why**: The workflow did not externalize its evidence-gathering into a deterministic tool. It relies on the agent to both *gather* and *attest to* the evidence, which is the weakest possible enforcement model — the `/investigate` Mute Witness Protocol itself states that instructional enforcement is weaker than architectural enforcement. The suite already applies architectural enforcement to a *lower*-stakes workflow (`/sentinel` is backed by `doorway.py`), but never applied it to its *highest*-stakes gate. Step 0 additionally lacked a single canonical plan filename, and STRICT RULE 13 lacked any mechanism (or `file_write` capability) to actually create the ledger it mandates.

## 3. Forensic Evidence

- **Primary plan lookup names a file the suite never produces**: [focus-plan Phase 0, underscore](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L74)
  *Evidence: Phase 0 priority-1 lookup is `implementation_plan.md` (underscore); a literal executor finds nothing and silently degrades to conversation-reconstruction.*
- **The workflow contradicts itself on the filename**: [frontmatter `consumes`, hyphen](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L21)
  *Evidence: The frontmatter declares it consumes `implementation-plan.md` (hyphen) while the body uses underscore in 8 places — the file disagrees with itself.*
- **The real artifact uses the hyphen spelling**: [implementation-plan.md in workspace root](file:///home/jwils/blueprint-workflows/implementation-plan.md#L1)
  *Evidence: `/implementation-plan` writes the hyphen form (its Phase 6e + `produces:`); the actual plan on disk is `implementation-plan.md`. Phase 0's underscore lookup misses it deterministically.*
- **A STRICT RULE mandates a file that does not exist**: [STRICT RULE 13](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L293)
  *Evidence: "maintain the Suite Memory Ledger ... now core responsibilities." `ls manifest/FOCUS-MEMORY-LEDGER.md` → file absent. Either the Final Review never completes, or the rule is silently skipped every run — training agents that STRICT RULES are optional.*
- **The core guarantee is enforced by instruction only**: [STRICT RULE 12](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L292)
  *Evidence: "SEARCH EVIDENCE must reflect live command execution, not reconstructed output." This is the only thing standing between the workflow and Hallucinated Success — a request, not a structural barrier.*
- **The suite's own proven architectural pattern, never applied here**: [sentinel.md invokes doorway.py](file:///home/jwils/blueprint-workflows/claude-commands/sentinel.md#L95), [read-only by construction](file:///home/jwils/blueprint-workflows/claude-commands/sentinel.md#L47)
  *Evidence: `/sentinel` delegates mechanical scanning to a deterministic, read-only script and reasons over its structured output. `/focus-plan` — higher stakes — has no such backing.*

## 4. Remediation: "Option D — Script-Backed Triad Verification (Deterministic Evidence + Judgment Layer)"

Applied in the same session as this ticket:

1. Built `scripts/focus/` — a deterministic, **architecturally read-only** verifier (modeled on `scripts/doorway/`) that locates the plan (canonical hyphen, underscore tolerated), parses it into items + anchors, greps the substrate for each anchor (excluding test/mock/fixture paths to defeat the Mock Trap), and emits a structured JSON evidence report. Because a script gathers the evidence, the agent cannot hallucinate it — the anti-Hallucinated-Success guarantee becomes structural.
2. Re-hardened `claude-commands/focus-plan.md` to a thin judgment layer that consumes the script's JSON and performs only what a model uniquely can: intent interpretation, the Negative Space Scan, and the HALT/PROCEED gate. The old per-item ceremony is preserved (not deleted, per `/nodelete`) as the documented **Manual Fallback Mode** for when the script is unavailable. Filename canonicalized to hyphen; STRICT RULE 13 ledger contradiction resolved; `phase_count` corrected.
3. Added `scripts/tests/test_focus.py` (unittest) covering plan location, parsing, anchor verification, Mock-Trap test-path exclusion, and a read-only invariant assertion. Verified via `scripts/run_tests.sh` and a live run against this workspace's real `implementation-plan.md`.

## 5. Recommendation to Senior Architect

Adopt **"prescribe the evidence standard and the gate, not the keystrokes"** as a suite-wide hardening principle. The form/function mismatch found here is not unique to `/focus-plan` — the same prescribed-ceremony pattern runs through `/execute-build`, `/iterate-test`, and `/redteam`. Where a guarantee matters (verification actually happened, a search was actually run), externalize the mechanical layer into a deterministic, read-only script and reserve the workflow `.md` for judgment. Instructional enforcement of a structural guarantee should be treated as a named anti-pattern in `/harden-workflow`. Separately, the underscore/hyphen plan-filename drift spans nine workflow files; consider a dedicated suite-wide normalization ticket so the canonical-name fix is not limited to `/focus-plan`.

---
**Status**: **REMEDIATED (Option D — script-backed Focus Evidence Engine + v3 thin-judgment focus-plan.md)**
**Verification**: `scripts/focus/` passes 18/18 unittests (`run_tests.sh`); live run located `implementation-plan.md` (hyphen — the exact file the old underscore lookup missed), extracted 18 anchors, verified each against substrate with citations, confirmed read-only (no `.focus/` written); `focus-plan.md` lints CLEAN (0 CRITICAL, 0 WARNING). Filename, phantom-ledger, and `phase_count` defects fixed. Same-session closure by creating agent per /helpdesk-tickets Phase 4.

---
*Signed,*
**Sovereign Crime Scene Investigator (Opus 4.8)**
*(/investigate session, acting as Senior Architect of Workflows)*
