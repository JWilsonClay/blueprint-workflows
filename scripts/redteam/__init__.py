"""
redteam — Schema-Agnostic Static Evidence Scanner
====================================================
Deterministic engine (sibling of scripts/harden_workflow/, scripts/triage/)
backing `/redteam`'s Phase 1a (Coverage Gap Analysis), Phase 1b (Mock
Audit), and Phase 3a (Secret Leakage Scan).

Unlike every other engine this campaign has built, `/redteam` audits an
ARBITRARY external codebase — its target's test framework, mock library,
log format, and database schema are unknown until Phase 0 discovers them.
This package is therefore deliberately schema-agnostic: pure text/pattern
analysis over files the caller points it at, assuming nothing about the
target project's internal structure.

Three modules, each a pure match-list (never a verdict):

  1. mock_scanner.py    — enumerates @patch/Mock()/MagicMock()/monkeypatch
                           call-sites. Cannot and does not judge whether a
                           mock is a tautology — that classification (Phase
                           1b's VALID/TAUTOLOGY/UNREALISTIC) stays with the
                           agent.
  2. secret_scanner.py   — enumerates secret-pattern hits (SECRET/API_KEY/
                           etc.) with the matched VALUE always redacted in
                           output — a structural enforcement of STRICT RULE
                           6 ("never expose actual secret values"), not
                           merely an instruction the agent must remember.
  3. coverage_gap.py     — parses `coverage.py`'s own stable, tool-owned
                           `coverage json` schema (not project-specific) for
                           below-threshold modules.

Explicitly NOT built here (see docs/compression-staging/redteam-honest-
design.md Section 3 for the full reasoning): Phase 5's Ghost Logic
DB-event-vs-log reconstruction does not survive the Mock-Trap test as a
generic engine — no schema-agnostic way exists to know whether a log entry
"documents" a given DB event without assuming that project's own event/log
schema, which would be scope invention. Phases 2/3b/4 (fault injection,
social engineering, Adversarial LLM Pressure) require live execution
against the target system, a fundamentally different problem than read-only
evidence collection.

Read-only; writes nothing.

Origin: implementation-plan.md Phase 5.1 (Sovereign Scaling Cluster).
"""

__version__ = "1.0.0"
