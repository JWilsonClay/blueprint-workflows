"""
continuous_verify — Anchor Verification CLI Wrapper
======================================================
Deterministic engine (sibling of scripts/sentinel/, scripts/redteam/)
backing `/continuous-verify`'s Phase 1 (Acceptance Criteria Verification)
and Phase 2 (Forward Contract Verification).

Does NOT duplicate `scripts/focus/anchor_scanner.py` — that module already
does exactly this verification, already proven in production for
`/focus-plan`, against arbitrary target workspaces. This package is a thin
CLI wrapper exposing `AnchorScanner.verify_file()`/`verify_symbol()`
directly for caller-supplied queries, since `anchor_scanner.py` previously
had no standalone entrypoint — it was only ever invoked as a class inside
`focus.py`'s full plan-parsing pipeline, which does more than
`/continuous-verify` needs (it re-parses the whole plan; `/continuous-verify`
already knows its scope from its own Phase 0c).

One real capability gap closed by this wrapper: `verify_symbol()`'s
`FOUND_TEST_ONLY` result is the Mock Trap signal `/focus-plan` already
relies on, but `/continuous-verify`'s SATISFIED/NOT SATISFIED/UNVERIFIABLE
vocabulary had no path to surface it — a criterion whose anchor exists only
in test/mock code could be marked SATISFIED with nothing flagging the risk.
This wrapper adds an explicit `mock_trap_candidate` flag on such results.

Neither `verify_file` nor `verify_symbol` judges whether the code at an
anchor actually implements a plan criterion correctly — only whether
something with that name/path exists, and where. That semantic judgment
stays entirely with the model.

Read-only; writes nothing.

Origin: implementation-plan.md Phase 5.3 (Sovereign Scaling Cluster).
"""

__version__ = "1.0.0"
