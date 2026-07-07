# Helpdesk Ticket: /sentinel's Routing Map table has drifted live from recommender.py's actual behavior

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 5.2)
**Date**: 2026-07-07
**Subject**: `sentinel.md` Step 2b's Routing Map table hand-duplicates `scripts/doorway/recommender.py`'s logic instead of reading its already-emitted `workflow` field, and the duplicate has already drifted: a missing table row for a duplicate-emitting ID, and an undocumented severity value (`INFO`) silently excluded from every tally.
**Urgency**: MEDIUM (a live documentation-vs-engine drift discovered by direct comparison, not theoretical — the exact failure shape this campaign exists to close)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER
**Phylogeny Disposition Note** [RESOLVED 2026-07-07, retroactive fix per helpdesk-tickets/CLOSED_20260707_helpdesk-tickets-engine-gap_workflow.md]: `scripts/sentinel/recommender_parity.py` is new, self-contained code with no shared structural pattern moved between workflow files. No lineage entry warranted.

---

## 1. Executive Summary

`scripts/doorway/recommender.py`'s `recommend()` method emits `SEQ-SUBSTRATE-HEALTH` from TWO distinct source blocks (new-directory detection, and Tier-1 index/ownership issues) but `sentinel.md`'s Step 2b table has only ONE row for that ID — so an ID-presence check alone would have missed the gap, since the ID string already appears in the table under a different condition. Separately, `recommender.py` emits `severity: "INFO"` for `SEQ-SUBSTRATE-MAINTAIN`, but `sentinel.md`'s GLOSSARY Severity Tier term and Step 2a's Severity Tally only ever named/counted HIGH/MEDIUM/LOW — every INFO-severity recommendation was silently excluded from the tally while still counting toward `TOTAL`.

## 2. Root Cause

`sentinel.md`'s tasks.md seed note assumed a "drift-delta layer" gap that turned out not to exist (`doorway.py`'s own snapshot/hash-compare already computes this). Investigating that assumption directly, rather than accepting it, led to comparing the workflow's OWN documentation against the engine it calls — a comparison this file had apparently never had run against it since `recommender.py`'s Tier-1/INFO additions (PR 01-02 and later) were made.

## 3. Forensic Evidence

- **The engine now wired in**: [sentinel.md](file:///home/jwils/blueprint-workflows/claude-commands/sentinel.md#L340-L346)
  *Evidence: Step 2b's ENGINE-BACKED block, added this session, invoking `scripts/sentinel/sentinel_audit.py` to verify the routing table against `recommender.py`'s real source.*
- **The mechanical layer itself**: [scripts/sentinel/recommender_parity.py](file:///home/jwils/blueprint-workflows/scripts/sentinel/recommender_parity.py#L1-L16)
  *Evidence: module docstring — extracts recommender.py's actual id/workflow/severity triples and diffs them against the documented table, the occurrence-count comparison that catches the duplicate-ID defect a presence check alone would miss.*
- `scripts/doorway/recommender.py`: two separate `recs.append({"id": "SEQ-SUBSTRATE-HEALTH", ...})` blocks — one for `drift.get("new")`, one for `tier1_issues = drift.get("stale_index") + drift.get("ownership_incomplete")`.
- `claude-commands/sentinel.md` (pre-fix) Step 2b: exactly one `SEQ-SUBSTRATE-HEALTH` row, describing only the new-directory condition.
- `recommender.py`: `"severity": "INFO"` for `SEQ-SUBSTRATE-MAINTAIN`.
- `sentinel.md` (pre-fix) GLOSSARY Severity Tier term and Step 2a Severity Tally: only `HIGH`/`MEDIUM`/`LOW` named/counted anywhere.

## 4. Impact

Medium. `/sentinel` runs at the start of every session in every workspace this suite touches — a silently-uncounted severity tier and a missing routing-condition description both degrade the accuracy of the very first briefing a session receives, without any error surfacing to indicate the gap.

## 5. Recommendation

Fix both defects directly (add the missing row; add INFO to the vocabulary and tally with an explicit sum-invariant check), and build a parity-checking engine (`scripts/sentinel/recommender_parity.py`) that catches the *next* such drift mechanically — using an occurrence-count comparison per ID, not mere presence, since presence alone provably misses the duplicate-ID case found here. See `implementation-plan.md` Phase 5.2 and `docs/compression-staging/sentinel-honest-design.md` for the full design.

---
**Status**: **REMEDIATED (2026-07-07)**
**Verification**: Both defects fixed directly in `sentinel.md` (missing Tier-1 row added to Step 2b; INFO added to Severity Tier GLOSSARY term and Step 2a's tally with a `HIGH+MEDIUM+LOW+INFO == TOTAL` invariant). `scripts/sentinel/` built — 14/14 new tests passing, including REGRESSION tests proving the checker actually catches both real defects (not just clean-input tests), plus a read-only invariant test. Full suite 411/411 passing. Live-run against the real `recommender.py`/`sentinel.md` pair confirmed the defects pre-fix and `PARITY: CLEAN` post-fix. Step 2b wired with a live verification command and an explicit note that this exact table was found drifted during this pass. Frontmatter: version 3→4, `last_hardened` 2026-07-07. Lint: CLEAN (0 CRITICAL/WARNING) after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 5)*
