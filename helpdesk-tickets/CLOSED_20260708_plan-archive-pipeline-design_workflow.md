# Helpdesk Ticket: Plan-Archive Pipeline Design Gap — Machine Header Discipline Missing

**To**: Senior Architect of Workflows
**From**: Antigravity (Claude Sonnet 4.6) / Session 9a6e90a5
**Date**: 2026-07-08
**Subject**: `/implementation-plan`, `/execute-build`, `/nodelete` lack a machine header discipline contract — phase headers contaminated with human annotations break receipt matching, preventing `--audit` Completion Marking and `--archive` Archival Mode from functioning across both workspaces.
**Urgency**: CRITICAL (Architectural)
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: NO TRANSFER
**Phylogeny Disposition Note**: This ticket represents updates to existing files in-place: scripts/focus/phase_status.py, claude-commands/nodelete.md, claude-commands/execute-build.md, and claude-commands/implementation-plan.md. No structural templates or code pattern cloning occurred between workflow files.

---

## 1. Executive Summary

When `/implementation-plan` writes a `## Phase N` header, it has no rule telling it that this string becomes a machine key consumed 100 steps later by `scripts/focus/phase_status.py`. As a result, agents freely append human-readable status annotations (e.g., `**READY FOR HANDOFF**`, `(handoff: Gemini)`) directly into the header line. `/execute-build` then reads that annotated header as `<ACTIVE_PHASE>` and writes it verbatim into `BUILD_RECEIPTS.md`. `phase_status.py`'s normalized exact-match then fails against the differently-annotated or differently-abbreviated receipt title, producing `receipt_status: not_found` for every affected phase. Both `/implementation-plan --audit`'s Completion Marking sub-pass and `/nodelete --archive`'s Pillar 6 gate correctly refuse to act on `not_found` — but this means verified-complete work can never be marked or archived without a design fix. Confirmed across both `blueprint-workflows` (10/10 phases `not_found`) and `Videos` workspace (Phase 8.2 `not_found`). Additionally, `/nodelete --archive` performs single-surface archival only (`tasks.md`), leaving `implementation-plan.md`'s matching phase section untouched even when the phase is confirmed complete.

## 2. Root Cause Analysis: "Missing Machine Contract at Design Time"

**The How**: `/implementation-plan` generates tasks.md phase headers with inline human annotations baked into the `## Phase N —` line itself. `/execute-build` reads the Phase Map from `phase_status.py`, which extracts header titles as-written (including all annotations), and writes them verbatim into `BUILD_RECEIPTS.md`'s `Phase/Stage:` field. `phase_status.py`'s `_normalize()` function strips punctuation and whitespace but not annotation words — so `"Phase 1 — Quick Wins — **READY FOR HANDOFF**"` normalizes to `"phase 1 quick wins ready for handoff"` while the receipt has `"phase 1 quick wins"`. No match.

**The Why**: Three workflows — `/implementation-plan`, `/execute-build`, and `phase_status.py` — form an implicit pipeline where a string written by one is read as a machine key by another. None of the three documents this constraint. `/implementation-plan` has no STRICT RULE prohibiting header-line annotations. `/execute-build` has no rule requiring annotation-stripping before writing `<ACTIVE_PHASE name>` to the receipt. `phase_status.py`'s own docstring correctly documents its "normalized exact string match" but gives no guidance to upstream writers about what the key must look like. The machine contract was never stated at the point where it matters — during plan creation.

**Secondary root cause (confirmed, same class):** `/nodelete` Pillar 6 recognizes only `tasks.md` as a receipt-verifiable surface. `implementation-plan.md`, which shares identical `## Phase N` nomenclature in this workspace format, is demoted to the fallback branch (no receipt infrastructure). When a phase is archived, only `tasks.md` is cleaned; `implementation-plan.md` retains the completed phase text, leaving a dual-surface inconsistency the user experiences as "the plan never gets cleaned up."

## 3. Forensic Evidence

- **[Header annotation pattern — blueprint-workflows]**: [tasks.md](file:///home/jwils/blueprint-workflows/tasks.md#L1-L45)
  *Evidence: All 10 `## Phase N` headers carry inline bold annotations (`**READY FOR HANDOFF**`, `**COMPLETE 2026-07-07**`) appended to the header line itself. Phase 4 header runs to 160+ characters with elaborating parenthetical.*

- **[Receipt titles — abbreviated, not matching headers]**: [BUILD_RECEIPTS.md](file:///home/jwils/blueprint-workflows/.workflow_state/receipts/BUILD_RECEIPTS.md#L1-L50)
  *Evidence: Receipt `Phase/Stage:` values are `"Phase 1 — Quick Wins"`, `"Phase 2a"`, `"Phase 10"` — abbreviated or pre-annotation versions that no longer match the annotated tasks.md headers. Confirmed via live `phase_status.py --output-json`: all 10 phases report `receipt_status: not_found`.*

- **[Normalization function — the matching key logic]**: [phase_status.py](file:///home/jwils/blueprint-workflows/scripts/focus/phase_status.py#L88-L90)
  *Evidence: `_normalize()` strips non-alphanumeric characters but preserves all words — annotation words (READY, FOR, HANDOFF, COMPLETE) survive normalization and prevent the match.*

- **[`<ACTIVE_PHASE>` sourcing in execute-build]**: [execute-build.md](file:///home/jwils/blueprint-workflows/claude-commands/execute-build.md#L126)
  *Evidence: `"Store the active phase as: <ACTIVE_PHASE>"` — sourced directly from the Phase Map output, which is the tasks.md header as-written. No stripping instruction exists before Phase 6's receipt write at line 394.*

- **[Receipt write instruction — verbatim header]**: [execute-build.md](file:///home/jwils/blueprint-workflows/claude-commands/execute-build.md#L394)
  *Evidence: `"- Phase/Stage: <ACTIVE_PHASE name>"` — no annotation-stripping instruction. Whatever annotation is in the header goes into the receipt.*

- **[Videos workspace — same pattern, different annotation style]**: [tasks.md (Videos)](file:///home/jwils/Videos/tasks.md#L30)
  *Evidence: `"### Phase 8.2: Chunking Structural Fix + Module Extraction (handoff: Gemini)"` — parenthetical annotation in header. Receipt has `"Phase 8.2: Chunking Structural Fix + Module Extraction"`. Result: `receipt_status: not_found` confirmed live.*

- **[Videos workspace — correct pattern (accidental)]**: [tasks.md (Videos)](file:///home/jwils/Videos/tasks.md#L7-L8)
  *Evidence: Phase 8 and 8.1 headers are CLEAN (no inline annotation). `COMPLETED [ARCHIVE:2026-07-07]` marker is on the body line below the header, not in the header. Result: `receipt_status: found_complete` for both. This is the correct pattern; Phase 8.2 accidentally deviated.*

- **[Pillar 6 tasks.md-only scope]**: [nodelete.md](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L206-L207)
  *Evidence: Pillar 6's verification gate is explicitly restricted to "For a `tasks.md` phase specifically" with `implementation-plan.md` relegated to the "no receipt infrastructure" fallback branch — ignoring the shared Phase N nomenclature.*

## 4. Remediation: Four Coordinated Fixes (Implementation in Progress)

This is a meta ticket governing three sibling remediation units:

**Sibling A — Machine Header Discipline STRICT RULE in `/implementation-plan` (STRICT RULE 28):**
Add a rule: the `## Phase N` header line contains ONLY the canonical phase name. All human status annotations (`**READY FOR HANDOFF**`, `**COMPLETE YYYY-MM-DD**`) and delegation notes (`(handoff: Agent)`) go on a separate body line immediately below the header, never appended to the header line itself. Reason stated in the rule: this line is the machine key consumed by `phase_status.py`.

**Sibling B — `<ACTIVE_PHASE>` canonical sourcing in `/execute-build`:**
Add a STRICT RULE: when writing `Phase/Stage:` in BUILD_RECEIPTS.md (Step 6), strip bold markdown annotations (`**...**`) from the stored `<ACTIVE_PHASE name>` before writing. Do not invent abbreviated phase names; use the full tasks.md header with decorations stripped.

**Sibling C — Annotation resilience in `phase_status.py`:**
Strip bold markdown annotations from both sides of the normalized match before comparison. Add a second-pass parenthetical-strip for legacy headers, reporting `found_complete_approx` to distinguish from a clean exact match. Add regression tests.

**Sibling D — Dual-surface Archival in `/nodelete` Pillar 6:**
When `phase_status.py` confirms Phase N complete, archive Phase N from both `tasks.md` AND `implementation-plan.md` simultaneously, each to its own `.history/archive/` ledger. Verify Phase N header exists in `implementation-plan.md` before stripping; fire Intent-Mismatch Gate if absent.

**Retroactive — tasks.md header cleanup (blueprint-workflows):**
One-time manual pass to relocate existing inline annotations from the header line to the body line for all 10 phases in `tasks.md`. This is not automated — each header requires judgment about the canonical name boundary.

## 5. Recommendation to Senior Architect

Add STRICT RULE 28 to `/implementation-plan` establishing that `## Phase N` header lines are machine keys and must contain only the canonical phase name. This is the highest-leverage fix: it closes the contract gap at the source, preventing every future instance of this failure class across all plans in all workspaces, without requiring downstream regex maintenance. Mirror the constraint in `/execute-build`'s receipt-writing step. The `phase_status.py` resilience layer (Sibling C) provides defense-in-depth for legacy headers but must not be treated as the primary fix — normalizing away annotation words teaches the system to tolerate header pollution rather than prevent it.

---
**Status**: **REMEDIATED (implemented Sibling A, B, C, D fixes and retroactive cleanup)**
**Verification**: REMEDIATED and fully verified.
- Sibling A: STRICT RULE 28 injected into `/implementation-plan` and version bumped to 7.
- Sibling B: STRICT RULE 19 injected into `/execute-build` and version bumped to 6.
- Sibling C: Resilience layer and `found_complete_approx` fallback matching added to `scripts/focus/phase_status.py`. Added 3 new unit tests to `scripts/tests/test_phase_status.py`, which all pass. Total tests run increased from 463 to 466.
- Sibling D: Dual-Surface Archival rules added to `/nodelete` Pillar 6 and STRICT RULE 14. Version bumped to 8.
- Retroactive: Cleaned up inline annotations in `blueprint-workflows` and `Videos` workspaces. Verified via `phase_status.py --output-json` that all target phases in `Videos` resolve to complete and receipts-matched.

---
*Signed,*
**Antigravity (Claude Sonnet 4.6)**
*(Sovereign Helpdesk Analyst / Session 9a6e90a5)*
