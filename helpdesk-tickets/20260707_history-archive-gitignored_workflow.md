# Helpdesk Ticket: `.history/archive/` was silently gitignored, contradicting nodelete.md Pillar 6's own design

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Redesign Cluster Stage 6 Task 6.2 — discovered while committing the first-ever real `/nodelete --archive` entry)
**Date**: 2026-07-07
**Subject**: `.gitignore`'s bare `.history/` pattern (both a top-level line and the auto-generated managed block's `[categories.suite]` entry) blocked the entire `.history/` tree from git, including `.history/archive/` — the Archival Ledger `nodelete.md` Pillar 6 (built 2026-07-04) explicitly designed as NOT ingestion-banned and meant to be a durable, human-readable, permanent record, distinct from `.history/quarantine/` (the actual ingestion-banned ledger).
**Urgency**: LOW (caught before any real archival content was lost — this session's own first-ever archive entry was the trigger for finding it, not a casualty of it; same category as the Stage 4 gitignore finding, smaller blast radius)
**Root Cause Type**: STRUCTURAL (repo/tooling configuration gap — `scripts/gitignore/seed.toml` + its `config.py` fallback mirror, not application logic)
**Phylogeny Disposition**: `NO TRANSFER` — same class of defect as the Stage 4 finding (`helpdesk-tickets/20260706_gitignore-untracked-self-and-ledgers_workflow.md`) but a different root cause (this one is the gitignore-seeder's own seed config being written before Pillar 6's archive/quarantine split existed, not the earlier finding's self-referential-rule/never-tracked issue) — noted as a pattern worth watching, not a structural transfer between workflow `.md` files.
**Status**: REMEDIATED
**Verification**: `git check-ignore -v .history/archive/<any-file>` → no match (was ignored via `.gitignore:15:quarantine/` — no, corrected: was `.history/`, now excluded correctly); `git check-ignore -v .history/quarantine/<any-file>` → still matches (`quarantine/` pattern). Full suite 295/295, `scripts/tests/test_gitignore.py` 15/15 unaffected (its `.history/` substring assertion still holds against the narrower `.history/quarantine/` pattern).

---

## 1. Executive Summary

Committing this session's own first-ever `/nodelete --archive` entry (`.history/archive/pr-06-02-tasks.md.ledger.md`) failed silently the same way Stage 4's ticket described for helpdesk tickets: `git status` never surfaced the new file as untracked-and-addable in a way that stood out, because the entire `.history/` tree — including `archive/` — was gitignored by both a legacy top-level `.gitignore` line and the auto-generated managed block's `[categories.suite]` entry (title: "Suite-generated / ingestion-banned (never tracked)").

## 2. Root Cause

The managed block's category title conflates two things `nodelete.md` Pillar 6 (added 2026-07-04, after the gitignore seeder's own `seed.toml` was last touched for this pattern) deliberately distinguishes: `.history/quarantine/` genuinely is ingestion-banned (write-only at runtime, never re-read); `.history/archive/` is explicitly the opposite — "Human-readable, **not** ingestion-banned... Retention Contract: Append-Only Ledger" (`nodelete.md` line 214). The seed config's bare `.history/` pattern predates that split and was never narrowed when Pillar 6 introduced it.

## 3. Evidence

- `scripts/gitignore/seed.toml` (pre-fix): `patterns = [".history/", "quarantine/", ...]` under `[categories.suite]`, titled "ingestion-banned (never tracked)".
- `scripts/gitignore/config.py`'s `DEFAULT_SEED` (pre-fix): identical bare `.history/`, explicitly documented as mirroring `seed.toml`.
- `.gitignore` (pre-fix): bare `.history/` present both as a standalone top-level line (line 9, predates the managed block, untouched by the Stage 4 fix since that fix's scope was the ticket-blocking and `process_learnings/*` rules specifically) and inside the managed block.
- `claude-commands/nodelete.md` lines 190-220 (Pillar 6): explicit `archive/` vs `quarantine/` distinction, "not ingestion-banned" stated directly for archive.
- `.history/archive/` existed on disk since 2026-07-04 (Pillar 6's creation) but had zero entries until this session's Task 6.2 — meaning this gap was latent and untested the entire time, exactly like the Stage 4 finding (nobody had exercised the archival path for real before now).

## 4. Impact

Low, self-contained, already fixed. No archival content was actually lost — this ticket's own trigger was discovering the gap while committing the very first entry, not recovering from a loss. The risk was forward-looking: every future `/nodelete --archive` invocation would have kept producing entries nobody could see in git history, the same "looks durable, isn't" gap Stage 4 found for `PROCESS_LEARNINGS.md` and helpdesk tickets.

## 5. Recommendation (already executed)

1. `scripts/gitignore/seed.toml`: narrowed `.history/` → `.history/quarantine/` under `[categories.suite]`, with an inline comment citing `nodelete.md` Pillar 6's own archive/quarantine distinction.
2. `scripts/gitignore/config.py`'s `DEFAULT_SEED`: mirrored the same narrowing (kept in sync per that dict's own stated contract).
3. Re-ran the actual seeder (`gitignore_seeder.py --workspace .`) against this real workspace rather than hand-editing the managed block — regenerated it deterministically from the corrected config, consistent with the block's own "never edit between the markers" rule.
4. Removed the redundant top-level `.history/` line (predated the managed block; the managed block's now-correct `.history/quarantine/` entry supersedes it — no need for both).
5. Verified `git check-ignore` on both subdirectories directly, not inferred from reading the pattern.
6. Committed `.history/archive/pr-06-02-tasks.md.ledger.md` (the actual triggering content) in the same commit as this fix.

## 6. References

- `scripts/gitignore/seed.toml`, `scripts/gitignore/config.py` (the fix).
- `claude-commands/nodelete.md` lines 190-220 (Pillar 6, the design this gitignore rule contradicted).
- `helpdesk-tickets/20260706_gitignore-untracked-self-and-ledgers_workflow.md` (the analogous Stage 4 finding — different root cause, same failure shape: a "permanent" record silently living outside git).
- `implementation-plan/sovereign-redesign-cluster/tasks.md` Stage 6 Task 6.2 (the work this finding emerged from — the pipeline's own capstone archival step).
