# Helpdesk Ticket: Focus Evidence Engine's Generic `build`-Directory Ignore Rule Blinds It to Legitimate Project Source Trees

**To**: Senior Architect of Workflows
**From**: Claude Code session (research/proforma workspace)
**Date**: 2026-07-29
**Subject**: `/focus-plan`'s substrate scanner unconditionally prunes any directory literally named `build`, producing a structural false-negative for any workspace that legitimately names a source directory `build` (e.g. `research/proforma/scripts/build/`)
**Urgency**: MEDIUM
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

`/focus-plan`'s Focus Evidence Engine skips any directory named exactly `build` when indexing a workspace's substrate — a rule clearly written to skip JS/web build-output directories (`dist`, `node_modules`, `build`). The `research/proforma` project keeps its real, hand-authored Python deliverable-generation pipeline at `research/proforma/scripts/build/` — a legitimate source tree that happens to share that name. The result: every file anchor under `scripts/build/` is reported `MISSING` regardless of whether the file actually exists, on every `/focus-plan` run against this workspace, indefinitely. This was discovered live during a `/focus-plan` run against `research/proforma` today, when 5 genuinely-existing scripts (`render_inventory.py`, `extract_facts.py`, `trajectory_chart.py`, `update_excel.py`, `sanitization.py`) all reported absent.

## 2. Root Cause Analysis: "Generic Ignore Convention Collides With Project-Specific Naming"

This is a **false-negative substrate-scanning defect**, not previously named in this suite's failure taxonomy under any of the existing four classes (Sound Effect, Context Erosion, Hallucinated Success, Ghost Logic) — it produces the mirror image of Ghost Logic: the engine reports code as *absent* when it is genuinely *present*, which risks the opposite failure (an agent halting on a false MISMATCH signal, or a user losing trust in a workflow that "can't find" code that's right there).

- **The How**: `AnchorScanner._walk()` prunes any directory whose bare name matches `IGNORE_DIRS`, with no further inspection of what that directory actually contains. `IGNORE_DIRS` includes `"build"` alongside `node_modules`, `dist`, `.git`, etc. — a set clearly tuned for JS/web project conventions, where `build`/`dist` are compiled, disposable output. In `research/proforma`, `scripts/build/` is the opposite: it is the hand-authored, version-controlled source of the project's client-deliverable generation pipeline (HTML/PDF inventory rendering, workbook-fact extraction, chart generation). The ignore rule cannot distinguish "a directory named build that holds generated output" from "a directory named build that holds source," because it never looks inside.
- **The Why**: The workflow's substrate scanner has no mechanism for a target workspace to override or narrow the suite-global `IGNORE_DIRS` set, and no heuristic (e.g. requiring a sibling `package.json`/`webpack.config.*`/`.gitignore` entry before treating a `build`-named directory as disposable output) to distinguish the convention's intended target from a legitimate namesake. The engine's own design principle — "the engine gathers evidence deterministically, so 'I looked and found nothing' is backed by a script, not a claim" (focus-plan.md, v3 Architecture note) — is violated in exactly the case it was built to prevent: the script's "I looked" silently skipped an entire real source tree, and its "found nothing" is not evidence of absence.

## 3. Forensic Evidence

- **The ignore rule itself**: [IGNORE_DIRS definition, including the bare `"build"` entry](file:///home/jwils/blueprint-workflows/scripts/focus/_utils.py#L33-L38)
  *Evidence: `"build"` sits in the same frozenset as `node_modules`, `dist`, `.git` — confirming it targets generic build-output directories, with no per-workspace override.*

- **The pruning mechanism**: [`AnchorScanner._walk()`](file:///home/jwils/blueprint-workflows/scripts/focus/anchor_scanner.py#L81-L85)
  *Evidence: `dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]` — unconditional bare-name pruning, no content inspection, applied identically regardless of what a directory actually holds.*

- **Confirmed source-extension inclusion (ruling out "not indexed for a different reason")**: [`CODE_EXTENSIONS`](file:///home/jwils/blueprint-workflows/scripts/focus/_utils.py#L27-L31)
  *Evidence: `.py` is explicitly included — the affected files (`render_inventory.py`, etc.) would be indexed and found if the directory containing them were ever walked. The failure is specifically the directory-level prune, not an extension filter.*

- **Files confirmed to genuinely exist, directly on disk**: `find research/proforma -iname "render_inventory.py" -o -iname "extract_facts.py" -o -iname "trajectory_chart.py" -o -iname "update_excel.py" -o -iname "sanitization.py"` → all 5 resolve to `research/proforma/scripts/build/{name}`.
  *Evidence: this is not a case of a plan citing a file that was never built — the substrate genuinely contains what the plan describes.*

- **Confirmed false-negative reproduced by calling the scanner directly, bypassing the full CLI** (session transcript, `research/proforma` workspace, 2026-07-29): `AnchorScanner(Path('research/proforma'), exclude={...}).verify_file('render_inventory.py')` → `{'status': 'MISSING', 'locations': []}`.
  *Evidence: rules out a CLI-layer or reporting-layer bug — the false negative originates in the scanner's own indexing, exactly at the pruning step cited above.*

- **Confirmed pre-existing, not introduced by today's session**: the same `focus.py --workspace research/proforma --output-json` run reported `update_excel.py` absent for `implementation-plan.md`'s "Phase 46" item — a phase built and closed well before today's session (`research/proforma/tasks.md`, `### Phase 46: Remediation of the 2026-07-28 Phase 45 Audit + Cold-Reviewer Client-Presentation Pass`).
  *Evidence: the defect is not scoped to any specific plan content added recently — it fires on any historical or future citation into `scripts/build/`.*

## 4. Remediation: Per-Workspace Ignore-Directory Override, or Content-Aware `build`/`dist` Detection

Not yet applied — recommendation only, for the Senior Architect's judgment on shape:

1. **Option A — per-workspace override/allowlist.** Let a workspace declare (e.g. a small `.focus-config.json` or a recognized marker file at the workspace root) directory names that should be exempted from `IGNORE_DIRS` for that workspace specifically. Lowest-risk, most explicit — no behavior change for any workspace that doesn't opt in.
2. **Option B — content-aware pruning.** Only treat a `build`/`dist`-named directory as disposable output if a corroborating signal is present nearby (a sibling `package.json`, `webpack.config.*`, `.gitignore` entry naming it, or similar) — closer to the actual intent ("skip compiled JS output"), but adds inference logic the pruning step doesn't currently have, and risks its own false negatives/positives on unusual project layouts.
3. **Option C — narrow the default set and document the tradeoff.** Drop `build`/`dist` from the unconditional default `IGNORE_DIRS`, accepting that some JS-project scans will index compiled output (lower-cost failure mode — noise, not silent invisibility) unless/until Option A or B ships.

I did not implement any of these — this ticket documents the defect and its evidence per this workflow's own mandate ("This workflow does NOT fix failures").

**Secondary observation, not a required fix**: `CODE_EXTENSIONS` also excludes binary formats (`.xlsx`, `.pdf`, `.svg`) entirely, so any file anchor pointing at those extensions is structurally unverifiable — confirmed live against a genuinely-existing `Continuum_North_End_Master_ProForma_Skeleton.PRE_REPAIR_BACKUP.xlsx` at the `research/proforma` root, also reported `MISSING`. This appears to be a deliberate, documented scope choice ("binaries aren't source" — `_utils.py` module docstring intent) rather than an oversight the way the `build`-name collision is. Recording it here since it surfaced in the same investigation; leaving the judgment of whether it warrants its own remediation or just an explicit documented-limitation note to the Senior Architect.

## 5. Recommendation to Senior Architect

Add a per-workspace override mechanism for `IGNORE_DIRS` (Option A above) as the general-purpose fix — it generalizes beyond this one `build`-named collision to any future workspace whose legitimate directory-naming convention collides with a suite-wide default tuned for a different project shape (JS/web), without requiring the engine to infer project type. This is a workflow-level structural gap — any Python, Rust, or Go project that names a source directory `build`, `dist`, or similar will hit the identical false-negative, not just this one project.

---
**Status**: **OPEN**
**Verification**: PENDING — no remediation applied yet.

---
*Signed,*
**Claude Code**
*(Creating Agent — research/proforma session)*
