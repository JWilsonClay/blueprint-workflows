"""
matrix_completeness.py — Trigger Matrix workflow extraction + report completeness
====================================================================================
Both functions are pure set/text operations. Neither judges whether a
workflow's triggers were genuinely evaluated with rigor — only whether its
name is present in the report text. See scripts/triage/__init__.py for the
full contract and its explicitly-stated limits.
"""

import re
from dataclasses import dataclass, field
from typing import List

from engine_utils import safe_read

# Bounds the scan to the Trigger Matrix section only, so a coincidental
# ``**`/something`**``-shaped match elsewhere in the file (there are none
# today, but this is a safety margin) is never counted.
_MATRIX_SECTION_RE = re.compile(
    r"###\s+Trigger Matrix\b(.*?)(?=\n##\s|\Z)", re.DOTALL
)

# Matches the block-header convention every Trigger Matrix entry uses:
# **`/workflow-name`** or **`/workflow-name --flag --flag2`**, optionally
# followed on the same line by an annotation such as "(audit trigger)" or
# "**[INJECTED ...]**". The bold-close "**" position varies (some
# annotations sit INSIDE the same bold span as the name, e.g.
# "**`/quality` (audit trigger)**" — the closing "**" comes after the
# annotation, not immediately after the backtick) so this pattern only
# anchors on "line starts with ** immediately followed by a backtick-wrapped
# name" and does not require anything specific to follow.
_BLOCK_HEADER_RE = re.compile(r"^\*\*`(/[^`]+)`", re.MULTILINE)


def extract_matrix_workflows(triage_md_path: str) -> List[str]:
    """
    Parse `triage.md`'s own `### Trigger Matrix` section for its block
    headers. Returns unique workflow names (including any flags, e.g.
    "/implementation-plan --workstreams") in first-appearance order. Returns
    an empty list if the file is missing/unreadable or has no Trigger Matrix
    section — the caller must not treat an empty list as "nothing to check,"
    only as "the section wasn't found," which is itself worth surfacing.
    """
    text = safe_read(triage_md_path)
    if not text:
        return []
    section_match = _MATRIX_SECTION_RE.search(text)
    if not section_match:
        return []
    section_text = section_match.group(1)

    seen = set()
    ordered: List[str] = []
    for match in _BLOCK_HEADER_RE.finditer(section_text):
        name = match.group(1).strip()
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


@dataclass
class CompletenessResult:
    matrix_workflows: List[str] = field(default_factory=list)
    present_in_report: List[str] = field(default_factory=list)
    missing_from_report: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "matrix_workflows": self.matrix_workflows,
            "present_in_report": self.present_in_report,
            "missing_from_report": self.missing_from_report,
        }


def check_report_completeness(matrix_workflows: List[str], report_text: str) -> CompletenessResult:
    """
    For each workflow name in `matrix_workflows`, check whether it appears
    literally in `report_text` (the base command, e.g. "/harden", is
    checked — a flagged variant like "/implementation-plan --workstreams"
    is considered present if "/implementation-plan --workstreams" appears,
    since that is a functionally distinct Trigger Matrix row from the bare
    "/implementation-plan" row and the report is expected to distinguish
    them the same way the matrix does).
    """
    present: List[str] = []
    missing: List[str] = []
    for name in matrix_workflows:
        if name in report_text:
            present.append(name)
        else:
            missing.append(name)
    return CompletenessResult(
        matrix_workflows=list(matrix_workflows),
        present_in_report=present,
        missing_from_report=missing,
    )
