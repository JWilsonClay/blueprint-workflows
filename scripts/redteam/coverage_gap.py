"""
coverage_gap.py — Coverage gap parsing from coverage.py's own JSON schema (Phase 1a)
=======================================================================================
Reads `coverage.py`'s own `coverage json` output (produced by running
`coverage json` after a test run — a stable, tool-owned schema, not
project-specific) and flags files below a threshold. Phase 1a's own text
sets two tiers: 80% for ordinary modules, 100% for anything named in the
Phase 0c Adversarial Surface Map — both are supported via `surface_map_files`.

This module does not run `pytest --cov` or `coverage json` itself (those
are execution steps, not read-only file analysis) — it parses an already-
produced JSON report, matching the read-only invariant every engine in this
suite holds.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

DEFAULT_THRESHOLD = 80.0
SURFACE_MAP_THRESHOLD = 100.0


@dataclass
class CoverageGap:
    file: str
    percent_covered: float
    threshold_applied: float
    below_threshold: bool

    def as_dict(self) -> dict:
        return {
            "file": self.file,
            "percent_covered": self.percent_covered,
            "threshold_applied": self.threshold_applied,
            "below_threshold": self.below_threshold,
        }


def parse_coverage_json(
    coverage_json_path: str,
    surface_map_files: Optional[List[str]] = None,
    default_threshold: float = DEFAULT_THRESHOLD,
    surface_map_threshold: float = SURFACE_MAP_THRESHOLD,
) -> List[CoverageGap]:
    """
    Returns a CoverageGap per file in the report, in the schema's own file
    order. `surface_map_files` (from Phase 0c) get the stricter
    `surface_map_threshold`; everything else gets `default_threshold`.
    Missing/unreadable/malformed input returns an empty list rather than
    raising — this mirrors every other engine's degrade-safe contract; the
    caller (Phase 1a) must fall back to reading `pytest --cov`'s terminal
    output directly if this returns empty and a report was expected.
    """
    text = safe_read(Path(coverage_json_path))
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    files = data.get("files")
    if not isinstance(files, dict):
        return []

    surface_map_set = set(surface_map_files or [])
    gaps: List[CoverageGap] = []
    for file_path, file_data in files.items():
        summary = file_data.get("summary", {}) if isinstance(file_data, dict) else {}
        percent = summary.get("percent_covered")
        if percent is None:
            continue
        threshold = surface_map_threshold if file_path in surface_map_set else default_threshold
        gaps.append(
            CoverageGap(
                file=file_path,
                percent_covered=float(percent),
                threshold_applied=threshold,
                below_threshold=float(percent) < threshold,
            )
        )
    return gaps
