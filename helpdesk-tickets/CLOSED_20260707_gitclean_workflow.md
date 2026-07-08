# Helpdesk Ticket: Gitclean Fails to Scrub Currently-Ignored Runtime Files from History

**To**: Senior Architect of Workflows
**From**: Antigravity Gemini
**Date**: 2026-07-07
**Subject**: The /gitclean workflow's Mode C design deliberately prevents history scrubbing for previously committed files that are newly added to .gitignore but still present on disk.
**Urgency**: HIGH
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER — a local fix to `gitclean.md`'s own Phase 3/3b/4/5/7, not a reusable engine or pattern transferred from elsewhere.

---

## 1. Executive Summary
A user accidentally committed runtime files (like databases) to git, subsequently added them to `.gitignore`, and executed `/gitclean mode c --y` expecting the workflow to purge those files from the entire git history while keeping them on disk. The workflow failed to do so. The design of `/gitclean` segregates "history scrubbing" (which strictly skips files still present on disk) from "index untracking" (which untracks files matching `.gitignore` but leaves past commits untouched), meaning no combination of modes supports scrubbing a locally-present, newly-ignored file from history.

## 2. Root Cause Analysis: "Structural Gap"
- **The How**: The agent accurately executed Mode C but left the database fully intact in the git history.
- **The Why**: The workflow lacks a mechanism to bridge Phase 3 (Tracked-but-ignored detection) and Phase 4 (History scrub). Phase 4 only consumes the list of files from Phase 2 (History-deleted files). Furthermore, Phase 2 explicitly excludes any file that still physically exists on disk. Lastly, a bug in Phase 3's `git check-ignore` command prevents it from evaluating tracked files because it lacks the `--no-index` flag.

## 3. Forensic Evidence
- **[Phase 2 Hard-Drive Check]**: [gitclean.md](file:///home/jwils/blueprint-workflows/claude-commands/gitclean.md#L147-L152)
  *Evidence: The workflow strictly skips removal candidates if they still exist on the local hard drive, preventing local runtime files from being targeted for history scrubs.*
- **[Phase 3 Check-Ignore Bug]**: [gitclean.md](file:///home/jwils/blueprint-workflows/claude-commands/gitclean.md#L176-L181)
  *Evidence: The tracked-but-ignored detection logic uses `git check-ignore "$file"` which silently skips already-tracked files; it requires the `--no-index` flag.*
- **[Phase 4 History Scrub Isolation]**: [gitclean.md](file:///home/jwils/blueprint-workflows/claude-commands/gitclean.md#L207-L215)
  *Evidence: The `filter-repo` command explicitly targets only `/tmp/gitclean-history-deleted.txt` (Phase 2's output), completely isolating it from Phase 3's tracked-but-ignored list.*

## 4. Remediation: Introduce "History Scrub for Ignored Files" Logic
1. Update Phase 3 to use `git check-ignore --no-index` to correctly identify currently-tracked files that match `.gitignore`.
2. Introduce a user prompt/gate when tracked-but-ignored files are found: ask if they should merely be untracked (current Phase 5 logic) OR aggressively scrubbed from all history (routing them to Phase 4).
3. If scrub is selected, append the tracked-but-ignored files to `/tmp/gitclean-paths-to-remove.txt` before Phase 4 runs.

## 5. Recommendation to Senior Architect
Update the `/gitclean` workflow protocol to explicitly support the "Local Runtime File Purge" use case. When a file is tracked but newly matched by `.gitignore`, the workflow should explicitly offer the user the choice to completely excise it from history using `git filter-repo`, bypassing the Phase 2 "must not exist on disk" restriction for that specific class of files.

---

## 6. Remediation Record — 2026-07-08

Implemented all three of this ticket's own remediation steps, plus one safety mechanism the ticket didn't name but that its own fix required:

1. **Phase 3 detection bug fixed**: `--no-index` added to `git check-ignore -q "$file"` (both the Phase 3 detection loop and the Phase 7 verification loop that duplicated it) — [gitclean.md#L176-L184](file:///home/jwils/blueprint-workflows/claude-commands/gitclean.md#L176-L184). Confirmed live in a throwaway repo: the pre-fix command found nothing for a committed-then-ignored file; the fixed command found it immediately.
2. **New Phase 3b — Purge Disposition**: bridges Phase 3's detections into Phase 4's history scrub via a per-file Untrack-only / Scrub-and-preserve (LRFP) choice, auto-escalating a Mode B session to run Phase 1/Phase 4 when LRFP is selected — [gitclean.md#L193-L235](file:///home/jwils/blueprint-workflows/claude-commands/gitclean.md#L193-L235).
3. **Not in the ticket's own remediation, added because the live dry-run proved it necessary**: `git filter-repo`'s checkout reset can delete a still-tracked file from the working tree as a side effect of rewriting the commit that tracks it — confirmed live (see below), not theoretical. Closed via a preserve-before/restore-and-verify-after wrapper (STRICT RULE 12): copy to `/tmp/gitclean-preserve/` before Phase 4, restore if missing after, and a mandatory three-part PASS check (on_disk / not_tracked / ignored) before Phase 6 (GC) makes anything irreversible.

**Verified via a full live dry run** (throwaway repo, not this workspace): committed a fake `app.db`, added it to `.gitignore`, ran the fixed Phase 3 detection (found it), ran the Phase 3b→Preserve→Phase 4→Restore→Verify sequence exactly as written in the workflow. Result: `git filter-repo` *did* remove `app.db` from the working tree as a side effect (confirming the risk was real) — the restore step fired and recovered it. Final verification line: `app.db: on_disk=PASS not_tracked=PASS ignored=PASS`, and `git log --all --full-history -- app.db` returned 0 entries.

`lint_workflows.py --file gitclean.md`: 0 CRITICAL, 0 WARNING after hash recompute. Frontmatter: version 2→3, `strict_rule_count` 11→12, `phase_count` 10→11, `last_hardened` 2026-07-08. Change Log entry 5 appended to `gitclean.md`.

---
**Status**: **REMEDIATED**
**Verification**: CONFIRMED — live end-to-end dry run in a disposable repo reproduced both the original bug and the new LRFP path, including catching a real (not hypothetical) filter-repo side effect and recovering from it as designed.

---
*Signed,*
**Antigravity Gemini**
*(Sovereign Helpdesk Analyst)*
*(Remediated by: Claude Code, Sovereign Scaling Cluster, blueprint-workflows main session, 2026-07-08)*
