"""
coverage.py — Receipt coverage computation
=============================================
Cross-references tasks.md's completed phases against the receipt
dimensions (Built/Validated/Hardened/Documented + DESIGN/TRIAGE v3 skeleton)
and the Quality-Process dimension, computing a gap percentage. Read-only; writes nothing.

Dimension matching is honestly scoped by what each receipt file actually keys
on — confirmed against the real receipt files this workspace already writes,
not just /receipt-check's own documentation of itself:

  * Built      — BUILD_RECEIPTS.md's "Phase/Stage" is the real phase name
                 (execute-build.md writes <ACTIVE_PHASE name> verbatim).
                 Matched by normalized exact string match against tasks.md's
                 phase titles.
  * Validated  — VALIDATION_RECEIPTS.md's "Phase/Stage" is <STAGE_ID>, the
                 same naming convention. Matched the same way.
  * Hardened   — HARDEN_GRADES.md is keyed by FILE PATH (the header target and
                 the "Files:" field) — "Phase/Stage" here holds a free-text
                 label instead (e.g. "Security Hardening (SoC extraction)"),
                 confirmed against this workspace's own HARDEN_GRADES.md.
                 Matched by checking whether any file the phase names in its
                 own tasks.md body text appears in a Harden entry's Files. A
                 phase naming no files is `unverifiable_no_file_list` for this
                 dimension — never silently marked covered or a gap.
  * Documented — DOCS_RECEIPTS.md's real-world "Phase/Stage" value is a fixed
                 constant ("Journal Update") in every entry this workspace has
                 ever written — confirmed, there is no per-phase key at all.
                 Reported as existence-only; never claimed as a per-phase match.

Only a phase tasks.md's own checkboxes mark COMPLETE is gap-checkable — a
not-yet-built phase is PENDING, not a gap, matching the exact PENDING/MISMATCH
distinction /focus-plan v4 already established (phase_status.py). This engine
must not reintroduce the bug that fix just closed.
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from engine_utils import safe_read

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from focus.phase_status import parse_tasks_md  # reuse — proven phase-boundary detection

RECEIPTS_DIR = Path(".workflow_state") / "receipts"
BUILD_RECEIPTS = RECEIPTS_DIR / "BUILD_RECEIPTS.md"
VALIDATION_RECEIPTS = RECEIPTS_DIR / "VALIDATION_RECEIPTS.md"
HARDEN_GRADES = RECEIPTS_DIR / "HARDEN_GRADES.md"
DOCS_RECEIPTS = RECEIPTS_DIR / "DOCS_RECEIPTS.md"
DESIGN_RECEIPTS = RECEIPTS_DIR / "DESIGN_RECEIPTS.md"
TRIAGE_RECEIPTS = RECEIPTS_DIR / "TRIAGE_RECEIPTS.md"
QUALITY_AUDIT_PATH = _HERE.parent / "quality" / "quality_audit.py"

_RECEIPT_SPLIT_RE = re.compile(r"^\s*---\s*$", re.MULTILINE)
_RECEIPT_FIELD_RE = re.compile(r"^-\s*([A-Za-z/ ]+?):\s*(.+)$")
_FILE_TOKEN_RE = re.compile(r"[\w./-]+\.(?:py|md|js|ts|toml|json|sh)\b")


def _normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


@dataclass
class ReceiptRecord:
    target: str          # the Phase/Stage field value, as written
    grade_status: str
    files: str = ""       # raw Files: field, as written


def parse_receipt_records(text: str) -> List[ReceiptRecord]:
    """
    Generic receipt-block parser: any '## DATE — WORKFLOW — TARGET' block with
    '- Phase/Stage:' / '- Grade/Status:' / optional '- Files:' lines, separated
    by '---'. All four receipt types share this field vocabulary regardless of
    what "Phase/Stage" semantically means for that particular receipt (see
    module docstring) — confirmed against the real files, not assumed.

    Malformed blocks are skipped, not raised on — an append-only heredoc log
    can have a partial/corrupted tail entry; that must not abort the parse.
    """
    records: List[ReceiptRecord] = []
    for block in _RECEIPT_SPLIT_RE.split(text):
        target = None
        grade_status = None
        files = ""
        for line in block.splitlines():
            m = _RECEIPT_FIELD_RE.match(line.strip())
            if not m:
                continue
            key = m.group(1).strip().lower()
            if key == "phase/stage":
                target = m.group(2).strip()
            elif key == "grade/status":
                grade_status = m.group(2).strip()
            elif key == "files":
                files = m.group(2).strip()
        if target and grade_status:
            records.append(ReceiptRecord(target=target, grade_status=grade_status, files=files))
    return records


def _load_receipt_records(workspace: Path, relpath: Path) -> tuple:
    """Read one receipt file and parse its records. Returns (present, records) —
    consolidates the read/bool-check/parse-or-empty sequence that was
    previously repeated once per receipt dimension (Build/Validation/Harden/Docs)."""
    text = safe_read(workspace / relpath)
    present = bool(text)
    records = parse_receipt_records(text) if present else []
    return present, records


def _phase_body_text(lines: List[str], phase, phases_sorted) -> str:
    """Slice the raw tasks.md lines belonging to one phase (for file-mention scanning)."""
    pos = phases_sorted.index(phase)
    start = phase.source_line - 1
    end = phases_sorted[pos + 1].source_line - 1 if pos + 1 < len(phases_sorted) else len(lines)
    return "\n".join(lines[start:end])


def _matched_status(phase_title: str, records: List[ReceiptRecord]) -> str:
    target = _normalize(phase_title)
    return "found" if any(_normalize(r.target) == target for r in records) else "missing"


def _hardened_status(phase_body: str, harden_records: List[ReceiptRecord]) -> str:
    file_tokens = _FILE_TOKEN_RE.findall(phase_body)
    if not file_tokens:
        return "unverifiable_no_file_list"
    for token in file_tokens:
        for rec in harden_records:
            if token in rec.files or token in rec.target:
                return "found"
    return "missing"


def _run_quality_audit(workspace: Path) -> dict:
    """
    Wire the Quality-Process dimension for real — receipt-check.md previously
    only *instructed* the agent to run this as a separate manual step; the
    engine now calls it directly as part of one unified coverage pass.
    quality_audit.py is suite infrastructure (always resolved relative to this
    engine's own location), not something that lives inside the target
    workspace being audited — only --workspace varies per call.
    """
    if not QUALITY_AUDIT_PATH.is_file():
        return {"available": False, "verdict_hint": None}
    try:
        proc = subprocess.run(
            [sys.executable, str(QUALITY_AUDIT_PATH), "--workspace", str(workspace), "--output-json"],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(proc.stdout)
        return {"available": True, "verdict_hint": data.get("summary", {}).get("verdict_hint")}
    except (subprocess.SubprocessError, ValueError, OSError, json.JSONDecodeError):
        return {"available": False, "verdict_hint": None}


def compute_coverage(workspace: Path) -> dict:
    workspace = Path(workspace)
    tasks_path = workspace / "tasks.md"
    quality_process = _run_quality_audit(workspace)

    if not tasks_path.is_file():
        return {
            "tasks_md_found": False,
            "phases": [],
            "checkable_dimensions": 0,
            "covered_dimensions": 0,
            "gap_percent": None,
            "quality_process": quality_process,
            "note": "tasks.md not found — no Component List to check coverage against.",
        }

    tasks_text = safe_read(tasks_path)
    phases = parse_tasks_md(tasks_text)
    lines = tasks_text.splitlines()

    build_present, build_records = _load_receipt_records(workspace, BUILD_RECEIPTS)
    validation_present, validation_records = _load_receipt_records(workspace, VALIDATION_RECEIPTS)
    harden_present, harden_records = _load_receipt_records(workspace, HARDEN_GRADES)
    docs_present, docs_records = _load_receipt_records(workspace, DOCS_RECEIPTS)
    design_present, design_records = _load_receipt_records(workspace, DESIGN_RECEIPTS)
    triage_present, triage_records = _load_receipt_records(workspace, TRIAGE_RECEIPTS)

    checkable_dims = 0
    covered_dims = 0
    phase_reports = []

    for phase in phases:
        if phase.status != "complete":
            # Not-yet-built is PENDING, not a gap — the exact distinction
            # /focus-plan v4 established. Do not check receipts for it.
            phase_reports.append({
                "title": phase.title, "checkbox_status": phase.status,
                "built": "not_applicable_pending", "validated": "not_applicable_pending",
                "hardened": "not_applicable_pending",
                "designed": "not_applicable_pending", "triaged": "not_applicable_pending",
            })
            continue

        built = _matched_status(phase.title, build_records) if build_present else "receipts_file_absent"
        validated = _matched_status(phase.title, validation_records) if validation_present else "receipts_file_absent"
        body = _phase_body_text(lines, phase, phases)
        hardened = _hardened_status(body, harden_records) if harden_present else "receipts_file_absent"
        designed = _matched_status(phase.title, design_records) if design_present else "receipts_file_absent"
        triaged = _matched_status(phase.title, triage_records) if triage_present else "receipts_file_absent"

        for dim_status in (built, validated, hardened, designed, triaged):
            if dim_status in ("found", "missing"):
                checkable_dims += 1
                covered_dims += (dim_status == "found")

        phase_reports.append({
            "title": phase.title, "checkbox_status": phase.status,
            "built": built, "validated": validated, "hardened": hardened,
            "designed": designed, "triaged": triaged,
        })

    gap_percent = round(100 * (1 - covered_dims / checkable_dims), 1) if checkable_dims else None

    return {
        "tasks_md_found": True,
        "receipt_files_present": {
            "build": build_present, "validation": validation_present,
            "harden": harden_present, "docs": docs_present,
            "design": design_present, "triage": triage_present,
        },
        "documented_dimension": {
            "note": "DOCS_RECEIPTS.md's real-world Phase/Stage value is a fixed "
                    "constant ('Journal Update') in every entry this workspace "
                    "has ever written — no per-phase key exists. Reported as "
                    "existence-only, never a per-phase match.",
            "entries_present": docs_present,
            "entry_count": len(docs_records),
        },
        "phases": phase_reports,
        "checkable_dimensions": checkable_dims,
        "covered_dimensions": covered_dims,
        "gap_percent": gap_percent,
        "quality_process": quality_process,
    }
