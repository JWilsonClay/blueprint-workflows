# Helpdesk Ticket: Script-Backed Workflows Give No Path-Resolution Anchor for `scripts/...` References

**To**: Senior Architect of Workflows
**From**: Claude Code / Videos workspace session
**Date**: 2026-07-07
**Subject**: `/implementation-plan`'s Phase 5 Completion Marking sub-pass (and, by the same pattern, every other script-backed workflow) references `scripts/...` engines with bare relative paths that are never anchored to the suite root, causing an executing agent working from a project workspace to falsely conclude the script doesn't exist.
**Urgency**: CRITICAL (Architectural)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER — this ticket's remediation is a path-anchoring and CLI-self-sufficiency fix local to `phase_status.py` and 4 prose sites, not a reusable engine or pattern transferred from elsewhere.

---

## 1. Executive Summary
While running `/implementation-plan --audit`'s Phase 5 Completion Marking sub-pass against `/home/jwils/Videos` (a project workspace, not `~/blueprint-workflows/` itself), the agent searched for `scripts/focus/phase_status.py`, found nothing under the project directory, and refused to mark two genuinely-complete phases — a false negative caused entirely by looking in the wrong place. The script exists at `~/blueprint-workflows/scripts/focus/phase_status.py`, but nothing in the workflow text says `scripts/...` paths are suite-root-relative rather than project-relative. A second, compounding defect: even the correct absolute path fails to execute out of the box (`ModuleNotFoundError: No module named 'engine_utils'`) because the script's own import assumes a `sys.path` setup that is documented nowhere. This is very likely systemic post-refactor — the same bare `scripts/...` reference pattern appears across `/focus-plan`, `/continuous-verify`, `/receipt-check`, `/harden-workflow`, and others.

## 2. Root Cause Analysis: "Structural Gap — Missing Path Anchor"
- **The How**: The agent, executing `/implementation-plan`'s Phase 5 Completion Marking sub-pass with cwd `/home/jwils/Videos`, ran `find /home/jwils/Videos -iname "phase_status.py"`, got no result, and recorded a refusal ("`scripts/focus/phase_status.py` not present anywhere in this workspace") in the persisted audit report for two units that were, in fact, mechanically verifiable as complete. Re-running with the correct suite-root path succeeded and produced `status: complete` / `receipt_status: found_complete` for both units.
- **The Why**: `implementation-plan.md` Phase 5 (and the GLOSSARY entry for Completion Marking) instructs the agent to "Run ... `scripts/focus/phase_status.py`'s `build_phase_status_report()`" with no statement of where that path resolves from. The workflow is explicitly designed to be invoked from inside arbitrary project workspaces (per the suite's own stated design — project-agnostic governance layer, Claude Code as the consumer) — so a bare relative path is ambiguous by construction, not just under-specified. Nothing distinguishes "this path is suite-root-relative, always resolve via `~/blueprint-workflows/scripts/...` regardless of cwd" from "this path is workspace-relative, expect it to be scaffolded into the calling project." The workflow silently assumes the former and never says so.
- **Compounding defect**: `phase_status.py` itself does `from engine_utils import safe_read` with no `sys.path` manipulation and no accompanying invocation instructions (no CLI entrypoint, no documented `PYTHONPATH` requirement) — so even an agent that resolves the correct absolute path cannot run the function without independently discovering that `engine_utils.py` lives as a sibling at `~/blueprint-workflows/scripts/engine_utils.py` and must be added to `sys.path` first.

## 3. Forensic Evidence
- **Bare relative reference #1 (GLOSSARY, Completion Marking)**: [implementation-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L63)
  *Evidence: "`scripts/focus/phase_status.py`'s derived `status` AND `receipt_status` must both confirm" — no path anchor stated anywhere in the definition.*
- **Bare relative reference #2 (Phase 5 sub-pass instruction, the exact step executed)**: [implementation-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L212-L213)
  *Evidence: "Run (or reuse, if already run this session) `scripts/focus/phase_status.py`'s `build_phase_status_report()` against that `tasks.md`" — again no anchor; this is the literal instruction the agent followed when it searched the project workspace and concluded the script was absent.*
- **STRICT RULE 27 (governs the refusal the agent correctly took, given the false premise)**: [implementation-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L849)
  *Evidence: mandates refusal when the dual check can't be computed — the agent's behavior was spec-compliant given what it could find; the spec itself is what misled it.*
- **The script's own unresolved import**: [phase_status.py](file:///home/jwils/blueprint-workflows/scripts/focus/phase_status.py#L52)
  *Evidence: `from engine_utils import safe_read`, which raises `ModuleNotFoundError` when the script is run/imported without `~/blueprint-workflows/scripts/` already on `sys.path` — confirmed live: `python3 ~/blueprint-workflows/scripts/focus/phase_status.py --help` fails with exactly this traceback.*
- **`dependencies:` frontmatter names the script but not its resolution rule**: [focus-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/focus-plan.md#L12-L19) and [implementation-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L15-L19)
  *Evidence: both files declare workflow-level `dependencies:` (other workflows), but neither frontmatter block declares anything about where the `scripts/` engines these files repeatedly invoke actually live relative to an arbitrary calling cwd.*
- **Live correction record (this session's own recovery, proving the fix)**: the audit report at `~/blueprint-workflows/implementation-plan/audits/20260707-1852-Videos-Phase8.md`, "Archival Markers Added" section, CORRECTION entries — documents the false refusal, the corrected invocation (`sys.path.insert(0, '~/blueprint-workflows/scripts')` before importing `phase_status`), and the resulting correct dual-confirmation for both units.

## 4. Remediation: Suite-Root Path Anchor + Script Self-Sufficiency
This has not yet been fixed at the workflow-definition level — only worked around, once, in this session (see forensic evidence above: the agent manually inserted the correct `sys.path` entries after discovering the gap by trial and error). Recommended concrete steps for the Senior Architect:
1. Add an explicit, suite-wide convention statement — likely best placed in `role.md` (the canonical architectural-constants document) and then referenced, not restated, from every script-backed workflow: *"All `scripts/...` paths referenced by any workflow in this suite are relative to `~/blueprint-workflows/`, regardless of the calling agent's working directory. Always invoke via the absolute path."*
2. Audit every script-backed workflow for the same bare-relative-path pattern — this ticket found it in `/implementation-plan` (Phase 5, GLOSSARY) and `/focus-plan` (frontmatter `dependencies`/description), but the same phrasing convention ("script-backed by...", "`scripts/X/Y.py`") appears in `/continuous-verify`, `/receipt-check`, `/harden-workflow`, `/redteam`, `/sentinel`, `/helpdesk-tickets` itself (this very file's Phase 0a/2 commands already use the correct absolute `~/blueprint-workflows/scripts/...` form — worth using as the reference pattern the others should match).
3. Fix `phase_status.py` (and check its siblings under `scripts/focus/`, `scripts/build/`, etc. for the same issue) so it doesn't require a caller to independently discover and prepend `sys.path` entries — either add a small `sys.path` bootstrap at the top of each entry-point script relative to its own `__file__`, or provide one documented CLI/import convention all script-backed workflows point to consistently.

## 5. Recommendation to Senior Architect
Establish one documented path-resolution rule for every `scripts/...` reference across the entire Sovereign Suite — stated once (in `role.md` or an equivalent architectural-constants location) and referenced by name from each script-backed workflow, rather than each workflow file re-describing (or, as found here, simply omitting) how its own dependency resolves. This is the same class of gap the suite has already named and fixed once for a related concern (see `helpdesk-tickets/20260707_phase-status-campaign-header-scope_workflow.md`, filed the same day, a *different* root cause in the same module — that ticket's own Section 5 already flagged "worth resolving together" for `phase_status.py`-adjacent issues). Given the user's own assessment that this is likely a broad regression from the recent Sovereign Suite refactor, this ticket's remediation should not stop at `/implementation-plan` and `/focus-plan` — a single pass across all script-backed `claude-commands/*.md` files, checking every `scripts/...` reference for an explicit resolution anchor, is warranted before considering this closed.

---

## 6. Remediation Record — 2026-07-07

**Scope-correcting finding first**: the ticket's own §1/§5 feared this was "very likely systemic post-refactor" across `/focus-plan`, `/continuous-verify`, `/receipt-check`, `/harden-workflow`, and others. A full audit of every `scripts/...` reference across all 21 `claude-commands/*.md` files found this was **not** the case — every actual EXECUTION MODEL invocation command in every one of those files already uses the correct absolute `python3 ~/blueprint-workflows/scripts/...` form. The defect was confined to `phase_status.py` — the one engine module in the suite with no CLI entrypoint of its own, reused only by internal Python import in its sibling engines (`build_audit.py`, `receipt_audit.py`, both of which already bootstrap `sys.path` correctly) — and 4 prose sites that instructed the agent to "run" it directly with no anchor.

**Fixed**:
1. [role.md](file:///home/jwils/blueprint-workflows/claude-commands/role.md#L56) — added the "Script path resolution" row to the Architectural Constants table: the single canonical statement every workflow should reference by name, not restate.
2. [phase_status.py](file:///home/jwils/blueprint-workflows/scripts/focus/phase_status.py#L52-L62) — added a `sys.path` bootstrap (matching `focus.py`/`build_audit.py`) plus a standalone `__main__` CLI (`--workspace`, `--tasks-file`, `--output-json`, `--quiet`), closing the `ModuleNotFoundError` this ticket's §3 reproduced live. Re-verified: `python3 ~/blueprint-workflows/scripts/focus/phase_status.py --help` now succeeds standalone, and `--workspace ~/blueprint-workflows --output-json` produces the correct real report.
3. [implementation-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L63) and [implementation-plan.md](file:///home/jwils/blueprint-workflows/claude-commands/implementation-plan.md#L212-L214) — the two bare references this ticket's §3 cited directly, now anchored to the absolute form.
4. [nodelete.md](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L206) and STRICT RULE 14 — same fix, same pattern.
5. [design-orchestrator.md](file:///home/jwils/blueprint-workflows/claude-commands/design-orchestrator.md#L88) — same fix, lower severity (this file's own EXECUTION MODEL already demonstrated the correct form elsewhere).

**Verified**: full suite run before and after (`./run_tests.sh`) — 463/463 pass, no regressions from the CLI addition. Frontmatter version/content_hash/last_hardened updated on all 4 workflow files via `lint_workflows.py --fix-hashes --write`. Change Log entries appended to `.changelogs/implementation-plan.md` (9), `.changelogs/nodelete.md` (9), `design-orchestrator.md` inline (3), `role.md` inline (8) — per `/nodelete`, appended not overwritten.

**Not addressed by this remediation** (out of scope, correctly): `helpdesk-tickets/20260707_phase-status-campaign-header-scope_workflow.md`, this ticket's own §5 cross-reference — a different root cause in the same module, left for its own ticket.

---
**Status**: **REMEDIATED**
**Verification**: CONFIRMED — 463/463 tests pass; live repro of the original `ModuleNotFoundError` and the bare-path failure both re-run and confirmed fixed.

---
*Signed,*
**Claude Code**
*(Videos workspace session — /implementation-plan Phase 5 Completion Marking sub-pass)*
*(Remediated by: Claude Code, Sovereign Scaling Cluster, blueprint-workflows main session, 2026-07-07)*
