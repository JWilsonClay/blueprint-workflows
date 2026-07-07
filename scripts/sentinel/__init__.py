"""
sentinel — Recommender/Routing-Table Parity Engine
=====================================================
Deterministic engine (sibling of scripts/redteam/, scripts/harden_workflow/)
backing `/sentinel`'s Phase 2b Routing Map. `/sentinel` already delegates
nearly all of its state-collection to real engines (`doorway.py`,
`gitignore_seeder.py`, `ensure_plan_templates.py`) — the tasks.md seed note's
assumed "drift-delta layer" gap does not exist; `doorway.py`'s own snapshot/
hash-compare mechanism already computes it.

The real gap this package closes: Phase 2b's Routing Map table
hand-duplicates logic `scripts/doorway/recommender.py` already owns and
emits per-recommendation via its own `workflow` field. Diffing the two
directly (not trusting the `.md`'s claim about itself) found the duplicate
had ALREADY DRIFTED — a missing routing row and an undocumented severity
value, both live defects, not hypothetical risk.

`recommender_parity.py` does one thing: extract the actual id/workflow/
severity triples `recommender.py`'s source emits, extract Phase 2b's
documented table rows, and report the set difference. It does not judge
whether a routing decision is *correct* — only whether the documentation
of an already-decided engine behavior is complete and current.

Read-only; writes nothing.

Origin: implementation-plan.md Phase 5.2 (Sovereign Scaling Cluster).
"""

__version__ = "1.0.0"
