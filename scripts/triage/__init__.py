"""
triage — Trigger Matrix Completeness Engine
==============================================
Deterministic engine (sibling of scripts/build/, scripts/secretary/) backing
`/triage`'s own most-repeated guarantee: STRICT RULES 3 and 9, plus Phase 1's
own injected "Completeness requirement," each independently state that every
workflow in the Trigger Matrix must appear in the final Triage Report —
either as a recommendation or under "NO ACTION NEEDED" — and that omission
is Hallucinated Success. Despite three separate prose statements of this
guarantee, nothing mechanically confirmed it before this package existed.

`matrix_completeness.py` does two things, both pure set operations:

  1. Parse `triage.md`'s own `### Trigger Matrix` section for its block
     headers (a fixed, parseable ``**`/name`**`` convention) — the
     authoritative list of workflows /triage is supposed to evaluate.
  2. Given the text of an emitted Triage Report, report which of those
     workflow names are absent from it.

This does NOT and cannot verify that a workflow's triggers were evaluated
with genuine rigor — only that its name appears somewhere in the report
text. That residual gap is real and stated explicitly in
docs/compression-staging/triage-honest-design.md Section 3, not papered
over. What this closes is the narrower, purely mechanical failure this
file's STRICT RULES actually describe: a workflow silently missing from the
report entirely.

`/triage`'s two other mechanical gaps (task/phase state, receipt state) are
not new modules here — they are direct calls to the existing
`scripts/focus/phase_status.py` and `scripts/receipt/coverage.py` engines,
per the Honest-Design finding that building new parsers for either would be
duplication, not new engine work.

Read-only; writes nothing.

Origin: implementation-plan.md Phase 4.4-4.5 (Sovereign Scaling Cluster).
"""

__version__ = "1.0.0"
