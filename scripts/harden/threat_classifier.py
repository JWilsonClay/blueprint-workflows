"""
threat_classifier.py — Threat Context Heuristic (read-only, ADVISORY)
======================================================================
Suggests a file's Threat Context — NETWORK-FACING > PRIVILEGED > DATA-HANDLING >
INTERNAL-ONLY — by matching import/keyword signatures. /harden Phase 1 uses the
threat context to weight checklist scrutiny.

⚠ ADVISORY ONLY. This is a heuristic suggestion, not a determination. The
/harden agent owns the final threat model (Phase 2a: attack surface, worst-case
impact, trust boundaries) — a keyword match cannot reason about how data
actually flows. The classifier exists to PRIORITIZE the file list, never to
conclude that a file is safe: an INTERNAL-ONLY label is a starting hypothesis,
not a clearance.
"""

import re
from typing import Dict, List, Tuple

# Ordered by tier priority — first tier with a match wins (matches the workflow's
# NETWORK-FACING > PRIVILEGED > DATA-HANDLING > INTERNAL-ONLY precedence).
_TIERS: List[Tuple[str, List[str]]] = [
    ("NETWORK-FACING", [
        r"\bflask\b", r"\bfastapi\b", r"\bdjango\b", r"\brequests\b",
        r"\burllib\b", r"\bhttp\.client\b", r"\bhttp\.server\b", r"\bsocket\b",
        r"\baiohttp\b", r"\btornado\b", r"\bbottle\b", r"\bwerkzeug\b",
        r"\bwebhook\b", r"\bexpress\b", r"\baxios\b", r"(?<![\w.])fetch\s*\(",
        r"\bboto3\b", r"\bparamiko\b", r"\bgrpc\b",
    ]),
    ("PRIVILEGED", [
        r"(?<![\w.])os\.set[ug]id\s*\(", r"(?<![\w.])os\.setegid\s*\(",
        r"(?<![\w.])os\.seteuid\s*\(", r"(?<![\w.])os\.chown\s*\(",
        r"\bsudo\b", r"\bsetuid\b", r"\bctypes\b", r"/etc/", r"\bpwd\b",
        r"\bspwd\b", r"(?<![\w.])os\.fork\s*\(", r"\bsubprocess\b",
    ]),
    ("DATA-HANDLING", [
        r"(?<![\w.])open\s*\(", r"\bsqlite3\b", r"\bpsycopg2\b",
        r"\bsqlalchemy\b", r"\bpymysql\b", r"\bpandas\b", r"(?<![\w.])csv\b",
        r"(?<![\w.])json\.load", r"\bpickle\b", r"\.read\s*\(", r"\.write\s*\(",
        r"\bpathlib\b", r"(?<![\w.])shutil\b",
    ]),
]


class ThreatClassifier:
    """Read-only, advisory threat-context suggester."""

    def classify(self, text: str) -> Dict:
        """
        Return {"context": <tier>, "signals": [matched keywords]} for one file.

        The highest-priority tier with at least one match wins; a file matching
        nothing is INTERNAL-ONLY (a hypothesis, never a clearance).
        """
        for tier, patterns in _TIERS:
            signals: List[str] = []
            for pat in patterns:
                if re.search(pat, text):
                    signals.append(pat.strip("\\b").replace("\\", ""))
                    if len(signals) >= 6:
                        break
            if signals:
                return {"context": tier, "signals": signals}
        return {"context": "INTERNAL-ONLY", "signals": []}
