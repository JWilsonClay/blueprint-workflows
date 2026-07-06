"""
audit_repairs.py — Audit Repair Manager
=========================================
Handles Tier 2 (qualitative audit) and Tier 3 (repair plan / success certificate)
operations of the Doorway Protocol.

Refactored from .blueprints/governance/thedoorway/audit_repairs.py:
  - Removed module-level PROJECT_ROOT constant.
  - 'project_root' constructor argument renamed to 'workspace' throughout.
  - Adjusted BestPracticesAuditor import path for new package location.
  - Added explicit encoding on all read/write operations.
  - Broad 'except Exception' replaced with specific OSError handling.
  - Missing audit_results keys handled gracefully (uses .get() with defaults).

[SECURITY — 2026-05-10 — /harden pass, /nodelete]
  - write_text() replaced with atomic_write() throughout (CWE-362 / CWE-732).
  - read_text() replaced with safe_read() with 512 KB template cap (CWE-400).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from doorway.best_practices import BestPracticesAuditor
except ImportError:
    BestPracticesAuditor = None  # type: ignore

from doorway._utils import atomic_write, safe_read


class AuditRepairManager:
    """
    Handles Tier 2 (qualitative audit) and Tier 3 (repair plan / success
    certificate) operations of the Doorway Protocol.

    Args:
        workspace:            Absolute path to the target workspace root.
        primary_templates:    Path to the primary templates directory.
        backup_templates:     Path to the fallback templates directory.
        repair_plan_file:     Path where the repair plan Markdown will be written.
        success_cert_file:    Path where the zero-finding JSON cert will be written.
        repair_template_file: Explicit path to the repair_plan.md.template file.
    """

    def __init__(
        self,
        workspace: Path,
        primary_templates: Path,
        backup_templates: Path,
        repair_plan_file: Path,
        success_cert_file: Path,
        repair_template_file: Path,
    ):
        self.workspace = workspace
        self.primary_templates = primary_templates
        self.backup_templates = backup_templates
        self.repair_plan_file = repair_plan_file
        self.success_cert_file = success_cert_file
        self.repair_template_file = repair_template_file

    # ------------------------------------------------------------------
    # Tier 2 — Qualitative Audit
    # ------------------------------------------------------------------

    def perform_qualitative_audit(
        self, audit_results: dict, current_map: dict, full_scan: bool
    ) -> Optional[dict]:
        """
        Runs the BestPracticesAuditor over modified or new Python files.
        Branches to generate_repair_plan() if violations are found, or
        write_success_certificate() if the workspace is clean.

        Returns None if BestPracticesAuditor is unavailable or no files
        qualify for auditing.
        """
        if BestPracticesAuditor is None:
            return None

        # Defensive clean for legacy/any "[BOOTSTRAP]" suffix in drift["new"] (P1 tagging
        # surface; paths must remain usable keys into current_map). See auditor.py drift doc.
        def _clean(p):
            if isinstance(p, str) and " [BOOTSTRAP]" in p:
                return p.split(" [BOOTSTRAP]", 1)[0]
            return p

        paths_to_audit = set(
            _clean(p) for p in (audit_results.get("new", []) + audit_results.get("modified", []))
        )
        files_to_audit: List[Path] = []

        if full_scan:
            for path, info in current_map.items():
                for f in info.get("py_files", []):
                    files_to_audit.append(self.workspace / path / f)
        else:
            for path in paths_to_audit:
                if path in current_map:
                    for f in current_map[path].get("py_files", []):
                        files_to_audit.append(self.workspace / path / f)

        if not files_to_audit:
            return None

        auditor = BestPracticesAuditor(self.workspace)
        results = auditor.run(files_to_audit)

        violations = results.get("summary", {}).get("violations", 0)
        warnings = results.get("summary", {}).get("warnings", 0)

        if violations > 0 or warnings > 0:
            self.generate_repair_plan(results, files_to_audit)
        else:
            self.write_success_certificate(results, files_to_audit)

        return results

    # ------------------------------------------------------------------
    # Tier 3 — Repair Plan Generation
    # ------------------------------------------------------------------

    def generate_repair_plan(self, results: dict, files: List[Path]) -> None:
        """
        Generates a Markdown repair plan from the audit results using the
        repair_plan.md.template. Falls back to the explicit repair_template_file
        path if template directories don't contain it.
        """
        template_content = None

        for base in [self.primary_templates, self.backup_templates]:
            tpl_file = base / "repair_plan.md.template"
            if tpl_file.exists():
                try:
                    template_content = safe_read(tpl_file, max_bytes=512 * 1024)  # CWE-400
                    break
                except (OSError, ValueError):
                    continue

        if template_content is None and self.repair_template_file.exists():
            try:
                template_content = safe_read(
                    self.repair_template_file, max_bytes=512 * 1024  # CWE-400
                )
            except (OSError, ValueError):
                pass

        if not template_content:
            print("[AUDIT] Repair plan template not found — skipping plan generation.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doctrines = results.get("doctrines", {})
        summary = results.get("summary", {})

        high_impact = []
        for v in doctrines.get("SOLID_KISS", []):
            if v.get("level") == "violation":
                msg = f"- **{v.get('file', '?')}**:{v.get('line', '?')} → {v.get('message', '')}"
                if "function" in v:
                    msg += f" in `{v['function']}`"
                if "cc" in v:
                    msg += f" (CC={v['cc']})"
                high_impact.append(msg)

        soc_violations = [
            f"- {v.get('file', '?')}:{v.get('line', '?')} → {v.get('message', '')}"
            for v in doctrines.get("SoC", [])
        ]
        dry_violations = [
            f"- {v.get('file', '?')}:{v.get('line', '?')} → {v.get('message', '')}"
            for v in doctrines.get("DRY", [])
        ]

        substitutions = {
            "{timestamp}": timestamp,
            "{count}": str(len(files)),
            "{violations}": str(summary.get("violations", 0)),
            "{warnings}": str(summary.get("warnings", 0)),
            "{auto_fixable}": str(summary.get("auto_fixable", 0)),
            "{pep8_count}": str(len(doctrines.get("PEP8", []))),
            "{soc_count}": str(len(doctrines.get("SoC", []))),
            "{solid_kiss_count}": str(len(doctrines.get("SOLID_KISS", []))),
            "{dry_count}": str(len(doctrines.get("DRY", []))),
            "{yagni_count}": str(len(doctrines.get("YAGNI", []))),
            "{high_impact_refactors}": "\n".join(high_impact) if high_impact else "_None detected_",
            "{soc_violations}": "\n".join(soc_violations) if soc_violations else "_None detected_",
            "{dry_violations}": "\n".join(dry_violations) if dry_violations else "_None detected_",
            "{other_recommendations}": "_Follow workspace architectural conventions._",
        }

        report = template_content
        for k, v in substitutions.items():
            report = report.replace(k, v)

        try:
            self.repair_plan_file.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(self.repair_plan_file, report)  # CWE-362 / CWE-732
            print(f"\n[!] Audit findings: repair plan written to {self.repair_plan_file}")
        except (OSError, ValueError) as e:
            print(f"[AUDIT] Failed to write repair plan: {e}")

    # ------------------------------------------------------------------
    # Tier 3 — Success Certificate
    # ------------------------------------------------------------------

    def write_success_certificate(self, results: dict, files: List[Path]) -> None:
        """
        Writes a zero-finding JSON certificate and removes any stale repair plan.
        """
        cert = {
            "status": "ZERO_FINDING",
            "timestamp": datetime.now().isoformat(),
            "summary": results.get("summary", {}),
            "files_scanned": len(files),
        }

        try:
            self.success_cert_file.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(  # CWE-362 / CWE-732
                self.success_cert_file, json.dumps(cert, indent=2)
            )
            if self.repair_plan_file.exists():
                self.repair_plan_file.unlink()
            print(f"\n[+] ZERO-FINDING STATE: Certificate written at {cert['timestamp']}")
        except (OSError, ValueError) as e:
            print(f"[AUDIT] Failed to write success certificate: {e}")
