"""
phase_status.py — tasks.md + BUILD_RECEIPTS.md Phase Status Engine
=====================================================================
Answers one mechanical question the Focus Evidence Engine could not
previously answer: for a plan item whose anchors are absent from the
substrate, has the phase that item belongs to actually been claimed
complete — or is it legitimately future work?

Without this, /focus-plan's PHASE 2 adjudication had no mechanical fact to
adjudicate against, and instead collapsed every not-yet-built item into
UNVERIFIABLE (a HALT), indistinguishable from a real problem. See
helpdesk-tickets/CLOSED_20260630_focus-plan_workflow.md.

Two read-only parses, cross-referenced by phase name:

  1. parse_tasks_md()      — tasks.md, split into phases ("Phase N" / "Stage N"
                              headers, matching the "Phase/Stage:" vocabulary
                              already used by /execute-build's receipt writer),
                              each with a checkbox tally and a derived status.
  2. parse_build_receipts() — .workflow_state/receipts/BUILD_RECEIPTS.md,
                              split into entries on the exact format
                              /execute-build writes (execute-build.md
                              Step 6 / Phase 7): "## DATE — /execute-build —
                              <phase>" blocks containing "- Phase/Stage:" and
                              "- Grade/Status:" lines, separated by "---".

Matching a tasks.md phase title to a BUILD_RECEIPTS.md "Phase/Stage:" value is
done by normalized exact string match. This is safe to do mechanically —
unlike matching an implementation-plan.md item to a tasks.md phase (two
independently-authored documents, which stays a judgment call for the agent)
— because both strings originate from the same <ACTIVE_PHASE name> in the
same /execute-build run (execute-build.md L301 marks the tasks, L327/331
write the receipt from the identical name).

Design note: phase boundaries are detected by title pattern ("Phase N" /
"Stage N"), not raw header level, so nested sub-headers inside a phase (e.g.
"### Acceptance Criteria") are correctly treated as part of that phase's body
rather than fragmenting into phantom phases. If a workspace's tasks.md uses a
naming convention this pattern does not recognize, `found` is still True but
`phases` is empty — the workflow must treat that as "structure not
recognized," not as "no phases exist."

Architecturally read-only, same contract as the rest of scripts/focus/: no
write primitives, bounded reads via safe_read.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

TASKS_MD_NAME = "tasks.md"
BUILD_RECEIPTS_RELPATH = Path(".workflow_state") / "receipts" / "BUILD_RECEIPTS.md"

_HEADER_RE = re.compile(r"^(#{2,4})\s+(.*\S)\s*$")
_PHASE_TITLE_RE = re.compile(r"^(phase|stage)\s+\d+\b", re.IGNORECASE)
_CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX/~])\]\s")
_FENCE_RE = re.compile(r"^\s*```")
_RECEIPT_SPLIT_RE = re.compile(r"^\s*---\s*$", re.MULTILINE)
_RECEIPT_FIELD_RE = re.compile(r"^-\s*([A-Za-z/ ]+?):\s*(.+)$")

# Grade/Status values the receipt writer is known to emit for a finished
# phase (execute-build.md L316, L329, L364, L374). Compared case-insensitively.
_COMPLETE_STATUSES = frozenset({"phase complete", "project build complete"})


def _normalize(title: str) -> str:
    """Collapse a phase title to a case/punctuation/whitespace-insensitive key."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


@dataclass
class PhaseCheckboxes:
    done: int = 0
    open: int = 0
    in_progress: int = 0

    def as_dict(self) -> dict:
        return {"done": self.done, "open": self.open, "in_progress": self.in_progress}


@dataclass
class Phase:
    """One tasks.md phase and everything mechanically knowable about its status."""
    title: str
    source_line: int
    checkboxes: PhaseCheckboxes
    status: str = "no_checkboxes"      # "complete" | "in_progress" | "not_started" | "no_checkboxes"
    receipt_status: str = "not_checked"  # "found_complete" | "found_incomplete" | "not_found" | "receipts_file_absent"

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "source_line": self.source_line,
            "checkboxes": self.checkboxes.as_dict(),
            "status": self.status,
            "receipt_status": self.receipt_status,
        }


@dataclass
class ReceiptEntry:
    phase: str
    grade_status: str


@dataclass
class TasksMdReport:
    found: bool
    path: Optional[str]
    receipts_file_found: bool
    phases: List[Phase] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "found": self.found,
            "path": self.path,
            "receipts_file_found": self.receipts_file_found,
            "phases": [p.as_dict() for p in self.phases],
        }


def _strip_fences(lines: List[str]) -> List[bool]:
    """Return a parallel bool list: True where the line is inside a fenced code block."""
    in_fence = []
    fenced = False
    for line in lines:
        if _FENCE_RE.match(line):
            fenced = not fenced
            in_fence.append(True)  # the fence marker line itself is excluded too
            continue
        in_fence.append(fenced)
    return in_fence


def parse_tasks_md(text: str) -> List[Phase]:
    """
    Split tasks.md into phases and tally each phase's own checkboxes.

    A phase boundary is a level 2-4 header whose title starts with "Phase N"
    or "Stage N" (case-insensitive) — the vocabulary /execute-build's Phase
    Map and receipt writer already use. Other headers (e.g. a "### Acceptance
    Criteria" sub-section) do not start a new phase; their checkboxes count
    toward the enclosing phase.
    """
    lines = text.splitlines()
    fenced = _strip_fences(lines)

    headers = []  # (line_idx, title)
    for idx, line in enumerate(lines):
        if fenced[idx]:
            continue
        m = _HEADER_RE.match(line)
        if m and _PHASE_TITLE_RE.match(m.group(2).strip()):
            headers.append((idx, m.group(2).strip()))

    phases: List[Phase] = []
    for i, (line_idx, title) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(lines)
        counts = PhaseCheckboxes()
        for line in lines[line_idx:end]:
            m = _CHECKBOX_RE.match(line)
            if not m:
                continue
            mark = m.group(1).lower()
            if mark == "x":
                counts.done += 1
            elif mark == " ":
                counts.open += 1
            else:  # "/" or "~"
                counts.in_progress += 1

        total = counts.done + counts.open + counts.in_progress
        if total == 0:
            status = "no_checkboxes"
        elif counts.done == total:
            status = "complete"
        elif counts.done > 0 or counts.in_progress > 0:
            status = "in_progress"
        else:
            status = "not_started"

        phases.append(Phase(title=title, source_line=line_idx + 1, checkboxes=counts, status=status))
    return phases


def parse_build_receipts(text: str) -> List[ReceiptEntry]:
    """
    Split BUILD_RECEIPTS.md into entries, extracting Phase/Stage + Grade/Status.

    Malformed blocks (missing either field) are skipped rather than raising —
    a receipt file is an append-only log written by shell heredocs; a
    corrupted or partial entry must not abort the whole parse.
    """
    entries: List[ReceiptEntry] = []
    for block in _RECEIPT_SPLIT_RE.split(text):
        phase = None
        grade_status = None
        for line in block.splitlines():
            m = _RECEIPT_FIELD_RE.match(line.strip())
            if not m:
                continue
            key = m.group(1).strip().lower()
            if key == "phase/stage":
                phase = m.group(2).strip()
            elif key == "grade/status":
                grade_status = m.group(2).strip()
        if phase and grade_status:
            entries.append(ReceiptEntry(phase=phase, grade_status=grade_status))
    return entries


def _receipt_status_for(title: str, receipts: List[ReceiptEntry]) -> str:
    target = _normalize(title)
    matches = [r for r in receipts if _normalize(r.phase) == target]
    if not matches:
        return "not_found"
    if any(r.grade_status.lower() in _COMPLETE_STATUSES for r in matches):
        return "found_complete"
    return "found_incomplete"


def build_phase_status_report(workspace: Path) -> TasksMdReport:
    """
    Locate tasks.md and (if present) BUILD_RECEIPTS.md, and produce the
    per-phase status report /focus-plan PHASE 2 uses to adjudicate absent
    anchors.

    found=False means tasks.md does not exist at all — itself meaningful:
    the plan has not been broken into execution phases yet, so every absent
    anchor is presumptively PENDING, not a MISMATCH candidate.
    """
    workspace = Path(workspace)
    tasks_path = workspace / TASKS_MD_NAME
    if not tasks_path.is_file():
        return TasksMdReport(found=False, path=None, receipts_file_found=False, phases=[])

    phases = parse_tasks_md(safe_read(tasks_path, max_bytes=5 * 1024 * 1024))

    receipts_path = workspace / BUILD_RECEIPTS_RELPATH
    receipts_file_found = receipts_path.is_file()
    receipts = (
        parse_build_receipts(safe_read(receipts_path, max_bytes=5 * 1024 * 1024))
        if receipts_file_found else []
    )

    for phase in phases:
        phase.receipt_status = (
            _receipt_status_for(phase.title, receipts)
            if receipts_file_found else "receipts_file_absent"
        )

    return TasksMdReport(
        found=True,
        path=str(tasks_path),
        receipts_file_found=receipts_file_found,
        phases=phases,
    )
