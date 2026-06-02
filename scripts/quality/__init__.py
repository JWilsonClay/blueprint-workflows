"""
quality — Quality Process Auditor (read-only)
==============================================
The deterministic verification rail behind the /quality workflow.

/quality is a behavioral modifier whose seven judgment steps CANNOT be scripted —
quality is irreducible judgment. This package therefore does NOT assess quality.
It verifies the quality *process receipts* and flags *mechanical anti-pattern
smells*, leaving the actual quality verdict to the model where it belongs:

  * ledger_auditor — parse/validate the Quality Witness log, compute the
    "unreviewed entries" count and the /triage P3 audit trigger.
  * tag_verifier   — extract and validate Quality Chain Tags (VALID/MALFORMED/
    ABSENT), making the cross-agent anti-trust mechanism structural.
  * smell_linter   — detect the specific mechanical anti-patterns /quality names
    (hedge-language, closing pleasantries, truncation, filler openers). STRICTLY
    one-directional and advisory: smells => likely defect; NO smells says NOTHING
    about quality. Reading absence-of-smells as quality is the Mock Trap.

Design invariant: ARCHITECTURALLY READ-ONLY on the target workspace. The witness
log is APPENDED by the model (the /quality protocol); this package only reads it.
Architectural sibling of scripts/doorway/ and scripts/focus/.
"""

__version__ = "1.0"
