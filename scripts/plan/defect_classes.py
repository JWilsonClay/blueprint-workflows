#!/usr/bin/env python3
"""
defect_classes.py — Defect-Class Preflight Engine
=====================================================
Matches an enumerated audit finding against defect classes this suite (or the
target project) has already diagnosed and paid for, and returns each matched
class's known counter-measure as acceptance-criterion text.

Consumed by `/implementation-plan --remediate` Phase 8c, before any `Fix N` is
drafted, so a previously-learned lesson is checked *while the fix is being
written* rather than rediscovered by the next audit.

Usage:
    python3 defect_classes.py --audit /abs/path/to/audit.md [--workspace /abs/path]
                              [--output-json] [--quiet]
    python3 defect_classes.py --list [--output-json]

Read-only; writes nothing. Adds no runtime gate to /execute-build, /nodelete
Pillar 6, or phase_status.py — it shapes a drafted fix's acceptance criteria
and nothing else.

Why this exists
---------------
The ticket that commissioned this engine asked why a two-phases-old
PROCESS_LEARNINGS.md lesson about receipt paths was able to recur. Reading the
triggering audit gives a sharper answer than "project memory failed": the suite
*already had* two mechanisms aimed at that exact defect class — Machine Header
Discipline (STRICT RULE 28) and the dual cross-reference in Completion Marking
(STRICT RULE 27) — and both fired correctly, returning
`receipt_status: not_found`. The phases were marked COMPLETED anyway.

So the gap was never detection. It was that nothing consulted the
already-diagnosed classes at *drafting* time, when the correct acceptance
criterion could still have been written into the fix.

Origin: helpdesk-tickets/20260727_implementation-plan_workflow.md, Component 3.
"""

import argparse
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from plan.findings import parse_audit  # noqa: E402

__all__ = ["SUITE_DEFECT_CLASSES", "match_finding", "load_project_lessons", "preflight"]


#: Suite-global defect classes. Every entry is earned — traceable to a closed
#: helpdesk ticket, a STRICT RULE, or a real finding in the persisted audit
#: corpus. This registry is deliberately small; an unearned entry would dilute
#: every match it participates in. Add on evidence, not on speculation.
SUITE_DEFECT_CLASSES = [
    {
        "id": "receipt-path-resolution",
        "name": "Receipt path resolution",
        "origin": "audits/20260727-1215-proforma.md CRIT-01; "
                  "CLOSED_20260707_suite-script-path-resolution_workflow.md",
        "signals": [
            r"\breceipt[s]?\b.{0,60}\bpath\b",
            r"\.\./.*\.workflow_state",
            r"\bwrong\s+(?:workspace|path|directory)\b",
            r"\breceipt_status\b.{0,30}not_found",
        ],
        "counter_measure":
            "Receipt destination is an absolute canonical path, resolved via "
            "`git rev-parse --show-toplevel` or written literally — never a "
            "relative `../` chain. Verify by reading the receipt back from the "
            "resolved path after the write.",
    },
    {
        "id": "header-contamination",
        "name": "Machine header contamination",
        "origin": "STRICT RULE 28; audits/20260707-2001-sovereign-scaling-cluster.md",
        "signals": [
            r"\bheader\b.{0,40}\b(contaminat|annotat|pollut)",
            r"\bPhase\s+\d+\b.{0,40}\*\*(READY|COMPLETE|COMPLETED)",
            r"\btitle\b.{0,40}\bexact[- ]match\b",
        ],
        "counter_measure":
            "The `## Phase N` / `### Phase N` header line carries the canonical "
            "phase name only. Every annotation sits on the line below it "
            "(STRICT RULE 28). Verify with `phase_status.py`, confirming "
            "`receipt_status: found_complete` for the affected unit.",
    },
    {
        "id": "checkbox-without-receipt",
        "name": "Completion claimed on one half of the dual check",
        "origin": "STRICT RULE 27; audits/20260727-1215-proforma.md CRIT-01",
        "signals": [
            r"\b(?:false|premature)\s+completion\b",
            r"\bmarked\s+complete\b.{0,60}\b(?:without|no)\b",
            r"\bcheckbox(?:es)?\b.{0,40}\breceipt\b",
            r"\bCOMPLETED\s*\[ARCHIVE",
        ],
        "counter_measure":
            "Completion requires BOTH `phase_status.py` fields to confirm "
            "independently — `status: complete` AND "
            "`receipt_status: found_complete`. Neither alone is sufficient "
            "(STRICT RULE 27). Record the actual command output, not a claim "
            "about it.",
    },
    {
        "id": "claim-without-verification",
        "name": "Verification asserted but never executed",
        "origin": "audits/20260727-1215-proforma.md CRIT-02; "
                  "Hallucinated Success (global failure-pattern vocabulary)",
        "signals": [
            r"\bclaim(?:ed|s)?\b.{0,60}\b(?:never|no|without)\b.{0,30}"
            r"\b(?:verif|recalculat|ran|run|execut)",
            r"\bverified\b.{0,60}\b(?:fabricat|false|untrue|never)\b",
            r"\bno\s+recalculation\b",
            r"\bself[- ]report",
        ],
        "counter_measure":
            "The verification command runs inside the build step itself and "
            "asserts on its read-back value. A receipt may only state "
            "'Verified' for a check whose output is quoted in that same "
            "receipt.",
    },
    {
        "id": "mock-trap",
        "name": "Mock Trap / Sound Effect Execution",
        "origin": "Global failure-pattern vocabulary (~/.claude/CLAUDE.md); "
                  "/iterate-test Step 4b",
        "signals": [
            r"\bmock(?:ed|s|ing)?\b",
            r"\bstub(?:bed|s)?\b",
            r"\bplaceholder\b",
            r"\btest(?:s)?\b.{0,50}\bnever\b.{0,40}\b(?:hit|reach|exercis)",
            r"\bunwired\b|\bGhost Logic\b",
        ],
        "counter_measure":
            "The acceptance criterion exercises the real substrate on the "
            "production path, not a mock or a test harness. State explicitly "
            "which real component the check reaches (Intelligence Bridge "
            "Declaration, /iterate-test Step 4b).",
    },
    {
        "id": "stale-derived-artifact",
        "name": "Derived artifact outlives its source",
        "origin": "audits/20260727-1215-proforma.md CRIT-03",
        "signals": [
            r"\bstale\b",
            r"\bnever\s+regenerated\b",
            r"\bout[- ]of[- ]date\b",
            r"\btimestamp[s]?\b.{0,50}\b(?:prove|show|before|after)\b",
            r"\bconsumes\s+only\b.{0,40}\bold\b",
        ],
        "counter_measure":
            "Regeneration runs the full source-to-artifact pipeline in one "
            "command, or the acceptance criterion compares the artifact's "
            "mtime against its source's and fails when the source is newer.",
    },
]

_MIN_SIGNAL_HITS = 1


def _compile(defect_class):
    return [re.compile(sig, re.IGNORECASE) for sig in defect_class["signals"]]


_COMPILED = {dc["id"]: _compile(dc) for dc in SUITE_DEFECT_CLASSES}


def match_finding(finding, extra_classes=None):
    """
    Return the defect classes a finding matches.

    Matching is signal-based and deliberately generous: a false positive costs
    one extra acceptance criterion on a drafted fix, while a false negative
    costs a repeat of a lesson already paid for. The asymmetry is the whole
    point — this is a drafting aid, not a gate, so over-inclusion is the safe
    failure direction.

    Each returned dict carries `matched_signals` so a reader can see *why* a
    class fired and discard it if the match is spurious.
    """
    haystack = " ".join(filter(None, [
        finding.get("claim", ""),
        finding.get("raw", ""),
        " ".join(finding.get("citations") or []),
        " ".join(finding.get("code_spans") or []),
    ]))

    matches = []
    catalogue = list(SUITE_DEFECT_CLASSES) + list(extra_classes or [])
    for defect_class in catalogue:
        patterns = _COMPILED.get(defect_class["id"]) or _compile(defect_class)
        hits = [p.pattern for p in patterns if p.search(haystack)]
        if len(hits) >= _MIN_SIGNAL_HITS:
            matches.append({
                "id": defect_class["id"],
                "name": defect_class["name"],
                "origin": defect_class["origin"],
                "counter_measure": defect_class["counter_measure"],
                "matched_signals": hits,
                "scope": defect_class.get("scope", "suite"),
            })
    return matches


def load_project_lessons(workspace):
    """
    Read the target workspace's own PROCESS_LEARNINGS.md into ad-hoc defect classes.

    Each `##`/`###` heading becomes one project-scoped class whose signal is its
    own heading text. This is intentionally shallow — a project's learnings file
    is prose written for humans, not a schema, and pretending to parse it deeply
    would manufacture confidence the format cannot support. It surfaces the
    lesson's existence and location so the drafter reads it; it does not claim
    to understand it.

    Returns [] when no learnings file exists — a normal, non-error condition.
    """
    if workspace is None:
        return []
    root = Path(workspace)
    candidates = [
        root / "PROCESS_LEARNINGS.md",
        root / "process_learnings" / "PROCESS_LEARNINGS.md",
        root / ".workflow_state" / "PROCESS_LEARNINGS.md",
    ]
    source = next((c for c in candidates if c.is_file()), None)
    if source is None:
        return []

    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    classes = []
    for line in text.splitlines():
        heading = re.match(r"^\s*#{2,4}\s+(.{6,160})$", line)
        if not heading:
            continue
        title = heading.group(1).strip().strip("#").strip()
        keywords = [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_.\-/]{4,}", title)][:4]
        if not keywords:
            continue
        classes.append({
            "id": f"project:{re.sub(r'[^a-z0-9]+', '-', title.lower())[:48].strip('-')}",
            "name": title,
            "origin": str(source),
            "scope": "project",
            "signals": [r"\b" + re.escape(k) + r"\b" for k in keywords],
            "counter_measure":
                f"This project already recorded a lesson titled '{title}' "
                f"({source}). Read it and carry its check into this fix's "
                f"acceptance criteria before marking the fix done.",
        })
    return classes


def preflight(audit_path, workspace=None):
    """
    Run the Defect-Class Preflight over every finding in an audit.

    Returns a report dict mirroring the Findings Ledger's shape, so Phase 8c
    consumes the same structure Phase 8b produced.
    """
    ledger = parse_audit(audit_path)
    report = {
        "audit_path": ledger["audit_path"],
        "audit_name": ledger["audit_name"],
        "status": ledger["status"],
        "workspace": str(workspace) if workspace else None,
        "project_classes_loaded": 0,
        "findings": [],
        "summary": {"findings": 0, "matched": 0, "unmatched": 0},
        "errors": list(ledger["errors"]),
    }
    if ledger["status"] != "ok":
        return report

    project_classes = load_project_lessons(workspace)
    report["project_classes_loaded"] = len(project_classes)

    matched_count = 0
    for finding in ledger["findings"]:
        classes = match_finding(finding, extra_classes=project_classes)
        if classes:
            matched_count += 1
        report["findings"].append({
            "id": finding["id"],
            "severity": finding["severity"],
            "claim": finding["claim"],
            "defect_classes": classes,
        })

    report["summary"] = {
        "findings": len(ledger["findings"]),
        "matched": matched_count,
        "unmatched": len(ledger["findings"]) - matched_count,
    }
    return report


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _render(report, quiet=False, output_json=False):
    if output_json:
        print(json.dumps(report, indent=2))
        return
    if quiet:
        return

    print(f"\n=== Defect-Class Preflight — {report.get('audit_name', 'audit')} ===")
    if report["status"] != "ok":
        print(f"  STATUS: {report['status'].upper()} — no preflight performed.")
        for err in report["errors"]:
            print(f"  [!] {err}")
        return

    for finding in report["findings"]:
        classes = finding["defect_classes"]
        if not classes:
            print(f"  {finding['id']} — no known defect class matched")
            continue
        print(f"  {finding['id']} — {', '.join(c['name'] for c in classes)}")
        for c in classes:
            print(f"      [{c['scope']}] {c['counter_measure']}")

    summary = report["summary"]
    print(f"\nSummary: {summary['matched']} of {summary['findings']} findings "
          f"matched a known defect class ({summary['unmatched']} unmatched)")
    if report["project_classes_loaded"]:
        print(f"Project lessons loaded: {report['project_classes_loaded']}")


def _parse_args():
    p = argparse.ArgumentParser(
        prog="defect_classes.py",
        description="Defect-Class Preflight — matches audit findings against "
                    "already-diagnosed defect classes and returns their "
                    "counter-measures as acceptance-criterion text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--audit", type=str, help="Path to a persisted audit report.")
    p.add_argument("--workspace", type=str, default=None,
                   help="Workspace root; loads its PROCESS_LEARNINGS.md if present.")
    p.add_argument("--list", action="store_true",
                   help="List the suite-global defect classes and exit.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p, p.parse_args()


def main():
    parser, args = _parse_args()

    if args.list:
        if args.output_json:
            print(json.dumps(SUITE_DEFECT_CLASSES, indent=2))
        elif not args.quiet:
            print("\n=== Suite-global defect classes ===")
            for dc in SUITE_DEFECT_CLASSES:
                print(f"  {dc['id']} — {dc['name']}")
                print(f"      origin: {dc['origin']}")
        return 0

    if not args.audit:
        parser.error("one of --audit or --list is required")

    audit_path = Path(args.audit).expanduser().resolve()
    if not audit_path.is_file():
        print(f"[ERROR] Audit report not found: {audit_path}", file=sys.stderr)
        return 1

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else None
    report = preflight(audit_path, workspace=workspace)
    _render(report, quiet=args.quiet, output_json=args.output_json)
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
