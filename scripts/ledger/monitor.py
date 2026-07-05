"""
monitor.py — Ledger growth checks (read-only "warn" mode + "shard" mode)
==========================================================================
Two modes, one engine, because they're the same problem: an Append-Only
Ledger with no ceiling and no compression.

  * check_warn()  — count entries/bytes in a single tracked file; report a
    WARN verdict if either threshold is crossed. Never writes to the watched
    file — advisory only, exactly like registry.py's REVIEW verdict.
  * check_shard() — a tracked *directory* of dated shard files. Determines
    the real calendar quarter via datetime.date.today() (injectable for
    tests; the CLI always passes the real OS clock — never an LLM's guess at
    what day it is), finds the active shard by filename-sort convention (no
    separate pointer file, matching helpdesk-tickets/'s own open/closed
    convention), and rolls over when the quarter changes or a within-quarter
    safety-valve threshold is crossed.

Rollover never deletes anything: the old shard gets one appended closing
marker pointing at its successor; the new shard gets a header pointing back.
"""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from ledger._utils import safe_read

_QUARTER_OF_MONTH = {m: (m - 1) // 3 + 1 for m in range(1, 13)}


def quarter_label(d: date) -> str:
    return f"{d.year}-Q{_QUARTER_OF_MONTH[d.month]}"


@dataclass
class LedgerStatus:
    name: str
    mode: str
    entries: int = 0
    bytes: int = 0
    threshold_entries: int = 0
    threshold_bytes: int = 0
    warn: bool = False
    active_file: str = ""
    rolled_over: bool = False
    rollover_reason: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name, "mode": self.mode, "entries": self.entries,
            "bytes": self.bytes, "threshold_entries": self.threshold_entries,
            "threshold_bytes": self.threshold_bytes, "warn": self.warn,
            "active_file": self.active_file, "rolled_over": self.rolled_over,
            "rollover_reason": self.rollover_reason,
        }


def _count_entries(text: str, pattern: str) -> int:
    if not text:
        return 0
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def _over_threshold(entries: int, size: int, cfg: dict) -> bool:
    thr_e = cfg.get("warn_threshold_entries", 0)
    thr_b = cfg.get("warn_threshold_bytes", 0)
    return bool((thr_e and entries >= thr_e) or (thr_b and size >= thr_b))


def check_warn(workspace: Path, cfg: dict) -> LedgerStatus:
    """Warn-only mode: count and compare. Read-only — never writes."""
    path = Path(workspace) / cfg["path"]
    text = safe_read(path)
    entries = _count_entries(text, cfg["entry_pattern"])
    size = len(text.encode("utf-8"))
    return LedgerStatus(
        name=cfg["name"], mode="warn", entries=entries, bytes=size,
        threshold_entries=cfg.get("warn_threshold_entries", 0),
        threshold_bytes=cfg.get("warn_threshold_bytes", 0),
        warn=_over_threshold(entries, size, cfg), active_file=str(path),
    )


def _extract_placeholder(filename: str, name_pattern: str) -> str:
    """Pull whatever "{quarter}" resolved to out of a shard filename."""
    prefix, suffix = name_pattern.split("{quarter}")
    if filename.startswith(prefix) and filename.endswith(suffix):
        return filename[len(prefix): len(filename) - len(suffix)]
    return ""


def _find_active_shard(shard_dir: Path, name_pattern: str) -> Optional[Path]:
    if not shard_dir.is_dir():
        return None
    prefix, suffix = name_pattern.split("{quarter}")
    matches = sorted(
        p for p in shard_dir.iterdir()
        if p.is_file() and p.name.startswith(prefix) and p.name.endswith(suffix)
    )
    return matches[-1] if matches else None


def _shard_header(label: str, prior_name: Optional[str]) -> str:
    lines = [
        f"# WORKFLOW_MANIFEST narrative — shard {label}",
        "# Append-only. Rolled over by scripts/ledger/monitor.py — never edit a prior entry.",
        f"# Superseded from: {prior_name}" if prior_name else "# First shard — no prior shard.",
        "---", "",
    ]
    return "\n".join(lines)


def _closing_marker(next_name: str) -> str:
    return (
        f"\n---\n**[SHARD CLOSED — superseded by {next_name}. "
        f"This shard's own content is unchanged and preserved; new entries continue there.]**\n"
    )


def _next_same_quarter_label(active_label: str, quarter: str) -> str:
    """First overflow within a quarter: "2026-Q3" -> "2026-Q3b". Then "b" -> "c", etc."""
    if active_label == quarter:
        return f"{quarter}b"
    return f"{active_label[:-1]}{chr(ord(active_label[-1]) + 1)}"


def check_shard(workspace: Path, cfg: dict, today: Optional[date] = None) -> LedgerStatus:
    """
    Determine the active shard, roll over if warranted, report status.
    `today` is injectable for deterministic tests; the CLI path always passes
    the real date. This function never infers "what day is it" itself.
    """
    workspace = Path(workspace)
    today = today or date.today()
    q = quarter_label(today)
    shard_dir = workspace / cfg["active_dir"]
    shard_dir.mkdir(parents=True, exist_ok=True)
    name_pattern = cfg["shard_name_pattern"]
    active = _find_active_shard(shard_dir, name_pattern)

    if active is None:
        new_path = shard_dir / name_pattern.replace("{quarter}", q)
        new_path.write_text(_shard_header(q, None), encoding="utf-8")
        return LedgerStatus(
            name=cfg["name"], mode="shard", entries=0, bytes=new_path.stat().st_size,
            threshold_entries=cfg.get("warn_threshold_entries", 0),
            threshold_bytes=cfg.get("warn_threshold_bytes", 0),
            warn=False, active_file=str(new_path), rolled_over=True,
            rollover_reason="first run — no shard existed",
        )

    text = safe_read(active)
    entries = _count_entries(text, cfg["entry_pattern"])
    size = len(text.encode("utf-8"))
    active_label = _extract_placeholder(active.name, name_pattern)
    quarter_changed = active_label != q and not active_label.startswith(q)
    size_exceeded = _over_threshold(entries, size, cfg)

    if not quarter_changed and not size_exceeded:
        return LedgerStatus(
            name=cfg["name"], mode="shard", entries=entries, bytes=size,
            threshold_entries=cfg.get("warn_threshold_entries", 0),
            threshold_bytes=cfg.get("warn_threshold_bytes", 0),
            warn=False, active_file=str(active), rolled_over=False,
        )

    if quarter_changed:
        new_label = q
        reason = f"quarter changed ({active_label} -> {q})"
    else:
        new_label = _next_same_quarter_label(active_label, q)
        reason = f"size threshold exceeded within {q} (entries={entries}, bytes={size})"

    new_name = name_pattern.replace("{quarter}", new_label)
    new_path = shard_dir / new_name
    active.write_text(text.rstrip("\n") + "\n" + _closing_marker(new_name), encoding="utf-8")
    new_path.write_text(_shard_header(new_label, active.name), encoding="utf-8")

    return LedgerStatus(
        name=cfg["name"], mode="shard", entries=0, bytes=new_path.stat().st_size,
        threshold_entries=cfg.get("warn_threshold_entries", 0),
        threshold_bytes=cfg.get("warn_threshold_bytes", 0),
        warn=False, active_file=str(new_path), rolled_over=True, rollover_reason=reason,
    )


def check_ledger(workspace: Path, cfg: dict, today: Optional[date] = None) -> LedgerStatus:
    """Dispatch by mode. Unknown modes are treated as warn-only, never crash."""
    if cfg.get("mode") == "shard":
        return check_shard(workspace, cfg, today=today)
    return check_warn(workspace, cfg)


def run_all(workspace: Path, ledgers, today: Optional[date] = None) -> list:
    return [check_ledger(workspace, cfg, today=today) for cfg in ledgers]
