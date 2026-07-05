#!/usr/bin/env python3
"""
engine_utils.py — Shared utilities for the Sovereign Suite's deterministic engines
=====================================================================================
safe_read: a bounded, side-effect-free file read (CWE-400 guard), consolidated
from seven independent, behaviorally-identical copies previously in registry/,
focus/, harden/, quality/, gitignore/, ledger/, and receipt/'s own _utils.py
files. Each engine's own max_bytes tuning is preserved via an explicit
argument at the call site where it differs from the shared default — this
removes only the duplicated control flow, not any engine's chosen bound.

doorway/_utils.py's safe_read is deliberately NOT included here: it raises
ValueError on an oversized file and propagates a missing/undecodable file's
exception uncaught, rather than degrading to "" like the other seven. Its 16
call sites each wrap it in their own try/except expecting exactly this (e.g.
breadcrumb.py catches (OSError, ValueError) to report a specific failure
message) — a different, load-bearing contract, not a tuning difference.
Merging it would have silently turned visible, logged failures into silent
empty-string returns.

Origin: /deepcode finding during
helpdesk-tickets/CLOSED_20260705_triage-workqueue_workflow.md.
"""

from pathlib import Path

DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB — matches the majority of prior callers.


def safe_read(path: Path, max_bytes: int = DEFAULT_MAX_BYTES, encoding: str = "utf-8") -> str:
    """
    Read a text file only if within *max_bytes* (CWE-400 guard). Returns ""
    for a missing, too-large, or undecodable file rather than raising — every
    caller's own scan/audit/monitor pass should degrade, not crash.
    """
    path = Path(path)
    try:
        if not path.exists() or path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding=encoding)
    except (OSError, UnicodeDecodeError, ValueError):
        return ""
