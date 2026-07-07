#!/usr/bin/env python3
"""
ensure_plan_templates.py — Canonical Plan & Tasks Template Populator CLI
===========================================================================
Idempotently ensures a target workspace has `tasks.md` and
`implementation-plan.md`, sourced from this suite's own `templates/plan/`
(never from the target workspace itself). Backs `/sentinel` Phase 1.6
("Plan & Tasks Format Check") — see claude-commands/sentinel.md.

Usage:
    python ensure_plan_templates.py --workspace /absolute/path/to/workspace [options]

Required:
    --workspace PATH   Absolute path to the target workspace root.

Optional:
    --dry-run          Report what would happen; write nothing.
    --force            Also populate a target file that exists but is
                        empty/whitespace-only (see Safety Invariant below).
    --output-json      Emit the report as JSON to stdout.
    --quiet            Suppress human-readable output (errors still print).

Workflow calling convention (from /sentinel Phase 1.6):
    python {SCRIPTS_DIR}/plan/ensure_plan_templates.py --workspace {TARGET} --output-json

SAFETY INVARIANT (deliberate, documented narrowing of
PILLAR_04_POST_BUILD_HYGIENE_ARCHIVAL_NODELETE.md §4.4's literal populator
description — Sovereign Redesign Cluster Stage 5):

PILLAR_04 §4.4 describes the populator as copying from template "if absent
OR missing required marker structure" — read literally, that would silently
overwrite ANY pre-existing tasks.md/implementation-plan.md that simply
predates the marker convention, which is every such file that existed
before this feature shipped, including this very cluster's own governing
tasks.md. That is a data-loss bug, not a feature, and this implementation
deliberately does not build it that way:

  - A target file that is ABSENT is populated from the template. Safe —
    nothing to lose.
  - A target file that EXISTS and has any non-whitespace content is NEVER
    written to, regardless of --force. No exceptions. Lacking the marker
    convention is not the same as being safe to destroy.
  - A target file that EXISTS but is empty or whitespace-only is populated
    ONLY when --force is passed (default: skipped, reported, left alone).

This is architecturally read-then-write, matching doorway/'s own
self-healing precedent (integrity.py creates missing files, never
overwrites existing ones) rather than a naive sync/clobber tool.

This tool is the second script in this suite (after doorway/) to write to a
target workspace. It is NOT read-only like scripts/focus/.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the parent of the plan/ package directory, AND this suite's own
# scripts/ root (for engine_utils), are importable when run directly.
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from plan import __version__
from plan.reporter import PlanReporter
from engine_utils import assert_within, atomic_write, safe_read

SCHEMA_VERSION = "1.0"

TASKS_FILENAME = "tasks.md"
PLAN_FILENAME = "implementation-plan.md"
TEMPLATES_RELPATH = Path("templates") / "plan"

_PLACEHOLDER = "[Workspace/Project Name]"


class PlanPopulator:
    """Idempotently ensures tasks.md + implementation-plan.md exist in a target workspace."""

    def __init__(self, workspace: Path, templates_dir: Path, dry_run: bool = False, force: bool = False):
        self.workspace = Path(workspace).resolve()
        self.templates_dir = Path(templates_dir).resolve()
        self.dry_run = dry_run
        self.force = force

    def run(self) -> dict:
        actions = [
            self._ensure_file(TASKS_FILENAME, "tasks.md.template"),
            self._ensure_file(PLAN_FILENAME, "implementation-plan.md.template"),
        ]
        populated = sum(1 for a in actions if a["action"] == "populated")
        would_populate = sum(1 for a in actions if a["action"] == "would_populate")
        skipped = sum(1 for a in actions if a["action"].startswith("skipped"))
        errors = sum(1 for a in actions if a["action"] == "error")
        return {
            "schema_version": SCHEMA_VERSION,
            "tool": "ensure_plan_templates",
            "tool_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(self.workspace),
            "dry_run": self.dry_run,
            "force": self.force,
            "actions": actions,
            "summary": {
                "populated": populated,
                "would_populate": would_populate,
                "skipped": skipped,
                "errors": errors,
            },
        }

    def _ensure_file(self, target_name: str, template_name: str) -> dict:
        try:
            target_path = assert_within(self.workspace / target_name, self.workspace)
        except ValueError as exc:
            return {"file": target_name, "action": "error", "reason": str(exc)}

        template_path = self.templates_dir / template_name
        if not template_path.is_file():
            return {
                "file": target_name, "action": "error",
                "reason": f"template not found: {template_path}",
            }

        if target_path.is_file():
            existing = safe_read(target_path)
            if existing.strip():
                return {
                    "file": target_name, "action": "skipped_exists",
                    "reason": "file has real content; never overwritten regardless of --force "
                              "(see module Safety Invariant)",
                }
            if not self.force:
                return {
                    "file": target_name, "action": "skipped_empty",
                    "reason": "file exists but is empty/whitespace-only; pass --force to populate it",
                }

        if self.dry_run:
            return {
                "file": target_name, "action": "would_populate",
                "reason": f"dry-run: would create from {template_name}",
            }

        template_content = safe_read(template_path)
        if not template_content:
            return {
                "file": target_name, "action": "error",
                "reason": f"template unreadable or empty: {template_path}",
            }
        atomic_write(target_path, self._customize(template_content))
        return {"file": target_name, "action": "populated", "reason": f"created from {template_name}"}

    def _customize(self, template_content: str) -> str:
        return template_content.replace(_PLACEHOLDER, self.workspace.name)


def _default_templates_dir() -> Path:
    # templates/plan/ lives at this suite's own repo root, three levels up
    # from scripts/plan/ensure_plan_templates.py (scripts/plan/ -> scripts/ -> repo root).
    return _HERE.parent.parent / TEMPLATES_RELPATH


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ensure_plan_templates.py",
        description="Canonical Plan & Tasks Template Populator — idempotently ensures a "
                    "target workspace has tasks.md + implementation-plan.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python ensure_plan_templates.py --workspace /home/user/project\n"
            "  python ensure_plan_templates.py --workspace /home/user/project --dry-run\n"
            "  python ensure_plan_templates.py --workspace /home/user/project --output-json\n"
        ),
    )
    parser.add_argument("--workspace", required=True, type=str,
                        help="Absolute path to the target workspace root.")
    parser.add_argument("--templates-dir", type=str, default=None,
                        help="Override the templates/plan/ source directory (default: "
                             "this suite's own templates/plan/).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would happen; write nothing.")
    parser.add_argument("--force", action="store_true",
                        help="Also populate a target file that exists but is "
                             "empty/whitespace-only. Never overwrites real content.")
    parser.add_argument("--output-json", action="store_true",
                        help="Emit the report as JSON to stdout.")
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

    templates_dir = Path(args.templates_dir).resolve() if args.templates_dir else _default_templates_dir()
    if not templates_dir.is_dir():
        print(f"[ERROR] Templates directory does not exist: {templates_dir}", file=sys.stderr)
        return 1

    populator = PlanPopulator(
        workspace=workspace, templates_dir=templates_dir,
        dry_run=args.dry_run, force=args.force,
    )
    report = populator.run()
    PlanReporter().render(report, quiet=args.quiet, output_json=args.output_json)
    return 1 if report["summary"]["errors"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
