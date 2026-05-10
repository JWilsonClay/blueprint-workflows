"""
_utils.py — Doorway Security Utilities
========================================
Shared security primitives used across all doorway modules.
Centralises atomic I/O and permission-hardened directory creation
so each module does not roll its own unsafe patterns.

Security contract:
  - atomic_write()  : POSIX-atomic write via temp-file + os.replace().
                      No partial file is ever visible to concurrent readers.
  - safe_mkdir()    : Creates directories with explicit mode (default 0o700)
                      rather than relying on the process umask.
  - safe_read()     : Reads a file only after validating its size is below
                      a caller-specified cap. Prevents memory exhaustion from
                      unexpectedly large workspace files.
  - assert_within() : Validates a resolved path stays inside the workspace.
                      Raises ValueError on path traversal attempts.

[SECURITY — 2026-05-10 — initial hardening pass, /nodelete]
All primitives in this module are intentionally small and free of side-effects
so they can be audited independently of the business logic that calls them.
"""

import os
import stat
import tempfile
from pathlib import Path

# Default permission modes.
_DIR_MODE = 0o700   # Only owner can read/write/execute the data directory.
_FILE_MODE = 0o600  # Only owner can read/write state files.


def atomic_write(
    path: Path,
    content: str,
    encoding: str = "utf-8",
    mode: int = _FILE_MODE,
) -> None:
    """
    Write *content* to *path* atomically.

    Strategy:
      1. Write to a temporary file in the same directory as *path*
         (guarantees the rename is on the same filesystem — essential for
         POSIX atomic rename to work).
      2. Set the file permission to *mode* before exposing it.
      3. os.replace() atomically swaps the temp file into position.
         Any reader either sees the old version or the new version, never
         a partial write.

    On failure the temporary file is removed and the original file
    (if it existed) is left untouched.

    Security benefit:
      - CWE-362 (TOCTOU / Race Condition): eliminated. No window exists
        where the target file is partially written.
      - CWE-732 (Incorrect Permission Assignment): explicit *mode* prevents
        world-readable state files created via lax umask.

    Args:
        path:     Absolute path to the target file.
        content:  String content to write.
        encoding: Character encoding (default utf-8).
        mode:     Unix permission bits for the created file (default 0o600).

    Raises:
        OSError: If the write or rename fails.
    """
    path = Path(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    # mkstemp returns (fd, tmp_path_str); use delete=False equivalent.
    fd, tmp_str = tempfile.mkstemp(dir=parent, prefix=f".{path.name}.tmp.")
    tmp_path = Path(tmp_str)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(content)
        # Set permissions before rename so the file is never visible at
        # the target path with wrong permissions.
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)   # POSIX-atomic on Linux.
    except Exception:
        # Clean up the temp file; do not leave orphaned .tmp files.
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def safe_mkdir(path: Path, mode: int = _DIR_MODE) -> None:
    """
    Create *path* (and all parents) with explicit *mode*.

    Unlike Path.mkdir(parents=True, exist_ok=True), this also calls
    os.chmod() after creation to enforce *mode* regardless of the process
    umask.  The parent directories receive their own umask-adjusted
    permissions (only the leaf directory is permission-hardened here, as
    hardening intermediate system directories would break things).

    Security benefit:
      - CWE-732: data directory is created 0o700 (owner-only) by default,
        preventing other users on a shared machine from reading doorway state.

    Args:
        path: Directory path to create.
        mode: Unix permission bits (default 0o700).
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    # Only chmod the leaf directory — parents may be shared system paths.
    try:
        os.chmod(path, mode)
    except OSError:
        pass  # Best-effort; do not crash if chmod fails (e.g., read-only mount).


def safe_read(
    path: Path,
    encoding: str = "utf-8",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB default cap.
) -> str:
    """
    Read a text file only if its size is within *max_bytes*.

    Prevents memory exhaustion from unexpectedly large workspace files
    (e.g., a MANIFEST.md that grew into a multi-GB file, or a malformed
    snapshot JSON left by a previous interrupted run).

    Security benefit:
      - CWE-400 (Uncontrolled Resource Consumption): bounded read prevents
        denial-of-service via large files in the target workspace.

    Args:
        path:      Absolute path to the file to read.
        encoding:  Character encoding.
        max_bytes: Maximum file size in bytes. Raises ValueError if exceeded.

    Returns:
        File content as a string.

    Raises:
        OSError:    If the file cannot be read.
        ValueError: If the file exceeds *max_bytes*.
    """
    path = Path(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(
            f"[SAFE-READ] Refusing to read {path.name}: "
            f"{size:,} bytes exceeds {max_bytes:,}-byte cap."
        )
    return path.read_text(encoding=encoding)


def assert_within(path: Path, workspace: Path) -> None:
    """
    Verify *path* is a descendant of *workspace* after both are resolved.

    Resolving both paths before comparison defeats symlink-based traversal
    attacks (e.g., a README that symlinks to /etc/passwd).

    Security benefit:
      - CWE-22 (Path Traversal): raises ValueError before any I/O operation
        touches a path outside the declared workspace boundary.

    Args:
        path:      The path to validate (may be unresolved).
        workspace: The allowed root (may be unresolved).

    Raises:
        ValueError: If *path* is outside *workspace*.
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
