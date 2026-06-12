"""
harden — Deterministic Hardening Evidence Engine (read-only)
=============================================================
The mechanical verification rail behind the /harden workflow.

/harden's terminal artifact is a Hardening Grade (Diamond/Gold/Silver/Bronze)
that /receipt-check reads as the project's security-coverage signal. That grade
is DEFINED as a function of finding-severity counts — yet historically it was
rendered by agent judgment with no mechanical detection of the signatures that
determine it. A grade asserted without the scan that backs it is Grade Fraud.

This package externalizes the deterministic half:

  * cwe_scanner       — detect deterministic CWE signatures (dynamic code
    execution, the shell-True subprocess keyword, command-exec calls, hardcoded
    credential candidates, unsafe deserialization, disabled TLS verification,
    weak crypto, world-writable permissions, insecure temp files).
  * threat_classifier — suggest a Threat Context (NETWORK-FACING / PRIVILEGED /
    DATA-HANDLING / INTERNAL-ONLY). Heuristic, ADVISORY only.
  * grade_computer    — compute a deterministic grade CEILING from real findings.

⚠ THE ONE-DIRECTIONAL HONESTY BOUNDARY (anti-Grade-Fraud / anti-Mock-Trap):
The engine computes the BEST grade the deterministic evidence still PERMITS — a
ceiling, never a certification. A CRITICAL signature FORBIDS Diamond/Gold/Silver.
But a clean scan (ceiling == Diamond) says NOTHING about whether a file deserves
Diamond — the threat model, exploitability adjudication, and Sound-Effect-
Execution check are irreducible judgment owned by the /harden agent, who assigns
the final grade AT OR BELOW the ceiling. Reading a clean ceiling as a Diamond
certification IS the Grade Fraud this engine exists to prevent.

Design invariant: ARCHITECTURALLY READ-ONLY on the target workspace. It opens
files for reading and writes nothing. The agent consuming its output cannot
fabricate the evidence it was handed (Mute Witness enforcement). Architectural
sibling of scripts/doorway/, scripts/focus/, and scripts/quality/.
"""

__version__ = "1.0"
