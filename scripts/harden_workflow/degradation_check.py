"""
degradation_check.py — Standard Version extraction + comparison
===================================================================
Formalizes /harden-workflow's Phase 1 Degradation Check: extract the
Standard Version a workflow was last certified under, compare it to the
current standard version. Pure text extraction + integer comparison — never
judges which new criteria matter or whether re-certification is warranted;
that stays with the model exactly as Phase 1's own text already states.
"""

import re
from dataclasses import dataclass
from typing import Optional

# Mirrors this workflow's own GLOSSARY: "Current Standard Version: 3".
# Update here AND in claude-commands/harden-workflow.md's GLOSSARY when the
# standard next increments — the two are independent statements of the same
# fact (one prose, one engine constant), same relationship as
# scripts/gitignore/seed.toml vs. its DEFAULT_SEED mirror.
CURRENT_STANDARD_VERSION = 3

_STANDARD_VERSION_RE = re.compile(r"Standard Version:\s*(\d+)")


def extract_standard_version(text: str) -> Optional[int]:
    """
    Return the LAST "Standard Version: N" mention in `text` — a Hardening
    Certificate's own field is typically the final and most authoritative
    such mention in a workflow file (Change Log entries may cite earlier
    versions historically). Returns None if no such mention exists.
    """
    matches = _STANDARD_VERSION_RE.findall(text)
    if not matches:
        return None
    return int(matches[-1])


@dataclass
class DegradationResult:
    certified_version: Optional[int]
    current_version: int
    degraded: bool

    def as_dict(self) -> dict:
        return {
            "certified_version": self.certified_version,
            "current_version": self.current_version,
            "degraded": self.degraded,
        }


def check_degradation(certified_version: Optional[int],
                       current_version: int = CURRENT_STANDARD_VERSION) -> DegradationResult:
    """
    `degraded` is True only when a certified version is known AND it is
    strictly behind `current_version`. A workflow with no certified version
    on record is reported as `degraded: False` here — absence of a stamp is
    a different finding (no prior certification to degrade from), not a
    degradation; the caller distinguishes the two via `certified_version`
    being None.
    """
    degraded = certified_version is not None and certified_version < current_version
    return DegradationResult(
        certified_version=certified_version,
        current_version=current_version,
        degraded=degraded,
    )
