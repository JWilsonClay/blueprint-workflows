# Helpdesk Ticket: A nested PR-plan's own tasks.md is never receipted under its own exact title

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Redesign Cluster, Stage 5 Task 5.5 — discovered while preparing the Completion Marking sub-pass's real-data verification)
**Date**: 2026-07-07
**Subject**: When `/execute-build`'s Native Execution Trigger (PILLAR_03 §15) spawns a nested `tasks.md` from a DESIGN's `## PR Plan`, but the actual `/execute-build` run is invoked against the *outer* (master) `tasks.md` that subsumed it, the resulting `BUILD_RECEIPTS.md` entry carries the outer stage's title — never the nested file's own `Phase N` title. `scripts/focus/phase_status.py`, run directly against the nested file, correctly (by its own documented design) reports `receipt_status: not_found` for that phase, even though the underlying work is genuinely complete and receipted — just under a different, outer title.
**Urgency**: LOW (a conservative false-negative — the affected code path refuses to mark rather than mis-marking; no risk of a false COMPLETED marker)
**Root Cause Type**: STRUCTURAL (a workflow-protocol/convention gap in how `/execute-build`'s Native Execution Trigger handles nested-tasks.md receipt-writing — not a `phase_status.py` code defect; its exact-title matching is working exactly as documented)
**Phylogeny Disposition**: PENDING
**Status**: OPEN
**Verification**: PENDING — see Recommendation.

---

## 1. Executive Summary

While preparing Sovereign Redesign Cluster Stage 5 Task 5.5 (real-data verification of the new Completion Marking sub-pass, `implementation-plan.md` Phase 5), the intended demonstration target — `.workflow_state/pr-01-03-tasks.md`, Stage 1's real, already-completed prototype — was checked directly against `scripts/focus/phase_status.py`. Result: `status=not_started` (its own checkboxes were never flipped to `[x]` — a separate, smaller finding, corrected directly as part of this same stage) AND `receipt_status=not_found`, despite PR 01-03 being genuinely, verifiably complete (Stage 1's own real Phase Build Receipt, commit `de82e10`, 239/239 tests passing at the time).

## 2. Root Cause

`scripts/focus/phase_status.py`'s `_receipt_status_for()` does an exact, normalized-string match between a `tasks.md` phase's own title and `BUILD_RECEIPTS.md` entries' `Phase/Stage:` values (by design — see that module's own docstring: "safe to do mechanically... because both strings originate from the same `<ACTIVE_PHASE name>` in the same `/execute-build` run"). That precondition genuinely held for every phase in *this* stage's own work. It does **not** hold for a nested PR-plan's own `tasks.md`: `/execute-build` was invoked against the *master* `implementation-plan/sovereign-redesign-cluster/tasks.md`'s "Stage 1" entry, which subsumed `.workflow_state/pr-01-03-tasks.md`'s own "Phase 1 — Retarget manifest.py" as inner work — no `/execute-build` run was ever invoked *directly* against the nested file, so no receipt was ever written under its own exact title. Confirmed empirically:

```
$ phase_status.py against .workflow_state/pr-01-03-tasks.md
'Phase 1 — Retarget manifest.py' -> status=not_started receipt_status=not_found

$ phase_status.py against implementation-plan/sovereign-redesign-cluster/tasks.md
'Stage 1 — Prototype Pass (...)' -> status=complete receipt_status=found_complete
```

Both are correct outputs for what each file actually contains — the gap is architectural (no convention for cross-referencing a nested file's completion to its outer receipt), not a bug in either the parser or the matcher.

## 3. Evidence

- `.workflow_state/pr-01-03-tasks.md` (gitignored, local) — its own "Phase 1" title never appears as a `Phase/Stage:` value anywhere in `.workflow_state/receipts/BUILD_RECEIPTS.md`.
- Same shape confirmed for Stage 4's own nested plan, `.workflow_state/pr-05-04-tasks.md` — its "Phase 1"/"Phase 2" titles are likewise absent from `BUILD_RECEIPTS.md`; only the master tasks.md's "Stage 4" title was ever receipted. This is not a one-off — it is the general shape of every nested tasks.md produced by the Native Execution Trigger so far.
- `claude-commands/implementation-plan.md` Phase 5's new Completion Marking sub-pass (Sovereign Redesign Cluster Stage 5, Task 5.1) names this exact limitation inline in its own text (point 4) rather than silently working around it — this ticket is the referenced "specific finding."

## 4. Impact

Low, and safely-directioned. The Completion Marking sub-pass, run against a nested tasks.md directly, will correctly *refuse* to mark a genuinely-complete unit (a false negative — the safe failure direction) rather than mark something unverified (a false positive). The practical consequence is narrower than it sounds: the sub-pass is meant to run against a workspace's *governing* tasks.md, and a nested PR-plan file is transient scratch state under `.workflow_state/` (gitignored, not meant to be a long-lived archival surface) — so in practice this ticket documents a known boundary of the tool's applicability, not a defect that blocks its primary use case.

## 5. Recommendation

Not urgent enough to fix as part of this stage (out of Task 5.1's stated scope, which is the marking sub-pass itself, not a receipt-writing convention change). Two directions worth considering later, not decided here:
1. When `/execute-build`'s Native Execution Trigger completes a phase that maps to a nested tasks.md, also write a second receipt entry under the nested file's own exact title (redundant but closes the gap without changing `phase_status.py`'s matching contract).
2. Accept the current shape as correct-by-design and document explicitly (in `phase_status.py`'s own docstring and/or `nodelete.md` Pillar 6) that nested PR-plan tasks.md files are not intended Completion-Marking targets — only a workspace's governing tasks.md is.

## 6. References

- `scripts/focus/phase_status.py` (`_receipt_status_for`, module docstring's own stated precondition).
- `.workflow_state/pr-01-03-tasks.md`, `.workflow_state/pr-05-04-tasks.md` (both gitignored, local — the two real instances of this shape).
- `.workflow_state/receipts/BUILD_RECEIPTS.md` (Stage 1 and Stage 4 entries, titled by the master tasks.md's stage names, not the nested files' own titles).
- `claude-commands/implementation-plan.md` Phase 5, Completion Marking Sub-Pass, point 4 (names this limitation inline).
- `implementation-plan/sovereign-redesign-cluster/tasks.md` Stage 5 Task 5.5 (the work this finding emerged from).
