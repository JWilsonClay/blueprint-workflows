"""
evidence.py — Completeness scan + scope diff (the two new mechanical checks)
==============================================================================
Both functions here return facts, never verdicts. Neither judges whether a
match is "justified" or a scope deviation "warranted" — that stays with the
agent, per this engine's own package docstring and the suite-wide Mock-Trap
test (implementation-plan.md, "HONEST-DESIGN DISCIPLINE").
"""

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

# Markers checked by /execute-build Step 5d ("Completeness Scan"). Order is
# the order they are reported in, not a priority ranking.
_MARKER_PATTERNS = [
    ("TODO", re.compile(r"\bTODO\b")),
    ("FIXME", re.compile(r"\bFIXME\b")),
    ("HACK", re.compile(r"\bHACK\b")),
    ("PLACEHOLDER", re.compile(r"\bPLACEHOLDER\b")),
    ("NotImplementedError", re.compile(r"\braise\s+NotImplementedError\b")),
    ("bare_pass", re.compile(r"^\s*pass\s*(#.*)?$")),
]

_FENCE_RE = re.compile(r"^\s*```")


@dataclass
class CompletenessMatch:
    file: str
    line: int
    marker: str
    snippet: str

    def as_dict(self) -> dict:
        return {"file": self.file, "line": self.line, "marker": self.marker, "snippet": self.snippet}


def scan_completeness(files: List[str], workspace: Optional[Path] = None) -> List[CompletenessMatch]:
    """
    Scan each given file for the Step 5d marker set. Returns a flat match
    list — file, line, which marker, and the raw line text (truncated).

    `files` may be absolute paths or paths relative to `workspace` (if given).
    A file that does not exist or cannot be read is silently skipped (it is
    not this scanner's job to report missing files — that is `git status`'s
    or the caller's concern); this mirrors `safe_read`'s existing degrade-safe
    contract used by every other read-only engine in this suite.

    Markdown files are scanned like any other file EXCEPT inside fenced code
    blocks that are demonstrating the marker syntax itself (e.g. this
    package's own docstrings) would produce noise for a build's own generated
    docs — fenced regions are skipped entirely, matching the same
    fence-stripping convention `focus/phase_status.py` already uses for
    `tasks.md` parsing.
    """
    matches: List[CompletenessMatch] = []
    for raw_path in files:
        path = Path(raw_path)
        if workspace is not None and not path.is_absolute():
            path = Path(workspace) / path
        text = safe_read(path)
        if not text:
            continue
        in_fence = False
        for line_idx, line in enumerate(text.splitlines(), start=1):
            if _FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for marker_name, pattern in _MARKER_PATTERNS:
                if pattern.search(line):
                    matches.append(
                        CompletenessMatch(
                            file=str(path),
                            line=line_idx,
                            marker=marker_name,
                            snippet=line.strip()[:200],
                        )
                    )
    return matches


@dataclass
class ScopeDiffReport:
    declared: List[str] = field(default_factory=list)
    touched: List[str] = field(default_factory=list)
    touched_not_declared: List[str] = field(default_factory=list)
    declared_not_touched: List[str] = field(default_factory=list)
    declared_and_touched: List[str] = field(default_factory=list)
    git_available: bool = True

    def as_dict(self) -> dict:
        return {
            "declared": self.declared,
            "touched": self.touched,
            "touched_not_declared": self.touched_not_declared,
            "declared_not_touched": self.declared_not_touched,
            "declared_and_touched": self.declared_and_touched,
            "git_available": self.git_available,
        }


_STATUS_LINE_RE = re.compile(r"^(..)\s+(.+)$")


def _parse_porcelain(output: str) -> List[str]:
    """
    Parse `git status --porcelain` output into a flat list of touched paths.
    Handles ordinary entries and rename entries ("R  old -> new" — both sides
    are reported as touched, since either could be the phase's real target).
    """
    touched: List[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        m = _STATUS_LINE_RE.match(line)
        if not m:
            continue
        rest = m.group(2)
        if " -> " in rest:
            old, new = rest.split(" -> ", 1)
            touched.append(old.strip().strip('"'))
            touched.append(new.strip().strip('"'))
        else:
            touched.append(rest.strip().strip('"'))
    return touched


def compute_scope_diff(workspace: Path, declared_files: List[str]) -> ScopeDiffReport:
    """
    Set-difference between a phase's declared file scope and what
    `git status --porcelain` reports as actually changed in `workspace`.

    Read-only: runs `git status` only, never a mutating git command. If git
    is unavailable or `workspace` is not a git repository, returns a report
    with `git_available: False` and empty touched/diff sets — the caller
    (the model, in Step 5f) must not treat that as "scope compliant," only as
    "unverifiable by this check."
    """
    declared_norm = sorted({str(Path(f)) for f in declared_files})

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ScopeDiffReport(declared=declared_norm, git_available=False)

    if result.returncode != 0:
        return ScopeDiffReport(declared=declared_norm, git_available=False)

    touched_norm = sorted({str(Path(p)) for p in _parse_porcelain(result.stdout)})

    declared_set = set(declared_norm)
    touched_set = set(touched_norm)

    return ScopeDiffReport(
        declared=declared_norm,
        touched=touched_norm,
        touched_not_declared=sorted(touched_set - declared_set),
        declared_not_touched=sorted(declared_set - touched_set),
        declared_and_touched=sorted(declared_set & touched_set),
        git_available=True,
    )
