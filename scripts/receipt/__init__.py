"""
receipt — Receipt Coverage Engine
===================================
Deterministic engine (sibling of doorway / focus / harden / iterate). Reads
`.workflow_state/receipts/*` + `tasks.md`, cross-references completed phases
against the four receipt dimensions (Built/Validated/Hardened/Documented) plus
the Quality-Process dimension (via `scripts/quality/quality_audit.py`), and
computes a gap percentage. Read-only; writes nothing.

Origin: Sovereign Verification-Spine Upgrade Campaign, QUEUE #11
(root implementation-plan.md), resolving
helpdesk-tickets/CLOSED_20260704_hallucinated-success-recurrence_workflow.md's
finding that /receipt-check's "coverage is sufficient" verdict was previously
unbacked by a receipt existing but never mechanically verified.
"""

__version__ = "1.0.0"
