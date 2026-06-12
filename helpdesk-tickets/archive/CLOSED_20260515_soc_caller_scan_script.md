# Helpdesk Ticket: /soc Divergence D4 — Automated CALLER MAP Script Not Yet Built

**To**: Senior Architect of Workflows
**From**: /harden-workflow --ticket CLOSED_20260512_soc_workflow.md (D4 deferral)
**Date**: 2026-05-15
**Subject**: Divergence D4 from the /soc audit — `soc_caller_scan.py` automation script was not in scope for the workflow text hardening pass and requires a dedicated implementation.
**Urgency**: LOW

---

## 1. Executive Summary

During the Stage 1a-style hardening of `soc/core.md` (ticket `CLOSED_20260512_soc_workflow.md`), all five addenda (A–E) were resolved via workflow text injections. Divergence D4 — the `soc_caller_scan.py` automated CALLER MAP script — was explicitly deferred because it requires new Python code, not a workflow text change. This ticket tracks that deferral.

## 2. What D4 Is

From the original ticket:
> **D4 — Automated CALLER MAP via soc_caller_scan.py**: Script parallel to `refactor_scout.py`. Generates `SOC_CALLER_MAP.txt` persisted to disk. Eliminates manual IDE discovery and solves F1 persistence (Addendum A).

Addendum A was resolved by mandating that the agent write the CALLER MAP to `SOC_MANIFEST.md` manually. D4 is the upgrade path: a Python script that performs the same discovery autonomously, without relying on the agent's IDE "Find References" access.

## 3. Scope of D4 Implementation

1. Create `scripts/soc/soc_caller_scan.py` in `global_workflows/scripts/`.
2. Script accepts: `--workspace <path>` and `--god-file <path>`.
3. Scans for: direct imports, `__init__.py` barrel exports, framework registry patterns (FastAPI, Django, Express), dynamic imports (`importlib.import_module`), test fixtures/mocks.
4. Outputs: structured CALLER MAP in the format SOC_MANIFEST.md expects.
5. Update `soc/core.md` Step 0 to optionally invoke the script instead of manual IDE discovery.

## 4. Precedent

`refactor_scout.py` in `global_workflows/scripts/` is the direct analog. D4 mirrors its design.

---
**Status**: **REMEDIATED**
**Verification**: PASSED — `soc_caller_scan.py` consolidated into `scripts/workstream/verify.py --mode callers`. Tested against blueprint-workflows workspace (produces populated CALLER MAP). `soc.md` Step 0 updated with optional `verify.py --mode callers --file <god_file>` invocation.

**Resolution Note (2026-05-25):** The standalone `soc_caller_scan.py` was not built as a separate script. Instead, the caller map functionality was consolidated into the Verification Substrate (`scripts/workstream/verify.py --mode callers`) which also handles Pre-Flight checks (`--mode preflight`), Diff Oracle analysis (`--mode diff-oracle`), and dependency boundary scanning (`--mode dependency`). Building two separate import-tracing scripts would have been redundant. The `/soc` workflow (Step 0) now references `verify.py --mode callers` as the optional automation path, with manual discovery as the fallback.

---
*Signed,*
**Claude Code (Senior Architect)**
*(Consolidated D4 into Verification Substrate — 2026-05-25)*
