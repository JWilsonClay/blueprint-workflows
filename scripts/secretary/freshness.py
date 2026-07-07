"""
freshness.py — Artifact freshness check (mtime vs. a reference time)
=======================================================================
Answers one mechanical question: did this file's mtime change at or after
`since`? Never asks whether the *content* written is good, complete, or
honest — only whether the file changed. A script cannot and must not grade
content; that stays with the model.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Union


@dataclass
class FreshnessResult:
    path: str
    exists: bool
    mtime_iso: str = ""
    touched_since: bool = False

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "exists": self.exists,
            "mtime_iso": self.mtime_iso,
            "touched_since": self.touched_since,
        }


def _to_datetime(since: Union[datetime, date]) -> datetime:
    """
    Normalize `since` to a tz-aware datetime. A bare `date` (e.g. today's
    calendar date, per the suite's "always the real OS clock, never
    LLM-inferred" convention already used by scripts/ledger/) is treated as
    midnight UTC on that date — the start of the day, not a point in time
    partway through it, so "touched today" reads as "touched any time today."
    """
    if isinstance(since, datetime):
        return since if since.tzinfo else since.replace(tzinfo=timezone.utc)
    return datetime(since.year, since.month, since.day, tzinfo=timezone.utc)


def check_freshness(paths: List[str], since: Union[datetime, date] = None) -> List[FreshnessResult]:
    """
    For each path: does it exist, and if so, is its mtime >= `since`?

    `since` defaults to the start of today (real OS clock — `date.today()`,
    never agent-inferred) if omitted, matching the common case ("was this
    touched today").
    """
    since_dt = _to_datetime(since if since is not None else date.today())
    results: List[FreshnessResult] = []
    for raw_path in paths:
        p = Path(raw_path)
        if not p.exists():
            results.append(FreshnessResult(path=str(p), exists=False))
            continue
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        results.append(
            FreshnessResult(
                path=str(p),
                exists=True,
                mtime_iso=mtime.isoformat(),
                touched_since=mtime >= since_dt,
            )
        )
    return results
