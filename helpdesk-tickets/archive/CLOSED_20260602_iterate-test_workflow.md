# Helpdesk Ticket: /iterate-test — The Mock-Trap Guarantee Is Enforced by Attestation, Not Detection (Mock Trap, Structural)

**To**: Senior Architect of Workflows
**From**: /implementation-plan session (Opus 4.8) — Verification-Spine Campaign, /iterate-test upgrade (QUEUE #2)
**Date**: 2026-06-02
**Subject**: /iterate-test is the suite's flagship **Mock Trap** workflow, yet its central guarantee — that a test reaches the real intelligence instead of a mock of it — rests on an *instructional* attestation. Step 4b (the Intelligence Bridge Declaration) asks the agent to self-declare each bridge as `HOT` or `MOCKED` and to issue a FIDELITY HALT if a PRIMARY bridge is MOCKED. Nothing mechanically reads the test file to confirm whether it actually imports and calls the production code it claims to validate, or only patches/mocks it. The same workflow that exists to prevent the Mock Trap can be satisfied by a declaration that is itself unverified — the textbook Hallucinated Success surface wrapped around the suite's most important fidelity check.
**Urgency**: HIGH

---

## 1. Executive Summary

`/iterate-test` was created out of the nelson_neighbor Phases 10/11 **Mock Trap** incident (`iterate-test.md#L417`): a test achieved a 100% pass rate by mocking the very intelligence it claimed to validate. The remedy was Step 4b — the **Intelligence Bridge Declaration** (`#L171`) — which mandates that, before any test code is written, the agent name every LLM/inference/model bridge, classify each as **PRIMARY** (the subject under test) or **INFRASTRUCTURE**, declare its execution mode **HOT** or **MOCKED**, and issue a **FIDELITY HALT** (`#L199`) if any PRIMARY bridge is MOCKED. STRICT RULE 13 (`#L372`) codifies this permanently, and STRICT RULE 10 (`#L369`) forbids asserting against hardcoded expected values.

Every one of these is enforced by **prose instruction the agent attests to**. The declaration block is hand-authored; the HALT is self-triggered; the "is this HOT or MOCKED?" determination is made by the agent looking at the code and reporting honestly. There is **no deterministic reader** of the test file that confirms the attestation is true — that the production module under test is actually imported and called un-patched, rather than replaced by `unittest.mock.patch`. A workflow whose entire reason for existing is to defeat the Mock Trap currently enforces that defeat with the same instructional model the suite has already replaced with engines in `/focus-plan` (v3), `/quality` (v4), and `/harden` (v3). This is the named pattern **Mock Trap** (role.md#L117), with a latent **Hallucinated Success** surface (role.md#L119): the agent can declare `HOT` over a test that mocks its subject, and nothing structural contradicts it.

## 2. Root Cause Analysis: "Instructional Enforcement of an Anti-Mock-Trap Artifact"

**Failure class:** Mock Trap (the guarantee), with Hallucinated Success exposure (an unverified `HOT` attestation) and Sound Effect Execution kinship (the plumbing around a mocked intelligence runs green while the intelligence is never reached).

- **The How**: Step 4b instructs the agent to emit a declaration block and self-classify each bridge `HOT`/`MOCKED` (`#L171–197`), then self-issue a FIDELITY HALT if a PRIMARY bridge is MOCKED (`#L199–218`). The determination is judgment-by-inspection with no mechanical backstop. Step 4g (`#L256`) and STRICT RULE 10 (`#L369`) likewise forbid hardcoded-value assertions by instruction only — the very `assert response == "..."` / `return_value`-echo signature that marks a tautological test is mechanically detectable but is left to the agent to catch.
- **The Why**: At creation (2026-05-08) and port (2026-05-21) the suite had no engine substrate. The deterministic half of the Mock-Trap check — *does this Python test import the production symbol and call it un-patched, or does it `patch()` it?* — is a static-analysis fact obtainable from the test file's AST without executing it. That half was never externalized. The suite's own Mute Witness principle (architectural enforcement > instruction), already realized in `scripts/focus/`, `scripts/quality/`, and `scripts/harden/`, was not applied to the workflow that needs it most.

## 3. Forensic Evidence

- **The anti-Mock-Trap artifact is an attestation**: [Step 4b — Intelligence Bridge Declaration](file:///home/jwils/blueprint-workflows/claude-commands/iterate-test.md#L171)
  *Evidence: "Emit the declaration block before writing any code" — the `HOT`/`MOCKED` and `PRIMARY`/`INFRASTRUCTURE` values are authored by the agent; nothing reads the test file to confirm them.*
- **The HALT is self-triggered**: [FIDELITY HALT](file:///home/jwils/blueprint-workflows/claude-commands/iterate-test.md#L199)
  *Evidence: "If any PRIMARY bridge is set to MOCKED: FIDELITY HALT" — the trigger depends on the agent having correctly (and honestly) declared MOCKED; a wrong or optimistic `HOT` declaration silently passes.*
- **The codified rule is instruction-only**: [STRICT RULE 13](file:///home/jwils/blueprint-workflows/claude-commands/iterate-test.md#L372)
  *Evidence: "Step 4b ... is mandatory and must be completed before any test code is written" — a mandate with no mechanical gate; identical in class to /focus-plan's pre-v3 SEARCH EVIDENCE and /harden's pre-v3 hand-run checklist.*
- **A mechanically-detectable deficiency left to instruction**: [Step 4g / STRICT RULE 10 — no hardcoded expected values](file:///home/jwils/blueprint-workflows/claude-commands/iterate-test.md#L256)
  *Evidence: "An assertion like `assert response == "I can help..."` is a hardcoded value — it is always a test deficiency." The `return_value`/`side_effect`-literal-echoed-in-assert tautology is an exact AST signature, but is checked by prose.*
- **The suite's own proven pattern, not yet applied here**: [harden v3 EXECUTION MODEL](file:///home/jwils/blueprint-workflows/claude-commands/harden.md#L72)
  *Evidence: a read-only engine gathers the mechanical evidence so the agent cannot hallucinate it; /iterate-test's Bridge Declaration has no such backing.*

## 4. Remediation: "Script-Backed Mock-Trap Detector + One-Directional Fidelity Signal"

Applied in the same session (Verification-Spine Campaign recipe):

1. Build `scripts/iterate/` — a **read-only**, **Python-first** Mock-Trap Detector (doorway/focus/quality/harden-modeled): a **`mock_analyzer`** that parses a test file's AST (no execution) and extracts its import set, the production symbols replaced by `patch`/`@patch`/`patch.object`/`mocker.patch`/`monkeypatch.setattr` (with the literal patch-target string), whether each patched symbol is ever *called un-patched* (live), the mock constructions, and the hardcoded-assertion tautology (`return_value`/`side_effect` literal echoed in an `assert ==`); a **`bridge_classifier`** that turns those facts into a per-file, one-directional **advisory** fidelity signal; a **`reporter`** (JSON + human); and an **`iterate_audit.py`** CLI (`--workspace`/`--test`/`--subject`/`--output-json`/`--quiet`). It reads the substrate and **writes nothing**. Reuses `scripts/focus/`'s `is_test_path` test-path classification.
2. The **one-directional honesty boundary** (the anti-Mock-Trap / anti-Hallucinated-Success core): the engine reports DETERMINISTIC FACTS — *symbol X is imported and its behavior is replaced by a mock; symbol Y is called live.* It does **not** decide whether a mocked symbol is the **PRIMARY intelligence** (a Mock Trap) or **INFRASTRUCTURE** (valid) — that classification is the agent's irreducible judgment (Step 4b), and scripting it would make the detector itself a Mock Trap. A finding (`MOCK_TRAP_CANDIDATE`) means *likely* trap pending the agent's PRIMARY/INFRASTRUCTURE call; a clean scan (`verdict_hint: NO_FINDINGS`) certifies **nothing** — a test that imports and calls live code can still be a tautology. Disclaimed loudly in code, schema, and the workflow.
3. Re-harden `iterate-test.md` to v3: inject an engine-backed **FIDELITY RAIL / EXECUTION MODEL** that runs the detector and feeds Step 4b with mechanical evidence the declaration can no longer contradict silently; preserve every judgment phase (re-contextualize, define goal, fail points, design/execute, repair, success gate) verbatim per /nodelete; add STRICT RULES for engine-preference and the one-directional boundary (1–13 untouched).
4. Wire the deterministic signal into `/triage` (a real `iterate_audit.py` call mirroring the existing `harden_audit.py --output-json` and `lint_workflows.py --quiet` precedents — a `MOCK_TRAP_CANDIDATE` in a test for a recently-built stage promotes the /iterate-test recommendation from receipt-absence to actual-finding evidence).
5. Add `scripts/tests/test_iterate.py` (unittest) incl. a read-only invariant, mock-trap detection cases, a live-call negative control, the hardcoded-assertion tautology case, and a non-Python-skip control; verify via `run_tests.sh` + live run + CLEAN lint.

## 5. Recommendation to Senior Architect

Extend the campaign principle — **prescribe the evidence standard and verify it structurally, not by instruction** — with the corollary this ticket proves: **where a workflow's terminal guarantee is an anti-trust / anti-fabrication artifact (a declaration that something was NOT faked), the artifact must be backed by a deterministic reader of the substrate; the engine supplies the mechanical facts the declaration asserts, the model still owns the irreducible classification, and a clean scan must never read as a fidelity certification — that reading is the Mock Trap wearing the mask of a passing declaration.** Register "instructional enforcement of an anti-Mock-Trap attestation" alongside the /focus-plan, /quality, and /harden entries in `/harden-workflow`.

---
**Status**: **REMEDIATED (Mock-Trap Detector engine + One-Directional Fidelity Signal + v3 engine-backed EXECUTION MODEL/Fidelity Rail + /triage deterministic-call wiring)**
**Verification**: `scripts/iterate/` passes 27/27 unittests (incl. the read-only invariant, the one-directional signal contract, the infrastructure-mock false-positive guard — mocking a dependency while the SUBJECT is called live is NOT flagged — and the `__init__.py`-exclusion regression); the full suite shows only the known unrelated `test_core.test_import_patterns_python` failure; the live run against this workspace analyzed 13 test files with 0 mock-trap candidates and 0 false positives (after an `__init__.py` package-marker exclusion fix surfaced by the live run), confirmed read-only (clean `git status`, no files written), and the JSON validates against `scripts/iterate/schema/iterate_report.schema.json`; `iterate-test.md` and `triage.md` both lint CLEAN (0 CRITICAL, 0 WARNING). The Mock-Trap surface is closed at the structural level: the Step-4b Intelligence Bridge Declaration is now reconciled against a read-only AST detector that cannot hallucinate the import/patch/call evidence (Mute Witness enforcement), while the irreducible PRIMARY-vs-INFRASTRUCTURE classification and the final fidelity verdict are preserved verbatim in the model per /nodelete (the engine never makes that call — scripting it would make the detector itself a Mock Trap). Same-session closure by the creating agent per /helpdesk-tickets Phase 4.

---
*Signed,*
**Sovereign Implementation Architect (Opus 4.8)**
*(/implementation-plan session, acting as Senior Architect of Workflows)*
