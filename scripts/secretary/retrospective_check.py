"""
retrospective_check.py — Last-dated-entry extraction + Retrospective Lag
===========================================================================
Formalizes two mechanisms secretary.md already specifies as shell commands
the model must eyeball:

  - ADDENDUM E: `tail -n 10 PROCESS_LEARNINGS.md`, then eyeball whether the
    last entry's date matches today.
  - Step 0b.5 (Retrospective Lag): two separate greps (manifest narrative
    shards' latest "SESSION APPEND" date; PROCESS_LEARNINGS.md's latest
    date), then eyeball which is later.

Both are pure date extraction + comparison — arithmetic, not judgment. This
module moves the comparison itself into a boolean the model reads as a fact,
per the corrected design in
docs/compression-staging/secretary-honest-design.md Section 4.
"""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

# Matches "## 2026-07-07" or "## 2026-07-06 to 2026-07-07 — ..." — the first
# YYYY-MM-DD on a "## "-prefixed line is the entry's date, per
# PROCESS_LEARNINGS.md's own convention. re.MULTILINE so "^" anchors to each
# line, not just the start of the whole file's text.
PROCESS_LEARNINGS_ENTRY_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})", re.MULTILINE)

# Matches "## **[SESSION APPEND — 2026-07-04 — ...]**" — the manifest
# narrative shards' own convention (manifest/history/*.md).
SESSION_APPEND_RE = re.compile(r"SESSION APPEND\s*[—-]+\s*(\d{4}-\d{2}-\d{2})")


def _parse_iso_date(text: str) -> Optional[date]:
    try:
        y, m, d = (int(x) for x in text.split("-"))
        return date(y, m, d)
    except (ValueError, AttributeError):
        return None


def last_dated_entry(paths: List[str], pattern: re.Pattern) -> Optional[date]:
    """
    Scan every given path with `pattern` (must have exactly one capture
    group producing a YYYY-MM-DD string) and return the MAXIMUM date found
    across all matches in all paths — not simply the last line's date, since
    a multi-shard glob's files are not guaranteed to be read in chronological
    order, and even a single append-only file could (rarely) receive an
    out-of-order backfilled entry. Missing/unreadable paths are silently
    skipped (mirrors every other read-only engine's degrade-safe contract).
    """
    latest: Optional[date] = None
    for raw_path in paths:
        text = safe_read(Path(raw_path))
        if not text:
            continue
        for match in pattern.finditer(text):
            d = _parse_iso_date(match.group(1))
            if d is not None and (latest is None or d > latest):
                latest = d
    return latest


@dataclass
class RetrospectiveFreshness:
    process_learnings_path: str
    latest_entry_date: Optional[str]
    matches_today: bool
    today: str

    def as_dict(self) -> dict:
        return {
            "process_learnings_path": self.process_learnings_path,
            "latest_entry_date": self.latest_entry_date,
            "matches_today": self.matches_today,
            "today": self.today,
        }


def check_retrospective_freshness(process_learnings_path: str, today: date = None) -> RetrospectiveFreshness:
    """
    Formalizes ADDENDUM E: does PROCESS_LEARNINGS.md's most recent entry
    date match today? `today` defaults to the real OS clock (never
    agent-inferred), per this suite's ledger-engine convention.
    """
    today = today or date.today()
    latest = last_dated_entry([process_learnings_path], PROCESS_LEARNINGS_ENTRY_RE)
    return RetrospectiveFreshness(
        process_learnings_path=str(process_learnings_path),
        latest_entry_date=latest.isoformat() if latest else None,
        matches_today=(latest == today),
        today=today.isoformat(),
    )


@dataclass
class LagReport:
    narrative_latest_date: Optional[str]
    process_learnings_latest_date: Optional[str]
    gap_detected: bool
    reason: str

    def as_dict(self) -> dict:
        return {
            "narrative_latest_date": self.narrative_latest_date,
            "process_learnings_latest_date": self.process_learnings_latest_date,
            "gap_detected": self.gap_detected,
            "reason": self.reason,
        }


def compute_retrospective_lag(history_paths: List[str], process_learnings_path: str) -> LagReport:
    """
    Formalizes Step 0b.5: compare the latest "SESSION APPEND" date across all
    `manifest/history/` shards against PROCESS_LEARNINGS.md's latest entry
    date. `gap_detected` is True when the narrative is strictly ahead of the
    retrospective log — meaning at least one session closed via Phase 1
    without its Phase 6 retrospective landing. This is advisory (STRICT RULE
    20) — the engine reports the fact; whether/how to act on a gap stays
    with the model.
    """
    narrative_latest = last_dated_entry(history_paths, SESSION_APPEND_RE)
    pl_latest = last_dated_entry([process_learnings_path], PROCESS_LEARNINGS_ENTRY_RE)

    if narrative_latest is None and pl_latest is None:
        return LagReport(None, None, False, "no dated entries found in either source")
    if narrative_latest is None:
        return LagReport(None, pl_latest.isoformat(), False, "no narrative shard entries found")
    if pl_latest is None:
        return LagReport(narrative_latest.isoformat(), None, True,
                          "narrative has entries but PROCESS_LEARNINGS.md has none")

    gap = narrative_latest > pl_latest
    reason = (
        f"narrative latest ({narrative_latest.isoformat()}) is ahead of "
        f"PROCESS_LEARNINGS.md latest ({pl_latest.isoformat()})"
        if gap else
        "narrative and PROCESS_LEARNINGS.md are consistent"
    )
    return LagReport(narrative_latest.isoformat(), pl_latest.isoformat(), gap, reason)
