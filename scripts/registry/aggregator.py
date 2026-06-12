"""
aggregator.py — Event collection + aggregation (read-only on the substrate)
===========================================================================
Mines free-form markdown by regex against a KNOWN vocabulary rather than a strict
schema, so it is resilient to the prose variation of real ledgers and tickets.

Sources:
  * helpdesk-tickets/**/*.md  → one Event per ticket file
  * .history/*.ledger.md      → one Event per dated `## YYYY-MM-DD — title` section
"""

import re
from pathlib import Path

from registry._utils import safe_read

# Canonical named failure patterns (the Sovereign failure vocabulary). Matched
# case-insensitively as substrings; normalized to the canonical label.
KNOWN_PATTERNS = {
    "mock trap": "Mock Trap",
    "context erosion": "Context Erosion",
    "hallucinated success": "Hallucinated Success",
    "ghost logic": "Ghost Logic",
    "sound effect": "Sound Effect Execution",
    "grade fraud": "Grade Fraud",
    "speculative resolution": "Speculative Resolution of Ambiguity",
}

_TICKET_NAME_RE = re.compile(r"(?:CLOSED_)?(\d{8})_([a-z0-9-]+)_")
_DATE_FIELD_RE = re.compile(r"\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})")
_HISTORY_SECTION_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+[—-]\s+(.+)$", re.MULTILINE)


class Event:
    __slots__ = ("date", "source", "ref", "patterns", "workflow", "title")

    def __init__(self, date, source, ref, patterns, workflow, title):
        self.date = date            # "YYYY-MM-DD" or ""
        self.source = source        # "ticket" | "history"
        self.ref = ref              # unique, pipe-free id
        self.patterns = patterns    # list[str] canonical
        self.workflow = workflow    # "/name" or ""
        self.title = title

    def as_dict(self):
        return {
            "date": self.date, "source": self.source, "ref": self.ref,
            "patterns": list(self.patterns), "workflow": self.workflow, "title": self.title,
        }


def _extract_patterns(text):
    low = text.lower()
    found = []
    for key, canon in KNOWN_PATTERNS.items():
        if key in low and canon not in found:
            found.append(canon)
    return found


def _fmt_date(yyyymmdd):
    return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def _sanitize(s):
    # Refs/titles must not contain the field delimiter used in the event log.
    return s.replace("|", "/").strip()


def collect_ticket_events(tickets_dir):
    events = []
    tickets_dir = Path(tickets_dir)
    if not tickets_dir.is_dir():
        return events
    for p in sorted(tickets_dir.rglob("*.md")):
        text = safe_read(p)
        m = _TICKET_NAME_RE.match(p.name)
        date = _fmt_date(m.group(1)) if m else ""
        workflow = ("/" + m.group(2)) if m else ""
        dm = _DATE_FIELD_RE.search(text)
        if dm:
            date = dm.group(1)
        events.append(Event(date, "ticket", _sanitize(p.name),
                            _extract_patterns(text), workflow, _sanitize(p.name)))
    return events


def collect_history_events(history_dir):
    events = []
    history_dir = Path(history_dir)
    if not history_dir.is_dir():
        return events
    for p in sorted(history_dir.glob("*.ledger.md")):
        text = safe_read(p)
        target = p.name
        if target.endswith(".ledger.md"):
            target = target[:-len(".ledger.md")]
        if target.endswith(".md"):
            target = target[:-len(".md")]
        workflow = target if target.startswith("/") else "/" + target
        for m in _HISTORY_SECTION_RE.finditer(text):
            date, title = m.group(1), m.group(2).strip()
            start = m.end()
            nxt = text.find("\n## ", start)
            body = text[start: nxt if nxt != -1 else len(text)]
            ref = _sanitize(f"{p.name}::{date}::{title[:40]}")
            events.append(Event(date, "history", ref, _extract_patterns(body),
                                workflow, _sanitize(title)))
    return events


def collect_events(workspace):
    workspace = Path(workspace)
    events = []
    events += collect_ticket_events(workspace / "helpdesk-tickets")
    events += collect_history_events(workspace / ".history")
    return events


def aggregate(events):
    by_pattern, by_workflow, by_source = {}, {}, {}
    for e in events:
        by_source[e.source] = by_source.get(e.source, 0) + 1
        if e.workflow:
            by_workflow[e.workflow] = by_workflow.get(e.workflow, 0) + 1
        for pat in e.patterns:
            by_pattern[pat] = by_pattern.get(pat, 0) + 1
    return {
        "total_events": len(events),
        "by_pattern": dict(sorted(by_pattern.items(), key=lambda kv: (-kv[1], kv[0]))),
        "by_workflow": dict(sorted(by_workflow.items(), key=lambda kv: (-kv[1], kv[0]))),
        "by_source": dict(sorted(by_source.items())),
    }
