"""
_utils.py — Focus Read-Only Security Utilities
================================================
Shared, side-effect-free primitives used across the focus package.

This package is read-only on the target workspace, so — unlike
doorway/_utils.py — it deliberately provides NO write primitives
(no atomic_write, no safe_mkdir). The only I/O is bounded reads and
path-boundary validation. Keeping the surface this small makes the
read-only guarantee auditable by inspection.

Security contract:
  - safe_read()    : bounded read (CWE-400) — see engine_utils.safe_read,
                     consolidated there as of 2026-07-05. This package's own
                     2 MB per-file cap is passed explicitly at each call site.
  - assert_within(): Validates a resolved path stays inside the workspace.
                     Raises ValueError on path-traversal attempts (CWE-22).
  - is_test_path() : Classifies a relative path as test/mock/fixture scaffolding
                     so symbol matches there can be separated from production
                     matches (Mock Trap defense).
"""

from pathlib import Path

# File extensions worth scanning for substrate anchors. Anything else
# (binaries, images, lockfiles) is skipped — both for signal and for safety.
CODE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".yaml", ".yml",
    ".sh", ".txt", ".toml", ".cfg", ".ini", ".html", ".css", ".sql",
    ".rb", ".go", ".rs", ".java", ".c", ".h", ".cpp", ".hpp",
})

# Directories never walked during substrate scanning.
IGNORE_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", ".ipynb_checkpoints",
    "node_modules", "build", "dist", ".pytest_cache", ".mypy_cache",
    ".doorway", ".focus", "site-packages",
})

# Substrings that mark a path as test/mock/fixture scaffolding rather than
# production substrate. A symbol found ONLY under these paths is a Mock Trap
# candidate: the plan item looks implemented, but only its test double exists.
_TEST_MARKERS = (
    "/test/", "/tests/", "/spec/", "/specs/", "/mock/", "/mocks/",
    "/fixture/", "/fixtures/", "/__mocks__/", "/stub/", "/stubs/",
)
_TEST_BASENAME_PREFIXES = ("test_", "spec_", "mock_", "conftest")
_TEST_BASENAME_SUFFIXES = ("_test", "_spec", ".test", ".spec")

# This package's own tuned bound for engine_utils.safe_read (2 MB per-file cap
# for scanning) — defined once here so call sites don't repeat the literal.
SAFE_READ_MAX_BYTES = 2 * 1024 * 1024


def assert_within(path: Path, workspace: Path) -> Path:
    """
    Verify *path* is a descendant of *workspace* after both are resolved.

    Resolving both paths before comparison defeats symlink-based traversal
    (e.g., a plan that references `../../etc/passwd`). Raises before any
    follow-on I/O touches a path outside the declared workspace boundary
    (CWE-22).

    Returns:
        The resolved path (inside the workspace).

    Raises:
        ValueError: If *path* resolves outside *workspace*.
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
    """
    Return True if *relpath* (a forward-slash relative path) is test/mock/
    fixture scaffolding rather than production substrate.

    Used to separate production anchor matches from test-only matches so the
    workflow can flag Mock Trap candidates (anchors that exist only as test
    doubles).
    """
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
