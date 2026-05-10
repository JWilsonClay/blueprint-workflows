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
"""

from datetime import datetime
from pathlib import Path


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
        """
        log_entry = (
            f"Folder: {folder_path}\n"
            f"Proposed breadcrumb: [PENDING AGENT SUMMARIZATION]\n"
            f"Reason: {reason}\n\n"
        )
        try:
            with open(self.update_log, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except OSError as e:
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
            content = self.update_log.read_text(encoding="utf-8")
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

            # Rewrite log with only the unapplied entries.
            self.update_log.write_text(
                "\n\n".join(remaining_proposals) + "\n" if remaining_proposals else "",
                encoding="utf-8",
            )

        except OSError as e:
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
        # Resolve and validate the target path stays within workspace.
        target = (self.workspace / folder_path_str / "README.md").resolve()
        workspace_resolved = self.workspace.resolve()
        if not str(target).startswith(str(workspace_resolved)):
            print(f"[BREADCRUMB] Path traversal blocked: {target}")
            return False

        # Create a minimal README if it does not exist.
        if not target.exists():
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    f"# {folder_path_str}\n\n## Contents\n"
                    "<!-- BREADCRUMB -->\n[PENDING]\n<!-- BREADCRUMB_END -->\n",
                    encoding="utf-8",
                )
            except OSError as e:
                print(f"[BREADCRUMB] Could not create README: {e}")
                return False

        try:
            content = target.read_text(encoding="utf-8")

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

            target.write_text(content, encoding="utf-8")
            return True

        except OSError as e:
            print(f"[BREADCRUMB] Failed to update README at {target}: {e}")
            return False
