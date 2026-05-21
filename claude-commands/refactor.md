---
description: Sovereign Refactor Protocol — Five-phase migration with shim layer, deterministic scripts, and diff review nodes
---

# 🏗️ /refactor — Sovereign Refactor Protocol: Master Index

> **INVOKE THIS FILE**: Only at the START of a new refactor project (Phase 0),
> or to onboard a new agent to a refactor already in progress.
> For active phase work, invoke the specific phase file instead:
> `/refactor-p0` through `/refactor-p4`.

---

## 🧠 The Core Principle (The Law)

A refactor is not a demolition. It is a **migration**.
The codebase must be in a **fully runnable state at every single commit**.
No import may ever break. No file may ever be deleted before its references
are fully migrated. No session may end without a passing verification gate.

---

## 🗺️ The Five Phases

| Invoke | Phase | Script (Deterministic Path) | Output |
| :--- | :--- | :--- | :--- |
| `/refactor-p0` | **0: Snapshot** | `refactor_scout.py` | `REFACTOR_MANIFEST.yaml` |
| `/refactor-p1` | **1: Bridge** | `refactor_bridge.py` | Shim Layer |
| `/refactor-p2` | **2: Migrate** | `refactor_migrate.py` | `git mv` + Reverse Shims |
| `/refactor-p3` | **3: Surgery** | `refactor_audit.py` | Direct Imports |
| `/refactor-p4` | **4: Clean** | `refactor_clean.py` | Clean Main Branch |

---

## 🛡️ Universal Agent Constraints (Apply to ALL Phases)

- Apply `@[/nodelete]` at all times. Shims are the alternative to deletion.
- Apply `@[/quality]`. Every verification gate must pass before committing.
- **Mandatory Determinism**: Use scripts for all mechanical operations. Manual overrides are forbidden unless scripted automation fails and is reviewed.
- **Mandatory Gates**: Run `refactor_diff.py --phase pN` before every commit.
- **Environment Context**: Always set `export PYTHONPATH=~/blueprint-workflows/scripts`.
- The agent may ONLY act within the bounds of the approved `REFACTOR_MANIFEST.yaml`.
- If a file is NOT in the Manifest, **STOP** and ask the user before touching it.
- If a verification gate **FAILS**, **STOP**. Do not attempt to fix forward.
  Diagnose, report to user, await guidance.

---

## 🚫 Anti-Patterns (Forbidden in All Phases)

| Anti-Pattern | Why It Causes Regressions | Correct Alternative |
| :--- | :--- | :--- |
| `rm` + recreate a file | Breaks git history, silent import failures | `git mv` + shim |
| Move 10+ files in one session | One failure cascades across all | One module per session |
| Modify imports before moving files | Old path gone before new path exists | Shims first, surgery second |
| Skip the verification gate | Breakage compounds silently | Gate is mandatory |
| Work without a Manifest | Agent drifts from intent | Manifest is law |
| Delete a shim early | Breaks any file not yet surgically updated | Shims live until Phase 4 |

---

## 🔍 The Diff Review Node (The Gatekeeper)

Every phase transition includes a mandatory **diff review** step that compares actual filesystem state against the manifest's declared intent. This prevents silent drift between intent and reality.

**Invoke**: `/refactor-diff`

| Phase Boundary | Diff Command | Blocks Commit if… |
| :--- | :--- | :--- |
| **Phase 0** | `refactor_diff.py --spec-summary` | Manifest intent is not approved by user |
| **After P1** | `refactor_diff.py --phase p1` | Shim missing or incorrect source path |
| **After P2** | `refactor_diff.py --phase p2` | Target is still a shim, reverse shim missing |
| **During P3** | `refactor_diff.py --phase p3` | Surgery inconsistency found |
| **After P4** | `refactor_diff.py --phase p4` | Shims remain, targets missing |
| **Pre-merge** | `refactor_diff.py --phase p4 --pre-merge` | Artifacts remain, unexpected source files |

**Loop-back rule**:
- 🔴 **CRITICAL** — fix it, re-run diff, confirm clean before committing.
- 🟡 **WARNING** — review and proceed at your discretion.
- 🔵 **INFO** — informational only.

---

## 📎 References
- Martin Fowler: Strangler Fig Application Pattern
- Google Large-Scale Change (LSC) Methodology
- Python `six` library: backward-compatible migration shim pattern

# 🏗️ /refactor-p0 — Phase 0: Cryogenic Snapshot

> **PHASE CONTEXT**: This is the first phase of the Sovereign Refactor Protocol.
> No previous phases have run. The codebase is in its original (pre-refactor) state.
> For the full protocol law, see `/refactor`.

---

## 🎯 Your Objective This Session

Produce three things and nothing else:
1. A clean `refactor/<project-name>` git branch.
2. A complete **Import Graph** document.
3. An approved **`REFACTOR_MANIFEST.md`** at the project root.

Do NOT move any files. Do NOT create any shims. Do NOT modify any code.
This phase is **read-only plus documentation only**.

---

## Step 1: Verify Clean Working Tree

```bash
git status
```

If there are any uncommitted changes, **STOP**. Report to the user.
Do not proceed until the working tree is clean.

---

## Step 2: Create the Refactor Branch

```bash
git checkout -b refactor/<project-name>
git push -u origin refactor/<project-name>
```

---

## Step 3: Generate the Import Graph

Run a dependency scan to map every file's imports. Save the output.
This is the "Dependency Constitution" — the ground truth for what will
break if any file moves without a shim.

```bash
# Python projects:
grep -rn "^from \|^import " --include="*.py" . \
  | grep -v "__pycache__" \
  | sort > IMPORT_GRAPH.txt

# JavaScript/TypeScript projects:
grep -rn "^import \|require(" --include="*.ts" --include="*.js" . \
  | grep -v "node_modules" \
  | sort > IMPORT_GRAPH.txt
```

Commit the import graph:
```bash
git add IMPORT_GRAPH.txt
git commit -m "refactor(p0): add import dependency graph"
```

---

## Step 4: Write the REFACTOR_MANIFEST.md

Create `REFACTOR_MANIFEST.md` at the project root using the template below.
Fill in every file in the project. Do not omit any file, even if its action
is `KEEP` (no change).

```markdown
# REFACTOR MANIFEST: <Project Name>
# Generated: <Date>
# Status: AWAITING USER APPROVAL

## Target Architecture Summary
<Brief description of the new structure and why>

## Current → Target File Map
| # | Current Path | Target Path | Action | Notes |
|---|---|---|---|---|
| 1 | old/path/file.py | new/path/file.py | MOVE | |
| 2 | old/god_file.py | new/mod_a.py | SPLIT | Split into mod_a + mod_b |
| 3 | old/god_file.py | new/mod_b.py | SPLIT | See row 2 |
| 4 | old/unused.py | old/unused.py | ARCHIVE | Delete after Phase 4 |
| 5 | keep/this.py | keep/this.py | KEEP | No change needed |

## New Directories to Create
- new/path/
- another/new/path/

## Files to Archive (Delete in Phase 4)
- old/unused.py

## Verification Gate Command
<The exact command to run to verify the project is working, e.g.:>
python3 -m pytest tests/smoke/ -x
```

---

## Step 5: Await User Approval

**STOP HERE.** Present the `REFACTOR_MANIFEST.md` to the user for review.
Do not proceed to Phase 1 until the user explicitly approves the manifest.

> [!IMPORTANT]
> The Manifest is the law of the entire refactor. Once approved, the agent
> may ONLY act within its bounds. If you discover a file not in the manifest
> during a later phase, STOP and ask before touching it.

---

---

## **[INJECTION — Script Integration — 2026-05-01]**

> **This step replaces the manual portions of Steps 3 and 4 above.**
> The script performs the grep import scan and manifest pre-population
> deterministically. The LLM's job is to fill in the architecture decisions
> after the script has enumerated the ground truth.

### Automated Scout: `refactor_scout.py`

```bash
# From any directory — point --project-root at the project being refactored:
python3 /path/to/global_workflows/scripts/refactor_scout.py \
  --project-root /path/to/your/project

# Explicit language flag (auto-detected by default):
python3 refactor_scout.py --project-root /path/to/project --language python
python3 refactor_scout.py --project-root /path/to/project --language javascript
```

**What the script produces**:
- `IMPORT_GRAPH.txt` — every import statement in the codebase, sorted. (Replaces the manual grep in Step 3.)
- `REFACTOR_MANIFEST.yaml` — every source file pre-listed with `action: TBD`. (Replaces the manual template in Step 4.)

**After the script runs**:
1. LLM opens `REFACTOR_MANIFEST.yaml` and fills in `action`, `target`, `notes` for each entry.
2. LLM sets `verification_gate` to the exact shell command that verifies the project is healthy.
3. Present the completed manifest to the user for approval.
4. **Do not proceed to Phase 1 until the user explicitly approves.**

> [!NOTE]
> `REFACTOR_MANIFEST.yaml` uses a structured YAML schema understood by all 5 phase scripts.
> See `~/blueprint-workflows/scripts/README.md` for the full schema reference.

---

## Phase 0 Completion Checklist

- [ ] `git status` confirmed clean before branching.
- [ ] `refactor/<project-name>` branch created and pushed.
- [ ] `IMPORT_GRAPH.txt` generated and committed.
- [ ] `REFACTOR_MANIFEST.md` written with every file accounted for.
- [ ] User has reviewed and explicitly approved the Manifest.

> Commit: `refactor(p0): cryogenic snapshot complete — manifest approved`

**Next Phase**: Invoke `/refactor-p1`

# 🏗️ /refactor-p1 — Phase 1: Shim Layer Creation

> **PHASE CONTEXT**: Phase 0 is complete. The following artifacts exist:
> - A `refactor/<project-name>` git branch (currently checked out).
> - An `IMPORT_GRAPH.txt` at the project root.
> - An approved `REFACTOR_MANIFEST.md` at the project root.
> No files have been moved yet. The codebase is in its original structure.
> For the full protocol law, see `/refactor`.

---

## 🎯 Your Objective This Session

Create **compatibility shim files** at every TARGET location listed in the
`REFACTOR_MANIFEST.md` for files marked `MOVE` or `SPLIT`.

A shim is a thin file that re-exports everything from the current (old)
location. It makes the new path "exist" in the filesystem before the actual
file arrives, so any code that imports from the new path will already work.

Do NOT move any files yet. Do NOT modify any existing imports.
This phase creates new files only.

---

## Step 1: Read the Manifest

Open `REFACTOR_MANIFEST.md`. Identify every row with action `MOVE` or `SPLIT`.
These are the files that need shims at their TARGET paths.

Files marked `KEEP` or `ARCHIVE` do NOT need shims.

---

## Step 2: Create New Directory Structure

Create all new directories listed in the Manifest's "New Directories to Create"
section. Create a `.gitkeep` or `__init__.py` in each to make them trackable.

```bash
mkdir -p new/path/to/module/
touch new/path/to/module/__init__.py
```

---

## Step 3: Write a Shim at Each Target Path

For each `MOVE` row, create a shim file at the TARGET path:

### Python Shim Template
```python
# ⚠️ SHIM FILE — Phase 1 of Sovereign Refactor Protocol
# This file is a temporary compatibility bridge. DO NOT REMOVE until Phase 4.
# Logic currently lives at: <current/path/file.py>
# This shim will be replaced by the real file in Phase 2 (git mv).
from <current.path.file> import *  # noqa: F401, F403
```

### JavaScript / TypeScript Shim Template
```typescript
// ⚠️ SHIM FILE — Phase 1 of Sovereign Refactor Protocol
// DO NOT REMOVE until Phase 4.
// Logic currently lives at: <current/path/file.ts>
export * from '<current/path/file>';
```

### For `SPLIT` rows:
Create a shim at each target path that imports ONLY the relevant
symbols from the current god-file. Coordinate with the user on
which symbols belong in which new module.

---

## Step 4: Verification Gate

Run the project's verification command from `REFACTOR_MANIFEST.md`.

```bash
<verification gate command>
```

**The project must pass with exit code 0.**
If it fails, diagnose and fix before committing. Do not proceed with failures.

---

## Step 5: Commit the Shim Layer

```bash
git add .
git commit -m "refactor(p1): inject shim layer at all target paths"
```

---

---

## **[INJECTION — Script Integration — 2026-05-01]**

> **This step automates Steps 2 and 3 above entirely.**
> Shim creation is 100% mechanical — every shim is identical in structure,
> with only the import path varying. The script cannot hallucinate an incorrect path.

### Automated Bridge: `refactor_bridge.py`

```bash
# Normal run — creates all shims from the approved manifest:
python3 /path/to/global_workflows/scripts/refactor_bridge.py \
  --project-root /path/to/your/project

# Preview without writing any files:
python3 refactor_bridge.py --project-root /path/to/project --dry-run
```

**What the script does**:
1. Reads `REFACTOR_MANIFEST.yaml` and validates all `MOVE`/`SPLIT` entries have distinct target paths.
2. For each `MOVE`/`SPLIT` entry: creates target directories + `__init__.py` files (Python), writes the shim.
3. Runs the verification gate after each shim. **Stops on first failure.**
4. Prints a per-shim success/failure report.

**After the script runs**:
```bash
git add .
git commit -m "refactor(p1): inject shim layer at all target paths"
```

> [!IMPORTANT]
> Do not manually write shims when this script is available. Manual shims are
> a hallucination vector — the script guarantees the import path is correct.

---

## **[INJECTION — Diff Review Node — 2026-05-01]**

> **Run this before `git commit`.** The diff review node compares what the
> bridge script did to what the manifest said should happen. If a shim was
> written with the wrong source path, or a file was missed, this catches it
> before the error propagates to Phase 2.

### Diff Review: `refactor_diff.py --phase p1`

```bash
python3 /path/to/global_workflows/scripts/refactor_diff.py \
  --project-root /path/to/your/project \
  --phase p1
```

**What it checks**:
- ✅ Forward shim exists at every `MOVE`/`SPLIT` target
- ✅ Every shim contains the `⚠️ SHIM FILE` header
- ✅ Every shim points to the correct `current:` path (no wrong import paths)
- ✅ Original source files still exist (no premature moves)
- ✅ `KEEP` files not accidentally shimmed

**Loop-back rule**:
- 🔴 Any CRITICAL finding → fix it, re-run `refactor_bridge.py`, re-run diff. Do not commit.
- 🟡 WARNING → review and proceed at your discretion.
- 🔵 INFO → informational only.

**Only commit after exit code 0 (clean)**:
```bash
git add .
git commit -m "refactor(p1): inject shim layer at all target paths"
```

> [!IMPORTANT]
> Invoke `/refactor-diff` for the full diff review node documentation.

---

## Phase 1 Completion Checklist

- [ ] All new directories created with `__init__.py` or `.gitkeep`.
- [ ] A shim file exists at every TARGET path for all `MOVE`/`SPLIT` rows.
- [ ] Every shim contains the mandatory `⚠️ SHIM FILE` header comment.
- [ ] No existing files were modified.
- [ ] No import statements were changed.
- [ ] Verification gate passes with exit code 0.
- [ ] All changes committed.

> **State of the codebase after this phase**:
> The new directory structure exists. All new paths resolve.
> All old paths still resolve. The project is fully functional.

**Next Phase**: Invoke `/refactor-p2`

# 🏗️ /refactor-p2 — Phase 2: Physical Migration

> **PHASE CONTEXT**: Phases 0 and 1 are complete. The following artifacts exist:
> - A `refactor/<project-name>` git branch (currently checked out).
> - An approved `REFACTOR_MANIFEST.md` at the project root.
> - **Shim files exist at ALL target paths** (new directory structure).
> - All existing files are still at their original locations.
> - The project passes the verification gate in its current state.
> For the full protocol law, see `/refactor`.

---

## 🎯 Your Objective This Session

Move every file from its current (old) path to its target (new) path
using `git mv` exclusively. After each move, update the OLD location
to become a reverse shim pointing to the new location.

**One module per session.** After moving one module, run the verification
gate and commit before proceeding to the next.

---

## Step 1: Read the Manifest

Open `REFACTOR_MANIFEST.md`. Work through `MOVE` rows in order, starting
with the modules that have the **fewest dependents** in `IMPORT_GRAPH.txt`
(leaf nodes first, core modules last).

---

## Step 2: Move the File (git mv ONLY)

```bash
git mv current/path/file.py new/path/file.py
```

> [!CAUTION]
> NEVER use `cp` + `rm`. NEVER delete and recreate.
> `git mv` is the ONLY acceptable move command.
> It preserves the complete line-by-line git history of every file.

---

## Step 3: Replace the Old Location with a Reverse Shim

After the `git mv`, the old path no longer exists. Create a new file
at the old path that is a reverse shim — it imports from the new location.

### Python Reverse Shim Template
```python
# ⚠️ REVERSE SHIM — Phase 2 of Sovereign Refactor Protocol
# DO NOT REMOVE until Phase 4 (all references have been surgically updated).
# This file exists to preserve import compatibility during migration.
# Logic has MOVED to: <new/path/file.py>
from <new.path.file> import *  # noqa: F401, F403
```

### JavaScript / TypeScript Reverse Shim Template
```typescript
// ⚠️ REVERSE SHIM — Phase 2 of Sovereign Refactor Protocol
// DO NOT REMOVE until Phase 4.
// Logic has MOVED to: <new/path/file.ts>
export * from '<new/path/file>';
```

---

## Step 4: Verification Gate

Run the project's verification command from `REFACTOR_MANIFEST.md`.

```bash
<verification gate command>
```

**Exit code must be 0.** If it fails, diagnose before committing.
Do not move the next file until this one passes.

---

## Step 5: Commit This Module's Migration

```bash
git add .
git commit -m "refactor(p2): git mv <old/path> → <new/path>"
```

---

## Step 6: Repeat for Next Module

Return to Step 1 and select the next module from the Manifest.
Each module is its own commit. Each commit is preceded by a passing gate.

---

---

## **[INJECTION — Script Integration — 2026-05-01]**

> **This step automates Steps 2 and 3 above.**
> `git mv` + reverse shim creation are purely mechanical. The script
> enforces `git mv` exclusively — `cp` + `rm` is structurally impossible.

### Automated Migrator: `refactor_migrate.py`

```bash
# Migrate one module (RECOMMENDED — one module per session):
python3 /path/to/global_workflows/scripts/refactor_migrate.py \
  --project-root /path/to/your/project \
  --module utils

# Migrate all MOVE entries sequentially (stops on first failure):
python3 refactor_migrate.py --project-root /path/to/project --all

# Preview without moving anything:
python3 refactor_migrate.py --project-root /path/to/project --module utils --dry-run
```

**What the script does per module**:
1. Removes the Phase 1 forward shim at the target path (if present).
2. Executes `git mv current target` — enforced. No `cp`, no `rm`.
3. Writes a `⚠️ REVERSE SHIM` at the old path pointing to the new location.
4. Runs the verification gate. Stops and reports on failure.

**After the script runs** (per module):
```bash
git add .
git commit -m "refactor(p2): git mv old/path → new/path"
```

> [!CAUTION]
> Never use `cp` + `rm`. Never delete and recreate files. The script
> enforces `git mv` to preserve the complete line-by-line git history.

---

## **[INJECTION — Diff Review Node — 2026-05-01]**

> **Run this after each module migration, before `git commit`.**
> Each `git mv` + reverse shim pair must be validated before the next module
> is touched. One drift compounds silently into the next.

### Diff Review: `refactor_diff.py --phase p2`

```bash
python3 /path/to/global_workflows/scripts/refactor_diff.py \
  --project-root /path/to/your/project \
  --phase p2
```

**What it checks** (per module just migrated):
- ✅ Real source file exists at the `target:` path (not a Phase 1 shim)
- ✅ `⚠️ REVERSE SHIM` header present at the `current:` (old) path
- ✅ Reverse shim points to the correct `target:` path
- ✅ `KEEP` files still exist and were not accidentally moved

**Loop-back rule**:
- 🔴 CRITICAL (e.g., target still a shim, reverse shim missing) → do not commit.
  Re-run `refactor_migrate.py --module <name>` for the affected module.
- 🟡 WARNING → review before committing.

**Only commit after exit code 0 (clean)**:
```bash
git add .
git commit -m "refactor(p2): git mv old/path → new/path"
```

> [!IMPORTANT]
> Invoke `/refactor-diff` for the full diff review node documentation.

---

## Phase 2 Completion Checklist

- [ ] Every `MOVE` row in the Manifest has been processed.
- [ ] Every file now lives at its TARGET path.
- [ ] Every OLD path now contains a reverse shim pointing to the new location.
- [ ] Verification gate passes after every individual move.
- [ ] One commit per module migration.
- [ ] No import statements have been modified yet (that is Phase 3).

> **State of the codebase after this phase**:
> Every file is in its new home with full git history.
> Old paths resolve via reverse shims. New paths resolve directly.
> The project is fully functional from both old and new import paths.

**Next Phase**: Invoke `/refactor-p3`

# 🏗️ /refactor-p3 — Phase 3: Reference Surgery

> **PHASE CONTEXT**: Phases 0, 1, and 2 are complete. The following is true:
> - Every file lives at its TARGET path (per the Manifest).
> - Every OLD path contains a reverse shim pointing to the new location.
> - Every NEW path (pre-Phase 2 shim) now contains the real file.
> - The project passes the verification gate.
> - No import statements have been updated yet — all imports still
>   reference old paths, which still work via reverse shims.
> For the full protocol law, see `/refactor`.

---

## 🎯 Your Objective This Session

Update import statements inside source files to point directly to the
new (target) paths, eliminating dependence on the reverse shims.

**THE IRON RULE: ONE MODULE PER SESSION.**
Pick one file. Update its imports. Run the gate. Commit. Stop.
The next module is the next session.

Do NOT remove any shim files yet. That is Phase 4.
Do NOT move any files. That was Phase 2.

---

## Step 1: Identify the Current Module

Ask the user which module (file) to operate on this session, OR
select the one with the most outdated imports from `IMPORT_GRAPH.txt`.

Work leaf-to-core: update files that import from many places
before updating files that are imported by many places.

---

## Step 2: Find All Outdated Import Statements

Use `grep` to find every import in the target file that references an
old path (a path that now contains a reverse shim):

```bash
grep -n "^from \|^import " target/path/module.py
```

Cross-reference each import against the Manifest to determine if the
imported path has moved.

---

## Step 3: Perform Surgical Import Updates

Update each outdated import to reference the new (target) path directly.

**Before:**
```python
from old.path.file import SomeClass
from another.old.path import some_function
```

**After:**
```python
from new.path.file import SomeClass
from another.new.path import some_function
```

Update ONE file only. Do not touch any other file in this session.

---

## Step 4: Verification Gate

Run the project's verification command from `REFACTOR_MANIFEST.md`.

```bash
<verification gate command>
```

**Exit code must be 0.** If it fails:
1. Do NOT attempt to fix by modifying additional files.
2. Diagnose the specific failure.
3. Report to the user.
4. Await guidance before proceeding.

---

## Step 5: Commit This Module's Surgery

```bash
git add target/path/module.py
git commit -m "refactor(p3): update imports → new paths in <module.py>"
```

---

## Step 6: Mark the Manifest

Update `REFACTOR_MANIFEST.md` to mark this module as `[SURGERY COMPLETE]`
in a new "Phase 3 Progress" tracking column. This allows any agent in
any future session to know exactly where the work stands.

---

---

## **[INJECTION — Script Integration — 2026-05-01]**

> **This augments Steps 2 and 4 above with a deterministic scanner.**
> The LLM's job (rewriting import statements) requires intelligence and cannot
> be scripted. But *discovering* what to rewrite and *verifying* completion
> are purely mechanical — that is the auditor's job.

### Automated Auditor: `refactor_audit.py`

**Before each surgery session** — generate the Surgery Queue:
```bash
python3 /path/to/global_workflows/scripts/refactor_audit.py \
  --project-root /path/to/your/project \
  --scan
```
The output is the LLM's session instructions. It lists every file with stale
imports and the exact line numbers. The LLM operates only on what the scan reports.

**After all surgery is complete** — verify zero stale imports remain:
```bash
python3 refactor_audit.py --project-root /path/to/project --verify
```
Exit code 0 = Phase 3 is complete. Proceed to Phase 4.
Exit code 1 = Stale imports remain. Return to surgery.

**Workflow per session**:
```
1. --scan  → get the queue
2. LLM updates ONE file's imports
3. Run verification gate manually
4. git add <file> && git commit -m "refactor(p3): update imports in <file>"
5. Repeat steps 1–4 until --scan shows empty queue
6. --verify → final confirmation → proceed to Phase 4
```

> [!IMPORTANT]
> Never skip `--verify` before moving to Phase 4. The auditor guarantees that
> no file was missed — even in directories the LLM did not think to check.

---

## **[INJECTION — Diff Review Node — 2026-05-01]**

> **Run on demand during Phase 3.** Phase 3 spans many sessions. The diff
> review node gives you a structural health snapshot at any point —
> catching if a surgery session accidentally introduced a regression.

### Diff Review: `refactor_diff.py --phase p3`

```bash
python3 /path/to/global_workflows/scripts/refactor_diff.py \
  --project-root /path/to/your/project \
  --phase p3
```

**What it checks**:
- ✅ All Phase 2 structural checks (inherited — regressions are caught here)
- ✅ Files marked `surgery_complete: true` do not still import from old paths
- 🔵 Progress report: `N / M` modules have `surgery_complete: true`

**When to run it**:
- At the start of each surgery session (confirm P2 state is intact)
- After marking any entry `surgery_complete: true` in the manifest
- Before moving to Phase 4 (use alongside `refactor_audit.py --verify`)

**Loop-back rule**:
- 🔴 CRITICAL (structural regression) → fix before continuing surgery.
- 🟡 WARNING (surgery_complete inconsistency) → update manifest or fix the import.

> [!NOTE]
> For import-level scanning (which files have stale imports), use
> `refactor_audit.py --scan` and `--verify`. The diff node validates
> *structure*; the audit node validates *import content*.
>
> Invoke `/refactor-diff` for full documentation.

---

## Phase 3 Completion Criteria

Phase 3 is complete ONLY when EVERY non-shim file in the project has
had its imports surgically updated. At that point:

- [ ] Every source file imports directly from new (target) paths.
- [ ] No source file imports from a path that is now a reverse shim
      (unless that file itself is a shim).
- [ ] Verification gate passes.
- [ ] `REFACTOR_MANIFEST.md` shows `[SURGERY COMPLETE]` for all modules.

> **State of the codebase after this phase**:
> All real source files import from real new paths.
> Reverse shims still exist at old paths but are no longer used
> by any real source file. They are now dead code ready for removal.

**Next Phase**: Invoke `/refactor-p4`

# 🏗️ /refactor-p4 — Phase 4: Shim Removal & Merge

> **PHASE CONTEXT**: Phases 0 through 3 are complete. The following is true:
> - Every file lives at its TARGET path.
> - Every real source file imports directly from new (target) paths.
> - Reverse shims still exist at old paths but are no longer imported
>   by any real source file — they are dead code.
> - Forward shims from Phase 1 at new paths were replaced by real
>   files in Phase 2 and no longer exist.
> - The project passes the verification gate.
> For the full protocol law, see `/refactor`.

---

## 🎯 Your Objective This Session

Remove all remaining shim files (dead code). Perform a final full
verification. Clean up the refactor artifacts. Merge to main.

This is the final phase. After this, the refactor is complete.

---

## Step 1: Identify All Remaining Shims

Find every file that still contains the shim header comment:

```bash
grep -rl "⚠️ REVERSE SHIM\|⚠️ SHIM FILE" . | grep -v "__pycache__"
```

This list should contain ONLY old-path reverse shims. If any file at
a new (target) path appears, STOP — it should not be a shim at this stage.
Report to the user before proceeding.

---

## Step 2: Verify Each Shim is Truly Dead

Before deleting any shim, confirm nothing still imports from that old path:

```bash
# Replace old/path/file with the actual old path (dots for Python)
grep -rn "from old.path.file\|import old.path.file" . | grep -v "__pycache__" | grep -v "SHIM"
```

If any result appears, **STOP**. That old path is still being used.
It means Phase 3 missed a reference. Return to `/refactor-p3` for that file.

---

## Step 3: Remove Each Shim (One at a Time)

Remove shim files individually, running the verification gate after each:

```bash
git rm old/path/file.py
```

Then immediately run:
```bash
<verification gate command>
```

**Exit code must be 0** before removing the next shim.

Commit after each shim removal:
```bash
git commit -m "refactor(p4): remove dead shim old/path/file.py"
```

---

## Step 4: Remove Refactor Artifacts

Once all shims are removed and the gate passes:

```bash
git rm IMPORT_GRAPH.txt
git rm REFACTOR_MANIFEST.md
git commit -m "refactor(p4): remove refactor artifacts"
```

---

## Step 5: Final Full Verification

Run the most comprehensive test suite available:

```bash
<full test suite or E2E command>
```

This is the final gate. The project must pass completely before merging.

---

## Step 6: Update Documentation

Update the project's `Concept.md` and `Architecture.md` to reflect the
new structure. This is mandatory — the manifest documents must stay in sync
with reality.

```bash
git add Concept.md Architecture.md
git commit -m "refactor(p4): update architecture documentation"
```

---

## Step 7: Merge to Main

```bash
git checkout main
git merge --no-ff refactor/<project-name>
git tag refactor/<project-name>-complete
git push origin main --tags
```

The `--no-ff` flag preserves the refactor branch as a visible unit in
git history, making it easy to review the entire migration as a single
logical change.

---

---

## **[INJECTION — Script Integration — 2026-05-01]**

> **This automates Steps 1, 2, 3, and the confirmation pass of Step 5.**
> The script verifies each shim's dependency safety before touching it.
> No shim is removed unless the scanner confirms zero importers remain.

### Automated Cleaner: `refactor_clean.py`

```bash
# Remove all removable shims (blocked shims are reported, not touched):
python3 /path/to/global_workflows/scripts/refactor_clean.py \
  --project-root /path/to/your/project

# Remove a single specific shim:
python3 refactor_clean.py --project-root /path/to/project --shim src/old/module.py

# Preview without removing anything:
python3 refactor_clean.py --project-root /path/to/project --dry-run
```

**What the script does**:
1. Scans the project for all files containing `⚠️ SHIM FILE` or `⚠️ REVERSE SHIM` headers.
2. For each shim: greps the codebase to verify nothing still imports from that path.
3. If safe: announces the action, then executes `git rm`. Runs the verification gate.
4. If blocked: reports the specific file(s) still importing the shim. Does NOT remove it.
5. Final pass: confirms zero shim headers remain anywhere in the codebase.

**After all shims are removed**:
```bash
git add .
git commit -m "refactor(p4): remove all shim files"

# Clean up refactor artifacts
git rm IMPORT_GRAPH.txt REFACTOR_MANIFEST.yaml
git commit -m "refactor(p4): remove refactor artifacts"
```

> [!CAUTION]
> Never manually delete a shim without running `--verify` first on its dependents.
> The cleaner script is the only safe mechanism for shim removal.

---

## **[INJECTION — Diff Review Node — 2026-05-01]**

> **Run twice in Phase 4**: once after shim removal, once immediately before
> `git merge`. The pre-merge run is the strictest gate in the entire protocol —
> it is the final safety check before the refactor branch touches main.

### Diff Review Post-Clean: `refactor_diff.py --phase p4`

```bash
# After refactor_clean.py — verify cleanup is complete:
python3 /path/to/global_workflows/scripts/refactor_diff.py \
  --project-root /path/to/your/project \
  --phase p4
```

**What it checks**:
- ✅ Zero shim headers remain anywhere in the project
- ✅ All `MOVE` target files exist and are real source files
- ✅ No old `current:` paths still exist (reverse shims should be gone)
- ✅ All `KEEP` files still exist

### Diff Review Pre-Merge: `refactor_diff.py --phase p4 --pre-merge`

```bash
# Run this immediately before git merge — the final gate:
python3 refactor_diff.py --project-root /path/to/project --phase p4 --pre-merge
```

**Additional pre-merge checks**:
- ✅ `IMPORT_GRAPH.txt` removed (refactor artifact)
- ✅ `REFACTOR_MANIFEST.yaml` removed (refactor artifact)
- ✅ No untracked source files outside the manifest

**The merge gate**:
```
refactor_diff.py --phase p4 --pre-merge   → exit 0
        │
        ▼
git checkout main
git merge --no-ff refactor/<project-name>
git tag refactor/<project-name>-complete
git push origin main --tags
```

**If exit code is 1**: Do NOT merge. Fix all CRITICAL deviations and re-run.

> [!CAUTION]
> The pre-merge diff is mandatory. It is the one gate that stands between
> a clean main branch and a subtly broken merge. Never skip it.
>
> Invoke `/refactor-diff` for full documentation.

---

## Phase 4 Completion Checklist

- [ ] `grep` for shim headers returns zero results.
- [ ] `IMPORT_GRAPH.txt` deleted.
- [ ] `REFACTOR_MANIFEST.md` deleted.
- [ ] Full verification gate passes with exit code 0.
- [ ] `Concept.md` and `Architecture.md` updated.
- [ ] Merged to main with `--no-ff`.
- [ ] Tagged `refactor/<project-name>-complete`.

> **State of the codebase after this phase**:
> The project is fully restructured. Every file is at its new home
> with complete git history. Every import is direct and clean.
> No shims exist. No refactor artifacts exist.
> The architecture matches the documented design.

---

# 🔍 /refactor-diff — Diff Review Node

> **INVOKE THIS FILE**: At every phase boundary, immediately before committing.
> This is a cross-cutting node — it applies between every phase transition.
> For the full protocol law, see `/refactor`.

---

## 🎯 Purpose

The Diff Review Node answers one deterministic question at every phase boundary:

> **Does the actual state of the filesystem match what the manifest said we intended to do?**

The manifest is the spec. The filesystem is the output. Any divergence between
them is a deviation. Deviations are classified, flagged, and — if critical —
block the commit and trigger a loop-back to fix the problem before it compounds.

---

## 🔁 The Loop-Back Mechanism

```
  [Phase script runs]
         │
         ▼
  [refactor_diff.py --phase pN]
         │
         ├─── EXIT 0 (clean) ──────────────────► [git commit] ──► [Next phase]
         │
         └─── EXIT 1 (deviations found)
                   │
                   ├─── 🔴 CRITICAL: must fix before committing
                   │         └──► Fix → re-run diff → if clean → commit
                   │
                   └─── 🟡 WARNING: human review advised (does not block)
                             └──► Review → proceed with caution
```

**CRITICAL** deviations → must be resolved. Do not commit. Do not proceed.
**WARNING** deviations → flag for human review. No hard block.
**INFO** items → informational. No action required.

---

## 📋 What Each Phase Checks

### Phase P1 Check (after `refactor_bridge.py`)
Validates that shim layer creation matched manifest intent:

| Checks | What It Catches |
|:---|:---|
| Forward shim exists at every `MOVE`/`SPLIT` target | `refactor_bridge.py` silently skipped a file |
| Shim header (`⚠️ SHIM FILE`) present in every shim | File exists but wrong content |
| Shim points to the correct `current:` path | Script generated shim with wrong import path |
| Original file still exists at `current:` path | File was moved before Phase 2 (anti-pattern) |
| `KEEP` files exist and are not shims | KEEP file was accidentally shimmed |

### Phase P2 Check (after `refactor_migrate.py`, per module)
Validates that physical migration matched manifest intent:

| Checks | What It Catches |
|:---|:---|
| Real file at `target:` (not a shim) | `git mv` never ran; target is still a Phase 1 shim |
| Reverse shim at `current:` with correct header | Reverse shim was never written |
| Reverse shim points to the correct `target:` path | Reverse shim has wrong destination |
| `KEEP` files still exist | KEEP file was accidentally deleted or moved |

### Phase P3 Check (during surgery, on demand)
Validates structural state + surgery tracking consistency:

| Checks | What It Catches |
|:---|:---|
| All P2 structural checks | Regression from previous phase |
| `surgery_complete: true` entries with stale imports | Manifest was marked complete prematurely |
| Progress report: `N/M surgery_complete` | Snapshot of how much surgery remains |

### Phase P4 Check (after `refactor_clean.py`)
Validates final state before merge:

| Checks | What It Catches |
|:---|:---|
| Zero shim headers anywhere in the project | `refactor_clean.py` left blocked shims |
| All `MOVE` target files exist | Migration was never completed for some entries |
| No old paths still present (should have been `git rm`'d) | Reverse shims not yet removed |
| All `KEEP` files still exist | KEEP file accidentally deleted during cleanup |

### Phase P4 `--pre-merge` (stricter, run just before `git merge`)
All P4 checks plus:

| Checks | What It Catches |
|:---|:---|
| `IMPORT_GRAPH.txt` has been removed | Refactor artifacts left in the tree |
| `REFACTOR_MANIFEST.yaml` has been removed | Refactor artifacts left in the tree |
| No untracked source files outside the manifest | Files created during refactor but never accounted for |

---

## 🖥️ Invocation

```bash
# After Phase 1 — validate shim layer:
python3 /path/to/global_workflows/scripts/refactor_diff.py \
  --project-root /path/to/project \
  --phase p1

# After each Phase 2 module migration:
python3 refactor_diff.py --project-root /path/to/project --phase p2

# During Phase 3 (on demand, between surgery sessions):
python3 refactor_diff.py --project-root /path/to/project --phase p3

# After Phase 4 shim cleanup:
python3 refactor_diff.py --project-root /path/to/project --phase p4

# Final pre-merge check (strictest):
python3 refactor_diff.py --project-root /path/to/project --phase p4 --pre-merge

# View what the manifest intends (no filesystem checks):
python3 refactor_diff.py --project-root /path/to/project --spec-summary
```

---

## 📖 Reading the Output

```
═══════════════════════════════════════════════════════════════════════
  🔍  DIFF REVIEW NODE — Phase P2 Report
       Project: /path/to/project
═══════════════════════════════════════════════════════════════════════
  Total findings  : 2
  🔴 CRITICAL     : 1
  🟡 WARNING      : 1
  🔵 INFO         : 0

  🔴  CRITICAL (1)
  ──────────────────────────────────────────────────────────────────
  [TARGET_STILL_SHIM]  src/new/utils.py
  ↳ Target path still contains a Phase 1 forward shim — real file not yet moved here.
  💡 Run git mv for this module: refactor_migrate.py --module utils

  🟡  WARNING (1)
  ──────────────────────────────────────────────────────────────────
  [REVERSE_SHIM_HEADER_MISSING]  src/old/utils.py
  ↳ Old path exists but lacks the '⚠️ REVERSE SHIM' header.
  💡 Confirm this is a proper reverse shim, not the original file.

  ═══ LOOP-BACK REQUIRED ══════════════════════════════════════════
  1 CRITICAL deviation(s) must be resolved before committing.
  Do NOT proceed to the next phase.
═══════════════════════════════════════════════════════════════════════
```

---

## 🔗 Integration with Phase Workflow Files

Each phase workflow (`/refactor-p1` through `/refactor-p4`) contains an
`[INJECTION — Diff Review Node]` block that specifies exactly when and how
to invoke this script within that phase's sequence.

The canonical position is: **after the phase script runs, before `git commit`**.

---

## Phase Boundary Reference

| Phase Boundary | Command |
|:---|:---|
| After P1 (bridge) | `refactor_diff.py --phase p1` |
| After each P2 module | `refactor_diff.py --phase p2` |
| Mid-P3 (optional) | `refactor_diff.py --phase p3` |
| After P4 (clean) | `refactor_diff.py --phase p4` |
| Pre-merge (final) | `refactor_diff.py --phase p4 --pre-merge` |

## 🏆 Refactor Complete

The Sovereign Refactor Protocol has been executed to completion.
Zero regressions. Full history preserved. Clean main branch.

---

### Change Log
1. **2026-05-01**: `[INJECTED — Script Integration + Diff Review Node]` All five phase scripts (refactor_scout.py, refactor_bridge.py, refactor_migrate.py, refactor_audit.py, refactor_clean.py) integrated into corresponding phase files as INJECTION blocks. Diff review node (refactor_diff.py) added to P1–P4 as mandatory gate. /refactor-diff documentation section added as standalone phase reference.
2. **2026-05-21**: `[PORTED — Claude Code migration]` Pointer/Payload architecture retired. Merged into single command file at `~/blueprint-workflows/claude-commands/refactor.md`. Universal Agent Constraints: PYTHONPATH updated from `/home/jwils/.gemini/antigravity/global_workflows/scripts` → `~/blueprint-workflows/scripts`. Scripts README note updated to reference `~/blueprint-workflows/scripts/README.md`.
