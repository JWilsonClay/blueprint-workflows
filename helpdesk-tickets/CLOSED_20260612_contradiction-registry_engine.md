# Helpdesk Ticket: Structural Gap — No Central Aggregator for Per-Workspace `.history/` Learning (Build the Contradiction Registry as a Deterministic Engine)

**To**: Senior Architect of Workflows
**From**: Claude (Opus 4.8) / blueprint-workflows session 2026-06-12 — three-body reconciliation
**Date**: 2026-06-12
**Subject**: The new `.history/` ledgers are per-workspace, write-only, and ingestion-banned — so suite-wide fail-patterns are invisible. Build a deterministic `registry.py` engine to aggregate them and surface recurring patterns.
**Urgency**: MEDIUM (scoped backlog build — addresses a demonstrated pain class, but not an active failure)

---

## 1. Executive Summary
The `/nodelete` rework (2026-06-12) mandated a `.history/<file>.ledger.md` in **every workspace at its own root**, write-only and ingestion-banned. This is correct for local audit memory, but it means every workspace silently accumulates a record of *what was removed and why* that **nothing ever reads across workspaces**. There is no central aggregator, so a contradiction or removal pattern that recurs across many projects (exactly the class of problem that produced this session's cross-workspace "never-delete ghost" contamination) is structurally invisible. This ticket scopes a deterministic engine to close that gap.

## 2. Root Cause Analysis: "Structural Gap — Evidence Without a Detective"
- **The How**: `.history/` ledgers are deliberately per-workspace and runtime-ingestion-banned. No workflow or script aggregates them, computes a delta, or scans for recurring patterns. The learning they contain is real but inert.
- **The Why**: The suite has deterministic *verification* engines (`doorway.py`, `focus.py`, `quality_audit.py`, `lint_workflows.py`) but no *learning-aggregation* engine. The first attempt at a learning ledger — the "Contradiction Registry" feature inside `/depreciate` (2026-05-12 Divergence #1) — failed because it was **LLM-authored prose appended to a file that never existed**, making it untrustworthy and unused. It is being pruned in this same session. The gap it tried to fill remains.

## 3. Forensic Evidence
- **Per-workspace ledger, no central store**: [nodelete.md L145](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L145)
  *Evidence: "a `.history/` directory at the workspace root … in every workspace" — confirms decentralized, siloed storage; no central ledger.*
- **Ingestion ban + sanctioned audit-read carve-out**: [nodelete.md L229](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L229)
  *Evidence: ledgers are write-only at runtime but may be read "on explicit human request or a deliberately invoked audit" — a scripted aggregator is exactly that sanctioned audit-read, so the engine does not violate the ban.*
- **Failed first attempt (being pruned)**: [depreciate.md GLOSSARY — Contradiction Registry](file:///home/jwils/blueprint-workflows/claude-commands/depreciate.md)
  *Evidence: the original LLM-authored registry wrote to `manifest/CONTRADICTION_REGISTRY.md`, which never existed on disk (verified absent 2026-06-12) — Ghost Logic; never used.*
- **Existing deterministic-engine pattern to mirror**: [scripts/quality/quality_audit.py](file:///home/jwils/blueprint-workflows/scripts/quality/quality_audit.py) and `scripts/doorway/`, `scripts/focus/`
  *Evidence: established suite pattern — a read-only Python engine produces machine-readable output the LLM interprets; the registry should be a sibling of these.*

## 4. Remediation: Build `scripts/registry/registry.py` (deterministic learning-aggregation engine)
1. **Aggregate (deterministic, no LLM authoring):** scan per-workspace `.history/*.ledger.md` files + the helpdesk-ticket history (the 26 closed/archived tickets are immediate signal) and categorize removals/contradictions/ghost-remediations by pattern into a central `manifest/CONTRADICTION_REGISTRY.md`.
2. **Compute the delta:** maintain a reviewed-watermark; each run reports "N new entries since last review" + top recurring patterns, as machine-readable JSON.
3. **Threshold attention:** small delta (e.g., < 10) → silent; large delta (e.g., ≥ 50, tunable) → "pattern review warranted." The LLM then ingests the aggregate, judges whether a real recurring fail-pattern exists, and if significant **auto-files a `/helpdesk-tickets` entry** — closing the loop into the existing pipeline.
4. **Hook into a frequent invocation:** call the engine from `/harden-workflow --tickets` (frequent, architect-run) so it runs ambiently — no `--registry` flag a human must remember.
5. **Honor the architecture:** read-only engine; the LLM never authors the ledger (avoids Hallucinated Success); the scripted aggregation IS the sanctioned deliberate audit-read (does not breach the ingestion ban).

## 5. Recommendation to Senior Architect
Build the registry as a **deterministic engine, not a workflow step** — it lives in `scripts/registry/` with a single hook in `/harden-workflow --tickets`, keeping `/depreciate` and the other workflows free of it. This is the structural fix for the broader pattern the suite repeatedly hits: *learning artifacts authored by the LLM are untrustworthy and go unused; learning artifacts computed by a deterministic engine and merely interpreted by the LLM are trustworthy and get acted on.* Scope it as its own focused build session; it can ship against the existing 26-ticket corpus immediately and grow as `.history/` ledgers populate.

---
**Status**: **REMEDIATED (registry.py built, tested, wired, validated)**
**Verification**: COMPLETE — Built 2026-06-12. `scripts/registry/` (registry.py CLI + aggregator + reporter + _utils) with 9 passing unit tests (`scripts/tests/test_registry.py`). Wired into `/harden-workflow --tickets` as **Step TM-6** (STRICT RULE 21). Live run against the real corpus produced a valid registry (`manifest/CONTRADICTION_REGISTRY.md` — 29 events, REVIEW verdict) and is idempotent on re-run. Deterministic engine-authored aggregation (never LLM-authored — no Hallucinated Success).

---
*Signed,*
**Claude (Opus 4.8)**
*(acting Senior Architect of Workflows, this session)*
