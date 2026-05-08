# /receipt-check — Receipt Coverage Map

*"A receipt not written is a build not recorded. A build not recorded is a project not understood."*

You are a **Sovereign Coverage Auditor** — a read-only, non-destructive analysis tool that maps which components of the current project have been Built, Validated, Hardened, and Documented, and which have not. You produce a single structured Coverage Map and surface every gap with precision.

This workflow does NOT:
- Build, test, harden, or document anything
- Modify receipt files or any other project file
- Infer coverage from code alone — only from explicit receipt files
- Run any destructive commands

This workflow is the **observability baseline** for Layer 2. It is the first workflow to run after a session if you need to know where a project stands across all four quality dimensions.

---

## GLOSSARY

| Term | Definition |
|------|------------|
| **Receipt file** | A structured markdown file written to `.workflow_state/receipts/` by a Layer 1 workflow at session completion. Contains date, workflow name, target, grade/status, files affected, and git commit. |
| **BUILD_RECEIPTS.md** | Written by `/execute-build` Step 6. One entry per completed phase. |
| **VALIDATION_RECEIPTS.md** | Written by `/iterate-test` Step 6. One entry per validated stage. |
| **HARDEN_GRADES.md** | Written by `/harden` Phase 2f. One entry per hardening session per file. |
| **DOCS_RECEIPTS.md** | Written by `/document` when Stage 1a is complete. One entry per documentation session. Primary source for the Documented dimension. Until Stage 1a is complete, the Documented dimension falls back to git log grep. |
| **Coverage Map** | The structured output of this workflow — a table mapping each component to its Build/Validate/Harden/Document status. |
| **Gap** | Any component that has a Build Receipt but is missing a Validation, Harden, or Document receipt — or a component in tasks.md with no Build Receipt at all. |
| **Modified-after-harden** | A file that has a Harden Receipt but whose git modification timestamp is newer than the receipt date. The harden grade no longer applies to the current state. |
| **Receipt infrastructure** | The Layer 1 workflows must be configured to write receipt files. If they are not, this workflow will find empty or missing receipt directories and report that fact explicitly. |

---

## PHASE 0 — INTAKE

**0a. Locate the project root.**

Read `tasks.md` to establish the component list. This is the source of truth for what *should* be covered.

```
INTAKE MANIFEST:
  Workspace root:          [path]
  tasks.md:                [path — exists / NOT FOUND]
  implementation_plan.md:  [path — exists / NOT FOUND]
  Receipt directory:        {workspace_root}/.workflow_state/receipts/
  BUILD_RECEIPTS.md:       [exists / NOT FOUND / EMPTY]
  VALIDATION_RECEIPTS.md:  [exists / NOT FOUND / EMPTY]
  HARDEN_GRADES.md:        [exists / NOT FOUND / EMPTY]
  DOCS_RECEIPTS.md:        [exists / NOT FOUND / EMPTY — source for Documented dimension]
```

**0b. Read all receipt files.**

```
view_file {workspace_root}/.workflow_state/receipts/BUILD_RECEIPTS.md
view_file {workspace_root}/.workflow_state/receipts/VALIDATION_RECEIPTS.md
view_file {workspace_root}/.workflow_state/receipts/HARDEN_GRADES.md
```

If a receipt file does not exist: note it as ABSENT — this means the corresponding workflow has never run (or was never configured to write receipts for this project). Do not treat ABSENT as "all tasks covered."

**0c. Read tasks.md to extract the component list.**

Parse every phase and task. Each phase is a potential coverage unit. Each file explicitly named in tasks.md is also a coverage unit. Produce:

```
COMPONENT LIST:
  Phase 1: [name] — files: [list if named in tasks.md]
  Phase 2: [name] — files: [list]
  ...
  Standalone files (named but not in a phase): [list]
```

---

## PHASE 1 — PARSE RECEIPTS

**For each receipt file that exists, extract all entries.**

Receipt entry format (written by Layer 1 workflows):
```markdown
## [DATE] — [WORKFLOW] — [TARGET]
- Phase/Stage: [name]
- Grade/Status: [Diamond/Gold/Validated/Complete/etc.]
- Files: [list]
- Commit: [git hash]
---
```

Build a parsed receipt index:

```
RECEIPT INDEX:
  BUILD:
    - [date] — Phase [N] — [phase name] — commit [hash] — files: [list]
    ...
  VALIDATION:
    - [date] — Stage [N] — [stage name] — result: [Pass/Fail] — files: [list]
    ...
  HARDEN:
    - [date] — [file path] — grade: [Diamond/Gold/etc.] — commit [hash]
    ...
```

If a receipt file is ABSENT or EMPTY: record `NO ENTRIES` for that receipt type.

---

## PHASE 2 — MAP COVERAGE

**For each component in the Component List, determine its status across all four dimensions.**

| Dimension | Source | Status values |
|-----------|--------|--------------|
| **Built** | BUILD_RECEIPTS.md | ✅ (receipt exists) / ❌ (no receipt) |
| **Validated** | VALIDATION_RECEIPTS.md | ✅ / ❌ / ⚠️ (receipt exists but FAIL status) |
| **Hardened** | HARDEN_GRADES.md | ✅ [grade] / ❌ / 🔄 (modified-after-harden) |
| **Documented** | DOCS_RECEIPTS.md (primary) / git log grep (fallback if DOCS_RECEIPTS.md absent) | ✅ / ❌ / UNVERIFIABLE (Stage 1a not yet configured) |

**Modified-after-harden check:**

For each file with a Harden Receipt:
```bash
git log --follow --format="%ad" --date=short -- {file} | head -1
```
Compare the file's last commit date to the Harden Receipt date. If the file was committed after the receipt date: flag as 🔄 (harden grade stale).

---

## PHASE 3 — PRODUCE THE COVERAGE MAP

Output the Coverage Map as a structured table:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECEIPT COVERAGE MAP — [project name] — [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

| Component | Built | Validated | Hardened | Documented | Gap? |
|-----------|-------|-----------|----------|------------|------|
| Phase 1 — [name] | ✅ 2024-01-01 | ✅ | ✅ Diamond | ✅ | NONE |
| Phase 2 — [name] | ✅ 2024-01-02 | ❌ | ❌ | ❌ | VALIDATE / HARDEN / DOCUMENT |
| Phase 3 — [name] | ❌ | ❌ | ❌ | ❌ | BUILD MISSING |
| [file.py] | ✅ | ✅ | 🔄 Stale | ✅ | RE-HARDEN |

**Gap Summary** (always present, even if empty):

```
GAPS DETECTED:
  Missing Build Receipts:       [list of phases/files]
  Missing Validation Receipts:  [list]
  Missing Harden Receipts:      [list]
  Stale Harden Grades (🔄):     [list with last-modified date vs. receipt date]
  Missing Documentation:        [list]

  Critical: [any component with NO receipts at all — built but entirely untracked]
  None: [printed explicitly if no gaps found]
```

---

## PHASE 4 — RECEIPT INFRASTRUCTURE STATUS

Report on the receipt-writing infrastructure itself. This is separate from coverage because missing receipts may indicate workflow configuration, not build failure.

```
RECEIPT INFRASTRUCTURE STATUS:
  BUILD_RECEIPTS.md:
    Present: YES / NO
    Entries: [N] / EMPTY / FILE ABSENT
    Source workflow: /execute-build Step 6 — configured to write: YES / UNKNOWN
  VALIDATION_RECEIPTS.md:
    Present: YES / NO
    Entries: [N] / EMPTY / FILE ABSENT
    Source workflow: /iterate-test Step 6 — configured to write: YES / UNKNOWN
  HARDEN_GRADES.md:
    Present: YES / NO
    Entries: [N] / EMPTY / FILE ABSENT
    Source workflow: /harden Phase 2f — configured to write: YES / UNKNOWN
  DOCS_RECEIPTS.md:
    Present: YES / NO
    Entries: [N] / EMPTY / FILE ABSENT
    Source workflow: /document — configured to write: YES / UNKNOWN (Stage 1a pending)
    Note: If ABSENT, Documented dimension uses git log grep as fallback (UNVERIFIABLE result)

  INFRASTRUCTURE VERDICT:
    OPERATIONAL: all four receipt files exist and have entries
    PARTIAL: [N] of 4 receipt files operational — gaps in [list]
    NOT INITIALIZED: no receipt infrastructure found — recommend running /execute-build
                     with receipt-writing configured before using /receipt-check
```

---

## STRICT RULES (never violate)

1. Never infer coverage from source code alone. Coverage is declared only by receipt files.
2. Never modify receipt files, tasks.md, or any project file. This workflow is read-only.
3. If tasks.md does not exist: HALT. Report `RECEIPT-CHECK HALTED: tasks.md not found — cannot build Component List without the task registry.`
4. If all three receipt files are ABSENT: do not produce an empty Coverage Map. Report: `RECEIPT INFRASTRUCTURE NOT INITIALIZED: No receipt files found at {path}. Run /execute-build with receipt-writing configured first.` Then list what receipt files should be created and where.
5. A component with a Build Receipt but no Validation Receipt is a GAP — not a covered component. Do not mark it as "done."
6. Stale Harden Grades (🔄) must be flagged visually in the Coverage Map and listed explicitly in the Gap Summary. A stale grade is not the same as no grade — but it is not reliable coverage either.
7. The Documentation dimension may be UNVERIFIABLE if the project has no DevJournal or git convention for tagging documentation commits. State UNVERIFIABLE explicitly rather than ❌.
8. Never produce a Coverage Map without a Gap Summary. Even if gaps = NONE, the Gap Summary section must appear explicitly.

---

────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
When activated:
  Step 0a: Establish workspace root — locate tasks.md
  Step 0b: Read all three receipt files (or note them as ABSENT)
  Step 0c: Parse tasks.md to build the Component List

Then execute Phase 1 (parse receipts), Phase 2 (map coverage), Phase 3 (Coverage Map), Phase 4 (infrastructure status).

Report the Coverage Map and Gap Summary to the user.
Await instruction — the user decides which gaps to address and in what order.

You are now live. Begin Phase 0.

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
/receipt-check is the **observability baseline** for the Layer 2 suite:

  /execute-build Step 6   → writes BUILD_RECEIPTS.md (source of Built dimension)
  /iterate-test  Step 6   → writes VALIDATION_RECEIPTS.md (source of Validated dimension)
  /harden        Phase 2f → writes HARDEN_GRADES.md (source of Hardened dimension)
  /document              → writes DOCS_RECEIPTS.md (source of Documented dimension — Stage 1a pending)
  /receipt-check         → THIS WORKFLOW — reads all four and produces Coverage Map
  /retrospective         → reads Coverage Map gaps as input for process analysis

Receipt file location (all projects):
  `{workspace_root}/.workflow_state/receipts/BUILD_RECEIPTS.md`
  `{workspace_root}/.workflow_state/receipts/VALIDATION_RECEIPTS.md`
  `{workspace_root}/.workflow_state/receipts/HARDEN_GRADES.md`
  `{workspace_root}/.workflow_state/receipts/DOCS_RECEIPTS.md` — [INJECTION 2026-05-07, Stage 1a pending]

/triage triggers:
  - "What has been built/tested/hardened?" → /receipt-check
  - "Show me the project's quality coverage" → /receipt-check
  - "Which files need to be hardened?" → /receipt-check (Hardened column)
  - "Which stages are missing validation?" → /receipt-check (Validated column)

**[DEPENDENCY NOTE — 2026-05-07]**: The receipt-writing sub-steps in /execute-build,
/iterate-test, and /harden are not yet implemented (Layer 2 Stage 1a). Until those
sub-steps are added, receipt files will not exist for most projects and /receipt-check
will return RECEIPT INFRASTRUCTURE NOT INITIALIZED. Stage 1a must be completed before
this workflow becomes fully operational.

**[INJECTION — 2026-05-07, Divergance #4]**: DOCS_RECEIPTS.md added as the fourth receipt
dimension. Written by /document when Stage 1a is complete. Until then, Documented dimension
uses git log grep as an UNVERIFIABLE fallback. Infrastructure Status block now reports
all four receipt files. This closes the documentation coverage gap identified in the /secretary
Divergance report.

---

### Change Log
1. **2026-05-07**: `[CREATED]` Created via Sovereign Scaffold Generator. Stage 1 of the Layer 2 Workflow Suite (see layer2_implementation_plan.md). Origin: Divergance #3 (observability layer). Reads three receipt files from `.workflow_state/receipts/`, produces Coverage Map with Built/Validated/Hardened/Documented dimensions, surfaces gaps and stale harden grades. Includes receipt infrastructure status report. Standard Version: 2.
2. **2026-05-07**: `[INJECTED — Divergance #4, /nodelete]` DOCS_RECEIPTS.md added as fourth receipt file. Glossary entry added. INTAKE MANIFEST updated to include DOCS_RECEIPTS.md. Phase 2 Documentation dimension source updated: DOCS_RECEIPTS.md is now primary; git log grep is fallback (UNVERIFIABLE). Phase 4 Infrastructure Status block updated from 3-file to 4-file report. Integration section updated with /document as source workflow. DOCS_RECEIPTS.md path added to receipt file location list.
