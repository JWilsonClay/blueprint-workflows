# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## What This Repo Is

A library of Markdown-based AI agent workflow protocols ("the Sovereign Suite"). Commands instruct an AI agent how to perform a specific task (build, review, harden, document, triage, etc.). There is no application runtime — the artifacts are the `.md` files themselves.

The suite was originally built for Antigravity (Google Gemini) and ported to Claude Code in May 2026. Migration is ongoing: ported commands live in `claude-commands/`; legacy Antigravity files (Pointer/Payload structure) still exist at the repo root and are being migrated progressively.

## Command Architecture (Claude Code)

Ported commands live in `claude-commands/` as single merged `.md` files. Each is symlinked into `~/.claude/commands/` so they are available as slash commands in every Claude Code session.

```
claude-commands/        ← canonical source; edit here
  quality.md            ← /quality (ported)
  ...                   ← remaining workflows porting in priority order

~/.claude/commands/     ← symlinks only; never edit here directly
  quality.md -> ~/blueprint-workflows/claude-commands/quality.md
```

**To add a new ported command:**
1. Write the merged `.md` file to `claude-commands/<name>.md`
2. Symlink it: `ln -s ~/blueprint-workflows/claude-commands/<name>.md ~/.claude/commands/<name>.md`
3. Verify: `ls -la ~/.claude/commands/`

## Scripts: Running Tests and Doorway

The only executable code lives in `scripts/`.

```bash
# Run the full refactor script test suite (from scripts/)
cd ~/blueprint-workflows/scripts && ./run_tests.sh

# Run a single test file
cd ~/blueprint-workflows/scripts && python -m pytest tests/test_manifest.py -v

# Run doorway drift detection against a target workspace
python ~/blueprint-workflows/scripts/doorway/doorway.py \
  --workspace /absolute/path/to/workspace

# Doorway flags: --full-scan, --auto-apply, --output-json, --quiet
```

## Standard Development Pipeline

```
/triage → /focus-plan → /execute-build (with /continuous-verify at each phase)
       → /iterate-test → /harden → /document
```

- `/triage` is the intake desk: reads observable workspace state (git, receipts, tasks.md, journal timestamps) and recommends which workflows to run. Always start here.
- `/focus-plan` is the blocking pre-gate before `/execute-build`: verifies Intent/Plan/Substrate triad alignment using the Anchor Manifest + SEARCH EVIDENCE pattern.
- `/execute-build` drives `tasks.md` phase-by-phase with a 7-step audit loop including a continuous-verify sub-gate (Step 5g) before issuing a Phase Build Receipt.
- `/sentinel` powers session initialization via `scripts/doorway/doorway.py`.

## Cross-Cutting Rules All Workflows Follow

**`/nodelete`** — The universal preservation rule: never overwrite, only append/inject. When correcting content, inject a clearly-marked reconciliation note and keep the original.

**Receipt Infrastructure** — All receipts land in `.workflow_state/receipts/` via `cat >>` (atomic append). Three files: `BUILD_RECEIPTS.md` (from `/execute-build`), `DOCS_RECEIPTS.md` (from `/document`), `HARDEN_GRADES.md` (from `/harden`). Absence of this directory is itself a `/triage` signal.

**Hardening Grades** — Scripts are graded Diamond > Gold > Silver > Bronze after `/harden` runs. Diamond = all 19 checklist items PASS with zero CRITICAL/HIGH/MEDIUM findings.

**Named Failure Patterns** — When detected, name them explicitly and file a helpdesk ticket. Full vocabulary in `~/.claude/CLAUDE.md`.

## Porting a Legacy Workflow to Claude Code

Legacy workflows use Pointer/Payload architecture (a `<name>.md` pointer at root + `<name>/core.md` payload). This was built for Antigravity's ~12,000 byte injection cap, which Claude Code does not have. The migration collapses each pair into a single file.

**Port steps:**
1. Take the payload (`<name>/core.md`) as the canonical content source
2. Apply frontmatter from the pointer (keep `description:`)
3. Adapt for Claude Code:
   - Remove any `view_file <path>` instructions — not a Claude Code tool
   - Update cross-workflow embeds: replace `view_file .../core.md` with `Read ~/.claude/commands/<name>.md and execute its HOW TO BEGIN protocol`
   - Update HOW TO BEGIN if it references Antigravity upload model
   - Update INTEGRATION activation pattern to Claude Code slash command model
4. Write merged file to `claude-commands/<name>.md`
5. Delete old pointer (`<name>.md`) and payload directory (`<name>/`)
6. Symlink into `~/.claude/commands/`
7. Append Change Log entry documenting the port
8. Port sub-workflows before parents (dependency order: `/continuous-verify` before `/execute-build`)

## Key Structural Files

| File/Dir | Role |
|----------|------|
| `claude-commands/` | Canonical location for all Claude Code-ported commands |
| `triage/core.md` | Trigger Matrix mapping workspace state → workflow recommendations *(pending port)* |
| `focus-plan/core.md` | Triad alignment loop with SEARCH EVIDENCE enforcement *(pending port)* |
| `execute-build/core.md` | Phase-by-phase build agent with 7-step audit *(pending port)* |
| `harden/core.md` | Security hardening with 19-item checklist and grading *(pending port)* |
| `harden-workflow/core.md` | Meta-hardening for workflow `.md` files themselves *(pending port)* |
| `document.md` | DevJournal append-only updater *(pending port)* |
| `secretary/core.md` | Session-close orchestrator *(pending port)* |
| `depreciate/core.md` | Contradiction quarantine protocol *(pending port)* |
| `divergence/core.md` | Six-vector lateral thinking engine *(pending port)* |
| `nodelete.md` | The core preservation doctrine *(pending port)* |
| `scripts/doorway/` | Python workspace drift detector powering `/sentinel` |
| `manifest/` | Suite-wide append-only ledgers (WORKFLOW_MANIFEST.md, FOCUS-MEMORY-LEDGER.md, CONTRADICTION_REGISTRY.md) |

## Scripts Directory Structure

```
scripts/
  doorway/          # Workspace drift detection (doorway.py, scanner.py, auditor.py, etc.)
  core/             # Shared library for refactor scripts
  workflows/        # Workflow runner scripts
  tests/            # pytest test suite for the refactor scripts
  run_tests.sh      # Test runner (uses coverage if installed)
  refactor_*.py     # Modular refactoring pipeline scripts
```

All scripts in `scripts/` accept `--workspace /absolute/path` as the primary input. Never hardcode workspace paths.
