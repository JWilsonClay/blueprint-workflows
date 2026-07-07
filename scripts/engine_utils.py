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

atomic_write / safe_mkdir / assert_within [ADDED 2026-07-07 — Sovereign Redesign
Cluster Stage 5, scripts/plan/ population]: promoted here from doorway/_utils.py
at the point of a second real consumer (scripts/plan/ensure_plan_templates.py
is the first script in this suite other than doorway/ that writes to a target
workspace). Logic is unchanged from doorway/_utils.py's originals. doorway/'s
own copies are deliberately left in place, not retargeted to import these —
zero-risk to a working module outside this stage's scope; a future
consolidation can retarget doorway/ separately if a third reason arises. This
mirrors safe_read's own precedent: consolidate the new duplication, don't
touch what already works. focus/_utils.py's own assert_within (read-only
package, different security contract note in its own docstring) is likewise
left untouched.
"""

import os
import tempfile
from pathlib import Path

DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB — matches the majority of prior callers.
_DIR_MODE = 0o700
_FILE_MODE = 0o600


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


def atomic_write(path: Path, content: str, encoding: str = "utf-8", mode: int = _FILE_MODE) -> None:
    """
    Write *content* to *path* atomically via temp-file + os.replace() (CWE-362
    guard: no reader ever observes a partial write). Sets *mode* before the
    rename so the file is never visible at the target path with wrong
    permissions (CWE-732). On failure, the temp file is removed and the
    original (if any) is left untouched.
    """
    path = Path(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(dir=parent, prefix=f".{path.name}.tmp.")
    tmp_path = Path(tmp_str)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def safe_mkdir(path: Path, mode: int = _DIR_MODE) -> None:
    """
    Create *path* (and all parents) with explicit *mode* enforced via chmod
    on the leaf directory regardless of process umask (CWE-732 guard).
    Best-effort chmod — does not raise if the filesystem refuses it (e.g.
    read-only mount).
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def assert_within(path: Path, workspace: Path) -> Path:
    """
    Verify *path* is a descendant of *workspace* after both are resolved
    (defeats symlink-based traversal, CWE-22). Returns the resolved path.
    Raises ValueError if *path* resolves outside *workspace*.
    """
    resolved_path = Path(path).resolve()
    resolved_workspace = Path(workspace).resolve()
    try:
        resolved_path.relative_to(resolved_workspace)
    except ValueError:
        raise ValueError(
            f"[PATH GUARD] Traversal blocked: "
            f"{resolved_path} is outside workspace {resolved_workspace}"
        )
    return resolved_path
