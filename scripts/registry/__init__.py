"""
registry — Suite Learning Aggregation Engine
============================================
Deterministic aggregator (sibling of doorway / focus / quality engines). It mines
the per-workspace `.history/*.ledger.md` ledgers and the `helpdesk-tickets/` corpus
for named failure-pattern events, aggregates them into a central
`manifest/CONTRADICTION_REGISTRY.md`, and computes a reviewed-watermark delta.

The script aggregates and counts — it does NOT judge significance. A `REVIEW`
verdict is a prompt for the LLM to ingest the aggregate and decide whether a real
recurring pattern warrants a /helpdesk-tickets entry. The engine never files tickets.

Origin: helpdesk ticket 20260612_contradiction-registry_engine.md.
"""

__version__ = "1.0.0"
