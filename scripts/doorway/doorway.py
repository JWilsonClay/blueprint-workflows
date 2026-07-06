#!/usr/bin/env python3
"""
doorway.py — Sovereign Workspace Contextualizer CLI
====================================================
Universal entry point for the Doorway Protocol.
Performs drift detection, breadcrumb regeneration, MANIFEST synchronization,
and protocol recommendations against any target workspace.

Usage:
    python doorway.py --workspace /absolute/path/to/workspace [options]

Required:
    --workspace PATH    Absolute path to the target workspace root.

Optional:
    --full-scan         Force deep scan of all directories (ignores hash cache).
    --auto-apply        Apply approved breadcrumb proposals from the update log.
    --output-json       Emit results as JSON to stdout (for workflow consumption).
    --quiet             Suppress all output except errors and JSON.

Workflow calling convention (from any global_workflows workflow):
    python {SCRIPTS_DIR}/doorway/doorway.py --workspace {TARGET_WORKSPACE}
    python {SCRIPTS_DIR}/doorway/doorway.py --workspace {TARGET_WORKSPACE} --output-json

Data directory:
    All runtime state is stored in {workspace}/.doorway/ (hidden, workspace-local).
    This directory is auto-created on first run.

Extracted from .blueprints/governance/thedoorway/dynamic_contextualizer.py.
Refactored 2026-05-09 for universal workspace-agnostic use.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Package-relative imports.  When called as a script, ensure the parent of
# the doorway/ package directory is on sys.path.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from doorway._utils import atomic_write, safe_mkdir, safe_read
from doorway.scanner import WorkspaceScanner
from doorway.breadcrumb import BreadcrumbManager
from doorway.integrity import IntegrityManager
from doorway.auditor import StructuralAuditor
from doorway.recommender import ProtocolRecommender
from doorway.manifest import ManifestManager
from doorway.reporter import SubstrateReporter
from doorway.audit_repairs import AuditRepairManager


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOORWAY_DATA_DIR_NAME = ".doorway"  # Hidden, workspace-local state directory.

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".ipynb_checkpoints",
    "node_modules",
    "build",
    "dist",
    ".pytest_cache",
    DOORWAY_DATA_DIR_NAME,  # Never scan our own data directory.
}

# P1 stabilization (pr-01-00 per PILLAR_01): configurable dirs whose README.md
# are intentionally not healed (e.g. nav files like claude-commands/README.md)
# and do not contribute to has_readme/ingested/missing_readme signals.
README_EXCLUDE_DIRS = {
    "claude-commands",
    "helpdesk-tickets/archive",
}


# ---------------------------------------------------------------------------
# Main contextualizer class
# ---------------------------------------------------------------------------

class DoorwayContextualizer:
    """
    Universal Workspace Contextualizer.
    Orchestrates all Doorway Protocol tiers against a caller-specified workspace.

    Args:
        workspace:    Resolved absolute Path to the target workspace root.
        quiet:        Suppress verbose console output.
        output_json:  Emit results as JSON instead of human-readable output.
    """

    def __init__(self, workspace: Path, quiet: bool = False, output_json: bool = False):
        self.workspace = workspace
        self.quiet = quiet
        self.output_json = output_json

        # Data directory: {workspace}/.doorway/
        self.data_dir = workspace / DOORWAY_DATA_DIR_NAME
        self.snapshot_file = self.data_dir / "workspace_snapshot.json"
        self.update_log = self.data_dir / "context_updates.log"
        self.success_cert = self.data_dir / "ctw_last_success.json"
        self.repair_plan_file = self.data_dir / "repair_implementation_plan.md"

        # Templates: bundled with this package.
        self.primary_templates = _HERE / "templates"
        # Fallback: workspace may carry its own templates directory.
        self.backup_templates = workspace / "templates" / "doorway"

        # Governance files (optional — gracefully skipped if absent).
        self.architecture_file = workspace / "governance" / "Architecture.md"
        self.manifest_file = workspace / "MANIFEST.md"
        self.ownership_file = workspace / "docs" / "FOLDER_OWNERSHIP.md"

        self.repair_template = self.primary_templates / "repair_plan.md.template"

        # Metrics shared across components.
        self.metrics: dict = {"created": 0, "ingested": 0, "repairs": 0}

        # Instantiate all components — workspace path flows through constructors.
        self.scanner = WorkspaceScanner(workspace, IGNORE_DIRS, README_EXCLUDE_DIRS)
        self.breadcrumb_manager = BreadcrumbManager(workspace, self.update_log)
        self.integrity_manager = IntegrityManager(
            workspace, self.primary_templates, self.backup_templates, README_EXCLUDE_DIRS
        )
        self.auditor = StructuralAuditor(
            workspace,
            self.ownership_file,
            self.breadcrumb_manager,
            self.integrity_manager,
            self.metrics,
            README_EXCLUDE_DIRS,
        )
        self.recommender = ProtocolRecommender()
        self.manifest_manager = ManifestManager(workspace, self.manifest_file)
        self.reporter = SubstrateReporter()
        self.audit_manager = AuditRepairManager(
            workspace,
            self.primary_templates,
            self.backup_templates,
            self.repair_plan_file,
            self.success_cert,
            self.repair_template,
        )

    def run(self, full_scan: bool = False, auto_apply: bool = False) -> dict:
        """
        Main execution loop.

        Steps:
          0. Ensure .doorway/ data directory and critical governance files exist.
          0.5 Apply any approved breadcrumb proposals (if --auto-apply).
          1. Load previous workspace snapshot.
          2. Run hash-based workspace scan.
          3. Structural audit: detect drift, heal missing READMEs.
          4. Promote WORKLOG entries to governance/Chronology.md.
          5. Persist the new snapshot.
          6. Sync MANIFEST.md.
          7. Generate protocol/workflow recommendations.
          8. Run qualitative best-practices audit (if BestPracticesAuditor available).
          9. Render the report (or emit JSON).

        Returns:
            dict with keys: map, drift, recommendations, overhead, skipped, data_dir
        """
        start = time.time()

        # Step 0 — Ensure data directory and critical governance files.
        # safe_mkdir creates .doorway/ with mode=0o700 (CWE-732).
        safe_mkdir(self.data_dir)
        critical_files = {}
        if not self.architecture_file.exists():
            critical_files[self.architecture_file] = "Architecture.md.template"
        if not self.manifest_file.exists():
            critical_files[self.manifest_file] = "MANIFEST.md.template"
        if not self.ownership_file.exists():
            critical_files[self.ownership_file] = "FOLDER_OWNERSHIP.md.template"
        self.integrity_manager.ensure_substrate(self.data_dir, critical_files)

        # Step 0.5 — Apply approved breadcrumb proposals.
        if auto_apply:
            self.breadcrumb_manager.apply_approved()

        # Step 1 — Load previous snapshot.
        previous_map = self._load_snapshot()

        # Step 2 — Scan workspace.
        current_map, ingested_count = self.scanner.scan(previous_map, full_scan)
        self.metrics["ingested"] = ingested_count

        # Step 3 — Structural audit.
        drift = self.auditor.audit(current_map, previous_map)

        # Option C auto-escalate (P1 stabilization, pr-01-00, PILLAR_01 §4.4):
        # If incremental scan produced self-heal repairs (stale has_readme from carry-over),
        # re-scan with full_scan to refresh has_readme post-heal so final drift/zero_finding clean.
        # This eliminates need for manual --full-scan after repairs on stale snapshots.
        escalated = False
        if (not full_scan and self.metrics.get("repairs", 0) > 0 and drift.get("missing_readme")):
            print("[DOORWAY] Auto-escalated to full-scan after self-heal repairs")
            current_map, ingested_count = self.scanner.scan(previous_map, full_scan=True)
            self.metrics["ingested"] = ingested_count
            drift = self.auditor.audit(current_map, previous_map)
            escalated = True

        # Step 4 — Worklog promotion.
        self._promote_worklogs(current_map)

        # Step 5 — Persist snapshot.
        self._save_snapshot(current_map)

        # Step 6 — MANIFEST sync.
        self.manifest_manager.sync(current_map)

        # Step 7 — Protocol recommendations.
        recommendations = self.recommender.recommend(drift)

        # Step 8 — Qualitative audit.
        self.audit_manager.perform_qualitative_audit(drift, current_map, full_scan)

        overhead = time.time() - start

        results = {
            "map": current_map,
            "drift": drift,
            "recommendations": recommendations,
            "overhead": overhead,
            "skipped": (
                len(previous_map)
                - len(drift.get("modified", []))
                - len(drift.get("deleted", []))
                if not full_scan
                else 0
            ),
            "data_dir": str(self.data_dir),
            "escalated": escalated,
        }

        # Step 9 — Report.
        self.reporter.render(
            results,
            self.metrics,
            workspace_name=self.workspace.name,
            quiet=self.quiet,
            output_json=self.output_json,
        )

        return results

    # ------------------------------------------------------------------
    # Worklog promotion
    # ------------------------------------------------------------------

    def _promote_worklogs(self, current_map: dict) -> None:
        """
        Discovers <!-- WORKLOG --> entries in workspace READMEs and appends
        them to governance/Chronology.md (only if that file exists).
        """
        chronology_file = self.workspace / "governance" / "Chronology.md"
        if not chronology_file.exists():
            return

        promoted_entries = []
        for path, info in current_map.items():
            if info.get("has_readme"):
                readme_path = self.workspace / path / "README.md"
                try:
                    content = readme_path.read_text(encoding="utf-8")
                except OSError:
                    continue

                if "<!-- WORKLOG -->" in content and "<!-- WORKLOG_END -->" in content:
                    worklog = (
                        content.split("<!-- WORKLOG -->")[1]
                        .split("<!-- WORKLOG_END -->")[0]
                        .strip()
                    )
                    if worklog:
                        promoted_entries.append(f"### Workspace: /{path}\n{worklog}\n")

        if not promoted_entries:
            return

        try:
            chron_content = safe_read(  # CWE-400: bounded read
                chronology_file, max_bytes=10 * 1024 * 1024
            )
            header = "\n## Promoted Workspace Worklogs\n"
            if header not in chron_content:
                chron_content += header
            for entry in promoted_entries:
                if entry not in chron_content:
                    chron_content += entry
            atomic_write(chronology_file, chron_content)  # CWE-362
            print(f"[PROMOTION] Promoted {len(promoted_entries)} worklogs to Chronology.md")
        except (OSError, ValueError) as e:
            print(f"[PROMOTION] Failed to write Chronology.md: {e}")

    # ------------------------------------------------------------------
    # Snapshot persistence
    # ------------------------------------------------------------------

    def _load_snapshot(self) -> dict:
        """Loads the previous workspace snapshot from .doorway/workspace_snapshot.json."""
        if self.snapshot_file.exists():
            try:
                raw = self.snapshot_file.read_text(encoding="utf-8")
                # Guard against extremely large snapshot files (>50 MB).
                if len(raw) > 50 * 1024 * 1024:
                    print("[SNAPSHOT] Snapshot file exceeds 50 MB — discarding and starting fresh.")
                    return {}
                return json.loads(raw)
            except (OSError, json.JSONDecodeError) as e:
                print(f"[SNAPSHOT] Could not load snapshot: {e} — starting fresh.")
        return {}

    def _save_snapshot(self, data: dict) -> None:
        """Persists the current workspace map to .doorway/workspace_snapshot.json."""
        try:
            # safe_mkdir ensures .doorway/ exists with 0o700 (CWE-732).
            safe_mkdir(self.data_dir)
            atomic_write(  # CWE-362: atomic snapshot write
                self.snapshot_file, json.dumps(data, indent=2)
            )
        except (OSError, ValueError) as e:
            print(f"[SNAPSHOT] Failed to save snapshot: {e}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="doorway.py",
        description=(
            "Sovereign Workspace Contextualizer — drift detection, breadcrumb "
            "regeneration, MANIFEST sync, and protocol recommendations."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python doorway.py --workspace /home/user/project\n"
            "  python doorway.py --workspace /home/user/project --full-scan --output-json\n"
            "  python doorway.py --workspace /home/user/project --auto-apply\n"
        ),
    )

    parser.add_argument(
        "--workspace",
        required=True,
        type=str,
        help="Absolute path to the target workspace root.",
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Force deep scan of all directories (ignores hash cache).",
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        help="Apply approved breadcrumb proposals from the update log.",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Emit results as JSON to stdout (for workflow consumption).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except errors and JSON.",
    )

    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    # Resolve and validate the workspace path.
    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        print(f"[ERROR] Workspace does not exist: {workspace}", file=sys.stderr)
        return 1
    if not workspace.is_dir():
        print(f"[ERROR] Workspace path is not a directory: {workspace}", file=sys.stderr)
        return 1

    contextualizer = DoorwayContextualizer(
        workspace=workspace,
        quiet=args.quiet,
        output_json=args.output_json,
    )
    contextualizer.run(full_scan=args.full_scan, auto_apply=args.auto_apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
