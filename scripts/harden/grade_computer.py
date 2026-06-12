"""
grade_computer.py — Deterministic Grade Ceiling (read-only, one-directional)
=============================================================================
Turns a file's findings into a Hardening Grade CEILING — the BEST grade the
deterministic evidence still PERMITS. This is the anti-Grade-Fraud core of the
engine: the /harden grade table (Phase 2f) is a closed-form function of finding
severities, so the engine can compute the ceiling exactly, instead of leaving it
to an unverified assertion.

⚠ THE CEILING IS ONE-DIRECTIONAL — read this before trusting it:

    A CRITICAL/HIGH firm finding LOWERS the ceiling (you may NOT certify above
    it). That direction is sound: you cannot honestly grade a file Diamond while
    a shell-injection or disabled-TLS signature sits in it unresolved.

    A clean scan RAISES nothing. ``grade_ceiling == "Diamond"`` means only "no
    deterministic finding caps the grade" — it is NOT a Diamond certification.
    The agent must still run the threat model, exploitability adjudication, and
    the Sound-Effect-Execution check, then assign the FINAL grade AT OR BELOW the
    ceiling. Reading a clean ceiling as a Diamond IS Grade Fraud.

Two finding classes are excluded from the *firm* ceiling and reported as caveats
that could lower it once the agent adjudicates:
  * ``requires_confirmation`` (credential candidates) — FP-prone; counting an
    unconfirmed match would penalize a false positive. Reported, not auto-applied.
  * ``advisory`` (weak hash, weak RNG, insecure temp) — frequently non-security;
    the agent decides whether each applies.

Grade table (from harden.md Phase 2f), as a severity function:
    Diamond  0 CRIT / 0 HIGH / 0 MED        (nothing)
    Gold     0 CRIT / 0 HIGH / 1-2 MED
    Silver   0 CRIT / 1-2 HIGH
    Bronze   0 CRIT / (>=3 HIGH or >=3 MED, known and justified)
    UNGRADED >=1 CRIT  (must be resolved before any grade)
"""

from typing import Dict, List

# Ascending order: a ceiling is the MAX grade still permitted.
GRADE_ORDER = ["UNGRADED", "Bronze", "Silver", "Gold", "Diamond"]


def _counts(findings: List[Dict]) -> Dict[str, int]:
    out = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        sev = f.get("severity")
        if sev in out:
            out[sev] += 1
    return out


def compute_ceiling(findings: List[Dict]) -> Dict:
    """
    Compute the grade ceiling and the supporting counts for one file's findings.

    Only *firm* findings (neither ``advisory`` nor ``requires_confirmation``)
    move the firm ceiling. The rest are surfaced as caveats.
    """
    firm = [f for f in findings
            if not f.get("advisory") and not f.get("requires_confirmation")]
    fc = _counts(firm)

    if fc["CRITICAL"]:
        ceiling = "UNGRADED"
        basis = (f"{fc['CRITICAL']} firm CRITICAL finding(s) — not certifiable at any "
                 f"grade until resolved.")
    elif fc["HIGH"] >= 3:
        ceiling = "Bronze"
        basis = f"{fc['HIGH']} firm HIGH findings (>2) cap the grade at Bronze."
    elif fc["HIGH"] >= 1:
        ceiling = "Silver"
        basis = f"{fc['HIGH']} firm HIGH finding(s) cap the grade at Silver."
    elif fc["MEDIUM"] >= 3:
        ceiling = "Bronze"
        basis = f"{fc['MEDIUM']} firm MEDIUM findings (>2) cap the grade at Bronze."
    elif fc["MEDIUM"] >= 1:
        ceiling = "Gold"
        basis = f"{fc['MEDIUM']} firm MEDIUM finding(s) cap the grade at Gold."
    else:
        ceiling = "Diamond"
        basis = ("No deterministic finding caps the grade. THIS IS NOT A DIAMOND "
                 "CERTIFICATION — the agent must still judge threat model, "
                 "exploitability, and Sound-Effect-Execution before grading.")

    confirmation_pending = sum(1 for f in findings if f.get("requires_confirmation"))
    advisory_count = sum(1 for f in findings if f.get("advisory"))

    return {
        "grade_ceiling": ceiling,
        "severity_counts": _counts(findings),       # all findings
        "firm_severity_counts": fc,                  # firm-only (drove the ceiling)
        "confirmation_pending": confirmation_pending,
        "advisory_count": advisory_count,
        "ceiling_basis": basis,
    }


def lowest_ceiling(ceilings: List[str]) -> str:
    """Return the worst (lowest) ceiling across a set of files."""
    if not ceilings:
        return "Diamond"
    return min(ceilings, key=lambda g: GRADE_ORDER.index(g)
               if g in GRADE_ORDER else 0)
