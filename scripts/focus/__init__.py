"""
focus — Deterministic Triad Evidence Engine
=============================================
The read-only mechanical layer behind the /focus-plan workflow.

/focus-plan historically asked the agent to *both* gather substrate evidence
*and* attest to it — the weakest possible defense against Hallucinated Success.
This package externalizes the mechanical half:

  * Locate the implementation plan (canonical `implementation-plan.md`,
    `implementation_plan.md` tolerated for legacy compatibility).
  * Parse it into items and extract verifiable anchors (file paths, symbols).
  * Verify each anchor against the real substrate via in-process grep,
    excluding test/mock/fixture paths (Mock Trap defense).
  * Emit a structured JSON evidence report for the workflow to reason over.

Design invariant: this package is ARCHITECTURALLY READ-ONLY. It never writes
to the target workspace. The agent consuming its output cannot fabricate the
evidence it was handed — the anti-Hallucinated-Success guarantee becomes
structural rather than instructional (realizing the /investigate Mute Witness
Protocol that /focus-plan STRICT RULE 12 only requests).

Architectural sibling: scripts/doorway/ (backs /sentinel the same way).
"""

__version__ = "1.0"
