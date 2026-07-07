"""
citation_fidelity.py — Citation existence + line-range verification
=======================================================================
Verifies /investigate's mandatory `[label](file:///absolute/path#LN-LM)`
citation format (STRICT RULE 2 / GLOSSARY "Citation" term) resolves to a
real file and a valid line range. Never judges whether the content at
those lines actually supports the finding it's attached to — that stays
entirely with the model.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

_CITATION_RE = re.compile(
    r'\[([^\]]+)\]\(file://(/[^)#]+)(?:#L(\d+)(?:-L?(\d+))?)?\)'
)


@dataclass
class Citation:
    label: str
    path: str
    line_start: Optional[int]
    line_end: Optional[int]
    raw: str

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "raw": self.raw,
        }


def extract_citations(report_text: str) -> List[Citation]:
    """Parse every `[label](file:///path#LN-LM)` citation out of report_text."""
    citations = []
    for m in _CITATION_RE.finditer(report_text):
        label, path, start, end = m.group(1), m.group(2), m.group(3), m.group(4)
        citations.append(
            Citation(
                label=label,
                path=path,
                line_start=int(start) if start else None,
                line_end=int(end) if end else None,
                raw=m.group(0),
            )
        )
    return citations


@dataclass
class CitationResult:
    citation: Citation
    status: str  # VALID | VALID_NO_LINE_RANGE | FILE_MISSING | LINE_OUT_OF_RANGE
    file_line_count: Optional[int] = None

    def as_dict(self) -> dict:
        return {
            "citation": self.citation.as_dict(),
            "status": self.status,
            "file_line_count": self.file_line_count,
        }


def verify_citation(citation: Citation) -> CitationResult:
    """
    Confirms the cited file exists and, if a line range is given, that the
    range falls within the file's actual line count. Does NOT open the
    cited lines to judge their content — existence and range validity only.
    """
    path = Path(citation.path)
    if not path.is_file():
        return CitationResult(citation=citation, status="FILE_MISSING")

    if citation.line_start is None:
        return CitationResult(citation=citation, status="VALID_NO_LINE_RANGE")

    text = safe_read(path)
    line_count = len(text.splitlines()) if text else 0
    end = citation.line_end or citation.line_start

    if citation.line_start < 1 or end < citation.line_start or end > line_count:
        return CitationResult(citation=citation, status="LINE_OUT_OF_RANGE", file_line_count=line_count)

    return CitationResult(citation=citation, status="VALID", file_line_count=line_count)
