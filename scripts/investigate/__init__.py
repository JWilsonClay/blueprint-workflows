"""
investigate — Citation & Search Log Fidelity Engine
======================================================
Deterministic engine (sibling of scripts/redteam/, scripts/continuous_verify/)
backing `/investigate`'s Phase 3 citation checks and Phase 1c search-log
verification.

Like `/redteam`, `/investigate` audits an arbitrary target system whose
internal schema is unknown in advance — but two of its OWN reporting
conventions (not the target's schema) are schema-agnostic to verify
mechanically:

  1. citation_fidelity.py    — the mandatory `[label](file:///path#LN-LM)`
                                citation format (STRICT RULE 2). Confirms a
                                citation resolves to a real file and a valid
                                line range. Never judges whether the content
                                at those lines actually supports the finding.
  2. search_log_verifier.py  — Phase 1c's `grep "pattern" path → N matches`
                                convention. Re-runs the exact search (via
                                Python's `re` module over file contents, not
                                a shell subprocess — the pattern/path come
                                from report text, which could originate from
                                an untrusted source in an autonomous
                                pipeline, so shell invocation is avoided)
                                and compares the actual count to the claimed
                                one. Never judges whether the search was the
                                *right* one to run.

Both operate on the Investigation Report's own text plus the real
filesystem — never on the target codebase's unknown internal schema, the
same discipline scripts/redteam/'s engines already established.

Read-only; writes nothing.

Origin: implementation-plan.md Phase 5.4 (Sovereign Scaling Cluster).
"""

__version__ = "1.0.0"
