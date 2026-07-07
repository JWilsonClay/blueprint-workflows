"""
ticket_parser.py — Ticket header/section/status extraction
==============================================================
Parses a helpdesk ticket's text against this workflow's own fixed
template (Phase 1's "Required structure"). Pure regex over a known,
suite-owned schema — not schema-agnostic parsing of an arbitrary target,
since the ticket format IS this workflow's own convention.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

_HEADER_FIELD_RE = re.compile(r'^\*\*([^*:]+)\*\*:\s*(.+)$', re.MULTILINE)
_SECTION_RE = re.compile(r'^##\s*(\d)\.', re.MULTILINE)
_STATUS_RE = re.compile(r'^\*\*Status\*\*:\s*\*\*(.+?)\*\*', re.MULTILINE)

_FILENAME_RE = re.compile(r'^(CLOSED_)?(\d{8})_(.+)_workflow\.md$')

REQUIRED_SECTIONS = {"1", "2", "3", "4", "5"}
VALID_ROOT_CAUSE_TYPES = {"STRUCTURAL", "SUBSTANTIVE-LOGIC"}


@dataclass
class TicketFields:
    header_fields: dict = field(default_factory=dict)
    sections_present: set = field(default_factory=set)
    status: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "header_fields": self.header_fields,
            "sections_present": sorted(self.sections_present),
            "status": self.status,
        }


def parse_ticket(text: str) -> TicketFields:
    """Extract header fields, present section numbers, and the Status value."""
    header_fields = {m.group(1).strip(): m.group(2).strip() for m in _HEADER_FIELD_RE.finditer(text)}
    sections_present = {m.group(1) for m in _SECTION_RE.finditer(text)}
    status_match = _STATUS_RE.search(text)
    status = status_match.group(1).strip() if status_match else None
    return TicketFields(header_fields=header_fields, sections_present=sections_present, status=status)


def parse_ticket_file(path: str) -> Optional[TicketFields]:
    """Convenience: read a ticket file and parse it. None if unreadable."""
    text = safe_read(Path(path))
    if not text:
        return None
    return parse_ticket(text)


@dataclass
class FilenameInfo:
    filename: str
    closed: bool
    date: str
    workflow_name: str

    def as_dict(self) -> dict:
        return {
            "filename": self.filename,
            "closed": self.closed,
            "date": self.date,
            "workflow_name": self.workflow_name,
        }


def parse_filename(filename: str) -> Optional[FilenameInfo]:
    """
    Parse the naming convention (STRICT RULE 10 / GLOSSARY "Ticket Naming
    Convention"): `[CLOSED_]YYYYMMDD_[workflow-name]_workflow.md`. Returns
    None if the filename doesn't match — a malformed filename is itself a
    validation finding, not something to guess at.
    """
    m = _FILENAME_RE.match(filename)
    if not m:
        return None
    closed_prefix, date, workflow_name = m.group(1), m.group(2), m.group(3)
    return FilenameInfo(filename=filename, closed=bool(closed_prefix), date=date, workflow_name=workflow_name)


def list_ticket_files(tickets_dir: str) -> List[str]:
    """List all `*_workflow.md` ticket filenames in tickets_dir (not recursive)."""
    d = Path(tickets_dir)
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_file() and p.name.endswith("_workflow.md"))
