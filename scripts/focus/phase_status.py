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

Scope boundary — only a *governing* tasks.md is a Completion-Marking target:
that same-origin precondition holds for a workspace's governing tasks.md, NOT
for a nested PR-plan tasks.md that /execute-build's Native Execution Trigger
spawns under .workflow_state/. Such a nested file's phases are receipted under
the *outer* master phase's title, never their own, so running this engine
directly against the nested file correctly returns receipt_status=not_found — a
safe-direction false negative (it refuses to mark, never mis-marks). That is
correct-by-design, not a defect; nested PR-plan tasks.md files are transient
gitignored scratch state, not intended Completion-Marking targets.
[DOCUMENTED 2026-07-22 — resolves helpdesk-tickets/20260707_nested-tasks-md-
receipt-title-mismatch_workflow.md via its Recommendation #2 (accept
correct-by-design + document the boundary), the proportionate resolution for a
LOW-impact, safe-direction gap affecting only transient scratch files.]

Design note: phase boundaries are detected by title pattern ("Phase N" /
"Stage N", including alphanumeric sub-phase suffixes like "Phase 3B" /
"Phase 3C-Rem"), not raw header level, so nested sub-headers inside a phase (e.g.
"### Acceptance Criteria") are correctly treated as part of that phase's body
rather than fragmenting into phantom phases. If a workspace's tasks.md uses a
naming convention this pattern does not recognize, `found` is still True but
`phases` is empty — the workflow must treat that as "structure not
recognized," not as "no phases exist." This distinction is now carried
explicitly in the output as `structure_recognized` (False when found-but-empty),
and — crucially, for the PARTIAL-miss case that boolean can't see — enforced by
the `--expect-phases N` count-verification gate: the ingesting agent asserts the
unit count it read, and the engine refuses (exit 2) if its own recognized count
differs, so no consumer has to re-derive the contract from this docstring alone.
[ADDED 2026-07-22 — resolves helpdesk-tickets/20260722_phase-status-empty-phases-contract_workflow.md.]

Architecturally read-only, same contract as the rest of scripts/focus/: no
write primitives, bounded reads via safe_read.

Standalone invocation: unlike its sibling engines (focus.py, harden_audit.py,
receipt_audit.py), this module previously had no CLI entrypoint of its own —
it was designed to be imported by other engines (build_audit.py,
receipt_audit.py), which each already do their own sys.path bootstrap before
importing it. Two workflow files (implementation-plan.md, nodelete.md)
nonetheless instructed the agent to "run" this module directly, with no path
anchor and no self-sufficient import path — see
helpdesk-tickets/CLOSED_20260707_suite-script-path-resolution_workflow.md.
The __main__ block below closes that gap: this file can now be invoked
exactly like its siblings, via
`python3 ~/blueprint-workflows/scripts/focus/phase_status.py --workspace
<path> --output-json`, regardless of the caller's cwd or whether anything
upstream has already set sys.path.
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from engine_utils import safe_read

TASKS_MD_NAME = "tasks.md"
BUILD_RECEIPTS_RELPATH = Path(".workflow_state") / "receipts" / "BUILD_RECEIPTS.md"

_HEADER_RE = re.compile(r"^(#{2,4})\s+(.*\S)\s*$")
# Phase-boundary title pattern. The leading "phase|stage" + digit is the required
# anchor; the trailing [A-Za-z0-9-]* admits alphanumeric sub-phase suffixes
# ("Phase 3B", "Phase 3C-Rem", "Phase 2a") without loosening that anchor — bare
# prose headers ("## Scope", "## Triage Report Recommendations") still lack the
# digit and are correctly NOT treated as phases.
# [BROADENED 2026-07-22 — resolves the code half of
#  helpdesk-tickets/20260707_phase-status-campaign-header-scope_workflow.md. The
#  prior `\d+\b` rejected letter-suffixed remediation phases (the "3B"/"3C-Rem"
#  Parser Alphanumeric Omission, independently rediscovered across the Videos and
#  hebrews_6_reader sessions — process_learnings/PROCESS_LEARNINGS.md, 2026-07-09).
#  This extends the SAME behavior the numeric pattern already had ("## Phase 3 —
#  anything" was always a boundary) to alphanumeric tokens; it is not a new risk
#  class. The ticket's STRUCTURAL descriptive-header / E2E-boundary half is deferred.]
_PHASE_TITLE_RE = re.compile(r"^(phase|stage)\s+\d+[A-Za-z0-9-]*\b", re.IGNORECASE)
_CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX/~])\]\s")
_FENCE_RE = re.compile(r"^\s*```")
_RECEIPT_SPLIT_RE = re.compile(r"^\s*---\s*$", re.MULTILINE)
_RECEIPT_FIELD_RE = re.compile(r"^-\s*([A-Za-z/ ]+?):\s*(.+)$")

# Grade/Status values the receipt writer is known to emit for a finished
# phase (execute-build.md L316, L329, L364, L374). Compared case-insensitively.
_COMPLETE_STATUSES = frozenset({"phase complete", "project build complete"})


def _strip_header_annotations(title: str) -> str:
    """Strip human-readable status annotations from a phase header title.

    This is the pre-processing step applied before normalization to prevent
    inline header annotations from contaminating the match key.

    Strips in this order:
    1. Trailing bold annotations: ' -- **READY FOR HANDOFF**',
       ' -- **COMPLETE 2026-07-07** (notes...)' etc.
    2. Does NOT strip plain parentheticals universally -- they may be part of
       a canonical title. A second-pass parenthetical strip is used in
       _receipt_status_for() only, returning a distinct 'found_complete_approx'
       status so the caller can distinguish a clean match from a legacy-header
       approximate match.

    Per /implementation-plan STRICT RULE 28 (Machine Header Discipline) and
    /execute-build STRICT RULE 19 (Canonical Receipt Title Discipline), this
    stripping should become unnecessary once all plan authors follow those rules.
    This function is the resilience layer for pre-existing legacy headers.

    Resolves: helpdesk-tickets/20260708_plan-archive-pipeline-design_workflow.md Fix 1
    """
    # Strip " -- **...**" bold annotations (and any trailing parenthetical after them)
    stripped = re.sub(r"\s*\u2014\s*\*\*[^*]+\*\*.*$", "", title).strip()
    # Also handle " - **...**" (hyphen-dash variant)
    stripped = re.sub(r"\s*-\s*\*\*[^*]+\*\*.*$", "", stripped).strip()
    # Strip standalone trailing "**ANNOTATION**" with no dash (edge case)
    stripped = re.sub(r"\s*\*\*[A-Z][A-Z ]+[A-Z]\*\*\s*$", "", stripped).strip()
    return stripped


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

    @property
    def structure_recognized(self) -> bool:
        """True only when a tasks.md exists AND at least one phase header was
        recognized. False when found-but-empty — the "structure not recognized"
        case consumers must NOT read as "no phases exist" (they distinguish it
        from the no-tasks.md case via `found`). Carried as a first-class output
        field so the distinction no longer lives only in this docstring, where
        no consumer executes it — resolves helpdesk-tickets/20260722_phase-
        status-empty-phases-contract. Note this is the all-or-nothing signal:
        a PARTIAL miss (some units recognized, others not) leaves it True — the
        --expect-phases count-verification gate is what catches that case."""
        return self.found and bool(self.phases)

    def as_dict(self) -> dict:
        return {
            "found": self.found,
            "path": self.path,
            "receipts_file_found": self.receipts_file_found,
            "structure_recognized": self.structure_recognized,
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
    or "Stage N" (case-insensitive), optionally with an alphanumeric sub-phase
    suffix ("Phase 3B", "Phase 3C-Rem") — the vocabulary /execute-build's Phase
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
    """Return the receipt match status for a given phase title.

    Match priority:
    1. Exact normalized match (after bold-annotation stripping) -> 'found_complete' /
       'found_incomplete' / 'not_found'
    2. Second-pass: also strip trailing parentheticals (e.g. '(handoff: Gemini)') from
       the tasks.md title and retry. If this second-pass matches, return
       'found_complete_approx' or 'found_incomplete_approx' to signal that the match
       required approximation -- indicating the header has legacy annotations and
       /implementation-plan STRICT RULE 28 has not yet been applied.

    'found_complete_approx' is treated as equivalent to 'found_complete' by
    /nodelete Pillar 6 and the --audit Completion Marking sub-pass, but the
    distinct value allows callers to log which phases still have dirty headers
    and require cleanup (Fix 3: retroactive header normalization).

    Resolves: helpdesk-tickets/20260708_plan-archive-pipeline-design_workflow.md Fix 1
    """
    # Pass 1: strip bold annotations, then normalize
    cleaned = _strip_header_annotations(title)
    target = _normalize(cleaned)
    matches = [r for r in receipts if _normalize(_strip_header_annotations(r.phase)) == target]
    if matches:
        if any(r.grade_status.lower() in _COMPLETE_STATUSES for r in matches):
            return "found_complete"
        return "found_incomplete"

    # Pass 2: additionally strip trailing parentheticals from the tasks.md title
    # (e.g. '(handoff: Gemini)', '(all four re-verification targets -- ...)')
    # Returns *_approx status to signal the match needed a looser strip.
    cleaned_paren = re.sub(r"\s*\([^)]*\)\s*$", "", cleaned).strip()
    target_paren = _normalize(cleaned_paren)
    if target_paren != target:  # Only retry if stripping actually changed anything
        matches_paren = [
            r for r in receipts
            if _normalize(_strip_header_annotations(r.phase)) == target_paren
        ]
        if matches_paren:
            if any(r.grade_status.lower() in _COMPLETE_STATUSES for r in matches_paren):
                return "found_complete_approx"
            return "found_incomplete_approx"

    return "not_found"



def build_phase_status_report(
    workspace: Path, tasks_md_path: Optional[Path] = None
) -> TasksMdReport:
    """
    Locate tasks.md and (if present) BUILD_RECEIPTS.md, and produce the
    per-phase status report /focus-plan PHASE 2 uses to adjudicate absent
    anchors.

    found=False means tasks.md does not exist at all — itself meaningful:
    the plan has not been broken into execution phases yet, so every absent
    anchor is presumptively PENDING, not a MISMATCH candidate.

    Args:
        workspace: Absolute path to the workspace root. BUILD_RECEIPTS.md is
            always located at workspace/.workflow_state/receipts/ — receipts
            are a workspace-wide ledger, not per-plan.
        tasks_md_path: Optional explicit path to tasks.md, overriding the
            default workspace/tasks.md lookup. [ADDED 2026-07-06 — Sovereign
            Redesign Cluster Stage 1 prototype found this hardcoded lookup
            could not verify a tasks.md deliberately placed outside workspace
            root; additive, backward-compatible — default behavior unchanged
            when omitted.]
    """
    workspace = Path(workspace)
    tasks_path = Path(tasks_md_path) if tasks_md_path is not None else workspace / TASKS_MD_NAME
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


def verify_phase_count(report: TasksMdReport, expected: int) -> dict:
    """Count-verification gate — the Intelligence-Bridge check for tasks.md ingestion.

    The agent asserts `expected`: the number of plan units (phases / steps /
    parts / whatever the plan calls them) it counted by *reading* tasks.md with
    judgment. The engine compares that to `recognized` — the units it matched
    via the canonical `Phase N` / `Stage N` convention. A MISMATCH means one or
    more real units use a header this parser cannot see (e.g. "Step 3", "Part 2",
    a descriptive title), so the engine is working from a PARTIAL parse and must
    not let downstream verification trust it — it refuses and tells the agent to
    reconcile tasks.md to the canonical format.

    This is the general answer to a class a regex can never enumerate: rather
    than trying to anticipate every hallucinated header spelling, the engine
    verifies its own parse against the agent's ground-truth count. It catches the
    PARTIAL miss that `structure_recognized` (all-or-nothing) cannot.

    Resolves helpdesk-tickets/20260722_phase-status-empty-phases-contract (rolled
    in per user direction as the more general form of the fix).
    """
    recognized = len(report.phases)
    if not report.found:
        return {
            "expected": expected, "recognized": 0, "verdict": "NO_TASKS_MD",
            "message": (
                f"No tasks.md found — nothing to count against your asserted {expected}. "
                "Either the plan has no tasks.md yet, or you are pointed at the wrong "
                "workspace/path."
            ),
        }
    if recognized == expected:
        return {
            "expected": expected, "recognized": recognized, "verdict": "MATCH",
            "message": (
                f"Engine recognizes all {recognized} unit(s) via the canonical "
                "Phase/Stage convention — the parse is complete; proceed."
            ),
        }
    return {
        "expected": expected, "recognized": recognized, "verdict": "MISMATCH",
        "message": (
            f"You assert {expected} unit(s); the engine recognizes {recognized} via the "
            "canonical `Phase N` / `Stage N` (+ alphanumeric suffix) header convention. "
            f"The difference of {abs(expected - recognized)} is unit(s) whose header this "
            "parser cannot match (e.g. 'Step N', 'Part N', a descriptive title). Revise "
            "tasks.md so every unit uses a `## Phase N` / `## Stage N` header, then re-run "
            "— downstream verification must not trust a partial parse."
        ),
    }


def _parse_args() -> "argparse.Namespace":
    import argparse
    p = argparse.ArgumentParser(
        prog="phase_status.py",
        description="tasks.md + BUILD_RECEIPTS.md Phase Status Engine — dual "
                    "cross-reference of checkbox state and receipt trail. Read-only.",
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the workspace root (tasks.md and "
                        ".workflow_state/receipts/BUILD_RECEIPTS.md are located relative to this).")
    p.add_argument("--tasks-file", default=None, type=str,
                   help="Optional explicit path to tasks.md, overriding the default "
                        "workspace/tasks.md lookup.")
    p.add_argument("--expect-phases", default=None, type=int, metavar="N",
                   help="Count-verification gate: the number of plan units (phases / "
                        "steps / parts) YOU counted by reading tasks.md. The engine "
                        "cross-checks its own recognized count against N and reports "
                        "MISMATCH (exit 2) if any unit uses a header convention it cannot "
                        "parse — forcing reconciliation to the canonical `## Phase N` "
                        "format before downstream work trusts the parse. Read-only.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def main() -> int:
    import json as _json
    args = _parse_args()
    report = build_phase_status_report(
        Path(args.workspace),
        tasks_md_path=Path(args.tasks_file) if args.tasks_file else None,
    )
    count_check = (
        verify_phase_count(report, args.expect_phases)
        if args.expect_phases is not None else None
    )
    if args.output_json:
        payload = report.as_dict()
        if count_check is not None:
            payload["count_verification"] = count_check
        print(_json.dumps(payload, indent=2))
    elif not args.quiet:
        if not report.found:
            print("tasks.md: NOT FOUND")
        else:
            print(f"tasks.md: {report.path}")
            print(f"BUILD_RECEIPTS.md: {'found' if report.receipts_file_found else 'absent'}")
            print(f"structure_recognized: {report.structure_recognized}")
            for phase in report.phases:
                print(f"  {phase.title}: status={phase.status} receipt_status={phase.receipt_status}")
        if count_check is not None:
            print(f"count_verification: {count_check['verdict']} "
                  f"(expected {count_check['expected']}, recognized {count_check['recognized']})")
            print(f"  {count_check['message']}")
    # A failed count gate exits non-zero so it functions as a real gate; the
    # default (no --expect-phases) path is unchanged and always exits 0.
    if count_check is not None and count_check["verdict"] in ("MISMATCH", "NO_TASKS_MD"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
