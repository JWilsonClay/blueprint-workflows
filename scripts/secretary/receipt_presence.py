"""
receipt_presence.py — Generalized receipt-family existence + tail check
==========================================================================
secretary.md currently hardcodes this exact pattern twice — once for
TRIAGE_RECEIPTS.md, once for DESIGN_RECEIPTS.md:

    ls .workflow_state/receipts/<NAME>.md 2>/dev/null && echo present || echo absent
    tail -n 5 .workflow_state/receipts/<NAME>.md 2>/dev/null || true

This module generalizes it to any filename, so a future receipt-family
member needs one more entry in a list, not a new hardcoded prose block.
Reports existence + last N lines only — never judges whether the receipt
content is adequate.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from engine_utils import safe_read


@dataclass
class ReceiptPresence:
    filename: str
    path: str
    present: bool
    last_lines: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "filename": self.filename,
            "path": self.path,
            "present": self.present,
            "last_lines": self.last_lines,
        }


def check_receipt_family(receipts_dir: str, filenames: List[str], tail_lines: int = 5) -> List[ReceiptPresence]:
    """
    For each filename in `filenames`, check for its presence under
    `receipts_dir` and report its last `tail_lines` lines if present.
    """
    results: List[ReceiptPresence] = []
    base = Path(receipts_dir)
    for filename in filenames:
        path = base / filename
        text = safe_read(path)
        present = path.is_file()
        last_lines = text.splitlines()[-tail_lines:] if text else []
        results.append(
            ReceiptPresence(filename=filename, path=str(path), present=present, last_lines=last_lines)
        )
    return results
