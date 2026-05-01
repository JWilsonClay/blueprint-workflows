# 🏗️ Refactor Script Suite — Sovereign Refactor Protocol

**Location**: `global_workflows/scripts/`  
**Protocol**: Sovereign Refactor Protocol (`/refactor`, `/refactor-p0` through `/refactor-p4`)

---

## Overview

> **LLMs provide intelligence. Scripts provide determinism.**

Every mechanical, filesystem-level operation in a refactor is a hallucination
risk when left to an LLM. These 5 Python scripts eliminate that risk by handling
all enumeration, shim creation, file movement, import scanning, and shim removal
deterministically — while the LLM focuses exclusively on the work that requires
intelligence: architectural decisions and import rewriting.

**The `REFACTOR_MANIFEST.yaml` is the contract between the LLM and the scripts.**
The LLM writes it once (Phase 0). You approve it. Every script reads it and executes
deterministically from that point forward.

---

## Requirements

- Python 3.8 or later
- PyYAML: `pip install pyyaml`
- `git` available in `PATH`
- All scripts must be run from any directory; they accept `--project-root` pointing
  to the project being refactored (not the workflow directory itself).

---

## REFACTOR_MANIFEST.yaml Schema

This YAML file is the single source of truth shared by all 5 scripts.

```yaml
# Top-level fields
project_name: "my-project"           # string — human-readable name
language: "python"                   # string — "python" or "javascript"
verification_gate: "python3 -m pytest tests/ -x"  # string — command that exits 0 if healthy

# One entry per source file
files:
  - current: "src/old/module.py"     # string — current relative path from project root
    target: "src/new/module.py"      # string — target relative path (fill in for MOVE/SPLIT)
    action: "MOVE"                   # enum   — TBD | MOVE | KEEP | SPLIT | ARCHIVE
    notes: "Moving to domain layer"  # string — optional rationale
    surgery_complete: false          # bool   — Phase 3 tracker (managed by refactor_audit.py)
```

### Action Enum Reference

| Action | Meaning | LLM Sets `target:` |
|:---|:---|:---|
| `TBD` | Not yet decided — placeholder from scout | N/A (fill this in) |
| `MOVE` | File moves to a new path | ✅ Yes — set the new path |
| `KEEP` | File stays where it is | ❌ No — leave `target` = `current` |
| `SPLIT` | File is broken into multiple new files | ✅ Yes — one entry per new file |
| `ARCHIVE` | File is deleted after Phase 4 | ❌ No |

---

## The 5 Scripts

---

### 📍 `refactor_scout.py` — Phase 0: Cryogenic Snapshot Scout

**Hallucination prevented**: The LLM forgetting files exist when writing the manifest.

**What it does**:
1. Walks the project directory tree, skipping caches, venvs, node_modules, etc.
2. Generates `IMPORT_GRAPH.txt` — every import statement in the codebase, sorted.
3. Pre-populates `REFACTOR_MANIFEST.yaml` with every file listed, each with `action: TBD`.

**Invocation**:
```bash
python3 /path/to/global_workflows/scripts/refactor_scout.py \
  --project-root /path/to/your/project

# Specify language explicitly (auto-detected by default):
python3 refactor_scout.py --project-root /path/to/project --language python
python3 refactor_scout.py --project-root /path/to/project --language javascript
```

**Outputs**:
- `<project-root>/IMPORT_GRAPH.txt`
- `<project-root>/REFACTOR_MANIFEST.yaml` (all entries: `action: TBD`)

**After running**: LLM fills in `action`, `target`, `notes`, and `verification_gate`
for each entry. User approves. Then run Phase 1.

---

### 🌉 `refactor_bridge.py` — Phase 1: Shim Layer Creation

**Hallucination prevented**: The LLM writing a shim with an incorrect import path,
or silently skipping a file because it ran out of context.

**What it does**:
1. Reads the approved `REFACTOR_MANIFEST.yaml`.
2. Validates all `MOVE`/`SPLIT` entries have distinct target paths set.
3. For each `MOVE` or `SPLIT` entry: creates the target directory, writes the
   language-appropriate shim file with the mandatory `⚠️ SHIM FILE` header.
4. Runs the verification gate after each shim. Stops on first failure.
5. Creates `__init__.py` files for new Python package directories.

**Invocation**:
```bash
# Normal run
python3 refactor_bridge.py --project-root /path/to/project

# Preview without writing files
python3 refactor_bridge.py --project-root /path/to/project --dry-run
```

**After running**: Commit the shim layer. Every new path now resolves. Every old
path still resolves. Proceed to Phase 2.

```bash
git add .
git commit -m "refactor(p1): inject shim layer at all target paths"
```

---

### 🚚 `refactor_migrate.py` — Phase 2: Physical Migration

**Hallucination prevented**: The LLM using `cp` + `rm` instead of `git mv`, or
writing a reverse shim that points to the wrong new path.

**What it does**:
1. Reads `REFACTOR_MANIFEST.yaml`.
2. For each `MOVE` entry (single module or all):
   a. Removes the Phase 1 forward shim at the target path (if present).
   b. Executes `git mv old_path new_path` — never `cp` + `rm`.
   c. Writes a `⚠️ REVERSE SHIM` at the old path pointing to the new location.
   d. Runs the verification gate.
3. With `--all`: processes all `MOVE` entries sequentially, stopping on first failure.

**Invocation**:
```bash
# Migrate one module (recommended: one module per session)
python3 refactor_migrate.py --project-root /path/to/project --module utils

# Migrate all MOVE entries (use with caution — stops on first failure)
python3 refactor_migrate.py --project-root /path/to/project --all

# Preview without moving anything
python3 refactor_migrate.py --project-root /path/to/project --module utils --dry-run
```

**After running** (per module):
```bash
git add .
git commit -m "refactor(p2): git mv src/old/module.py → src/new/module.py"
```

---

### 🔬 `refactor_audit.py` — Phase 3: Reference Surgery Auditor

**Hallucination prevented**: The LLM believing it updated all import references
when it missed 3 files deep in a subdirectory.

**What it does (dual mode)**:

**`--scan` mode**: Greps the entire codebase for any import statement that still
references an OLD path (a path that has been moved). Produces a "Surgery Queue"
report listing every file that needs updating and exactly which import lines require
changing. The LLM uses this report as its session-by-session instructions.

**`--verify` mode**: Re-runs the same scan after the LLM's surgery. Confirms zero
stale imports remain. Runs the verification gate. Must pass before Phase 4 begins.

**Invocation**:
```bash
# Generate the Surgery Queue (before LLM surgery)
python3 refactor_audit.py --project-root /path/to/project --scan

# Verify zero stale imports remain (after LLM surgery)
python3 refactor_audit.py --project-root /path/to/project --verify
```

**Workflow**:
1. `--scan` → produce queue.
2. LLM updates one file's imports.
3. Run verification gate manually.
4. `git commit` the updated file.
5. Repeat steps 2–4 for each file in the queue.
6. `--verify` → confirm complete. Exit code 0 = ready for Phase 4.

---

### 🧹 `refactor_clean.py` — Phase 4: Safe Shim Removal

**Hallucination prevented**: The LLM deleting a shim that is still being imported
by one overlooked file, causing a silent runtime crash.

**What it does**:
1. Finds every file containing a `⚠️ SHIM FILE` or `⚠️ REVERSE SHIM` header.
2. For each shim: scans the codebase to verify nothing still imports from that path.
3. If safe: announces what it will do, then executes `git rm`. Runs the gate.
4. If NOT safe: reports the specific file(s) still referencing the shim. Does NOT remove it.
5. Final pass: confirms zero shim headers remain anywhere in the codebase.

**Invocation**:
```bash
# Remove all removable shims (skips any that still have dependents)
python3 refactor_clean.py --project-root /path/to/project

# Remove a single specific shim
python3 refactor_clean.py --project-root /path/to/project --shim src/old/module.py

# Preview without removing anything
python3 refactor_clean.py --project-root /path/to/project --dry-run
```

**After running**:
```bash
git add .
git commit -m "refactor(p4): remove all shim files"

# Clean up refactor artifacts
git rm IMPORT_GRAPH.txt REFACTOR_MANIFEST.yaml
git commit -m "refactor(p4): remove refactor artifacts"

# Merge to main
git checkout main
git merge --no-ff refactor/<project-name>
git tag refactor/<project-name>-complete
git push origin main --tags
```

---

## Division of Labor

| Phase | Script | Script's Job | LLM's Job |
|:---|:---|:---|:---|
| **P0** | `refactor_scout.py` | Enumerate all files, generate import graph | Design the architecture, fill in manifest decisions |
| **P1** | `refactor_bridge.py` | Create all shim files from manifest | Approve the manifest, trigger the script |
| **P2** | `refactor_migrate.py` | `git mv` + reverse shims | Select module order, trigger `--module` per session |
| **P3** | `refactor_audit.py` | Scan for stale imports, verify after surgery | Rewrite the import statements (requires intelligence) |
| **P4** | `refactor_clean.py` | Verify shim safety, `git rm`, final gate | Approve each removal, merge to main |

---

## Quick-Reference Command Sequence

```bash
# Phase 0 — Scout
python3 scripts/refactor_scout.py --project-root ./my-project
# → LLM fills in REFACTOR_MANIFEST.yaml → User approves

# Phase 1 — Bridge
python3 scripts/refactor_bridge.py --project-root ./my-project
git add . && git commit -m "refactor(p1): inject shim layer"

# Phase 2 — Migrate (one module at a time)
python3 scripts/refactor_migrate.py --project-root ./my-project --module utils
git add . && git commit -m "refactor(p2): git mv utils"
# Repeat for each module

# Phase 3 — Audit & Surgery (iterate until verify passes)
python3 scripts/refactor_audit.py --project-root ./my-project --scan
# → LLM updates one file's imports → git commit
python3 scripts/refactor_audit.py --project-root ./my-project --verify

# Phase 4 — Clean
python3 scripts/refactor_clean.py --project-root ./my-project
git add . && git commit -m "refactor(p4): remove all shims"
git rm IMPORT_GRAPH.txt REFACTOR_MANIFEST.yaml
git commit -m "refactor(p4): remove refactor artifacts"
git checkout main && git merge --no-ff refactor/my-project
git tag refactor/my-project-complete && git push origin main --tags
```

---

## Exit Codes

All scripts follow a consistent exit code convention:

| Code | Meaning |
|:---|:---|
| `0` | Success — all operations completed without error |
| `1` | Failure — at least one operation failed; details printed to stdout |

Scripts **never** silently succeed. Every destructive action (git rm, overwrite) is
announced before execution. `--dry-run` is available on all write/delete scripts.

---

## Language Support

Scripts detect language from `REFACTOR_MANIFEST.yaml → language` field.

| Language | Shim Template | Import Pattern Scan |
|:---|:---|:---|
| `python` | `from <module> import *  # noqa: F401, F403` | `from X`, `import X` |
| `javascript` | `export * from '<path>';` | `from 'X'`, `require('X')` |
