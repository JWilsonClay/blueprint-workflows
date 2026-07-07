"""
helpdesk_tickets — Ticket Lifecycle Evidence Engine
======================================================
Deterministic engine (sibling of scripts/investigate/, scripts/redteam/)
backing `/helpdesk-tickets`'s Phase 2 (TICKET VALIDATION), STRICT RULE 7
(duplicate-ticket detection), and staleness detection — three mechanisms
tasks.md's own seed note named directly, plus a fourth found by reading
STRICT RULE 12 directly: the Phylogeny-Disposition-vs-Status contradiction
check.

Unlike `/redteam`/`/investigate`, `/helpdesk-tickets` operates entirely on
this repo's own fixed ticket schema (Phase 1's "Required structure") — not
an arbitrary external target — so this package parses that schema directly,
the same architectural class as `scripts/build/`, `scripts/triage/`, etc.

Four modules:

  1. ticket_parser.py      — extracts header fields, section presence, and
                              Status value from a ticket's text.
  2. schema_validator.py   — checks the Phase 2 TICKET VALIDATION checklist
                              mechanically, plus the STRICT RULE 12
                              Phylogeny/Status contradiction. Citation
                              checks are delegated to
                              scripts/investigate/citation_fidelity.py,
                              imported directly — not reimplemented, since
                              the citation format is byte-for-byte
                              identical to /investigate's own convention.
  3. duplicate_detector.py — STRICT RULE 7: lists open tickets already
                              naming a given faulting workflow.
  4. staleness.py          — days-open per ticket from its filename's
                              YYYYMMDD prefix. Advisory only — reports the
                              number, never judges whether it's "too long,"
                              which STRICT RULE 9 already reserves for the
                              agent.

None of these judge the failure class, root-cause narrative, urgency
correctness, or Phylogeny Disposition *correctness* — only presence,
format, and cross-field consistency.

Read-only; writes nothing.

Origin: implementation-plan.md Phase 5.5 (Sovereign Scaling Cluster).
"""

__version__ = "1.0.0"
