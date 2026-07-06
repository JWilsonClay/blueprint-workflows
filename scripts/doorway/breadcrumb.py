"""
breadcrumb.py — Breadcrumb Manager
=====================================
Handles breadcrumb orchestration for the Doorway Protocol.
Responsible for logging proposals and auto-applying approved summaries
into README.md files via surgical tag replacement.

README tag channels supported:
  <!-- BREADCRUMB -->...<!-- BREADCRUMB_END -->   The "What" — directory summary
  <!-- INTERFACE -->...<!-- INTERFACE_END -->      The "How to talk to me" — public contract
  <!-- REQUESTS -->...<!-- REQUESTS_END -->        The "What I need from others"
  <!-- WORKLOG -->...<!-- WORKLOG_END -->          The "What I did" — append-only journal

Refactored from .blueprints/governance/thedoorway/breadcrumb_manager.py:
  - Removed module-level PROJECT_ROOT constant.
  - 'project_root' constructor argument renamed to 'workspace' throughout.
  - All internal path references use self.workspace.
  - Added explicit file encoding ('utf-8') on all read/write operations.
  - Added Path validation before write operations.

[SECURITY — 2026-05-10 — /harden pass, /nodelete]
  - All write_text() calls replaced with atomic_write() (CWE-362 / CWE-732).
  - open(append) replaced with atomic_write of full log content.
  - read_text() replaced with safe_read() with 5 MB cap (CWE-400).
  - str-based path guard replaced with assert_within() (CWE-22).
"""

from datetime import datetime
from pathlib import Path

from doorway._utils import atomic_write, assert_within, safe_read


class BreadcrumbManager:
    """
    Handles breadcrumb orchestration for the Doorway Protocol.

    Args:
        workspace:        Absolute path to the target workspace root.
        update_log_file:  Absolute path to the pending-proposals log file.
    """

    def __init__(self, workspace: Path, update_log_file: Path):
        self.workspace = workspace
        self.update_log = update_log_file

    # ------------------------------------------------------------------
    # Proposal logging
    # ------------------------------------------------------------------

    def propose(self, folder_path: str, reason: str) -> None:
        """
        Logs a breadcrumb update request to the context log.
        The entry is marked [PENDING AGENT SUMMARIZATION] until an agent
        rewrites it with real content and calls apply_approved().

        Structural inventory (file names, counts, subdirectories) is enumerated
        here and written into the log entry so the LLM agent reading the log
        during /sentinel Phase 1.5 has the raw facts it needs to compose the
        compact agentic summary without requiring an additional filesystem scan.

        [HARDENED 2026-05-15 — Bug #2 fix: structural inventory for agent context,
        /harden-workflow --ticket 20260514_sentinel_workflow.md + /nodelete]
        """
        _IGNORE_NAMES = {
            ".git", ".venv", "__pycache__", "node_modules", "build",
            "dist", ".pytest_cache", ".doorway", ".ipynb_checkpoints",
        }

        files: list[str] = []
        subdirs: list[str] = []
        dir_path = self.workspace / folder_path
        try:
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith(".") or item.name in _IGNORE_NAMES:
                    continue
                if item.is_file():
                    files.append(item.name)
                elif item.is_dir():
                    subdirs.append(item.name + "/")
        except OSError:
            pass  # Directory unreadable — agent will get empty inventory.

        file_count = len(files)
        _MAX_SAMPLE = 20
        if file_count > _MAX_SAMPLE:
            file_sample = ", ".join(files[:_MAX_SAMPLE]) + f" ... +{file_count - _MAX_SAMPLE} more"
        else:
            file_sample = ", ".join(files) if files else "none"
        subdir_list = ", ".join(subdirs) if subdirs else "none"

        log_entry = (
            f"--- PROPOSAL\n"
            f"Folder: {folder_path}\n"
            f"Proposed breadcrumb: [PENDING AGENT SUMMARIZATION]\n"
            f"Reason: {reason}\n"
            f"Files ({file_count}): {file_sample}\n"
            f"Subdirs: {subdir_list}\n\n"
        )
        # Atomic append: read existing log, append, atomic_write full content.
        # Avoids the non-atomic open("a") pattern (CWE-362).
        try:
            existing = ""
            if self.update_log.exists():
                existing = safe_read(self.update_log)
            atomic_write(self.update_log, existing + log_entry)
        except (OSError, ValueError) as e:
            print(f"[BREADCRUMB] Failed to write proposal: {e}")

    # ------------------------------------------------------------------
    # Approved proposal application
    # ------------------------------------------------------------------

    def apply_approved(self) -> None:
        """
        Processes the update log and applies any non-placeholder breadcrumbs
        to their target README files. Entries that have been applied are
        removed from the log; pending entries remain.
        """
        if not self.update_log.exists():
            return

        try:
            content = safe_read(self.update_log)  # CWE-400: bounded read
            if not content.strip():
                return

            proposals = content.split("--- PROPOSAL")
            remaining_proposals = []

            if not proposals[0].strip():
                proposals = proposals[1:]

            for prop in proposals:
                prop_str = (
                    "--- PROPOSAL" + prop
                    if not prop.startswith("Folder:")
                    else prop
                )
                lines = prop_str.strip().splitlines()

                folder = None
                breadcrumb = None

                for line in lines:
                    if line.startswith("Folder:"):
                        folder = line.replace("Folder:", "").strip()
                    if line.startswith("Proposed breadcrumb:"):
                        val = line.replace("Proposed breadcrumb:", "").strip()
                        if val and val != "[PENDING AGENT SUMMARIZATION]":
                            breadcrumb = val

                if folder and breadcrumb:
                    if self.update_readme(folder, breadcrumb):
                        print(f"[AUTO-APPLY] Updated {folder}")
                    else:
                        remaining_proposals.append(prop_str)
                else:
                    remaining_proposals.append(prop_str)

            # Atomic rewrite log with only unapplied entries (CWE-362).
            atomic_write(
                self.update_log,
                "\n\n".join(remaining_proposals) + "\n" if remaining_proposals else "",
            )

        except (OSError, ValueError) as e:
            print(f"[BREADCRUMB] Auto-apply failed: {e}")

    # ------------------------------------------------------------------
    # README tag surgery
    # ------------------------------------------------------------------

    def update_readme(
        self,
        folder_path_str: str,
        breadcrumb: str,
        interface: str = None,
        requests: str = None,
        worklog: str = None,
    ) -> bool:
        """
        Surgically updates the BREADCRUMB, INTERFACE, REQUESTS, and WORKLOG
        tag sections in a README.md. Creates a minimal README if absent.

        The WORKLOG channel is append-only with timestamps; all others replace
        the current content between their tags.

        Returns:
            True if the README was successfully written; False on error.
        """
        # Resolve and validate the target path stays within workspace (CWE-22).
        target = (self.workspace / folder_path_str / "README.md").resolve()
        try:
            assert_within(target, self.workspace)
        except ValueError as e:
            print(f"[BREADCRUMB] {e}")
            return False

        # Create a minimal README if it does not exist (atomic write, CWE-362).
        if not target.exists():
            try:
                atomic_write(
                    target,
                    f"# {folder_path_str}\n\n## Contents\n"
                    "<!-- BREADCRUMB -->\n[PENDING]\n<!-- BREADCRUMB_END -->\n",
                )
            except OSError as e:
                print(f"[BREADCRUMB] Could not create README: {e}")
                return False

        try:
            content = safe_read(target, max_bytes=2 * 1024 * 1024)  # 2 MB README cap (CWE-400)

            def replace_tag(text: str, start_tag: str, end_tag: str, new_val: str) -> str:
                """Replace content between start_tag and end_tag, or append if absent."""
                if start_tag in text and end_tag in text:
                    before = text.split(start_tag)[0]
                    after = text.split(end_tag, 1)[1]
                    return f"{before}{start_tag}\n{new_val}\n{end_tag}{after}"
                return text + f"\n\n{start_tag}\n{new_val}\n{end_tag}\n"

            # 1. Breadcrumb — replaces existing summary.
            content = replace_tag(
                content, "<!-- BREADCRUMB -->", "<!-- BREADCRUMB_END -->", breadcrumb
            )

            # 2. Interface — public module contract (optional).
            if interface:
                content = replace_tag(
                    content, "<!-- INTERFACE -->", "<!-- INTERFACE_END -->", interface
                )

            # 3. Requests — cross-substrate change requests (optional).
            if requests:
                content = replace_tag(
                    content, "<!-- REQUESTS -->", "<!-- REQUESTS_END -->", requests
                )

            # 4. Worklog — append-only timestamped journal (optional).
            if worklog:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_entry = f"### {ts}\n{worklog}\n"
                if "<!-- WORKLOG -->" in content and "<!-- WORKLOG_END -->" in content:
                    parts = content.split("<!-- WORKLOG_END -->")
                    content = f"{parts[0]}{new_entry}<!-- WORKLOG_END -->{parts[1]}"
                else:
                    content += f"\n\n<!-- WORKLOG -->\n{new_entry}\n<!-- WORKLOG_END -->\n"

            atomic_write(target, content)  # CWE-362: atomic README update
            return True

        except (OSError, ValueError) as e:
            print(f"[BREADCRUMB] Failed to update README at {target}: {e}")
            return False
