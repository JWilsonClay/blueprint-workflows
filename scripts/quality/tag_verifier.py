"""
tag_verifier.py — Quality Chain Tag Verifier (read-only)
==========================================================
Extracts and validates Quality Chain Tags embedded by /quality Step 7 in
cross-agent outputs:

    [QUALITY: type=<...> | level=<Standard/Elevated/Maximum> | critique_findings=<N> | agent=<...>]

The Quality Chain Tag exists so a RECEIVING agent can verify quality-protocol
application WITHOUT trusting the producing agent's claim. /quality formerly left
that verification to instruction ("the receiving agent should note ... UNVERIFIED").
This module makes it structural: a tag is VALID, MALFORMED, or ABSENT — checkable,
not trusted.
"""

import re
from typing import Dict

VALID_LEVELS = ("Standard", "Elevated", "Maximum")
_TAG_RE = re.compile(r"\[QUALITY:(?P<body>[^\]]*)\]")
_REQUIRED = ("type", "level", "critique_findings", "agent")


def _parse_kv(body: str) -> Dict[str, str]:
    fields = {}
    for part in body.split("|"):
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
    return fields


class TagVerifier:
    """Read-only verifier of Quality Chain Tags in a block of text."""

    def verify_text(self, text: str) -> Dict:
        tags = []
        for m in _TAG_RE.finditer(text):
            body = m.group("body")
            # A `[QUALITY: …]` with no key=value is a documentation reference to
            # the tag syntax, not an emitted tag. Don't flag prose as MALFORMED.
            if "=" not in body:
                continue
            fields = _parse_kv(body)
            issues = []
            for field in _REQUIRED:
                if not fields.get(field):
                    issues.append(f"missing/empty: {field}")
            level = fields.get("level")
            if level and level not in VALID_LEVELS:
                issues.append(f"invalid level: {level}")
            cf = fields.get("critique_findings")
            if cf and not cf.lstrip("-").isdigit():
                issues.append("critique_findings not an integer")
            tags.append({"fields": fields, "issues": issues, "valid": not issues})

        if not tags:
            status = "ABSENT"
        elif all(t["valid"] for t in tags):
            status = "VALID"
        else:
            status = "MALFORMED"
        return {"status": status, "count": len(tags), "tags": tags}
