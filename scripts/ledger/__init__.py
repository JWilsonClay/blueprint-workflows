"""
ledger — Append-Only Ledger Growth Monitor + Quarterly Sharder
================================================================
Deterministic engine (sibling of doorway / registry / gitignore). Two modes,
one problem: an Append-Only Ledger with no ceiling and no compression.

  * "warn" mode  — count entries/bytes in a tracked file; if a threshold is
    crossed, report a WARN verdict. Advisory only, like registry.py's REVIEW
    verdict — the engine never judges significance and never rewrites the
    file it's watching.
  * "shard" mode — a tracked directory of dated shard files. Rolls over to a
    new shard on a real calendar-quarter change or a within-quarter size
    safety valve. Always driven by the real OS clock (datetime.date.today()),
    never by agent memory or inference of what day it is.

Origin: helpdesk ticket 20260704_workflow-manifest-growth_workflow.md.
"""

__version__ = "1.0.0"
