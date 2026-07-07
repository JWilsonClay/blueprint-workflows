"""
search_log_verifier.py — Search Log claim verification
==========================================================
Verifies /investigate's Phase 1c SEARCH LOG convention
(`grep "[pattern]" [path] → [N matches]`) by re-running the exact search
and comparing the actual match count to the claimed one. Never judges
whether the search was the *right* one to run, or whether the matches
found are relevant — only whether the claimed count is accurate.

Re-implemented via Python's `re` module over file contents rather than
shelling out to the real `grep` binary: the pattern and path strings come
from Investigation Report text, which in an autonomous pipeline could
originate from a source this engine should not trust enough to pass into
a shell command. This is a deliberate, honestly-documented divergence from
literal `grep` semantics (Python regex vs. POSIX/GNU grep regex dialect
differences exist) — close enough for verification purposes, not a
byte-for-byte reimplementation of grep's exact behavior.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

_SEARCH_LOG_RE = re.compile(
    r'grep\s+"([^"]+)"\s+(\S+)\s*(?:→|->)\s*(\d+)\s*match'
)

_MAX_FILES = 5000
_IGNORE_DIRS = frozenset({".git", "__pycache__", "node_modules", ".venv", ".doorway"})


@dataclass
class SearchLogEntry:
    pattern: str
    path: str
    claimed_count: int
    raw: str

    def as_dict(self) -> dict:
        return {"pattern": self.pattern, "path": self.path, "claimed_count": self.claimed_count, "raw": self.raw}


def extract_search_log_entries(report_text: str) -> List[SearchLogEntry]:
    """Parse every `grep "pattern" path → N matches` line out of report_text."""
    entries = []
    for m in _SEARCH_LOG_RE.finditer(report_text):
        pattern, path, count = m.group(1), m.group(2), int(m.group(3))
        entries.append(SearchLogEntry(pattern=pattern, path=path, claimed_count=count, raw=m.group(0)))
    return entries


def _count_matches_in_file(pattern: re.Pattern, path: Path) -> int:
    text = safe_read(path)
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if pattern.search(line))


def _count_matches(pattern: re.Pattern, target: Path) -> int:
    if target.is_file():
        return _count_matches_in_file(pattern, target)
    if not target.is_dir():
        return 0
    total = 0
    scanned = 0
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS and not d.startswith(".")]
        for name in files:
            total += _count_matches_in_file(pattern, Path(root) / name)
            scanned += 1
            if scanned >= _MAX_FILES:
                return total
    return total


@dataclass
class SearchVerifyResult:
    entry: SearchLogEntry
    actual_count: Optional[int]
    matches_claim: bool
    status: str  # VERIFIED | MISMATCH | PATH_NOT_FOUND | INVALID_PATTERN

    def as_dict(self) -> dict:
        return {
            "entry": self.entry.as_dict(),
            "actual_count": self.actual_count,
            "matches_claim": self.matches_claim,
            "status": self.status,
        }


def verify_search_entry(entry: SearchLogEntry) -> SearchVerifyResult:
    target = Path(entry.path)
    if not target.exists():
        return SearchVerifyResult(entry=entry, actual_count=None, matches_claim=False, status="PATH_NOT_FOUND")

    try:
        pattern = re.compile(entry.pattern)
    except re.error:
        return SearchVerifyResult(entry=entry, actual_count=None, matches_claim=False, status="INVALID_PATTERN")

    actual = _count_matches(pattern, target)
    matches = actual == entry.claimed_count
    return SearchVerifyResult(
        entry=entry,
        actual_count=actual,
        matches_claim=matches,
        status="VERIFIED" if matches else "MISMATCH",
    )
