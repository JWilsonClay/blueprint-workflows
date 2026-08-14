"""
surface — Delivery-Surface Population Tooling
================================================
The write-capable companion to `scripts/secretary/delivery_surfaces.py`
(which is read-only by its package's contract and stays that way). Where
that module answers "does every canonical payload resolve on every active
surface?", this package answers "make it so" for the one surface that is
now per-workspace: Antigravity's `<workspace>/.agents/workflows/` pointer
convention, the sole live Antigravity delivery surface since the
2026-08-13 release (helpdesk-tickets/20260813_secretary_workflow.md,
Antigravity Restoration Cluster, work item 2 / remediation step 5).

One module:

  populate_workspace.py — generate/refresh the pointer set for a target
                          workspace from the canonical claude-commands/
                          payloads, in the byte-established pointer format
                          (frontmatter + view_file + PAYLOAD MISSING halt).
                          Writes ONLY inside <workspace>/.agents/workflows/,
                          guarded by engine_utils.assert_within; all writes
                          are engine_utils.atomic_write. check mode is
                          read-only and reuses the secretary engine's
                          resolver — one resolution implementation, not two.

Existing pointers are left alone by default (sync fills gaps; it does not
churn history); orphans are reported, and --prune removes only orphans
whose own view_file target is DEAD (the limitations.md class) — never a
live-target project-local pointer, which is legitimate.

Second consumer of engine_utils.atomic_write/safe_mkdir/assert_within
(after scripts/plan/ensure_plan_templates.py), per that module's own
promotion note.
"""

__version__ = "1.0.0"
