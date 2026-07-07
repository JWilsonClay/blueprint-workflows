"""
secret_scanner.py — Secret-pattern leakage scan with structural redaction (Phase 3a)
=======================================================================================
Same keyword set Phase 3a already gives verbatim in
claude-commands/redteam.md: SECRET|SALT|API_KEY|TOKEN|PASSWORD|ADMIN_PATH|
BACKDOOR. The one thing this module adds beyond a plain grep: **the matched
line is never included in the output, only which keyword matched and
where** — a structural enforcement of STRICT RULE 6 ("Never expose actual
secret values in the REDTEAM RECEIPT or in any log entry"). A plain grep
result pasted into a receipt is exactly the failure this rule warns
against; this scanner makes that failure mode architecturally impossible
rather than trusting the agent to remember to redact it every time.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from engine_utils import safe_read

DEFAULT_PATTERNS = [
    "SECRET", "SALT", "API_KEY", "TOKEN", "PASSWORD", "ADMIN_PATH", "BACKDOOR",
]


@dataclass
class SecretHit:
    file: str
    line: int
    pattern_matched: str

    def as_dict(self) -> dict:
        return {"file": self.file, "line": self.line, "pattern_matched": self.pattern_matched}


def scan_for_secrets(paths: List[str], patterns: List[str] = None) -> List[SecretHit]:
    """
    Scan each given file for any of `patterns` (default: DEFAULT_PATTERNS).
    Returns file/line/which-keyword-matched only — deliberately NEVER the
    matched line's actual content, so a live secret cannot leak into this
    tool's own output, its JSON report, or any receipt built from it.
    """
    patterns = patterns or DEFAULT_PATTERNS
    compiled = [(p, re.compile(re.escape(p))) for p in patterns]

    hits: List[SecretHit] = []
    for raw_path in paths:
        path = Path(raw_path)
        text = safe_read(path)
        if not text:
            continue
        for line_idx, line in enumerate(text.splitlines(), start=1):
            for pattern_name, pattern in compiled:
                if pattern.search(line):
                    hits.append(SecretHit(file=str(path), line=line_idx, pattern_matched=pattern_name))
    return hits
