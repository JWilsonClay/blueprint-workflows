"""
anchor_scanner.py — Substrate Anchor Verifier (in-process, read-only)
======================================================================
Verifies plan anchors against the real codebase by building a one-time,
bounded, in-memory index of the workspace's text files and matching each
anchor against it. No subprocess, no shell — deterministic and injection-free.

Two anchor kinds:

  * file   — does the referenced file exist? Bare filenames (no directory) are
             matched by basename anywhere in the tree, so `triage.md` resolves
             even though it lives under claude-commands/.

  * symbol — whole-word search across the substrate, split into PRODUCTION vs
             TEST-ONLY matches. A symbol found only under test/mock/fixture
             paths is a Mock Trap candidate: the plan item looks implemented,
             but only its test double exists.

The scanner is read-only: it opens files for reading and never writes.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from focus._utils import (
    CODE_EXTENSIONS,
    IGNORE_DIRS,
    assert_within,
    is_test_path,
    safe_read,
)

_MAX_FILES = 8000          # Bound the index (CWE-400).
_MAX_LOCATIONS = 5         # Locations reported per anchor.


class AnchorScanner:
    """Read-only verifier of plan anchors against a workspace substrate."""

    def __init__(self, workspace: Path, max_files: int = _MAX_FILES, exclude=None):
        self.workspace = Path(workspace).resolve()
        self.max_files = max_files
        # Paths excluded from the substrate index — most importantly the plan
        # file itself: a plan that *mentions* `GhostClass` is intent, not
        # substrate. Counting that mention as a hit would make every anchor
        # trivially "found" and the verifier useless.
        self._exclude = {Path(p).resolve() for p in (exclude or set())}
        self._index: Optional[List[Dict]] = None  # [{relpath, text, is_test}]

    # ------------------------------------------------------------------
    # Index construction (lazy, once)
    # ------------------------------------------------------------------

    def _ensure_index(self) -> List[Dict]:
        if self._index is not None:
            return self._index
        index: List[Dict] = []
        for root, dirs, files in self._walk():
            for name in files:
                if not name.lower().endswith(tuple(CODE_EXTENSIONS)):
                    continue
                full = Path(root) / name
                if full.resolve() in self._exclude:
                    continue
                relpath = str(full.relative_to(self.workspace)).replace("\\", "/")
                text = safe_read(full)
                if not text:
                    continue
                index.append(
                    {"relpath": relpath, "text": text, "is_test": is_test_path(relpath)}
                )
                if len(index) >= self.max_files:
                    self._index = index
                    return index
        self._index = index
        return index

    def _walk(self):
        """os.walk-style generator that prunes ignored directories in place."""
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            yield root, dirs, files

    # ------------------------------------------------------------------
    # File anchors
    # ------------------------------------------------------------------

    def verify_file(self, query: str) -> Dict:
        """
        Verify a file anchor.

        Returns a dict: {status, locations}. status ∈
        {EXISTS, MISSING, INVALID}. A bare filename matches by basename
        anywhere in the tree; a path with separators is checked relative to
        the workspace root.
        """
        query = query.strip().strip("/")
        if not query:
            return {"status": "INVALID", "locations": []}

        # Path with directory component → check relative to workspace root.
        if "/" in query:
            try:
                target = assert_within(self.workspace / query, self.workspace)
            except ValueError:
                return {"status": "INVALID", "locations": []}
            if target.exists():
                return {"status": "EXISTS", "locations": [query]}
            # Fall through to basename search before declaring MISSING.

        basename = query.rsplit("/", 1)[-1]
        hits = [
            entry["relpath"]
            for entry in self._ensure_index()
            if entry["relpath"].rsplit("/", 1)[-1] == basename
        ]
        if hits:
            return {"status": "EXISTS", "locations": hits[:_MAX_LOCATIONS]}
        return {"status": "MISSING", "locations": []}

    # ------------------------------------------------------------------
    # Symbol anchors
    # ------------------------------------------------------------------

    def verify_symbol(self, query: str) -> Dict:
        """
        Verify a symbol anchor via whole-word search.

        Returns {status, production_matches, test_matches, locations}. status ∈
        {FOUND_PRODUCTION, FOUND_TEST_ONLY, ABSENT}. FOUND_TEST_ONLY marks a
        Mock Trap candidate.
        """
        query = query.strip()
        if len(query) < 3:
            return {"status": "ABSENT", "production_matches": 0, "test_matches": 0, "locations": []}

        pattern = re.compile(r"\b" + re.escape(query) + r"\b")
        prod_locations: List[str] = []
        test_locations: List[str] = []
        prod_count = 0
        test_count = 0

        for entry in self._ensure_index():
            line_no = _first_match_line(pattern, entry["text"])
            if line_no is None:
                continue
            loc = f"{entry['relpath']}:L{line_no}"
            if entry["is_test"]:
                test_count += 1
                if len(test_locations) < _MAX_LOCATIONS:
                    test_locations.append(loc)
            else:
                prod_count += 1
                if len(prod_locations) < _MAX_LOCATIONS:
                    prod_locations.append(loc)

        if prod_count > 0:
            status = "FOUND_PRODUCTION"
            locations = prod_locations
        elif test_count > 0:
            status = "FOUND_TEST_ONLY"
            locations = test_locations
        else:
            status = "ABSENT"
            locations = []

        return {
            "status": status,
            "production_matches": prod_count,
            "test_matches": test_count,
            "locations": locations,
        }


def _first_match_line(pattern: re.Pattern, text: str) -> Optional[int]:
    """Return the 1-based line number of the first regex match, or None."""
    m = pattern.search(text)
    if not m:
        return None
    return text.count("\n", 0, m.start()) + 1
