"""
staleness.py — Days-open computation for OPEN tickets
=========================================================
Reports days-open per open ticket, derived from the filename's own
YYYYMMDD prefix (STRICT RULE 10: "the date of the failure event"). Never
judges whether a given age is "too stale" — that threshold is context-
dependent and STRICT RULE 9 already reserves urgency judgment for the
agent. A caller-supplied threshold is used only to set an advisory flag,
never a hardcoded suite opinion about what counts as stale.
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from helpdesk_tickets.ticket_parser import list_ticket_files, parse_filename


@dataclass
class StalenessResult:
    filename: str
    filed_date: str
    days_open: int
    exceeds_threshold: bool

    def as_dict(self) -> dict:
        return {
            "filename": self.filename,
            "filed_date": self.filed_date,
            "days_open": self.days_open,
            "exceeds_threshold": self.exceeds_threshold,
        }


def compute_staleness(
    tickets_dir: str, today: Optional[date] = None, threshold_days: int = 14
) -> List[StalenessResult]:
    """
    For every open (non-CLOSED_) ticket in `tickets_dir`, compute days
    between its filename's YYYYMMDD and `today` (defaults to the real OS
    clock, matching this suite's ledger-engine convention of never letting
    an LLM infer "what day is it"). A malformed filename's date cannot be
    parsed and is silently skipped — that's a schema_validator finding, not
    a staleness one.
    """
    today = today or date.today()
    results: List[StalenessResult] = []
    for filename in list_ticket_files(tickets_dir):
        info = parse_filename(filename)
        if info is None or info.closed:
            continue
        try:
            filed = date(int(info.date[0:4]), int(info.date[4:6]), int(info.date[6:8]))
        except ValueError:
            continue
        days_open = (today - filed).days
        results.append(
            StalenessResult(
                filename=filename,
                filed_date=info.date,
                days_open=days_open,
                exceeds_threshold=days_open > threshold_days,
            )
        )
    return results
