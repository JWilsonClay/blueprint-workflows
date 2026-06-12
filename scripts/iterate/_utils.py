"""
_utils.py — Iterate Read-Only Utilities (Python-first)
=======================================================
Shared, side-effect-free primitives used across the iterate package.

This package is read-only on the target workspace, so — like focus/_utils.py,
quality/_utils.py, and harden/_utils.py — it deliberately provides NO write
primitives (no atomic_write, no safe_mkdir). The only I/O is bounded reads and
path-boundary validation. Keeping the surface this small makes the read-only
guarantee auditable by inspection.

Security contract:
  - safe_read()     : Bounded read (CWE-400) — skips files above a size cap.
  - assert_within() : Path-traversal guard (CWE-22) — a resolved path must stay
                      inside the declared workspace.
  - is_test_path()  : Classifies a path as test/spec/mock/fixture scaffolding.
                      /iterate-test analyzes TEST files (the inverse of /harden,
                      which excludes them), so discovery KEEPS these and the
                      classifier uses the marker to confirm a --test target is a
                      test file. Same vocabulary as focus/_utils.py.
"""

from pathlib import Path

# /iterate-test's AST analysis is exact for Python only. The engine is
# Python-first by deliberate scope (see ticket 20260602_iterate-test): it does
# not parse or reason about other languages, and says so rather than pretending.
PY_EXTENSIONS = frozenset({".py"})

# Directories never walked during test discovery.
IGNORE_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", ".ipynb_checkpoints",
    "node_modules", "build", "dist", ".pytest_cache", ".mypy_cache",
    ".doorway", ".focus", ".harden", ".iterate", "site-packages",
})

# Substrings marking a path as test/spec/mock/fixture scaffolding.
_TEST_MARKERS = (
    "/test/", "/tests/", "/spec/", "/specs/", "/mock/", "/mocks/",
    "/fixture/", "/fixtures/", "/__mocks__/", "/stub/", "/stubs/",
)
_TEST_BASENAME_PREFIXES = ("test_", "spec_", "mock_", "conftest")
_TEST_BASENAME_SUFFIXES = ("_test", "_spec", ".test", ".spec")


def safe_read(
    path: Path,
    encoding: str = "utf-8",
    max_bytes: int = 2 * 1024 * 1024,  # 2 MB per-file cap.
) -> str:
    """
    Read a text file only if its size is within *max_bytes* (CWE-400).

    Returns "" for files that are too large or cannot be decoded as text, so a
    scan degrades rather than crashing on a binary or a giant generated file.
    """
    path = Path(path)
    try:
        if path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding=encoding)
    except (OSError, UnicodeDecodeError, ValueError):
        return ""


def assert_within(path: Path, workspace: Path) -> Path:
    """
    Verify *path* is a descendant of *workspace* after both are resolved.

    Resolving both paths before comparison defeats symlink-based traversal
    (e.g., a `--test ../../etc/passwd`). Raises before any follow-on I/O touches
    a path outside the declared workspace boundary (CWE-22).
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


def is_test_path(relpath: str) -> bool:
    """Return True if *relpath* is test/spec/mock/fixture scaffolding."""
    norm = "/" + relpath.replace("\\", "/").strip("/") + "/"
    if any(marker in norm for marker in _TEST_MARKERS):
        return True
    basename = relpath.replace("\\", "/").rsplit("/", 1)[-1]
    stem = basename.rsplit(".", 1)[0]
    if any(stem.startswith(p) for p in _TEST_BASENAME_PREFIXES):
        return True
    if any(basename.endswith(s) or stem.endswith(s) for s in _TEST_BASENAME_SUFFIXES):
        return True
    return False
