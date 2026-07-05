"""
reporter.py — Focus Evidence Reporter
======================================
Renders the FocusVerifier report as either a structured JSON payload (for
/focus-plan to consume) or a compact human-readable summary (for direct CLI
use). Mirrors the doorway reporter contract: --output-json wins, --quiet
suppresses human output.
"""

import json


class FocusReporter:
    """Renders a focus report dict to stdout."""

    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        summary = report.get("summary", {})
        print(f"\n=== {report.get('workspace', 'workspace')} — Focus Triad Evidence ===")
        self._render_tasks_md(report.get("tasks_md", {}))

        if not report.get("plan_found"):
            print("[!] NO IMPLEMENTATION PLAN FOUND.")
            for note in report.get("notes", []):
                print(f"    {note}")
            print(f"\nVerdict hint: {summary.get('verdict_hint', 'RED')} (advisory)")
            return

        print(f"Plan:    {report.get('plan_file')}  ({report.get('plan_spelling')})")
        cb = report.get("checkboxes", {})
        print(
            f"Tasks:   {cb.get('done', 0)} done / "
            f"{cb.get('in_progress', 0)} in-progress / {cb.get('open', 0)} open"
        )
        print(
            f"Anchors: {summary.get('total_anchors', 0)} total across "
            f"{summary.get('items_with_anchors', 0)}/{summary.get('total_items', 0)} items "
            f"→ {summary.get('present', 0)} present, {summary.get('absent', 0)} absent"
        )

        for item in report.get("items", []):
            absent = item.get("absent_anchors", [])
            mock = item.get("mock_trap_candidates", [])
            if not absent and not mock:
                continue
            print(f"\n  Item {item['id']} (L{item['source_line']}): {item['title']}")
            if absent:
                print(f"    [GHOST?] absent in substrate: {', '.join(absent)}")
            if mock:
                print(f"    [MOCK?]  found only in tests: {', '.join(mock)}")

        print(f"\nVerdict hint: {summary.get('verdict_hint', '?')} (advisory)")
        print(f"  {summary.get('advisory', '')}")

    @staticmethod
    def _render_tasks_md(tasks_md: dict) -> None:
        if not tasks_md.get("found"):
            print("Tasks:   tasks.md not found — no execution phases yet (absences are PENDING, not failures)")
            return
        receipts_note = "" if tasks_md.get("receipts_file_found") else "  [no BUILD_RECEIPTS.md]"
        print(f"Tasks:   {tasks_md.get('path')}{receipts_note}")
        for phase in tasks_md.get("phases", []):
            cb = phase.get("checkboxes", {})
            print(
                f"    Phase (L{phase.get('source_line')}): {phase.get('title')} — "
                f"{phase.get('status')} ({cb.get('done', 0)} done / "
                f"{cb.get('in_progress', 0)} in-progress / {cb.get('open', 0)} open) "
                f"— receipt: {phase.get('receipt_status')}"
            )
