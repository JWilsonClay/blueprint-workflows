# blueprint-workflows DevJournal
# opencode to activate Grok

---

## 2026-05-21 — Antigravity → Claude Code Migration: Port Complete, Dual-Runtime Architecture Established

### Today's Progress
- Completed forensic investigation of the post-refactor workspace state using `/investigate` protocol — identified three open items: two missing symlinks, uncommitted git state, and pending legacy cleanup
- Confirmed `personality.md` and `role.md` were ported to `claude-commands/` but never symlinked into `~/.claude/commands/`; created both symlinks (now 31/31 commands live)
- Ported workflow identified as committed (git commit `3f70a85` confirms `claude-commands/` now under version control)
- Executed TODO ITEM 6 destructive cleanup in three steps: deleted 17 legacy payload directories, deleted `core.md` from 2 partial-cleanup dirs (preserving ticket files and audit subdirectory), deleted 25 root pointer files — workspace root now contains only `CLAUDE.md` and structural directories
- Investigated `/home/jwils/.gemini/antigravity-ide/` — confirmed it is the Antigravity IDE-mode data directory (same installation ID as main, 4.5GB, diverged May 20); user deleted it
- Established dual-runtime architecture: 31 Antigravity pointer files written to `/home/jwils/.gemini/antigravity/global_workflows/` pointing to canonical files in `claude-commands/`; both runtimes now share one canonical payload per command
- Modularized the "Senior Architect of Workflows" identity out of `~/.claude/CLAUDE.md` (global, loads in all workspaces) — moved to workspace-scoped files only (`~/blueprint-workflows/CLAUDE.md` + `claude-commands/role.md`)
- Wrote a universal agent identity for `~/.claude/CLAUDE.md`: nature-of-the-tool, world-class quality floor, dissent mandate, workspace-role adapter pattern

### Architecture Updates
- **Pointer/Payload architecture: FULLY RETIRED** — no `*/core.md` files remain in blueprint-workflows. All content lives in `claude-commands/<name>.md` (single merged files)
- **Dual-runtime pointer system established**: Claude Code accesses commands via symlinks (`~/.claude/commands/`); Antigravity accesses via pointer files (`~/.gemini/antigravity/global_workflows/`) — both point to the same canonical payload in `claude-commands/`
- **Identity scoping corrected**: Global `~/.claude/CLAUDE.md` now carries a universal role (applies in all workspaces). Workspace-specific architect identity loads only when blueprint-workflows project is open via `~/blueprint-workflows/CLAUDE.md`
- **Command count**: 31 commands total — all ported, all symlinked, all Antigravity-pointed. `personality.md` and `role.md` included (required in Antigravity since it has no global injection mechanism equivalent to CLAUDE.md)

### Implementation Plan
- Git commit pending (working tree currently clean after `3f70a85`) — WORKFLOW_MANIFEST.md needs update to reflect: 31 commands (not 29), personality/role now symlinked, cleanup complete
- TODO ITEM 7 (CLAUDE.md identity modularization) — RESOLVED this session; mark complete
- TODO ITEM 6 (destructive cleanup) — RESOLVED this session; mark complete
- Open helpdesk ticket `20260515_soc_caller_scan_script.md` — still open, unrelated to this session

### Key Decisions & Learnings
- **One canonical file, two pointer systems**: The architecture decision to keep `claude-commands/<name>.md` as the single source of truth and build pointer layers on top of it (rather than maintaining separate files per runtime) prevents content drift between runtimes permanently
- **`personality` and `role` are not slash commands in Claude Code** — they are reference/behavioral documents. In Antigravity, they require pointers because Antigravity has no global injection equivalent to `~/.claude/CLAUDE.md`; in Claude Code they are accessed via the workspace-scoped CLAUDE.md and `/role` slash command respectively
- **`antigravity-ide` = IDE-mode data directory** — same installation ID as main Antigravity, not a failed upgrade. Contains legitimate session history but was consuming 4.5GB; user chose to delete
- **Universal identity design principle**: A global agent identity should define nature, quality floor, and dissent posture — not workspace-specific role. Workspace roles overlay without replacing the universal frame

### Challenges & Resolutions
- **Missing symlinks for personality/role**: Discovered via `diff` between `claude-commands/` and `~/.claude/commands/`; resolved by creating both symlinks
- **Antigravity pointer format verification**: Used `antigravity-backup/global_workflows/` as the reference for exact pointer format (`view_file` + YAML frontmatter + PAYLOAD MISSING halt instruction) since the live `antigravity/global_workflows/` had been emptied during the port
- **antigravity-ide path ambiguity**: Resolved by user creating a test workflow to confirm which path Antigravity actually reads from

### Next Actions
1. Update `manifest/WORKFLOW_MANIFEST.md` — reflect 31 commands, cleanup complete, both TODO items resolved
2. Close TODO ITEM 6 and ITEM 7 in `TODO/TODO.md` — move to ARCHIVE
3. Close this session with git commit covering WORKFLOW_MANIFEST and TODO updates
4. Monitor `helpdesk-tickets/20260515_soc_caller_scan_script.md` — still open

---

### Documentation Changes Summary
- **Created**: `~/blueprint-workflows/DevJournal.md` (this file — inaugural entry)
- **Modified**: `~/.claude/CLAUDE.md` — Identity section rewritten (universal role, architect identity modularized out)
- **Created**: `~/.gemini/antigravity/global_workflows/*.md` — 31 Antigravity pointer files
- **Deleted**: 17 legacy payload directories, 25 root pointer files, `helpdesk-tickets/core.md`, `implementation-plan/core.md`
- **Created symlinks**: `~/.claude/commands/personality.md`, `~/.claude/commands/role.md`

## 2026-05-23 through 2026-05-25 — Multi-Agent Workstream Orchestration System: Build, Test, Harden

### Today's Progress
- Built `/workstream` workflow from scratch via `/harden-workflow --generator` — Sovereign grade at creation (33K bytes). Four flags: `--claude`, `--gemini`, `--grok`, `--pm`. Scaffold mode, execution mode, structured handoff blocks, PM oversight reports.
- Built `grok_web_architect.log` — Grok Web context trigger on Desktop. Project-agnostic with concept.md halt condition. Two output formats (Architect Directive, Architect Review).
- Enhanced `/implementation-plan` with two new modes: `--workstreams` (PM designs parallel workstreams from concept.md parity analysis) and `--audit --workstreams` (PM audits completed work with adversarial quality scoring).
- Updated `/triage` with 4 new trigger matrix blocks + Phase 0h workstream state collection.
- Created 31 individual pointer files at `~/.opencode/commands/` for Grok OpenCode — replaced bulk-load architecture that caused Context Erosion via Front-Loading.
- Ran the full system through 10 iterations on the RustCRM project, then performed a comprehensive `/investigate` on the results.
- Post-investigation hardening: 7 helpdesk tickets filed and closed, 5 divergences approved and injected, adversarial scoring simplified from custom system to proven Phase 5 methodology, forced context refresh mechanism deployed.

### Architecture Updates
- **New workflow: `/workstream`** — the first multi-platform workflow in the suite. Claude Code invokes as slash command, Grok and Gemini read via filesystem pointers. Platform-agnostic protocol.
- **Triple-runtime pointer architecture**: Claude Code (symlinks at `~/.claude/commands/`), Grok OpenCode (pointer files at `~/.opencode/commands/`), Antigravity Gemini (pointer files at `~/.gemini/antigravity/global_workflows/`). One canonical payload, three delivery mechanisms.
- **Platform Invocation Requirement formalized**: any AI runtime must have per-workflow pointer files before it is authorized for workstream execution. Bulk-load architectures are disqualified (STRICT RULE 24 in /workstream).
- **Forced Context Refresh mechanism**: targeted `grep` commands embedded in implementation plans force agents to re-read critical workflow sections at the point of action, not at session start. Prevents Context Erosion during long execution sessions.
- **Iteration Ledger + 10th-iteration checkpoint**: longitudinal governance system — one row per iteration in project root, summary checkpoint to blueprint-workflows every 10 iterations.
- **Rotation Engine**: autonomous workstream reassignment on iterations mod 8 == 4 (+1 shift) and mod 8 == 0 (+2 shift). Provides implicit cross-agent code review. Tested at iterations 4 and 8.
- **Diff Oracle**: machine-generated ground truth from git diff run BEFORE PM reviews agent self-reports. Cross-references against handoff blocks to detect Hallucinated Success and Ghost Logic. Caught two full workstream failures in Iteration 2.
- **Pre-Flight Manifest**: automated pre-execution checks (git state, build status, guardrail baseline) with BLOCKED halt condition. Correctly blocked Workstream C in Iteration 5 when 38 Rust compile errors were detected.
- **Adversarial scoring simplified**: custom scoring system (calibration → remove calibration → evidence mandates → difficulty weighting) replaced with the proven `/implementation-plan --audit` (Phase 5) methodology applied per-workstream. Value is in cited weaknesses and rationale, not the number.
- **Helpdesk ticket archival**: `/harden-workflow --ticket` mode now archives closed tickets older than 7 days to `helpdesk-tickets/archive/`. 13 tickets archived this session.

### Implementation Plan
- `scripts/workstream/verify.py` — the Verification Substrate script. Proposed but not yet built. Would automate Pre-Flight, Diff Oracle, and dependency scanning. Follows the `doorway.py` pattern.
- `WORKSTREAM_CHECKPOINT_LOG.md` — 10th-iteration checkpoint was a missed obligation. Data exists in the 10 PM reports; needs synthesis.
- `grok_web_architect.log` Section 6 — calibration guide needs updating to reflect Phase 7d simplification (currently references old scoring system).

### Key Decisions & Learnings
- **HITL is the primary architectural constraint, not a limitation**: the entire workflow is designed around the user as message bus. Every output format is paste-ready, self-contained, and requires no interpretation.
- **Context Erosion is the root cause of most agent failures**: across 10 iterations, failures were inconsistent in type but consistent in pattern — agents understood the workflow at session start but lost fidelity during execution. Forced targeted context refresh at the point of action is the structural countermeasure.
- **Adversarial scoring gaming is a real threat**: telling the scoring agent what score range is "expected" causes the agent to produce scores in that range regardless of evidence. Solution: remove all calibration from the agent-facing instructions; put it in the Architect-only review document.
- **Permanent workstream letter assignment prevents HITL confusion**: Claude=A, Gemini=B, Grok=C. Every iteration. Rotation temporarily changes this on a deterministic schedule, but the letters remain stable references.
- **Grok OpenCode performs best with narrow scope**: broad multi-task workstreams cause premature termination; focused single-objective iterations produce consistent PASS results. Possible platform-level token optimization interference.
- **Any agent can run any workstream flag**: `/workstream --gemini` in a Claude terminal works — the flag is a scope filter, not an identity. Agents sign handoff blocks with their real model name for PM visibility.

### Challenges & Resolutions
- **Handoff blocks output to terminal only**: agents couldn't write to files because `.workflow_state/handoffs/` didn't exist and the workflow didn't specify file output. Fixed with mandatory `mkdir -p` + explicit file paths in Phase 4.
- **Adversarial scoring collapsed to compliance checking**: PM scored 90+ on trivial tasks (documentation, .gitignore rules) because "completed cleanly" = high score. Fixed by replacing custom scoring with Phase 5 methodology (ruthless engineer persona, minimum weaknesses with score deductions, comparative scoring).
- **Grok bulk-load caused Context Erosion**: single `workflow-pointer.md` front-loaded all 30+ workflows at session start. By execution time, instructions had drifted from active context. Fixed by creating 31 per-workflow pointer files.
- **DECISIONS.md referenced but never populated**: PM reported escalations that were never formally logged. Fixed with STRICT RULE 19 (escalations must be logged before they can be referenced).

### Next Actions
1. Build `scripts/workstream/verify.py` (Verification Substrate) — automate Pre-Flight, Diff Oracle, dependency scan
2. Write the 10th-iteration `WORKSTREAM_CHECKPOINT_LOG.md` — fulfill governance obligation
3. Update `grok_web_architect.log` Section 6 — align with simplified Phase 5 adversarial methodology
4. Monitor open ticket `20260515_soc_caller_scan_script.md` — LOW urgency, 10 days open
5. Evaluate `/soc` on `scripts/refactor_diff.py` (606 LOC god-file)
6. Address Gemini token depletion — platform unavailability clause in `/workstream` tested and ready

---

### Documentation Changes Summary
- **Created**: `~/blueprint-workflows/claude-commands/workstream.md` — new Sovereign workflow (50K bytes)
- **Created**: `~/Desktop/grok_web_architect.log` — Grok Web Architect Mode context trigger
- **Created**: `~/.opencode/commands/*.md` — 31 per-workflow pointer files for Grok OpenCode
- **Created**: `~/blueprint-workflows/helpdesk-tickets/archive/` — archived 13 closed tickets
- **Modified**: `~/blueprint-workflows/claude-commands/implementation-plan.md` — +workstreams, +audit --workstreams, Rotation Engine, Dependency Scan, Diff Oracle, forced context refresh, Phase 5 adversarial alignment (56K bytes)
- **Modified**: `~/blueprint-workflows/claude-commands/triage.md` — 4 new trigger blocks, Phase 0h
- **Modified**: `~/blueprint-workflows/claude-commands/harden-workflow.md` — TM-5 ticket archival step
- **Modified**: `~/blueprint-workflows/manifest/WORKFLOW_MANIFEST.md` — /workstream entry, count 32
- **Replaced**: `~/.opencode/commands/workflow-pointer.md` — retired bulk-load with per-workflow pointers
