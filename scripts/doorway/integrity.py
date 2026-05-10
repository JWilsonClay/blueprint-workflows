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
"""

from pathlib import Path


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
                data_dir.mkdir(parents=True, exist_ok=True)
                (data_dir / ".gitkeep").touch()
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
        # Validate target stays within workspace.
        try:
            target_path.resolve().relative_to(self.workspace.resolve())
        except ValueError:
            print(f"[SELF-HEAL] Blocked: target outside workspace: {target_path}")
            return

        template_content = None

        primary = self.primary_templates / template_name
        if primary.exists():
            try:
                template_content = primary.read_text(encoding="utf-8")
            except OSError:
                pass

        if template_content is None:
            backup = self.backup_templates / template_name
            if backup.exists():
                try:
                    template_content = backup.read_text(encoding="utf-8")
                    print(
                        f"[SELF-HEAL] Primary template missing. Used backup for "
                        f"{target_path.name}."
                    )
                except OSError:
                    pass

        if template_content is not None:
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(template_content, encoding="utf-8")
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

        # Validate target stays within workspace.
        try:
            target.resolve().relative_to(self.workspace.resolve())
        except ValueError:
            print(f"[SELF-HEAL] Blocked: README target outside workspace: {target}")
            return False

        template_content = None
        for base in [self.primary_templates, self.backup_templates]:
            tpl_file = base / "README.md.template"
            if tpl_file.exists():
                try:
                    template_content = tpl_file.read_text(encoding="utf-8")
                    break
                except OSError:
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
            target.write_text(template_content, encoding="utf-8")
            return True
        except OSError as e:
            print(f"[SELF-HEAL] Failed to create README at {target}: {e}")
            return False
