#!/usr/bin/env python3
"""
focus.py — Deterministic Triad Evidence Engine CLI
===================================================
The read-only mechanical layer behind /focus-plan. Locates the implementation
plan, parses it into items + anchors, verifies every anchor against the real
substrate, and emits a structured JSON evidence report.

Because a script gathers the evidence, the agent consuming the report cannot
hallucinate it — the anti-Hallucinated-Success guarantee that /focus-plan
historically enforced by instruction (STRICT RULE 12) becomes architectural.

Usage:
    python focus.py --workspace /absolute/path/to/workspace [options]

Required:
    --workspace PATH   Absolute path to the target workspace root.

Optional:
    --plan PATH        Explicit plan file (overrides auto-location).
    --output-json      Emit the evidence report as JSON to stdout.
    --quiet            Suppress human-readable output (errors still print).

Workflow calling convention (from /focus-plan):
    python {SCRIPTS_DIR}/focus/focus.py --workspace {TARGET} --output-json

This tool is READ-ONLY on the target workspace. It opens files for reading and
never writes — the architectural sibling of scripts/doorway/ (which backs
/sentinel). All runtime output goes to stdout.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the parent of the focus/ package directory is importable when this
# file is run directly as a script (mirrors doorway.py).
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from focus import __version__
from focus.anchor_scanner import AnchorScanner
from focus.phase_status import build_phase_status_report
from focus.plan_parser import load_and_parse, locate_plan
from focus.reporter import FocusReporter

SCHEMA_VERSION = "1.1"

_ADVISORY = (
    "verdict_hint is a mechanical signal from substrate coverage only. The "
    "/focus-plan agent makes the final GREEN/YELLOW/RED call after intent "
    "interpretation, the Negative Space Scan, and the HALT gate. An absent "
    "anchor may be Ghost Logic OR a legitimately not-yet-built item — check "
    "tasks_md.phases for that item's phase status before classifying it. No "
    "tasks_md ('found': false) means the plan has no execution phases yet — "
    "treat absences as PENDING, not a failure signal. But a tasks.md that "
    "EXISTS yet yields zero phases ('found': true, 'structure_recognized': false) "
    "is UNRECOGNIZED STRUCTURE, not 'no phases' — do NOT treat its absences as "
    "PENDING; the plan has units the parser could not read. And because a PARTIAL "
    "miss (some units recognized, others not) leaves structure_recognized true, "
    "run the count-verification gate before trusting any phase-based judgment: "
    "count the plan's units (phases/steps/parts) by reading tasks.md yourself, "
    "then `phase_status.py --workspace <ws> --expect-phases <your-count>`; a "
    "MISMATCH (exit 2) means revise tasks.md to the canonical `## Phase N` format "
    "before proceeding. (helpdesk-tickets/20260722_phase-status-empty-phases-contract)"
)


class FocusVerifier:
    """Orchestrates plan location, parsing, and anchor verification."""

    def __init__(self, workspace: Path, plan_override: Path = None):
        self.workspace = Path(workspace).resolve()
        self.plan_override = Path(plan_override).resolve() if plan_override else None

    def run(self) -> dict:
        plan_path, spelling = self._resolve_plan()
        report = {
            "schema_version": SCHEMA_VERSION,
            "tool": "focus",
            "tool_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(self.workspace),
            "plan_found": plan_path is not None,
            "plan_file": str(plan_path) if plan_path else None,
            "plan_spelling": spelling,
            "checkboxes": {"open": 0, "done": 0, "in_progress": 0},
            "items": [],
            "notes": [],
            "tasks_md": build_phase_status_report(self.workspace).as_dict(),
        }

        if plan_path is None:
            report["notes"].append(
                "No implementation plan found. Looked for 'implementation-plan.md' "
                "(canonical) then 'implementation_plan.md' (legacy) at the workspace "
                "root. /focus-plan should fall back to conversation extraction."
            )
            report["summary"] = self._summary(0, 0, 0, 0, 0, 0, plan_found=False)
            return report

        items, checkboxes = load_and_parse(plan_path)
        report["checkboxes"] = checkboxes
        # Exclude the plan file from the substrate index: its own anchor
        # mentions are intent, not implementation.
        scanner = AnchorScanner(self.workspace, exclude={plan_path})

        present = absent = mock = total_anchors = items_with_anchors = 0

        for item in items:
            anchor_results = []
            absent_anchors = []
            mock_candidates = []
            if item.anchors:
                items_with_anchors += 1
            for anchor in item.anchors:
                total_anchors += 1
                if anchor.kind == "file":
                    res = scanner.verify_file(anchor.query)
                    entry = {**anchor.as_dict(), "status": res["status"],
                             "locations": res["locations"]}
                    if res["status"] == "EXISTS":
                        present += 1
                    elif res["status"] == "MISSING":
                        absent += 1
                        absent_anchors.append(anchor.query)
                    # INVALID (path traversal) counts as neither; surfaced via status.
                else:
                    res = scanner.verify_symbol(anchor.query)
                    entry = {**anchor.as_dict(), "status": res["status"],
                             "production_matches": res["production_matches"],
                             "test_matches": res["test_matches"],
                             "locations": res["locations"]}
                    if res["status"] == "FOUND_PRODUCTION":
                        present += 1
                    elif res["status"] == "FOUND_TEST_ONLY":
                        mock += 1
                        mock_candidates.append(anchor.query)
                    else:  # ABSENT
                        absent += 1
                        absent_anchors.append(anchor.query)
                anchor_results.append(entry)

            report["items"].append({
                "id": item.item_id,
                "title": item.title,
                "level": item.level,
                "source_line": item.source_line,
                "anchors": anchor_results,
                "absent_anchors": absent_anchors,
                "mock_trap_candidates": mock_candidates,
            })

        report["summary"] = self._summary(
            len(items), items_with_anchors, total_anchors, present, absent, mock,
            plan_found=True,
        )
        return report

    def _resolve_plan(self):
        if self.plan_override is not None:
            if self.plan_override.is_file():
                return self.plan_override, "explicit"
            return None, None
        return locate_plan(self.workspace)

    @staticmethod
    def _summary(total_items, items_with_anchors, total_anchors,
                 present, absent, mock, plan_found):
        if not plan_found:
            verdict = "RED"
        elif mock > 0:
            verdict = "RED"      # test-only implementation masquerading as done.
        elif absent > 0:
            verdict = "YELLOW"   # coverage gaps: Ghost Logic or not-yet-built.
        else:
            verdict = "GREEN"
        return {
            "total_items": total_items,
            "items_with_anchors": items_with_anchors,
            "total_anchors": total_anchors,
            "present": present,
            "absent": absent,
            "mock_trap_candidates": mock,
            "verdict_hint": verdict,
            "advisory": _ADVISORY,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="focus.py",
        description="Deterministic Triad Evidence Engine — the read-only "
                    "mechanical layer behind /focus-plan.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python focus.py --workspace /home/user/project\n"
            "  python focus.py --workspace /home/user/project --output-json\n"
            "  python focus.py --workspace /home/user/project --plan ./plan.md --output-json\n"
        ),
    )
    parser.add_argument("--workspace", required=True, type=str,
                        help="Absolute path to the target workspace root.")
    parser.add_argument("--plan", type=str, default=None,
                        help="Explicit plan file (overrides auto-location).")
    parser.add_argument("--output-json", action="store_true",
                        help="Emit the evidence report as JSON to stdout.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress human-readable output.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        print(f"[ERROR] Workspace does not exist: {workspace}", file=sys.stderr)
        return 1
    if not workspace.is_dir():
        print(f"[ERROR] Workspace path is not a directory: {workspace}", file=sys.stderr)
        return 1

    verifier = FocusVerifier(workspace=workspace, plan_override=args.plan)
    report = verifier.run()
    FocusReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
