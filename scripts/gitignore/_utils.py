"""
_utils.py — Gitignore Seeder Security Primitives
================================================
Small, side-effect-isolated IO and path primitives so the seeder logic does not
roll its own unsafe patterns. Mirrors the security contract used across the suite
(doorway/_utils.py): atomic writes, bounded reads, and path-containment guards.

Security contract:
  - atomic_write()  : POSIX-atomic write via temp-file + os.replace() (CWE-362).
                      Preserves an explicit permission mode (CWE-732).
  - safe_read()     : Bounded read (CWE-400) — see engine_utils.safe_read,
                      consolidated there as of 2026-07-05.
  - assert_within() : Validates a resolved path stays inside the workspace,
                      defeating symlink traversal before any write (CWE-22).
"""

import os
import tempfile
from pathlib import Path

_FILE_MODE = 0o644  # .gitignore is a normal, readable repo file (not a secret).


def atomic_write(path: Path, content: str, encoding: str = "utf-8",
                 mode: int = _FILE_MODE) -> None:
    """
    Write *content* to *path* atomically: write a temp file in the same directory,
    set *mode*, then os.replace() it into position. A concurrent reader sees either
    the old file or the new one — never a partial write (CWE-362). *mode* is applied
    before the file is exposed at the target path (CWE-732).
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
        os.replace(tmp_path, path)  # POSIX-atomic on Linux.
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def assert_within(path: Path, workspace: Path) -> None:
    """
    Verify *path* is a descendant of *workspace* after both are resolved. Resolving
    first defeats symlink-based traversal (CWE-22). Raises ValueError if outside.
    """
    resolved_path = Path(path).resolve()
    resolved_workspace = Path(workspace).resolve()
    try:
        resolved_path.relative_to(resolved_workspace)
    except ValueError:
        raise ValueError(
            f"[PATH GUARD] Traversal blocked: {resolved_path} is outside "
            f"workspace {resolved_workspace}"
        )
