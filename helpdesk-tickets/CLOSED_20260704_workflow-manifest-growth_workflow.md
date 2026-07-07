# Helpdesk Ticket: `WORKFLOW_MANIFEST.md` Combines Unbounded Append-Only Growth With a Mandatory Full-Read-Every-Session Instruction, and Nothing Compresses It

**To**: Senior Architect of Workflows
**From**: Claude (session agent — found during the user-directed documentation-strategy audit, 2026-07-04)
**Date**: 2026-07-04
**Subject**: `manifest/WORKFLOW_MANIFEST.md` conflates a Live-State suite index (small, current-state-only) with an Append-Only session narrative (growing forever) in one physical file, and `role.md`/`CLAUDE.md` mandate reading the whole thing at every session start. **[EXPANDED 2026-07-04, same day]**: `manifest/SUITE_PHYLOGENY.md` shares the identical unbounded-Append-Only-growth shape, at smaller scale today — married into this same ticket's remediation rather than filed separately, per explicit user direction, since it is the same problem over several files.
**Urgency**: MEDIUM
**Root Cause Type**: SUBSTANTIVE-LOGIC — **[CORRECTED 2026-07-04]** originally filed STRUCTURAL; corrected once the decided remediation required new code (`scripts/ledger/`), which `/harden-workflow` explicitly cannot touch (its own opening line and STRICT RULE 3).
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

This is the finding this ticket exists to hold open for active iteration, not a done deal — filed at the user's explicit request, to be discussed and decided live, not remediated in this pass. `manifest/WORKFLOW_MANIFEST.md` is instructed to be read in full at the start of every new session (`role.md` Section VI, `CLAUDE.md`'s "On session boundaries" section) — but it is also an Append-Only Ledger by contract (`/nodelete` Pillar 1: "never thinned"), and it has no compression, sharding, or summarization layer analogous to what `doorway.py` provides for filesystem drift (a compact JSON signal, not raw file dumps) or what `secretary.md`'s own `tail -n 30` (ADDENDUM B) already does for a narrower purpose. Measured: 44,861 bytes, grown from zero across 58 calendar days (2026-05-07 → 2026-07-04) in 17 recorded session entries — no ceiling, and it has only grown since this measurement.

## 2. Root Cause Analysis: "Conflated Retention Contract"

- **The How**: The file's own template (`secretary.md` Phase 1) has two structurally distinct parts: a `## Suite Health` / `## Workflow Index` block (a Live-State snapshot — one current value per workflow, already treated as in-place-edited in practice, never appended) and a growing sequence of `**[SESSION APPEND — ...]**` narrative blocks (a genuine Append-Only Ledger — a session history). These are two different Retention Contracts under `/nodelete`'s own Pillar 1 taxonomy, living in one file, read as one unit.
- **The Why**: When the mandatory-full-read instruction was written (`role.md`, `CLAUDE.md`), the file was small and the distinction didn't matter yet. Nothing has revisited that instruction as the Append-Only half has grown. There is no equivalent, for this file, of the compression step `doorway.py` performs before `sentinel.md` ever surfaces a report to the agent.

## 3. Forensic Evidence

- **The mandatory full-read instruction**: [role.md#L175](file:///home/jwils/blueprint-workflows/claude-commands/role.md#L175)
  *Evidence: "it should read this file, the `~/blueprint-workflows/manifest/WORKFLOW_MANIFEST.md`, and any open helpdesk tickets... These three documents constitute the minimum context a fresh agent needs." No partial-read qualifier.*
- **The Append-Only contract**: [claude-commands/nodelete.md#L85](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L85), [secretary.md#L410](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L410)
  *Evidence: "never thinned"; "HANDOFF.md is overwritten each session... WORKFLOW_MANIFEST.md [is not, elsewhere in the same file's own STRICT RULES] — this is the only correct behavior."*
- **Measured growth, no ceiling**: `manifest/WORKFLOW_MANIFEST.md` — 44,861 bytes, 17 session entries, 2026-05-07 to 2026-07-04 (58 days). Growth rate ≈ 770 bytes/entry, unbounded by design.
- **The suite's own working precedent for compression already exists, twice**: [scripts/doorway/doorway.py](file:///home/jwils/blueprint-workflows/scripts/doorway/doorway.py) (compact JSON drift report, never a raw file dump) and [secretary.md#L392-L396](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L392-L396) (`tail -n 30` before emitting the Suite Health Score — the suite already knows how to do a partial read of this exact file for a narrower purpose).
- **A working example of the right shape already exists, on the same conceptual axis**: `.workflow_state/HANDOFF.md` is Live-State (overwritten each session, not accumulated), current-session-focused, and small — already praised in this session's earlier audit as "the one document actually shaped like a context-budget solution."

## 4. Remediation: Decided Design — Option 1 (Retention-Contract Split) + Option 4 (Quarterly Sharding), Scripted, Married With a Phylogeny Growth-Warning

**[DECIDED 2026-07-04, same day, after live discussion]** Options 2 and 3 (from the original four-option list, preserved below for the record) were set aside — neither addresses the file's own unbounded growth, only how much of it gets read. Options 1 and 4 were chosen, and only work well combined: sharding without first separating the Live-State table from the narrative would force the table to "follow" whichever shard is currently active, reintroducing the exact lookup friction being removed.

**The design:**
1. **Split**: `manifest/SUITE_HEALTH.md` (new) — the Live-State table only, in-place-edited, mandatory-read at session start. `manifest/WORKFLOW_MANIFEST.md` — repointed to a short redirect note; its former narrative content moves, verbatim, into dated shards.
2. **Shard**: `manifest/history/WORKFLOW_MANIFEST_{YYYY-Q}.md`, one per quarter, discovered by filename-sort convention (no separate pointer file — matches `helpdesk-tickets/`'s own open/closed convention). Rollover trigger is **scripted, not LLM-judged** — the user's own explicit requirement: an LLM should never be the sole source of truth for "what quarter is it." A hybrid trigger: calendar (quarter boundary crossed) as primary, entry-count/byte-size safety valve as backstop for an unusually active quarter (e.g. this one).
3. **Married in**: `manifest/SUITE_PHYLOGENY.md` gets the same growth-check machinery in **warn-only** mode (not shard-eligible yet — too small to need it) — a single script checks both files, since it is the same problem shape. On threshold crossing it throws a warning for the agent to see and judge, mirroring the exact NONE/REVIEW pattern `registry.py` already established in this repo — reused, not reinvented.
4. **New engine**: `scripts/ledger/` (config-driven, mirrors `scripts/registry/` and `scripts/gitignore/` conventions exactly) — `monitor.py` performs both the warn check and the shard rollover, driven by real `datetime.date.today()`, never agent memory or inference.

**Preserved for the record (superseded, not deleted) — the original four options:**
2. *Tail-based mandatory read, one file, no restructuring* — rejected: cheapest, but leaves growth completely unbounded.
3. *Demote to on-demand; promote HANDOFF.md* — rejected: a workaround around the file's own design, not a fix to it.

## 5. Recommendation to Senior Architect

Whatever is decided, apply it consistently: if `WORKFLOW_MANIFEST.md`'s narrative half is judged genuinely Append-Only (never thinned), any restructuring must move content, not lose it — matching this session's own practice everywhere else (the `.history/` split, the Phylogeny backfill). This is a design decision about a doctrine (Append-Only, never-thinned) the user set deliberately — not a mechanical fix to apply unilaterally.

---
**Status**: **REMEDIATED (WORKFLOW_MANIFEST.md split by Retention Contract into SUITE_HEALTH.md + quarterly-sharded manifest/history/*.md; scripts/ledger/ built to automate both the rollover and a matching SUITE_PHYLOGENY.md growth-warning; all in-workspace cross-references retargeted, plus ~/.claude/CLAUDE.md under explicit mid-session user authorization)**
**Verification**: See Remediation Record below.

---
*Signed,*
**Claude**
*(Session Agent — Senior Architect of Workflows role)*

---

## REMEDIATION RECORD

```
REMEDIATION RECORD
  Ticket:            20260704_workflow-manifest-growth_workflow.md
  Faulting workflow: /secretary (produces the file), role.md/CLAUDE.md (the onboarding
                     mandate) — plus manifest/SUITE_PHYLOGENY.md, married into this same
                     ticket per explicit user instruction (same problem shape).
  Root cause fixed:  WORKFLOW_MANIFEST.md conflated a Live-State suite index with an
                     unbounded Append-Only session narrative in one file, mandatory-full-
                     read every session, no compression layer. SUITE_PHYLOGENY.md carries
                     the identical risk at smaller scale.
  Changes made:      Built scripts/ledger/ (_utils.py, config.py + ledger_config.toml,
                     monitor.py, reporter.py, ledger.py CLI) — warn mode (count/report,
                     never writes) and shard mode (quarterly rollover + within-quarter
                     size safety valve), both driven by the real datetime.date.today(),
                     never LLM-inferred, per the user's explicit requirement.
                     One-time migration (by hand): manifest/SUITE_HEALTH.md (new,
                     Live-State half) + manifest/history/WORKFLOW_MANIFEST_2026-Q2.md +
                     _2026-Q3.md (narrative half, split exactly on the real quarter
                     boundary). Old combined file replaced with a short redirect stub —
                     nothing deleted.
                     Cross-references retargeted: secretary.md (Phase 1 reworked — new
                     Step 1.2 ledger check, ADDENDUM B/C retargeted, STRICT RULES 2/9/14/15
                     updated, new STRICT RULE 19, GLOSSARY +3, v3->v4), role.md (onboarding
                     instruction, constants table, Section VIII, Change Log entry 5),
                     onboard.md, harden.md, depreciate.md, this project's CLAUDE.md, and
                     ~/.claude/CLAUDE.md (outside this workspace — edited only after the
                     user's explicit mid-session authorization).
                     Root Cause Type corrected STRUCTURAL -> SUBSTANTIVE-LOGIC once new
                     code became the actual fix.
  Tests:             14 new (scripts/tests/test_ledger.py): warn-threshold crossing
                     (entries and bytes independently), first-run shard creation,
                     no-rollover case, quarter-boundary rollover with content-preservation
                     verification, within-quarter size-overflow rollover with letter-suffix
                     incrementing (2026-Q3 -> Q3b -> Q3c), never-deletes-a-prior-shard.
                     Full suite: 183/183 passed (169 pre-existing + 14 new), 0 regressions.
  Linter:            lint_workflows.py --workspace ~/blueprint-workflows: 0 CRITICAL,
                     19 WARNING (identical pre-existing baseline — nodeleteshort.md/
                     refactor.md/soc.md/testpackage.md structure gaps, role.md structure
                     gaps, sentinel.md stale hash — none introduced; every file touched
                     this pass is hash-clean).
  Deferred:          NONE for this ticket's scope. Phylogeny Disposition for this change
                     itself: CONFIRMED — see manifest/SUITE_PHYLOGENY.md's "X.5 insertion
                     convention" lineage entry (the same convention reused a third time,
                     nothing new to record there) and the NONE/REVIEW verdict pattern
                     transferred a second time, from registry.py into ledger.py.
```
