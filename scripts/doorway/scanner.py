"""
scanner.py — Workspace Scanner
================================
Handles filesystem intelligence for the Doorway Protocol.
Responsible for recursive workspace scanning, content-based hashing,
and delta determination.

Refactored from .blueprints/governance/thedoorway/scanner.py:
  - Removed module-level PROJECT_ROOT constant.
  - 'project_root' constructor argument renamed to 'workspace' throughout.
  - All internal path references use self.workspace (passed in, never hardcoded).
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path


class WorkspaceScanner:
    """
    Handles filesystem intelligence for the Doorway Protocol.
    Responsible for recursive workspace scanning, content-based hashing,
    and delta determination.

    Args:
        workspace:    Absolute path to the target workspace root.
        ignore_dirs:  Set of directory names to skip during traversal.
        readme_exclude_dirs: Optional set of dirs (and children) to skip
            README heal contribution / ingested count / missing_readme signals
            (P1 stabilization pr-01-00).
    """

    def __init__(self, workspace: Path, ignore_dirs: set, readme_exclude_dirs: set = None):
        self.workspace = workspace
        self.ignore_dirs = ignore_dirs
        self.readme_exclude_dirs = readme_exclude_dirs or set()

    def _is_readme_excluded(self, rel_path_str: str) -> bool:
        """Return True if this dir (or parent) is in README_EXCLUDE_DIRS (P1)."""
        if not self.readme_exclude_dirs or not rel_path_str:
            return False
        p = Path(rel_path_str)
        for ex in self.readme_exclude_dirs:
            if str(p) == ex or str(p).startswith(ex + "/"):
                return True
        return False

    def compute_dir_hash(self, root_path: Path) -> str:
        """
        Computes a SHA-256 hash from the concatenated content of all sorted
        .py files in root_path. Returns an empty-string hash if no .py files
        are present (directory is considered structurally stable).
        """
        py_files = sorted([f for f in root_path.glob("*.py") if f.is_file()])
        hasher = hashlib.sha256()

        for py_file in py_files:
            try:
                hasher.update(py_file.name.encode("utf-8"))
                hasher.update(py_file.read_bytes())
            except OSError:
                # Unreadable file: skip but continue hashing remaining files.
                continue

        return hasher.hexdigest()

    def scan(self, previous_map: dict, full_scan: bool) -> tuple:
        """
        Lazy-recursive scan using content hashes.
        Only recurses into directories whose hash has changed since the last
        snapshot, unless full_scan=True forces a complete traversal.

        Returns:
            Tuple[dict, int]: (workspace_map, ingested_readme_count)
        """
        workspace_map = {}
        ingested_count = 0

        def should_recurse(rel_path_str: str, current_hash: str) -> bool:
            if full_scan or rel_path_str == ".":
                return True
            prev_info = previous_map.get(rel_path_str)
            if not prev_info:
                return True
            return prev_info.get("content_hash") != current_hash

        for root, dirs, files in os.walk(self.workspace):
            # Filter ignored directories in-place to prevent os.walk from descending.
            dirs[:] = [
                d for d in dirs
                if d not in self.ignore_dirs and not d.startswith(".")
            ]

            root_path = Path(root)
            try:
                rel_path = root_path.relative_to(self.workspace)
            except ValueError:
                continue
            rel_path_str = str(rel_path)

            # Content-based hash for change detection.
            content_hash = self.compute_dir_hash(root_path)

            has_readme = "README.md" in files
            if has_readme and not self._is_readme_excluded(rel_path_str):
                ingested_count += 1

            workspace_map[rel_path_str] = {
                "has_readme": has_readme,
                "files_count": len(files),
                "py_files": [f for f in files if f.endswith(".py")],
                "content_hash": content_hash,
                "last_modified": datetime.fromtimestamp(
                    root_path.stat().st_mtime
                ).isoformat(),
                "subdirs": dirs[:],  # snapshot, not a live reference
                "last_seen": datetime.now().isoformat(),
            }

            # Skip recursion if nothing in this branch has changed.
            if not should_recurse(rel_path_str, content_hash):
                # Carry over all known children of this path from the previous map.
                for p_old, info_old in previous_map.items():
                    if (
                        p_old.startswith(rel_path_str + "/")
                        and p_old not in workspace_map
                    ):
                        workspace_map[p_old] = info_old
                        if info_old.get("has_readme") and not self._is_readme_excluded(p_old):
                            ingested_count += 1
                dirs[:] = []  # Halt os.walk recursion for this branch.

        return workspace_map, ingested_count
