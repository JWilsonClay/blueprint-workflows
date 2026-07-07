# Helpdesk Ticket: `.gitignore` was never tracked in git, and two of its rules silently blocked the suite's own append-only ledgers

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Redesign Cluster, Stage 4 Task 4.4 — discovered while investigating why a new helpdesk ticket wouldn't `git add`)
**Date**: 2026-07-06
**Subject**: `.gitignore` itself was untracked (never committed, in any prior session) — a fresh clone of this public repo would receive zero secrets protection. Two of its rules also silently excluded 9 open helpdesk tickets, 11 already-closed-but-not-yet-archived tickets, and the entire `process_learnings/` directory (including `PROCESS_LEARNINGS.md`, the suite's canonical append-only learning ledger) from ever being committed.
**Urgency**: HIGH (public-repo secrets-protection gap + silent loss-of-durability risk for two records the suite treats as permanent)
**Root Cause Type**: STRUCTURAL (repo configuration / governance gap — not workflow `.md` structure, not application code logic; remediated directly rather than via `/harden-workflow` since no workflow file is at fault)
**Phylogeny Disposition**: `NO TRANSFER` — a repo-configuration correction (three over-broad `.gitignore` rules narrowed), not a structural pattern that moved between workflow `.md` files. **[RESOLVED 2026-07-07]**
**Status**: REMEDIATED (fixed in the same commit that files this ticket)
**Verification**: See the commit this ticket ships in — `.gitignore` corrected, all newly-unblocked files added, secret-scanned first (see Section 3).

---

## 1. Executive Summary

While trying to `git add` a brand-new helpdesk ticket (`20260706_check-glossary-usage-divider-bug_workflow.md`), the add was silently rejected as gitignored. Tracing the matching rule (`helpdesk-tickets/*workflow*.md`) led to three escalating discoveries:

1. That rule (plus its sibling `helpdesk-tickets/*script*.md`) blocks essentially every ticket filename in this repo's own naming convention — confirmed empirically: `git ls-files helpdesk-tickets/*.md` returned only ONE non-archived, non-`CLOSED_` ticket (this session's own meta ticket, which became tracked via a branch merge, not a fresh `git add`). Every other currently-open ticket, and 11 `CLOSED_*` tickets still sitting in the root directory (not yet swept to `archive/` by `/harden-workflow`'s TM-5 step), had **never** been part of git history.
2. `process_learnings/*` (a flat, un-narrowed directory exclusion) did the same to `process_learnings/PROCESS_LEARNINGS.md` — the file `~/.claude/CLAUDE.md` names explicitly as one of only two files in the entire suite that are "Append-Only" and "never overwritten." 55KB of accumulated retrospective content existed only on local disk.
3. Most significantly: `.gitignore` **itself** was never tracked (`git ls-files .gitignore` → blank; `git show HEAD:.gitignore` → `fatal: no such path in HEAD`). It contained a self-referential rule (`.gitignore` as its own line 6), which hid it from ever showing up as untracked in routine `git status`/`git add -A` review — the exact mechanism made it invisible to the review process that would normally catch this. Since this repo is public GitHub, a fresh clone would receive **no `.gitignore` at all**, meaning the "NEVER commit" secrets block (`.env`, `*.key`, `*.pem`, `id_rsa*`, `credentials*.json`, `service-account*.json`, `.aws/`) was never actually shared or version-controlled — it only ever worked because this one local working tree happened to have the file sitting unstaged.

## 2. Root Cause

`.gitignore` line 6 read `.gitignore` (self-exclusion). Lines 7-9 read `process_learnings/*`, `helpdesk-tickets/*workflow*.md`, `helpdesk-tickets/*script*.md`. No commit in this repository's history (85 commits checked via `git log --oneline -- .gitignore`, which returns empty) ever added `.gitignore` to the index. Origin of the three over-broad rules is not recoverable from git history since the file predates its own tracking; `scripts/gitignore/` (the gitignore-seeder module) was checked and does not reference any of these three patterns, ruling it out as the source.

## 3. Evidence

- `git ls-files .gitignore` → empty. `git check-ignore -v .gitignore` → `.gitignore:6:.gitignore	.gitignore` (self-match).
- `git ls-files helpdesk-tickets/*.md | grep -v CLOSED_ | grep -v archive` → exactly one file (this session's meta ticket), against 9 actually-open tickets on disk.
- `git ls-files process_learnings/` → empty, against 2 files on disk (`PROCESS_LEARNINGS.md`, `README.md`).
- Secret scan run against all 24 newly-surfaced files (`grep -liE "api[_-]?key|secret|password|token\s*[:=]|sk-[a-zA-Z0-9]{10,}|ssh-rsa|BEGIN.*PRIVATE KEY|AKIA[0-9A-Z]{16}"`) before staging: 4 files matched on the substring `secret` — all four were false positives, every match was the workflow name `/secretary`. No actual credentials found. A second scan confirmed no currently-tracked file in the whole repo matches common secret-file patterns (`.env*`, `*.key`, `*.pem`, `id_rsa*`, `credentials*.json`, `service-account*.json`) — the gap was real but no actual secret leak resulted from it.

## 4. Impact

- **Public-repo exposure risk (the serious part):** any collaborator or future-you cloning this repo fresh gets zero `.gitignore`. The very first `git add -A` on a fresh clone would offer up `.env`, keys, and credentials for commit with no automatic protection. This is a live risk for a repo confirmed public on GitHub, not a hypothetical.
- **Durability risk for named permanent records:** `PROCESS_LEARNINGS.md` (append-only, cross-session institutional memory) and the open-ticket corpus (the suite's own audit trail, and the mandatory session-start read per `~/.claude/CLAUDE.md`) were one lost/corrupted local disk away from being unrecoverable — despite the suite's architecture assuming git is the durable substrate for exactly this content.
- **Why it went unnoticed so long:** the self-referential rule made `.gitignore` invisible to the one review mechanism (`git status`) that would normally surface an uncommitted file sitting in a repo root for 85 commits' worth of history.

## 5. Recommendation (already executed in this commit)

1. Removed `.gitignore` line 6 (self-exclusion) so the file can be tracked and reviewed like any other config file going forward.
2. Removed the flat `process_learnings/*` exclusion; both files in that directory are meant to be permanent.
3. Removed `helpdesk-tickets/*workflow*.md` and `helpdesk-tickets/*script*.md`; no legitimate exclusion target was found for either pattern, and both collide with the suite's own ticket-naming convention.
4. Added `.gitignore` itself, all 9 open tickets, all 11 root-level `CLOSED_*` tickets (candidates for `/harden-workflow` TM-5's next archive sweep), both `helpdesk-tickets/` READMEs, and `process_learnings/` in full — 26 files, secret-scanned first per Section 3.
5. **Not done, and flagged rather than assumed:** whether "Silent Persistence Gap" (content assumed git-durable that was actually working-tree-only, invisible to routine review) belongs in the Failure Pattern Vocabulary in `~/.claude/CLAUDE.md` is the user's call, not mine to silently add — that file is outside this workspace's edit boundary per the Workspace Edit Boundary rule.
6. Recommend a one-time repo-wide audit (`git ls-files` vs `find` diff, or equivalent) to check whether any OTHER path is silently excluded the same way, now that this class of bug is known. Not performed here — out of scope for Stage 4 Task 4.4's immediate blocker, called out as a follow-up rather than assumed clean.

**[CORRECTION — 2026-07-06, /nodelete]** Item 4's counts above were written before a precise recount. The exact, `git ls-tree`-verified split (parent commit vs. `66313dd`) is: **10 open tickets** and **12 root-level `CLOSED_*` tickets** newly tracked (22 ticket files total, not 20 as first stated), plus both READMEs and `process_learnings/` in full — 26 files in the commit, unchanged. Original prose above preserved per /nodelete; this note is the corrected figure of record. Does not change Section 4's Impact assessment or the fix itself, only the descriptive count.

## 6. References

- `.gitignore` (the file, before and after this commit).
- `~/.claude/CLAUDE.md` — "Append-only" row naming `PROCESS_LEARNINGS.md` as one of two suite-wide never-overwritten files.
- `CLAUDE.md` (project) — "CLOSED_ prefix" row; helpdesk tickets as mandatory session-start context.
- `implementation-plan/sovereign-redesign-cluster/tasks.md` Stage 4 Task 4.4 (the work this finding interrupted).
