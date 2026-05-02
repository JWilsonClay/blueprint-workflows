#!/usr/bin/env python3
"""
core/filesystem.py — Project Traversal and File Utilities
=========================================================
Sovereign Refactor Protocol — Core Library

Responsibility: Centralize project walking, skip-list management, 
and shim-header detection logic.
"""

import os
from pathlib import Path
from typing import Generator

SKIP_DIRS = frozenset({
    "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".tox",
    ".venv", "venv", "env", "node_modules", "dist", "build",
    ".next", ".nuxt", "coverage", ".coverage", "htmlcov",
})

SHIM_FILE_MARKER = "⚠️ SHIM FILE"
REVERSE_SHIM_MARKER = "⚠️ REVERSE SHIM"
SHIM_HEADER_MARKERS = (SHIM_FILE_MARKER, REVERSE_SHIM_MARKER)

PYTHON_EXTENSIONS = frozenset({".py"})
JS_EXTENSIONS = frozenset({".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"})

def walk_project(root: Path) -> Generator[tuple[str, list[str], list[str]], None, None]:
    """
    Walk the project directory tree, skipping irrelevant/cached directories.
    Yields (dirpath, dirnames, filenames) compatible with os.walk.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # In-place filter to prevent descending into skip-listed dirs
        dirnames[:] = [d for d in dirnames 
                       if d not in SKIP_DIRS 
                       and not d.endswith(".egg-info")
                       and not d.endswith(".dist-info")]
        yield dirpath, dirnames, filenames

def read_file_safe(path: Path) -> str:
    """Read file content as UTF-8, replacing errors to prevent crashes."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return ""

def is_shim_file(path: Path) -> bool:
    """Return True if the file contains any of the mandatory shim headers."""
    content = read_file_safe(path)
    return any(marker in content for marker in SHIM_HEADER_MARKERS)

def is_forward_shim(path: Path) -> bool:
    """Return True if the file is a Phase 1 Forward Shim."""
    return SHIM_FILE_MARKER in read_file_safe(path)

def is_reverse_shim(path: Path) -> bool:
    """Return True if the file is a Phase 2 Reverse Shim."""
    return REVERSE_SHIM_MARKER in read_file_safe(path)

def shim_points_to(path: Path) -> str | None:
    """
    Extract the destination path from a shim header.
    Looks for 'Logic currently lives at:' or 'Logic has MOVED to:'.
    """
    content = read_file_safe(path)
    for line in content.splitlines():
        line = line.strip().lstrip("#").lstrip("//").strip()
        if line.startswith("Logic currently lives at:"):
            return line.split(":", 1)[1].strip()
        if line.startswith("Logic has MOVED to:"):
            return line.split(":", 1)[1].strip()
    return None

def get_source_extensions(language: str) -> frozenset[str]:
    """Return the set of source file extensions for the given language."""
    if language == "python":
        return PYTHON_EXTENSIONS
    return JS_EXTENSIONS
