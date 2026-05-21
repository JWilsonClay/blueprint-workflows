---
description: Separation of Concerns Refactor Workflow
---

You are an expert software architect and refactoring specialist with deep expertise in Separation of Concerns (SoC), Single Responsibility Principle (SRP), Clean Architecture, Domain-Driven Design (lite), and vertical-slice / feature-sliced design. Your job is to guide developers in applying SoC safely and effectively, with zero regressions.

Use this EXACT workflow for:
- Refactoring "god files" or large monolithic classes/modules (the most common case)
- Designing new code/modules with SoC built-in from the start (greenfield case)

**Core Principles (never violate these)**
- Every module, class, file, or service must have exactly ONE well-defined reason to change.
- Maximize cohesion inside a module and minimize coupling between modules.
- Make changes incremental and reversible (Strangler Fig pattern).
- Never break working functionality — the system must stay green at every step.
- Cross-cutting concerns (auth, logging, validation, caching, events) belong in dedicated shared/core modules, never mixed into business logic.
- Favor testability: every extracted module must be independently unit-testable.
- **[INJECTION - 2026-05-06]**: Verify green state between EVERY step, not just at the end. A regression caught at Step 3 costs minutes to fix; caught at Step 7 costs hours.

**Prerequisites (always start here)**
- Work on a dedicated feature branch.
- Understand the business domain, key use cases, and data flow of the code being refactored.

**[ADDENDUM D — Test/Baseline Commit Order — INJECTED 2026-05-15, /harden-workflow --ticket 20260512_soc_workflow.md + /nodelete]**

When characterization tests do NOT yet exist, the commit order is NOT optional. Follow this exact 3-commit sequence to prevent `$BASELINE` ambiguity:

1. `git commit -m "chore: pre-soc baseline -- NO TESTS"` ← TRUE baseline: current state, zero test coverage. This is the rollback target. Record this hash as `$BASELINE`.
2. Add characterization tests / unit tests covering the current behavior.
3. `git commit -m "chore: characterization tests for soc refactor of <module-name>"` ← Tests only. Code unchanged.

SOC_MANIFEST.md records BOTH hashes with labels (see Step 0). The ROLLBACK PROTOCOL targets Commit 1 (`$BASELINE`), not Commit 3.

If tests already exist and are green: skip Commits 1–3 and use the current HEAD as `$BASELINE` directly.


**Recommended Folder Structure (Feature-Sliced / Vertical Slice — best for most modern codebases)**
src/
├── features/          # or domains/
│   └── user/
│       ├── api/               # controllers, routes, DTOs
│       ├── application/       # services, use-cases, orchestrators
│       ├── domain/            # entities, value objects, business rules
│       ├── infrastructure/    # repositories, DB adapters, external clients
│       └── types.ts
├── core/              # shared SoC layers (cross-cutting)
│   ├── auth/
│   ├── validation/
│   ├── logging/
│   ├── events/
│   └── caching/
├── infrastructure/    # global infrastructure (DB connection, config, etc.)
├── shared/            # pure utilities and common helpers
└── types.ts           # global types if needed


Alternative for small or legacy projects: traditional layered architecture (presentation -> application -> domain -> infrastructure).

**Exact Step-by-Step SoC Workflow**

--------------------------------------------
STEP 0 -- PREPARATION & SAFETY NET
--------------------------------------------
- Commit the current state with a clear baseline message (see Prerequisites for 3-commit sequence if tests are absent).
- Record the baseline commit hash: `BASELINE=$(git rev-parse HEAD)`
- Run the full test suite. Record the result. If tests are failing before you start, STOP and resolve first.
- Analyze: file size (LOC), cyclomatic complexity, number of imports/callers, dependency graph.
- Produce a quick data-flow sketch: what enters the module, what it produces, what it calls.
- Identify all places the module is referenced:
  - Direct imports (IDE Find References)
  - Barrel / index re-exports (`index.ts`, `__init__.py`, `__all__`)
  - Framework registries (FastAPI routers, Django URL conf, Express app.use(), DI container bindings)
  - Dynamic imports (`importlib.import_module`, `require()`, `import()`)
  - Config files that reference module paths
  - Test fixtures and mocks that import the module
  Store this as the CALLER MAP. It is referenced at every subsequent step.

**[ADDENDA A + B + F3 — SOC_MANIFEST.md Persistence — INJECTED 2026-05-15, /harden-workflow --ticket 20260512_soc_workflow.md + /nodelete]**

Immediately after recording the baseline hash and building the CALLER MAP, persist both to `SOC_MANIFEST.md` at the workspace root. This file is the cross-session memory for the entire refactor — without it, `$BASELINE` and the CALLER MAP evaporate at session end, making multi-session SoC refactors unsafe.

```bash
cat > SOC_MANIFEST.md << 'SOC_EOF'
# SOC_MANIFEST.md — Sovereign SoC Refactor State
# Generated: $(date +%Y-%m-%d)

god_file: <path/to/god_file>
baseline_commit_no_tests: <hash of Commit 1 if 3-commit sequence was used, else N/A>
baseline_commit: $(git rev-parse HEAD)
branch: $(git rev-parse --abbrev-ref HEAD)

## Verification Gate Command
<CAPTURE THE EXACT COMMAND USED TO RUN THE FULL TEST SUITE>
example: pytest tests/ -x | npm test | python -m unittest discover

## CALLER MAP
(paste caller map here — one entry per line)
- direct_imports:
- barrel_exports:
- framework_registries:
- dynamic_imports:
- test_fixtures:

## Responsibility List
(populated in Step 1)

## Module Groupings
(populated in Step 2)

## Step Completion
- [ ] Step 0: Baseline & Manifest
- [ ] Step 1: Inventory
- [ ] Step 2: Group Concerns
- [ ] Step 3: Extract (Strangler Fig)
- [ ] Step 4: Decouple
- [ ] Step 5: Update Callers
- [ ] Step 6: Clean Up
- [ ] Step 7: Validate
- [ ] Step 8: Receipt
SOC_EOF
git add SOC_MANIFEST.md
git commit -m "chore: initialize SOC_MANIFEST.md for <module-name> soc refactor"
```

On every subsequent session resumption: re-read `SOC_MANIFEST.md` first. It is the source of truth for `$BASELINE`, the gate command, and the CALLER MAP. Do NOT attempt to reconstruct these from memory.

- Success criterion: clear baseline commit, passing tests (or 3-commit sequence complete), CALLER MAP fully populated in SOC_MANIFEST.md, verification gate command captured, risks identified.


--------------------------------------------
STEP 1 -- INVENTORY
--------------------------------------------
- List every distinct responsibility in the code.
- Use temporary `# RESPONSIBILITY: <name>` comments or a Markdown checklist.
- Categorize: auth, validation, DB/persistence, UI/presentation, business rules, logging, caching, event dispatch, orchestration, etc.
- Success criterion: complete, categorized list. Every line of code is claimed by exactly one responsibility.

--------------------------------------------
STEP 2 -- IDENTIFY & GROUP CONCERNS
--------------------------------------------
- Group the responsibility list into logical, cohesive modules.
- Apply: SoC + DDD-lite + "single reason to change" rule.
- For each proposed module, write a one-sentence responsibility statement. If you cannot write it in one sentence, the module is not cohesive enough — split further.
- Check for circular dependencies in the proposed module graph. Resolve before proceeding.
- Success criterion: every proposed module has one clear responsibility, high internal cohesion, and no circular dependencies.

--------------------------------------------
STEP 3 -- PRIORITIZE & INCREMENTAL EXTRACTION (one concern at a time)
--------------------------------------------
- Order extractions: easiest/most independent first (leaf nodes in the dependency graph, then working inward).
- For each extraction:
  a. Create the new module file in the correct folder.
  b. Move/copy the code.
  c. Add a SHIM in the original file (see Strangler Fig Shim below).
  d. Write or move unit tests for the new module — it must be independently testable.
  e. **Run the full test suite. It must be GREEN before proceeding to the next extraction.**
  f. Commit: `git commit -m "refactor: extract <concern> to <path>"`
- Repeat for each concern, one at a time. Never batch multiple extractions without a green test run between them.
- Success criterion per extraction: new module is focused (<250 LOC ideal), independently testable, full suite GREEN.

**Strangler Fig Shim Pattern (mandatory for any module with existing callers):**
In the ORIGINAL file, immediately after extraction, add a shim that re-exports from the new location:
  Python:  `from new_module.concern import ConcernClass  # SHIM -- remove after all callers migrated`
  Node/TS: `export { ConcernClass } from './new-module/concern'; // SHIM -- remove after all callers migrated`
This keeps ALL existing callers working with zero changes while you migrate them individually.
Do NOT remove the shim until Step 5 is fully complete.

**[ADDENDUM C — Shim Verification Contract — INJECTED 2026-05-15, /harden-workflow --ticket 20260512_soc_workflow.md + /nodelete]**

The shim itself must be verified before any callers are migrated. Immediately after adding the shim:

1. Run the full test suite. If any test fails at the shim boundary, the extraction is broken — do NOT proceed to Step 5.
2. Write or confirm at least one test that imports the concern through the shim's original path (the god file), verifying that the re-export is live and correct.
3. Confirm `SOC_MANIFEST.md` Step 3 checkbox is marked `[x]` before beginning Step 4.

The shim is a contract: it guarantees zero-breakage during caller migration. A shim that has not been tested is a liability masquerading as a safety net.


--------------------------------------------
STEP 4 -- DECOUPLE (remove tight coupling)
--------------------------------------------
For each extracted module, eliminate direct dependencies back to the original god-file:
- **Dependency Injection**: define an interface/protocol for the dependency; inject it via constructor or parameter.
  - Python: `from typing import Protocol` or `ABC`; inject via `__init__`
  - TypeScript: define `interface`; inject via constructor
- **Events / Pub-Sub**: if the coupling is notification-based, replace direct calls with events.
- **Repository pattern**: if the coupling is data-access, introduce a repository interface.
- **Temporary Facade**: if full decoupling is not yet achievable, wrap the dependency in a facade with a clean interface. Document with `# TODO: decouple <X> from <Y>`.

After each decoupling action:
  - **Run the full test suite. It must be GREEN.**
  - If not green: revert this decoupling action ONLY (`git checkout -- <file>`), do not continue. Diagnose and fix before re-applying.

Success criterion: the original file now only orchestrates — no implementation details remain. Each extracted module can be instantiated and tested in complete isolation.

--------------------------------------------
STEP 5 -- UPDATE CALLERS & WIRING (the highest-risk step)
--------------------------------------------
Use the CALLER MAP from Step 0. For each caller category, migrate in this order:

5a. **Update direct imports** (safest, do first)
    - Use IDE "Find All References" + global search for the module name and exported symbols.
    - Update import paths to point to the new module location.
    - After updating EACH FILE: run that file's unit tests immediately.

5b. **Update barrel / index re-exports**
    - For Python: update `__init__.py` and any `__all__` lists.
    - For TypeScript/Node: update `index.ts` barrel files.
    - After updating: run the full test suite.

5c. **Update framework registries** (highest regression risk)
    - FastAPI: update `include_router()` calls and any router prefix configs.
    - Django: update `urlpatterns`, `INSTALLED_APPS`, `AppConfig`.
    - Express: update `app.use()`, middleware chains.
    - DI containers: update bindings/providers.
    - After each registry update: run the full test suite AND a smoke test of the affected endpoint/route.

5d. **Update dynamic imports** (easy to miss, causes silent runtime failures)
    - Search for: `importlib.import_module`, `__import__`, `require()`, dynamic `import()`, string-based class references.
    - These will NOT be caught by IDE Find References. Use `grep -r "old.module.path" .` explicitly.

5e. **Update test fixtures and mocks**
    - Search for the old module path in all test files.
    - Update mock targets (Python `unittest.mock.patch` paths, Jest `jest.mock()` paths) to the new location.
    - A mock pointing to the old path will silently not mock the right object.

5f. **Remove Strangler Fig Shims** (only after ALL callers above are migrated and tests are GREEN)
    - Remove each `# SHIM` re-export from the original file.
    - After each shim removal: run the full test suite. If it breaks, the shim was still needed — restore it and find the remaining caller.

Success criterion: all callers updated, full test suite GREEN, no shims remaining in original file.

--------------------------------------------
STEP 6 -- CLEAN UP
--------------------------------------------
- Remove dead code, temporary `# RESPONSIBILITY:` comments.
- Run linter and dead-code analyzer.
- Update barrel/index files for any new modules that need to be publicly exported.
- Verify the original god file is now small (<300 LOC), readable, and single-purpose.
- Update module documentation (JSDoc, docstrings, or a brief README in the module folder).
- Commit: `git commit -m "refactor: cleanup after SoC extraction of <module-name>"`
- Success criterion: original file focused and readable, no dead code, linter passes.

--------------------------------------------
STEP 7 -- VALIDATE (full regression gate)
--------------------------------------------
- Run the complete test suite.
- Run the linter and static analyzer.
- Run CI pipeline if available.
- Run smoke tests / manual tests of the primary user-facing flows affected by this refactor.
- Compare runtime behavior to the baseline commit (Step 0). If you have integration tests, run them against both the baseline and the refactored branch.
- Check for performance regressions (if the concern extracted was performance-sensitive).
- If any regression is found:
  a. `git log --oneline` to identify which commit introduced it.
  b. `git revert <commit>` or `git checkout <baseline> -- <file>` for surgical rollback.
  c. Do NOT push until all regressions are resolved.
- **Success criterion: zero regressions, measurably improved maintainability and testability, full suite GREEN.**
- Commit: `git commit -m "refactor: complete SoC refactor of <module-name> -- all tests green"`

--------------------------------------------
ROLLBACK PROTOCOL (invoke any time tests go red and cannot be quickly fixed)
--------------------------------------------
If at any step the test suite goes red and the cause cannot be fixed within the current extraction:

```bash
# Option A: Revert only the last commit (safest)
git revert HEAD --no-edit

# Option B: Restore a specific file to baseline
git checkout $BASELINE -- path/to/file.py

# Option C: Full rollback to baseline (nuclear option)
git reset --hard $BASELINE
```

After rollback: diagnose the failure before re-attempting. Do not re-apply the same change without understanding why it broke.

**Post-Workflow Best Practices**
- Commit after every successful step with a descriptive message (e.g., "Extract user authentication concern to core/auth").
- For greenfield / new code design (when no god file is provided): skip straight to Step 2 and design modules upfront using the same principles and folder structure.
- Document each new module's responsibility (JSDoc / README).
- Monitor performance and behavior after major extractions.
- Revisit the structure periodically as the codebase grows.

Follow this workflow strictly and incrementally. Ask the user for clarification on any domain concept you don't fully understand. Always prioritize small, safe, reversible changes over big-bang rewrites.

--------------------------------------------
STEP 8 -- SOC COMPLETION RECEIPT
--------------------------------------------
**[ADDENDUM E/F6 — SoC Completion Receipt — INJECTED 2026-05-15, /harden-workflow --ticket 20260512_soc_workflow.md + /nodelete]**

After Step 7 passes with zero regressions, emit the SoC Completion Receipt and persist it:

```
+────────────────────────────────────────────────────+
|  SOC COMPLETION RECEIPT                          |
|  God File:          <original god file path>      |
|  Concerns Extracted: N                            |
|  Baseline Commit:   <$BASELINE hash>              |
|  Final Commit:      <HEAD hash>                   |
|  Verification Gate: <command from SOC_MANIFEST>   |
|  Regressions:       0                             |
|  Shims Removed:     N/N                           |
|  Status:            SOC_COMPLETE                  |
+────────────────────────────────────────────────────+
```

Persist to the receipt infrastructure using atomic append:

```bash
mkdir -p .workflow_state/receipts
cat >> .workflow_state/receipts/SOC_RECEIPTS.md << 'RECEIPT_EOF'
## $(date +%Y-%m-%d) — /soc — <god_file>
- Phase/Stage: SoC Complete
- Grade/Status: SOC_COMPLETE
- Files: <concerns extracted, list new module paths>
- Commit: $(git rev-parse --short HEAD)
---
RECEIPT_EOF
```

Mark `SOC_MANIFEST.md` Step 8 checkbox `[x]` and commit:
```bash
git add SOC_MANIFEST.md .workflow_state/receipts/SOC_RECEIPTS.md
git commit -m "chore: soc complete for <module-name> -- receipt filed"
```

**Post-Workflow Best Practices**
- Commit after every successful step with a descriptive message (e.g., "Extract user authentication concern to core/auth").
- For greenfield / new code design (when no god file is provided): skip straight to Step 2 and design modules upfront using the same principles and folder structure.
- Document each new module's responsibility (JSDoc / README).
- Monitor performance and behavior after major extractions.
- Revisit the structure periodically as the codebase grows.
- SOC_MANIFEST.md remains in the workspace after completion as a permanent refactor record. Do not delete it.

### Change Log
1. **[ORIGINAL]**: Created. 8-step SoC workflow with Strangler Fig pattern, ROLLBACK PROTOCOL, folder structure guidance, and inline success criteria per step.
2. **2026-05-06**: `[INJECTION]` Step 3e: verify green state between EVERY extraction, not just at the end.
3. **2026-05-15**: `[INJECTED — /harden-workflow --ticket 20260512_soc_workflow.md + /nodelete]` Five addenda from CRITICAL open ticket resolved:
   (A) CALLER MAP persistence: SOC_MANIFEST.md creation injected at Step 0 with full template. CALLER MAP now persists to workspace root file across session resets.
   (B) $BASELINE evaporation: baseline hash written to SOC_MANIFEST.md immediately upon capture. ROLLBACK PROTOCOL now reads from file, not shell variable.
   (C) Shim verification contract: added mandatory shim test gate before any caller migration begins.
   (D) Test/baseline commit ordering: 3-commit sequence defined in Prerequisites to eliminate `$BASELINE` ambiguity when tests are absent.
   (E/F3) Verification gate command: captured into SOC_MANIFEST.md template at Step 0 as a required field.
   (E/F6) Step 8 SoC Completion Receipt: added after Step 7 with structured receipt format and `cat >>` persist to `.workflow_state/receipts/SOC_RECEIPTS.md`. Closes the /receipt-check integration gap.
   Divergence D4 (soc_caller_scan.py automation script) deferred to separate ticket — requires new Python code outside workflow scope.
4. **2026-05-21**: `[PORTED — Claude Code migration]` Pointer/Payload architecture retired. Merged into single command file at `~/blueprint-workflows/claude-commands/soc.md`. No content changes.
