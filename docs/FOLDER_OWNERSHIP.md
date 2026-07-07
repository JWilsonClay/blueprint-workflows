# Folder Ownership

*[RECONCILED 2026-07-05 — /document following /sentinel inaugural scan + /investigate. Replaced generic Doorway self-heal template (core/, logic/, data/, tests/) with blueprint-workflows actual layout.]*

*[NOTE — ADDED 2026-07-06, PR 01-06]* This file is the "ownership file" named in the Doorway Design Invariant (`role.md`, `sentinel.md`, `scripts/doorway/doorway.py`): agent context is delivered by the engine's index plus this file, never by counting per-directory README.md files.

- /: Sovereign Workflow Suite workspace root — library of Markdown agent workflow protocols and governance scripts
- claude-commands/: Canonical source for all Claude Code-ported slash commands; symlinked to ~/.claude/commands/
- scripts/: Workspace-agnostic Python engines callable by any workflow (doorway, focus, suite, receipt, etc.)
- docs/: Architecture documentation; this file is the directory-boundary source of truth
- governance/: Sovereign Substrate architecture manifests and cross-cutting protocol documents
- manifest/: Live-State suite index (SUITE_HEALTH.md) and append-only narrative shards (history/)
- process_learnings/: Append-only PROCESS_LEARNINGS.md — institutional memory of named failure patterns and session lessons
- helpdesk-tickets/: Open workflow failure incident tickets consumed by /harden-workflow --ticket mode
- implementation-plan/: Generated implementation plans and adversarial audit records (audits/)
- TODO/: Active task tracking, divergence notes, and archived completed items
- templates/: Canonical templates consumed by suite scripts (plan/ — tasks.md.template + implementation-plan.md.template for the sentinel populator and audit Completion Marking, Pillar 4)