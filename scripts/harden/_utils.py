"""
_utils.py — Harden Read-Only Security Utilities
=================================================
Shared, side-effect-free primitives used across the harden package.

This package is read-only on the target workspace, so — like focus/_utils.py and
quality/_utils.py — it deliberately provides NO write primitives (no atomic_write,
no safe_mkdir). The only I/O is bounded reads and path-boundary validation.
Keeping the surface this small makes the read-only guarantee auditable by
inspection.

Security contract:
  - safe_read()        : Bounded read (CWE-400) — skips files above a size cap.
  - assert_within()    : Path-traversal guard (CWE-22) — a resolved path must
                         stay inside the declared workspace.
  - is_test_path()     : Classifies a path as test/spec/mock/fixture scaffolding.
                         /harden explicitly EXCLUDES test files from hardening, so
                         the scanner skips these (matches harden.md scope).
  - looks_like_script(): Identifies an eligible script either by extension or by
                         an interpreter shebang on the first line.
"""

from pathlib import Path

# Script file extensions /harden treats as in-scope. Narrower than focus's
# CODE_EXTENSIONS on purpose: /harden targets *scripts*, not documentation or
# data files. (Documentation is excluded, which also avoids flagging a workflow
# .md file that merely *documents* a dangerous pattern.)
SCRIPT_EXTENSIONS = frozenset({
    ".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".rb", ".pl", ".ps1", ".php",
})

# Credential scanning also covers .env files (where secrets commonly leak),
# matching the workflow's own Phase-0 credential-scan extension set.
SECRET_SCAN_EXTENSIONS = frozenset(SCRIPT_EXTENSIONS | {".env"})

# Directories never walked during scanning.
IGNORE_DIRS = frozenset({
    ".git", ".venv", "venv", "__pycache__", ".ipynb_checkpoints",
    "node_modules", "build", "dist", ".pytest_cache", ".mypy_cache",
    ".doorway", ".focus", ".harden", "site-packages",
})

# Interpreters that mark an extensionless file as a script via its shebang.
_SHEBANG_INTERPRETERS = (
    "python", "bash", "sh", "zsh", "node", "ruby", "perl", "php", "pwsh",
)

# Substrings marking a path as test/spec/mock/fixture scaffolding. /harden's
# stated scope excludes any file whose name or path contains these markers.
_TEST_MARKERS = (
    "/test/", "/tests/", "/spec/", "/specs/", "/mock/", "/mocks/",
    "/fixture/", "/fixtures/", "/__mocks__/", "/stub/", "/stubs/",
)
_TEST_BASENAME_PREFIXES = ("test_", "spec_", "mock_", "conftest")
_TEST_BASENAME_SUFFIXES = ("_test", "_spec", ".test", ".spec")


def safe_read(
    path: Path,
    encoding: str = "utf-8",
    max_bytes: int = 2 * 1024 * 1024,  # 2 MB per-file cap for scanning.
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
    (e.g., a `--file ../../etc/passwd`). Raises before any follow-on I/O touches
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


def looks_like_script(path: Path, first_line: str = "") -> bool:
    """
    True if *path* is an eligible script: a known script extension, or an
    extensionless/unknown file whose first line is an interpreter shebang.
    """
    ext = Path(path).suffix.lower()
    if ext in SCRIPT_EXTENSIONS:
        return True
    if ext and ext not in SCRIPT_EXTENSIONS:
        return False  # known non-script extension (.md, .json, .png, ...)
    line = first_line.strip()
    if line.startswith("#!"):
        return any(interp in line for interp in _SHEBANG_INTERPRETERS)
    return False
