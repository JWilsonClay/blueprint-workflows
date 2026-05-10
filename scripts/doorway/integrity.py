"""
integrity.py — Substrate Integrity Manager
==========================================
Handles substrate integrity and self-healing for the Doorway Protocol.
Ensures critical governance artifacts (Architecture.md, MANIFEST.md) exist
and recreates them from templates when missing.

Refactored from .blueprints/governance/thedoorway/integrity_manager.py:
  - Removed module-level PROJECT_ROOT constant.
  - 'project_root' constructor argument renamed to 'workspace' throughout.
  - Added explicit encoding on all read/write operations.
  - Added path validation in heal() to prevent writes outside workspace.

[SECURITY — 2026-05-10 — /harden pass, /nodelete]
  - write_text() replaced with atomic_write() throughout (CWE-362 / CWE-732).
  - read_text() replaced with safe_read() with template size cap (CWE-400).
  - mkdir() + touch() in ensure_substrate replaced with safe_mkdir() (CWE-732).
  - assert_within() added to heal() and create_readme() (CWE-22).
"""

from pathlib import Path

from doorway._utils import atomic_write, assert_within, safe_mkdir, safe_read


class IntegrityManager:
    """
    Handles substrate integrity and self-healing for the Doorway Protocol.

    Args:
        workspace:          Absolute path to the target workspace root.
        primary_templates:  Path to the primary templates directory.
        backup_templates:   Path to the fallback templates directory.
    """

    def __init__(
        self,
        workspace: Path,
        primary_templates: Path,
        backup_templates: Path,
    ):
        self.workspace = workspace
        self.primary_templates = primary_templates
        self.backup_templates = backup_templates

    # ------------------------------------------------------------------
    # Substrate bootstrap
    # ------------------------------------------------------------------

    def ensure_substrate(self, data_dir: Path, critical_files: dict) -> None:
        """
        Self-healing bootstrap:
          1. Creates the data/.doorway directory if missing.
          2. Recreates any missing critical governance files from templates.

        Args:
            data_dir:       Path to the workspace's .doorway data directory.
            critical_files: Dict mapping target_file_path → template_name.
        """
        if not data_dir.exists():
            try:
                # safe_mkdir creates with mode=0o700 (owner-only, CWE-732).
                safe_mkdir(data_dir)
                atomic_write(data_dir / ".gitkeep", "")  # CWE-362
                print("[SELF-HEAL] Created missing .doorway/ data directory.")
            except OSError as e:
                print(f"[SELF-HEAL] Failed to create data directory: {e}")
                return

        for file_path, template_name in critical_files.items():
            if not file_path.exists():
                self.heal(file_path, template_name)

    # ------------------------------------------------------------------
    # File healing from templates
    # ------------------------------------------------------------------

    def heal(self, target_path: Path, template_name: str) -> None:
        """
        Recreates a missing file from the first available template.
        Primary template location is tried first; backup is used as fallback.

        Args:
            target_path:   The path that should exist but doesn't.
            template_name: Filename of the template to use (e.g. 'Architecture.md.template').
        """
        # Validate target stays within workspace (CWE-22).
        try:
            assert_within(target_path, self.workspace)
        except ValueError as e:
            print(f"[SELF-HEAL] {e}")
            return

        template_content = None

        for base in [self.primary_templates, self.backup_templates]:
            primary = base / template_name
            if primary.exists():
                try:
                    # safe_read: template files should be small (CWE-400).
                    template_content = safe_read(primary, max_bytes=512 * 1024)
                    if base == self.backup_templates:
                        print(
                            f"[SELF-HEAL] Primary template missing. Used backup for "
                            f"{target_path.name}."
                        )
                    break
                except (OSError, ValueError):
                    continue

        if template_content is not None:
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(target_path, template_content)  # CWE-362 / CWE-732
                print(
                    f"[SELF-HEAL] Recreated {target_path.relative_to(self.workspace)} "
                    f"from template."
                )
            except OSError as e:
                print(f"[SELF-HEAL] Write failed for {target_path.name}: {e}")
        else:
            print(
                f"[ERROR] Cannot heal {target_path.name}: "
                "no template found in primary or backup location."
            )

    # ------------------------------------------------------------------
    # README self-healing
    # ------------------------------------------------------------------

    def create_readme(self, folder_path_str: str) -> bool:
        """
        Creates a standard README.md in folder_path_str using the README
        template. Falls back to an inline minimal template if no template
        is found.

        Args:
            folder_path_str: Workspace-relative path string (e.g. 'governance/roles').

        Returns:
            True if the README was created; False on failure.
        """
        target = self.workspace / folder_path_str / "README.md"
        name = Path(folder_path_str).name

        # Validate target stays within workspace (CWE-22).
        try:
            assert_within(target, self.workspace)
        except ValueError as e:
            print(f"[SELF-HEAL] {e}")
            return False

        template_content = None
        for base in [self.primary_templates, self.backup_templates]:
            tpl_file = base / "README.md.template"
            if tpl_file.exists():
                try:
                    template_content = safe_read(tpl_file, max_bytes=512 * 1024)  # CWE-400
                    break
                except (OSError, ValueError):
                    continue

        if template_content:
            template_content = template_content.replace("{name}", name)
            template_content = template_content.replace("{path}", folder_path_str)
        else:
            # Minimal inline fallback — no external dependency.
            template_content = (
                f"# {name} — [One Sentence Owner Description Placeholder]\n\n"
                "## Ownership\n"
                "- **Owner**: [Defined in FOLDER_OWNERSHIP.md]\n\n"
                "## Contents\n"
                "<!-- BREADCRUMB -->\n"
                "Auto-generated summary for navigation.\n"
                "<!-- BREADCRUMB_END -->\n"
            )

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(target, template_content)  # CWE-362 / CWE-732
            return True
        except (OSError, ValueError) as e:
            print(f"[SELF-HEAL] Failed to create README at {target}: {e}")
            return False
