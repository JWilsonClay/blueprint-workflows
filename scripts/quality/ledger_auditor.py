"""
ledger_auditor.py — Quality Witness Ledger Auditor (read-only)
================================================================
Parses and validates the Quality Witness log produced by /quality Step 7:

    [YYYY-MM-DD HH:MM] | type=<...> | level=<...> | findings=<N> | agent=<...> | target=<...>

Computes `unreviewed_entries` = valid entries appearing AFTER the last
`[REVIEWED <date>]` marker line (this gives the previously-undefined "unreviewed"
count a deterministic meaning), and raises the P3 audit trigger at the threshold
/triage acts on. Makes the formerly write-only, never-verified witness log a
checkable artifact.
"""

import re
from pathlib import Path
from typing import Dict

from engine_utils import safe_read

VALID_LEVELS = ("Standard", "Elevated", "Maximum")
AUDIT_THRESHOLD = 25  # /triage fires a P3 recommendation at 25+ unreviewed entries.

_ENTRY_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s*\|\s*(?P<rest>.+)$")
# Accept both marker styles: the engine's `[REVIEWED <date>]` and the
# `## REVIEWED` form referenced in triage.md, so "unreviewed" means the same
# thing to the engine and to the workflow that documents it.
_REVIEWED_RE = re.compile(
    r"^(?:\[REVIEWED(?:\s+(?P<date>[^\]]+?))?\]"
    r"|#{1,6}\s*REVIEWED(?:\s+(?P<date2>.+?))?)\s*$",
    re.IGNORECASE,
)
_REQUIRED_FIELDS = ("type", "level", "findings", "agent")


def _parse_kv(rest: str) -> Dict[str, str]:
    fields = {}
    for part in rest.split("|"):
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
    return fields


class LedgerAuditor:
    """Read-only auditor of the Quality Witness log."""

    def audit(self, log_path: Path) -> Dict:
        log_path = Path(log_path)
        result = {
            "log_found": False,
            "log_path": str(log_path),
            "total_entries": 0,
            "valid_entries": 0,
            "malformed_lines": [],
            "last_reviewed": None,
            "unreviewed_entries": 0,
            "entries_by_level": {lvl: 0 for lvl in VALID_LEVELS},
            "audit_trigger": "NONE",
        }
        if not log_path.is_file():
            return result

        result["log_found"] = True
        text = safe_read(log_path)
        entries_since_review = 0

        for line_no, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue

            reviewed = _REVIEWED_RE.match(line)
            if reviewed:
                gd = reviewed.groupdict()
                result["last_reviewed"] = gd.get("date") or gd.get("date2") or "(unspecified)"
                entries_since_review = 0
                continue

            m = _ENTRY_RE.match(line)
            if not m:
                result["malformed_lines"].append(
                    {"line_no": line_no, "reason": "does not match witness format",
                     "raw": line[:120]}
                )
                continue

            result["total_entries"] += 1
            fields = _parse_kv(m.group("rest"))
            reason = self._field_error(fields)
            if reason:
                result["malformed_lines"].append(
                    {"line_no": line_no, "reason": reason, "raw": line[:120]}
                )
                continue

            result["valid_entries"] += 1
            entries_since_review += 1
            result["entries_by_level"][fields["level"]] += 1

        result["unreviewed_entries"] = entries_since_review
        if result["unreviewed_entries"] >= AUDIT_THRESHOLD:
            result["audit_trigger"] = "P3"
        return result

    @staticmethod
    def _field_error(fields: Dict[str, str]):
        missing = [f for f in _REQUIRED_FIELDS if f not in fields]
        if missing:
            return f"missing fields: {', '.join(missing)}"
        if fields["level"] not in VALID_LEVELS:
            return f"invalid level '{fields['level']}'"
        if not fields["findings"].lstrip("-").isdigit():
            return f"findings not an integer: '{fields['findings']}'"
        return None
