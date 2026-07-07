"""
mock_scanner.py — Mock call-site enumeration (Phase 1b)
==========================================================
Reports facts only: file, line, which construct, and the raw line text.
Whether a mock is VALID, a TAUTOLOGY, or UNREALISTIC is never this module's
call — that classification requires reading what the mock's return value
represents and whether the test would still pass if the mocked function
were deleted, both genuinely semantic judgments.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from engine_utils import safe_read

_MOCK_PATTERNS = [
    ("patch_decorator", re.compile(r"@(?:mock\.)?patch(?:\.object)?\(")),
    ("Mock_call", re.compile(r"\bMock\(")),
    ("MagicMock_call", re.compile(r"\bMagicMock\(")),
    ("monkeypatch_call", re.compile(r"\bmonkeypatch\.")),
]


@dataclass
class MockUsage:
    file: str
    line: int
    construct: str
    snippet: str

    def as_dict(self) -> dict:
        return {"file": self.file, "line": self.line, "construct": self.construct, "snippet": self.snippet}


def scan_for_mocks(paths: List[str]) -> List[MockUsage]:
    """
    Scan each given file for mock construct usage. Non-.py files and
    missing/unreadable files are silently skipped (mirrors every other
    read-only engine's degrade-safe contract).
    """
    usages: List[MockUsage] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix != ".py":
            continue
        text = safe_read(path)
        if not text:
            continue
        for line_idx, line in enumerate(text.splitlines(), start=1):
            for construct, pattern in _MOCK_PATTERNS:
                if pattern.search(line):
                    usages.append(
                        MockUsage(
                            file=str(path),
                            line=line_idx,
                            construct=construct,
                            snippet=line.strip()[:200],
                        )
                    )
    return usages
