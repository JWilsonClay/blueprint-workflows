"""
bridge_classifier.py — One-Directional Fidelity Signal (read-only, advisory)
=============================================================================
Turns the mechanical facts from mock_analyzer into a per-file fidelity signal
for /iterate-test's Step 4b (the Intelligence Bridge Declaration).

⚠ THE SIGNAL IS ONE-DIRECTIONAL — read this before trusting it:

    A finding LOWERS confidence. ``MOCK_TRAP_CANDIDATE`` means a production
    symbol the test imports has its behavior replaced by a mock — IF that symbol
    is the PRIMARY intelligence under test, the test is a Mock Trap. The engine
    deliberately does NOT decide PRIMARY vs INFRASTRUCTURE: that is the
    irreducible judgment /iterate-test exists to make (Step 4b). Scripting it
    would make this detector itself a Mock Trap.

    A clean scan RAISES nothing. ``LIVE`` / ``verdict NO_FINDINGS`` means only
    "no imported production symbol is mocked and no canned-value tautology was
    found" — it is NOT a fidelity certification. A test that imports and calls
    production code live can still be a tautology in ways the AST cannot see
    (asserting a value the production trivially returns, exercising a path that
    never reaches the intelligence — Sound Effect Execution). The HOT/MOCKED
    determination and the final "does this test the real intelligence?" verdict
    stay with the agent.

File signals:
    MOCK_TRAP_CANDIDATE  — >=1 imported production symbol is patched/mocked. The
                           agent must classify each as PRIMARY (trap) or
                           INFRASTRUCTURE (valid) in the Step-4b declaration.
    HARDCODED_ASSERTION  — a mock's canned return_value/side_effect literal is
                           echoed in an assertion (Step-4g / RULE-10 deficiency).
    NO_PRODUCTION_IMPORT — the test imports no non-infrastructure module: there is
                           no production substrate for it to exercise.
    LIVE                 — production symbols are imported and called un-patched;
                           no mocked-import or tautology finding. NOT a pass.
    PARSE_ERROR          — the file could not be parsed as Python.
"""

from typing import Dict


def classify_file(file_report: Dict) -> Dict:
    """Attach ``file_signal`` and ``signal_basis`` to one analyzer file report."""
    if file_report.get("parse_error"):
        file_report["file_signal"] = "PARSE_ERROR"
        file_report["signal_basis"] = (
            "File could not be parsed as Python; no fidelity evidence available. "
            + file_report.get("parse_error_detail", "")
        ).strip()
        return file_report

    symbols = file_report.get("symbols", [])
    prod_imports = file_report.get("imports", {}).get("production_candidates", [])
    tautologies = file_report.get("hardcoded_assertions", [])

    candidates = [s for s in symbols if s["fidelity"] == "MOCK_TRAP_CANDIDATE"]
    subject_candidates = [s for s in candidates if s.get("is_subject")]
    live = [s for s in symbols if s["fidelity"] == "CALLED_LIVE"]

    if not prod_imports:
        signal = "NO_PRODUCTION_IMPORT"
        basis = ("The test imports no non-infrastructure module — there is no "
                 "production substrate for it to exercise. Confirm the stage "
                 "under test is actually imported (Step 4a/4b).")
    elif candidates:
        signal = "MOCK_TRAP_CANDIDATE"
        who = ", ".join(s["name"] for s in (subject_candidates or candidates)[:5])
        subj_note = (" The --subject symbol is among them." if subject_candidates
                     else "")
        basis = (f"{len(candidates)} imported production symbol(s) are patched/"
                 f"mocked ({who}); their behavior in this test is the mock's, not "
                 f"the real code's.{subj_note} If any is the PRIMARY intelligence "
                 f"under test, this is a Mock Trap — classify each as PRIMARY or "
                 f"INFRASTRUCTURE in the Step-4b declaration. The engine does not "
                 f"and cannot make that call.")
    elif tautologies:
        signal = "HARDCODED_ASSERTION"
        basis = (f"{len(tautologies)} assertion(s) echo a mock's canned "
                 f"return_value/side_effect literal — the test asserts the value "
                 f"the mock was told to return (Step-4g / RULE-10 deficiency). No "
                 f"mocked production import detected.")
    elif live:
        signal = "LIVE"
        basis = (f"{len(live)} production symbol(s) imported and called "
                 f"un-patched; no mocked-import or canned-assertion finding. THIS "
                 f"IS NOT A FIDELITY CERTIFICATION — a live-called test can still "
                 f"be a tautology or never reach the intelligence (Sound Effect "
                 f"Execution). The HOT verdict stays the agent's (Step 4b).")
    else:
        signal = "LIVE"
        basis = ("Production symbols imported but neither mocked nor observed "
                 "called in this file; no finding. Not a certification.")

    # A tautology alongside a mock-candidate is still surfaced, but the
    # mock-candidate signal dominates the file verdict (worse finding wins).
    if tautologies and signal == "MOCK_TRAP_CANDIDATE":
        basis += f" Additionally, {len(tautologies)} hardcoded-assertion smell(s) found."

    file_report["file_signal"] = signal
    file_report["signal_basis"] = basis
    return file_report
