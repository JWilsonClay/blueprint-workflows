# Project Architecture

## System Overview
This project follows the **Sovereign Substrate** pattern.

## Directory Structure
*Source of Truth: FOLDER_OWNERSHIP.md*

- `TODO/`: Active task tracking, divergence notes, and archived completed items
- `claude-commands/`: Canonical source for all Claude Code-ported slash commands; symlinked to ~/.claude/commands/
- `helpdesk-tickets/`: Open workflow failure incident tickets consumed by /harden-workflow --ticket mode
- `implementation-plan/`: Generated implementation plans and adversarial audit records (audits/)
- `manifest/`: Live-State suite index (SUITE_HEALTH.md) and append-only narrative shards (history/)
- `process_learnings/`: Append-only PROCESS_LEARNINGS.md — institutional memory of named failure patterns and session lessons
- `scripts/`: Workspace-agnostic Python engines callable by any workflow (doorway, focus, suite, receipt, etc.)

---

## Communication Patterns
- **Direct Imports**: Cross-substrate communication is achieved via explicit, direct imports.
- **Path Isolation**: All file I/O must use absolute paths anchored in the workspace root.

## Hardening Standards
- **Atomic Persistence**: Database writes and configuration updates are performed surgically to prevent state corruption.
- **Refactor Protocol**: All structural changes must follow the 5-phase Refactor Protocol (Bridge, Migrate, Surgery, Verify, Clean).

## Global API Map (Discovered Interfaces)
<!-- Discovered interfaces will be automatically synced below -->

---