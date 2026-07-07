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

[HARDENED 2026-05-15 — /harden-workflow --ticket 20260514_sentinel_workflow.md, /nodelete]
  - _expand_template() added: replaces [DIRECTORY_LIST_PLACEHOLDER] with real
    enumerated directory listing from the target workspace, and expands
    {workspace} and {workspace_name} tokens. heal() now calls this before
    writing any template to disk, eliminating the verbatim-template clone bug.

[HARDENED 2026-07-07 — Sovereign Scaling Cluster, resolves the gap between
doorway.py's own stated "Doorway Design Invariant" (PR 01-06: "Agent context
is delivered by the engine [substrate_index.json], not by filesystem
cardinality") and this module's actual behavior, which kept auto-creating
README.md everywhere except two hardcoded exclusions. create_readme() is now
gated behind autoheal_enabled (default False) -- README materialization
becomes opt-in, completing the invariant PR 01-01/01-06 already declared but
never finished enforcing. heal() (Architecture.md/MANIFEST.md self-repair)
is unaffected -- this gate is README-specific.]
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
        readme_exclude_dirs: Set of dirs whose READMEs are never auto-healed
            (P1 pr-01-00 stabilization; e.g. claude-commands). Only relevant
            when autoheal_enabled is True.
        autoheal_enabled:   Master switch for create_readme() (default False).
            README materialization is opt-in, per the Doorway Design
            Invariant this package already declares (see module docstring,
            2026-07-07 entry) -- context comes from substrate_index.json,
            not from N x README.md. heal() (Architecture.md/MANIFEST.md) is
            unaffected by this flag.
    """

    def __init__(
        self,
        workspace: Path,
        primary_templates: Path,
        backup_templates: Path,
        readme_exclude_dirs: set = None,
        autoheal_enabled: bool = False,
    ):
        self.workspace = workspace
        self.primary_templates = primary_templates
        self.backup_templates = backup_templates
        self.readme_exclude_dirs = readme_exclude_dirs or set()
        self.autoheal_enabled = autoheal_enabled

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
            # Expand workspace-specific tokens before writing (Bug #1 fix).
            template_content = self._expand_template(template_content)
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
    # Template token expansion
    # ------------------------------------------------------------------

    def _expand_template(self, content: str) -> str:
        """
        Expands workspace-generic tokens in a template string before it is
        written to disk.

        Tokens handled:
          [DIRECTORY_LIST_PLACEHOLDER]  — replaced with a formatted markdown
              list of the workspace's top-level directories (excluding hidden
              dirs and common artifact dirs). Each entry reads:
              '- `dirname/`: [awaiting FOLDER_OWNERSHIP.md]'
          {workspace}       — absolute path to the workspace root
          {workspace_name}  — basename of the workspace root directory

        [HARDENED 2026-05-15 — Bug #1 fix, /harden-workflow --ticket
        20260514_sentinel_workflow.md + /nodelete]
        """
        _IGNORE = {
            ".git", ".venv", "__pycache__", "node_modules", "build",
            "dist", ".pytest_cache", ".doorway", ".ipynb_checkpoints",
        }

        if "[DIRECTORY_LIST_PLACEHOLDER]" in content:
            try:
                dirs = sorted(
                    p for p in self.workspace.iterdir()
                    if p.is_dir()
                    and p.name not in _IGNORE
                    and not p.name.startswith(".")
                )
                if dirs:
                    listing = "\n".join(
                        f"- `{d.name}/`: [awaiting FOLDER_OWNERSHIP.md]"
                        for d in dirs
                    )
                else:
                    listing = "- *(no top-level directories detected)*"
            except OSError:
                listing = "- *(directory enumeration failed — re-run doorway after permissions are set)*"

            content = content.replace("[DIRECTORY_LIST_PLACEHOLDER]", listing)

        content = content.replace("{workspace}", str(self.workspace))
        content = content.replace("{workspace_name}", self.workspace.name)
        return content

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
            True if the README was created; False on failure or if a README
            already exists on disk (see existence re-check below).
        """
        # [2026-07-07, Sovereign Scaling Cluster] Materialization is opt-in.
        # See __init__ docstring and module docstring's Doorway Design
        # Invariant entry.
        if not self.autoheal_enabled:
            return False

        target = self.workspace / folder_path_str / "README.md"
        name = Path(folder_path_str).name

        # Validate target stays within workspace (CWE-22).
        try:
            assert_within(target, self.workspace)
        except ValueError as e:
            print(f"[SELF-HEAL] {e}")
            return False

        # P1: skip heal entirely for README_EXCLUDE_DIRS (configurable, no-heal).
        if self._is_readme_excluded(folder_path_str):
            return False

        # [SECURITY — 2026-07-07, Sovereign Redesign Cluster Stage 6, found via
        # independent design review, ticket 20260705_doorway_lazy-scan-stale-readme]
        # This method is called specifically because the caller's has_readme flag
        # says the file doesn't exist — but that flag can be stale (scanner.py's
        # carry-over logic copies forward has_readme from a prior snapshot without
        # re-statting disk for children of a hash-stable parent). Re-verify against
        # the actual filesystem before writing: if a README genuinely exists, this
        # is a false-positive repair signal, not a real gap — do nothing rather
        # than silently overwrite real content with boilerplate.
        if target.exists():
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

    def _is_readme_excluded(self, folder_path_str: str) -> bool:
        """Respect README_EXCLUDE_DIRS (and subpaths) — no heal, no contrib."""
        if not self.readme_exclude_dirs or not folder_path_str:
            return False
        p = Path(folder_path_str)
        for ex in self.readme_exclude_dirs:
            if str(p) == ex or str(p).startswith(ex + "/"):
                return True
        return False
