"""
iterate — Deterministic Mock-Trap Detector (read-only, Python-first)
=====================================================================
The mechanical verification rail behind the /iterate-test workflow.

/iterate-test exists to defeat the **Mock Trap**: a test that achieves a 100%
pass rate by mocking the very intelligence it claims to validate, proving only
that the mock works. Its remedy is the Step-4b Intelligence Bridge Declaration —
the agent attests, before writing test code, that each PRIMARY intelligence
bridge runs HOT (real) rather than MOCKED. Historically that attestation was
enforced by *instruction*: nothing read the test file to confirm it. An
unverified "HOT" declaration over a test that mocks its subject is Hallucinated
Success wrapped around the suite's most important fidelity check.

This package externalizes the deterministic half:

  * mock_analyzer     — parse a Python test file's AST (NO execution) and extract
    its import set, the production symbols replaced by patch()/@patch/patch.object
    /mocker.patch/monkeypatch.setattr (with the literal patch-target string),
    how often each imported symbol is called, the mock constructions, and the
    hardcoded-assertion tautology (a return_value/side_effect literal echoed in an
    `assert ==` — the workflow's own Step-4g / RULE-10 deficiency).
  * bridge_classifier — turn those facts into a per-file, one-directional ADVISORY
    fidelity signal.

⚠ THE ONE-DIRECTIONAL HONESTY BOUNDARY (anti-Mock-Trap / anti-Hallucinated-Success):
The engine reports DETERMINISTIC FACTS — *symbol X is imported and its behavior is
replaced by a mock; symbol Y is called un-patched.* It does NOT decide whether a
mocked symbol is the **PRIMARY intelligence under test** (a Mock Trap) or
**INFRASTRUCTURE** around it (a valid mock). That PRIMARY/INFRASTRUCTURE call is
the irreducible judgment /iterate-test exists to make (Step 4b); scripting it would
make this detector itself a Mock Trap. So a finding (MOCK_TRAP_CANDIDATE) means
*likely* trap PENDING the agent's role classification; a clean scan
(verdict_hint NO_FINDINGS) certifies NOTHING — a test that imports and calls live
code can still be a tautology. Reading a clean scan as proven fidelity IS the Mock
Trap this engine exists to surface.

Design invariant: ARCHITECTURALLY READ-ONLY on the target workspace. It parses
files for reading and writes nothing. The agent consuming its output cannot
fabricate the evidence it was handed (Mute Witness enforcement). Python-first by
design — the AST analysis is exact for Python; it does not overpromise other
languages. Architectural sibling of scripts/doorway/, scripts/focus/,
scripts/quality/, and scripts/harden/.
"""

__version__ = "1.0"
