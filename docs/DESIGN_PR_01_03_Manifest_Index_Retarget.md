---
description: "Small native DESIGN for PR 01-03 (Manifest + integrity retarget) — Stage 1 prototype vehicle for the Sovereign Redesign Cluster's native design→build→hygiene pipeline"
---

# DESIGN: Retarget ManifestManager.sync() to the Substrate Index

**Author:** Claude Code (Sovereign Redesign Cluster, Stage 1 prototype — no Grok delegation)
**Date:** 2026-07-06
**Status:** Draft, self-reviewed (see Review Pass below)
**Governing:** `docs/design-pillars/PILLAR_01_CONTEXT_SESSION_INITIALIZATION.md` §10 "PR 01-03: Manifest + Integrity Retarget"

---

## [INTENT]

> `manifest.py`'s `ManifestManager.sync()` rebuilds MANIFEST.md's auto-synced directory list by re-traversing the raw scanner map (`current_map`) every run — recomputing display names and README checks from scratch, independent of the canonical `substrate_index.json` that `auditor.build_substrate_index()` now produces (landed this session, PR 01-01). This is the "MANIFEST syncs wrong abstraction" gap named in the original sentinel-doorway-redesign ticket: two code paths deriving the same facts from the same scan, instead of one canonical index feeding both. Retarget `sync()` to consume the substrate index as its source of truth, and — since the index already carries a `breadcrumb_summary` per directory — surface that summary in each MANIFEST entry instead of a bare link, closing the "optional README writer from index summaries" half of PR 01-03 at the same time.
>
> Marked /nodelete: not applicable (net-new small DESIGN, not an existing governance document).

---

## Investigation (evidence, not assumption)

- `scripts/doorway/manifest.py:41-99` (`ManifestManager.sync()`): loops `current_map.items()`, checks `info.get("has_readme")`, builds `f"- [{display_name}](file://{abs_path}/) : [README](file://{abs_readme})"` per directory — no reference to `substrate_index.json` anywhere in the file.
- `scripts/doorway/auditor.py` (`build_substrate_index()`, landed PR 01-01, this session): already computes, per directory, `owner_ref`, `breadcrumb_summary`, `files_count`, `py_files`, `subdirs`, `has_readme`, `content_hash` — a strict superset of what `manifest.py` re-derives independently.
- `scripts/doorway/integrity.py:44-54,215,251-256` (`IntegrityManager.__init__`, `_is_readme_excluded`): **already** takes and respects `readme_exclude_dirs` (landed PR 01-00, this session). The "integrity.py... excludes" half of PILLAR_01 §10's PR 01-03 scope is **already satisfied** — no code change needed here. Recording this as an explicit finding rather than inventing unnecessary work.
- `scripts/doorway/doorway.py:157-172` (`DoorwayContextualizer.run()`): already computes `substrate_index` (Step 3.5, after the Tier-1 zero-finding calc) *before* Step 6 (`self.manifest_manager.sync(current_map)`) runs — meaning the substrate index is already available in scope at the exact point `sync()` is called. No reordering needed, only a signature change and a call-site update.

## Scope & Boundaries

**In scope:** `manifest.py`'s `sync()` signature and body (accept the substrate index dict, derive entries from `index["directories"]` instead of raw `current_map`); the one call site in `doorway.py` Step 6.
**Out of scope:** `integrity.py` (already correct, per Investigation above); `Architecture.md`'s Global API Map generation (`_update_api_map`, unrelated code path, untouched); any change to `substrate_index.json`'s own schema (PR 01-01, already landed and tested).

## Build Ingestion Manifest

- **Native gates mapping:** Build Audit 5a-5f (this file's own Acceptance Criteria below) + 5g `/continuous-verify` (forward contract: Stage 2/Stage 5 of the cluster's own tasks.md do not depend on this file's internals, so no forward-contract risk from prior Sovereign Redesign Cluster stages) + 5h `/divergence --convergence` (scoped to the 2 files touched).
- **Receipt:** `.workflow_state/receipts/BUILD_RECEIPTS.md`, standard `/execute-build` heredoc.
- **PR fidelity:** single PR, matches PILLAR_01 §10's PR 01-03 scope exactly (minus the already-satisfied integrity.py portion, documented above rather than silently dropped).

## Acceptance Criteria (measurable)

1. `ManifestManager.sync()` accepts the substrate index (or is called with it available) and builds MANIFEST.md entries from `index["directories"]`, not from re-derived `current_map` traversal.
2. Each MANIFEST.md auto-synced entry includes the directory's `breadcrumb_summary` from the index (truncated to a reasonable display length), not just a bare link.
3. `manifest.py`'s existing behavior is preserved where the index doesn't change the outcome: root-first sort, `governance/Architecture.md` Global API Map generation, graceful skip when `MANIFEST.md` doesn't exist.
4. No regression: `doorway.py`'s existing call site updates cleanly; all 238 existing tests continue to pass; new test coverage added for the retargeted `sync()`.
5. `integrity.py`: no code change (confirmed already correct); this criterion is "verify, don't touch."

## PR Plan

**PR 01-03 (single, small): Manifest index retarget**
- Files: `scripts/doorway/manifest.py` (retarget `sync()`), `scripts/doorway/doorway.py` (call-site update, Step 6), `scripts/tests/test_integration.py` or a new `test_manifest.py` (coverage for the retargeted method).
- Verification: py_compile, full test suite (238 baseline), manual run of `doorway.py --workspace .` confirming MANIFEST.md's auto-synced section now shows breadcrumb summaries.

---

## Review Pass (native, no Grok — self-critique per §15 Mock Trap guard)

**Critique 1:** Does "retarget to the index" risk losing the `has_readme`-gating behavior (only directories *with* a README get a MANIFEST entry today)? — Checked: `substrate_index["directories"]` includes ALL scanned directories with a `has_readme: bool` field per entry (per `auditor.build_substrate_index()`), so the retargeted `sync()` must filter on `v.get("has_readme")` from the index the same way the original filtered on `current_map`'s `info.get("has_readme")` — same gating logic, different data source. Addressed explicitly in the implementation task below, not left implicit.

**Critique 2:** Is "truncate breadcrumb_summary to a reasonable display length" vague enough to cause implementation drift? — Fixed: breadcrumb_summary strings in this codebase are already short, single-line, field-delimited (`FILES:N PY:M SUBDIRS:K ...`), per `build_substrate_index()`'s own format — no truncation logic is actually needed; display it verbatim. Corrected the Acceptance Criterion's phrasing mentally; the implementation will not add unneeded truncation code.

**Zero remaining open issues.** Ready for Stage 1 Task 1.2 (nested `/implementation-plan` run, direct to Phase 4 per the tasks.md shortcut note).
