"""
manifest.py — Manifest Manager
================================
Handles surgical updates to the workspace MANIFEST.md and generates
the Global API Map section in Architecture.md from <!-- INTERFACE --> tags.

Refactored from .blueprints/governance/thedoorway/manifest_manager.py:
  - Removed module-level PROJECT_ROOT constant.
  - 'project_root' constructor argument renamed to 'workspace' throughout.
  - Added explicit encoding on all read/write operations.
  - Added existence checks before Architecture.md update (workspace may not have one).
  - Silenced print on Architecture.md update when file does not exist.

[SECURITY — 2026-05-10 — /harden pass, /nodelete]
  - write_text() replaced with atomic_write() throughout (CWE-362 / CWE-732).
  - read_text() replaced with safe_read() with size caps (CWE-400).
  - assert_within() added before each README is read during sync (CWE-22).
"""

from pathlib import Path

from doorway._utils import atomic_write, assert_within, safe_read


class ManifestManager:
    """
    Handles surgical updates to the workspace MANIFEST.md.
    Syncs discovered READMEs into the (Auto-Synced) section.
    Extracts <!-- INTERFACE --> tags from READMEs and builds a Global API Map
    in governance/Architecture.md (only if the file exists).

    Args:
        workspace:      Absolute path to the target workspace root.
        manifest_file:  Absolute path to the workspace's MANIFEST.md.
    """

    def __init__(self, workspace: Path, manifest_file: Path):
        self.workspace = workspace
        self.manifest_file = manifest_file

    def sync(self, substrate_index: dict) -> None:
        """
        Main sync entry point. Updates MANIFEST.md with all discovered
        README directories. Optionally updates Architecture.md's Global API Map
        if any directories expose an <!-- INTERFACE --> tag.

        [RETARGETED 2026-07-06 — PR 01-03, Sovereign Redesign Cluster Stage 1]
        Previously re-derived directory facts (has_readme, display name) from
        the raw scanner map on every call — a second code path deriving the
        same facts substrate_index.json already computes canonically. Now
        consumes the index directly (single source of truth) and surfaces
        each directory's breadcrumb_summary in the MANIFEST entry, where
        before only a bare link was shown.

        Args:
            substrate_index: The dict produced by auditor.build_substrate_index()
                (same shape as the persisted substrate_index.json), containing
                a "directories" map keyed by relative path.
        """
        if not self.manifest_file.exists():
            # Not all workspaces have a MANIFEST.md — skip silently.
            return

        try:
            discovered_readmes = []
            api_map_entries = []
            directories = substrate_index.get("directories", {})

            for path, info in directories.items():
                if info.get("has_readme"):
                    abs_path = self.workspace / path
                    abs_readme = abs_path / "README.md"

                    # Build MANIFEST entry, including the index's breadcrumb
                    # summary (already a short, single-line, field-delimited
                    # string — no truncation needed).
                    display_name = f"/{path}" if path != "." else "/root"
                    summary = info.get("breadcrumb_summary", "")
                    entry = (
                        f"- [{display_name}](file://{abs_path}/) : "
                        f"[README](file://{abs_readme})"
                        + (f" — {summary}" if summary else "")
                    )
                    discovered_readmes.append((path, entry))

                    # Validate README path stays within workspace (CWE-22).
                    try:
                        assert_within(abs_readme, self.workspace)
                    except ValueError as e:
                        print(f"[MANIFEST] {e}")
                        continue
                    try:
                        content = safe_read(abs_readme, max_bytes=2 * 1024 * 1024)  # CWE-400
                        if (
                            "<!-- INTERFACE -->" in content
                            and "<!-- INTERFACE_END -->" in content
                        ):
                            interface = (
                                content.split("<!-- INTERFACE -->")[1]
                                .split("<!-- INTERFACE_END -->")[0]
                                .strip()
                            )
                            if interface:
                                api_map_entries.append(f"### /{path}\n{interface}\n")
                    except (OSError, ValueError):
                        pass

            # Sort: root (.) first, then alphabetical.
            discovered_readmes.sort(key=lambda x: (x[0] != ".", x[0]))
            formatted_entries = [entry for _, entry in discovered_readmes]
            self._update_manifest(formatted_entries)

            if api_map_entries:
                self._update_api_map(api_map_entries)

        except OSError as e:
            print(f"[MANIFEST] Sync failed: {e}")

    def _update_manifest(self, formatted_entries: list) -> None:
        """
        Surgically replaces the Auto-Synced section in MANIFEST.md with
        the current list of discovered README directories.
        """
        try:
            content = safe_read(self.manifest_file, max_bytes=5 * 1024 * 1024)  # CWE-400
        except (OSError, ValueError) as e:
            print(f"[MANIFEST] Cannot read MANIFEST.md: {e}")
            return

        lines = content.splitlines()
        new_lines = []
        in_auto_section = False
        section_replaced = False

        for line in lines:
            if (
                line.startswith("## Root Directories")
                or "(Auto-Synced)" in line
            ):
                new_lines.append("## Root Directories (Auto-Synced)")
                new_lines.extend(formatted_entries)
                in_auto_section = True
                section_replaced = True
                continue
            if in_auto_section:
                # End of the auto-synced section — resume normal output.
                if line.startswith("---") or (
                    line.startswith("## ") and "(Auto-Synced)" not in line
                ):
                    in_auto_section = False
                    new_lines.append("")
                    new_lines.append(line)
                continue
            new_lines.append(line)

        if not section_replaced:
            new_lines.append("\n## Root Directories (Auto-Synced)")
            new_lines.extend(formatted_entries)

        try:
            atomic_write(  # CWE-362 / CWE-732
                self.manifest_file,
                "\n".join(new_lines) + "\n",
            )
        except (OSError, ValueError) as e:
            print(f"[MANIFEST] Cannot write MANIFEST.md: {e}")

    def _update_api_map(self, api_map_entries: list) -> None:
        """
        Generates or replaces the Global API Map section in
        governance/Architecture.md. Silently skips if the file does not exist.
        """
        arch_file = self.workspace / "governance" / "Architecture.md"
        if not arch_file.exists():
            return

        try:
            content = safe_read(arch_file, max_bytes=5 * 1024 * 1024)  # CWE-400
        except (OSError, ValueError) as e:
            print(f"[MANIFEST] Cannot read Architecture.md: {e}")
            return

        header = "\n## Global API Map (Discovered Interfaces)\n"
        footer = "\n---"
        joined_entries = "\n".join(api_map_entries)

        if header in content:
            parts = content.split(header)
            after = parts[1].split(footer) if footer in parts[1] else ["", ""]
            new_content = (
                f"{parts[0]}{header}\n{joined_entries}{footer}"
                f"{after[1] if len(after) > 1 else ''}"
            )
        else:
            new_content = (
                content.rstrip()
                + f"\n\n{header}\n{joined_entries}{footer}\n"
            )

        try:
            atomic_write(arch_file, new_content)  # CWE-362 / CWE-732
            print("[API MAP] Updated Global API Map in Architecture.md.")
        except (OSError, ValueError) as e:
            print(f"[MANIFEST] Cannot write Architecture.md: {e}")
