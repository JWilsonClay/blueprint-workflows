"""
auditor.py — Structural Auditor
=================================
Handles structural auditing and drift detection for the Doorway Protocol.
Compares current and previous workspace maps to detect new, modified,
deleted, and unowned directories, and flags README gaps triggering self-healing.

Refactored from .blueprints/governance/thedoorway/structural_auditor.py:
  - Renamed from structural_auditor.py to auditor.py (shorter, convention-consistent).
  - 'project_root' constructor argument renamed to 'workspace' throughout.
  - 'ownership_file' constructor argument renamed to 'ownership_file'
    (unchanged) — passed as absolute path from caller.
  - Added explicit encoding on FOLDER_OWNERSHIP.md read.
  - 'readme_gaps' key renamed to 'missing_readme' in drift dict
    for clarity and alignment with recommender.py expectations.
  - Broad 'except Exception: pass' replaced with specific OSError handling.
"""

from pathlib import Path


class StructuralAuditor:
    """
    Handles structural auditing and drift detection for the Doorway Protocol.

    Args:
        workspace:          Absolute path to the target workspace root.
        ownership_file:     Absolute path to the FOLDER_OWNERSHIP.md file
                            (may not exist; gracefully skipped if absent).
        breadcrumb_manager: BreadcrumbManager instance for proposal logging.
        integrity_manager:  IntegrityManager instance for README self-healing.
        metrics:            Shared metrics dict {'created': int, 'repairs': int, ...}.
    """

    def __init__(
        self,
        workspace: Path,
        ownership_file: Path,
        breadcrumb_manager,
        integrity_manager,
        metrics: dict,
    ):
        self.workspace = workspace
        self.ownership_file = ownership_file
        self.breadcrumb_manager = breadcrumb_manager
        self.integrity_manager = integrity_manager
        self.metrics = metrics

    def audit(self, current_map: dict, previous_map: dict) -> dict:
        """
        Compares current_map against previous_map to detect structural drift.
        Logs breadcrumb proposals for new and modified directories.
        Triggers README self-healing for directories missing a README.

        Returns:
            drift dict with keys:
              new           — directories first seen in this scan
              modified      — directories whose content hash changed
              deleted       — directories present in previous scan but now gone
              unowned       — directories absent from FOLDER_OWNERSHIP.md
              missing_readme — directories that lacked a README (healed if possible)
        """
        drift = {
            "new": [],
            "modified": [],
            "deleted": [],
            "unowned": [],
            "missing_readme": [],
        }
        ownership_map = self.parse_ownership()

        for path, info in current_map.items():
            # Change detection.
            if path != "." and path not in previous_map:
                drift["new"].append(path)
                self.breadcrumb_manager.propose(path, "new directory")
            elif path in previous_map:
                prev_hash = previous_map[path].get("content_hash")
                if info["content_hash"] != prev_hash:
                    drift["modified"].append(path)
                    self.breadcrumb_manager.propose(path, "hash drift detected")

            # README check — trigger self-healing if missing.
            if not info["has_readme"]:
                drift["missing_readme"].append(path)
                if self.integrity_manager.create_readme(path):
                    self.metrics["created"] += 1
                    self.metrics["repairs"] += 1

            # Ownership check.
            if path != "." and not self.is_owned(path, ownership_map):
                drift["unowned"].append(path)

        # Deletion detection.
        for path in previous_map:
            if path not in current_map:
                drift["deleted"].append(path)

        return drift

    def is_owned(self, path_str: str, ownership_map: list) -> bool:
        """
        Returns True if path_str or any of its parents appears in ownership_map.
        Uses exact-match or parent-of logic so sub-directories inherit ownership
        from their parent without requiring explicit listing.
        """
        if path_str == ".":
            return True

        path = Path(path_str)
        current = path
        while str(current) != ".":
            if str(current).rstrip("/") in ownership_map:
                return True
            parent = current.parent
            if parent == current:
                break
            current = parent

        return False

    def parse_ownership(self) -> list:
        """
        Extracts directory paths from FOLDER_OWNERSHIP.md.
        Expects lines formatted as '- path/to/dir: description'.
        Returns an empty list if the file is absent or unreadable.
        """
        owned_dirs = []
        if not self.ownership_file.exists():
            return owned_dirs

        try:
            lines = self.ownership_file.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if line.strip().startswith("- "):
                    parts = line.split(":")
                    if parts:
                        path_part = parts[0].replace("- ", "").strip().rstrip("/")
                        if path_part:
                            owned_dirs.append(path_part)
        except OSError as e:
            print(f"[AUDITOR] Cannot read FOLDER_OWNERSHIP.md: {e}")

        return owned_dirs
