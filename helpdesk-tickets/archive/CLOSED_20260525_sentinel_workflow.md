# Helpdesk Ticket: Missing Automated Folder Ownership Bootstrap Workflow

**To**: Senior Architect of Workflows
**From**: Antigravity / Sentinel Session
**Date**: 2026-05-25
**Subject**: Missing automated bootstrap workflow and self-healing logic for the FOLDER_OWNERSHIP.md manifest.
**Urgency**: MEDIUM

---

## 1. Executive Summary
During workspace initialization scans, `/sentinel` flags all project subdirectories as unowned because the `docs/FOLDER_OWNERSHIP.md` file is missing. Although `doorway.py` carries a template for this file (`FOLDER_OWNERSHIP.md.template`), the system lacks any automated workflow or self-healing routine to copy or initialize it. This leads to a persistent hygiene finding that cannot be resolved without manual intervention.

## 2. Root Cause Analysis: "Structural Gap"
- **The How**: The agent running `/sentinel` detects unowned directories because `docs/FOLDER_OWNERSHIP.md` is absent. Since Sentinel is read-only and `/document` is strictly append-only, neither workflow is authorized or equipped to automatically create or populate this governance file.
- **The Why**: The `doorway.py` script's initialization sequence (`ensure_substrate`) does not list `FOLDER_OWNERSHIP.md` in its `critical_files` dictionary. Furthermore, no independent setup or bootstrap workflow is defined to handle initial governance document generation when entering a new workspace substrate.

## 3. Forensic Evidence
- **Orchestrator Setup Code**: [doorway.py:L169-175](file:///home/jwils/blueprint-workflows/scripts/doorway/doorway.py#L169-175)
  *Evidence: The bootstrapper in `doorway.py` registers `Architecture.md` and `MANIFEST.md` under `critical_files` for self-healing, but ignores the folder ownership manifest.*
- **Ownership Manifest Template**: [FOLDER_OWNERSHIP.md.template:L1-11](file:///home/jwils/blueprint-workflows/scripts/doorway/templates/FOLDER_OWNERSHIP.md.template#L1-11)
  *Evidence: A valid fallback template exists in the `doorway/templates` directory but is never deployed by any workflow.*
- **Sentinel Routing Definition**: [sentinel.md:L237-238](file:///home/jwils/blueprint-workflows/claude-commands/sentinel.md#L237-238)
  *Evidence: Sentinel maps `SEQ-SUBSTRATE-HYGIENE` (unowned directories) to the `/document` workflow, which is documentation-only and cannot write project files.*

## 4. Remediation: Automated Governance Bootstrap Logic
1. Update `doorway.py`'s `ensure_substrate` call to include `FOLDER_OWNERSHIP.md` in `critical_files` mapping to `FOLDER_OWNERSHIP.md.template`.
2. Ensure `docs/FOLDER_OWNERSHIP.md` is generated during Phase 0 of the scan process, automatically listing all active top-level directories so the user or agent only has to assign owners.
3. Update `IntegrityManager` to support folder-list token expansion within the ownership manifest template to auto-populate the folder rows.

## 5. Recommendation to Senior Architect
We recommend expanding the `ensure_substrate` mechanism in `doorway.py` to treat all core files defined in templates as self-healing targets. Alternatively, introduce a dedicated setup/bootstrap phase inside the Sentinel protocol to initialize missing governance manifests (like `FOLDER_OWNERSHIP.md`) before executing the diagnostic scan.

---
**Status**: **REMEDIATED**
**Verification**: PASSED — `FOLDER_OWNERSHIP.md` added to `doorway.py` critical_files (line 174). Template `FOLDER_OWNERSHIP.md.template` already exists. Self-healing now triggers on first scan when the file is missing.

**Resolution (2026-05-25):** One-line fix in `doorway.py`: added `self.ownership_file` → `FOLDER_OWNERSHIP.md.template` to the `critical_files` dictionary in the `ensure_substrate` call. The Doorway Protocol's existing self-healing mechanism now handles this file identically to `Architecture.md` and `MANIFEST.md`. No new bootstrap workflow needed — the existing infrastructure was sufficient; it just wasn't configured for this file.

---
*Signed,*
**Claude Code (Senior Architect)**
*(Remediated 2026-05-25)*
