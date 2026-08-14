# Helpdesk Ticket: Ticket Archival Orphaned by the Two-Path Fork — the Third, Unaudited Casualty of a Defect Already Found and Partially Fixed

**To**: Senior Architect of Workflows
**From**: Claude Code (Opus 5), session-diagnostic pass at user request
**Date**: 2026-07-26
**Subject**: Closed-ticket archival (`/harden-workflow` Step TM-5) has not run since approximately 2026-06-12 — not because the mechanism is broken, but because it is bolted to `/harden-workflow --ticket`, a path the two-path ticket model structurally bypasses for every Substantive/Logic closure. 43 closed tickets have accumulated in `helpdesk-tickets/`; 39 of them are eligible for archival right now.
**Urgency**: HIGH
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: **CONFIRMED — TRANSFER.** Lineage entry added to `manifest/SUITE_PHYLOGENY.md`, 2026-07-26: *"The 're-home a session-boundary step out of `/harden-workflow --ticket`' gene expresses a second time; the two-path fork's third casualty is found six weeks late."* Resolved at filing rather than at closure — this ticket stays OPEN pending a live trial run, and a phylogeny judgment is not recoverable later with the same fidelity, so it is captured now while the reasoning is in view.

---

## 1. Executive Summary

Closed helpdesk tickets are supposed to be moved into `helpdesk-tickets/archive/` once they are more than 7 days old. That has not happened for roughly six weeks: `archive/` holds 24 tickets, the newest dated `CLOSED_20260602_*`, while 43 closed tickets sit unarchived in the directory root, the oldest dated `CLOSED_20260612_*`. **The archival command itself is not broken** — run against the live directory it correctly identifies 39 of the 43 as eligible, skipping exactly the 4 that are genuinely under 7 days old. The mechanism never runs because it lives inside `/harden-workflow`'s ticket mode, and ticket mode has effectively not been invoked since mid-June: every recent closure has taken the Substantive/Logic path, which by design never touches `/harden-workflow` at all. This is the **third** artifact orphaned by that same architectural fork — and the only one of the three that was never audited when the first two were found and fixed.

## 2. Root Cause Analysis: "Structural Gap — Orphaned Step (mandatory housekeeping bolted to an optional path)"

- **The How**: `/harden-workflow` Step TM-5 archives closed tickets older than 7 days via a `find ... -exec mv` one-liner, and STRICT RULE 18 of that same file declares the step "mandatory at the end of every session." But the qualifier that governs it is *"in ticket mode"* — TM-5 exists only inside the `--ticket` invocation path. When `/helpdesk-tickets` forked into two closure paths (STRUCTURAL → `/harden-workflow --ticket`; SUBSTANTIVE-LOGIC → direct remediation), every ticket taking the second path closed without `/harden-workflow` ever running. TM-5 therefore never fired. Of the twelve most recently closed tickets, every single one that declares a closure method declares a **Remediation Record** — the Substantive/Logic artifact. Not one Hardening Certificate appears among them.
- **The Why**: The workflow did not separate *"housekeeping that must happen because a session ended"* from *"processing that happens because a specific sub-workflow was invoked."* TM-5 is the former in substance but was implemented as the latter in structure. Nothing in `/harden-workflow` is at fault for not running — it correctly did not run. The gap is that a step whose trigger condition is genuinely "a session closed" was given a trigger condition of "this particular workflow was invoked," making its execution contingent on a routing decision that has nothing to do with whether archival is due.

This is a **known, already-documented defect class in this suite, recurring after an incomplete remediation.** `helpdesk-tickets.md`'s own Change Log entry 4 (2026-07-04) diagnosed exactly this fork fallout and fixed two casualties — Phylogeny Disposition (moved into `/helpdesk-tickets` Step 4a.5) and the Suite Learning Registry (moved into `/secretary` Step 1.0.5). It closed with the lesson: *"when a pipeline is forked into two legitimate paths, audit everything that assumed the old path was the only one in, not just the routing logic itself."* That audit found two of three. TM-5 was the third and was missed. The freeze dates corroborate a single common cause: entry 4 records `SUITE_PHYLOGENY.md` and `CONTRADICTION_REGISTRY.md` as "frozen since 2026-06-12," and ticket archival stops at the identical boundary.

## 3. Forensic Evidence

- **The orphaned step, and the "in ticket mode" qualifier that strands it**: [harden-workflow.md, Step TM-5, lines 175-197](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L175-L197)
  *Evidence: contains the working `find ~/blueprint-workflows/helpdesk-tickets/ -maxdepth 1 -name 'CLOSED_*' -mtime +7 -exec mv {} .../archive/ \;` command, and the sentence "This step runs at the END of every ticket-mode session" — the scope limitation that is the entire defect.*
- **The STRICT RULE that calls it mandatory while scoping it to a path that no longer runs**: [harden-workflow.md, STRICT RULE 18, line 768](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L768)
  *Evidence: "In ticket mode, Step TM-5 (archive stale closed tickets) is mandatory at the end of every session." Both halves are true and they contradict each other in practice — mandatory every session, but only reachable in a mode not being used.*
- **The same defect, diagnosed and partially fixed three weeks ago, with the freeze date that matches this one**: [helpdesk-tickets.md, Change Log entry 4, line 414](file:///home/jwils/blueprint-workflows/claude-commands/helpdesk-tickets.md#L414)
  *Evidence: records that Substantive/Logic closures "structurally bypass that workflow entirely," that `SUITE_PHYLOGENY.md` and `CONTRADICTION_REGISTRY.md` were "frozen since 2026-06-12," and states the general lesson this ticket is the proof was not fully applied.*
- **The exact fix precedent, already in the destination file**: [secretary.md, Step 1.0.5, lines 169-182](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L169-L182)
  *Evidence: the Suite Learning Registry pass, relocated into `/secretary` for this identical reason, including the governing rationale — "Tying the pass to /secretary instead makes freshness a property of 'a session closed,' which is far harder to skip than 'a specific sub-workflow ran.'" That sentence is the complete argument for this ticket's remediation, written three weeks before this ticket existed.*
- **Live measurement of the directory state** (run 2026-07-26): `ls helpdesk-tickets/archive/ | wc -l` → 24; `find helpdesk-tickets/ -maxdepth 1 -name 'CLOSED_*' | wc -l` → 43; `find helpdesk-tickets/ -maxdepth 1 -name 'CLOSED_*' -mtime +7 | wc -l` → **39**.
  *Evidence: the predicate works correctly against real data — 39 eligible, 4 correctly skipped as under 7 days. This rules out a broken command and isolates the cause to non-invocation.*

## 4. Remediation: Relocate the Trigger to Session-Close, Preserve the Original

Applied in this session:

1. **Add Step 1.0.6 to `/secretary` Phase 1**, immediately after Step 1.0.5, running the archival unconditionally on every `/secretary` run — mirroring 1.0.5's structure, placement, and rationale exactly, since it is the same defect with the same fix.
2. **Do not remove TM-5 from `/harden-workflow`.** Per `/nodelete`, and following 1.0.5's own explicit precedent ("This is deliberately a second, independent trigger... TM-6 still fires on its own path unchanged"), the original stays. The operation is idempotent — a second run in the same day finds nothing left to move — so duplication costs nothing and preserves correct behavior for anyone who does invoke ticket mode. Removing it would also strip STRICT RULE 18 of its referent without a superseding replacement, which `/nodelete` prohibits.
3. **Fix a latent `/nodelete` violation found while relocating**: the original uses bare `mv`, which silently overwrites a same-named file already in `archive/`. Verified by direct test — the archived original was destroyed with no warning and no error. No collision exists today (confirmed by set intersection), but the relocated copy uses `mv -n` and reports any skipped collisions rather than destroying history.
4. **Wire the result into the Secretary Receipt** (Phase 7) so the archival's outcome is visible per session rather than silent.

## 5. Recommendation to Senior Architect

**Any step whose real trigger condition is "a session ended" must be attached to the workflow that owns session boundaries, never to a workflow that merely happens to run often.** This is now the third confirmed instance of the same failure — Phylogeny, the Suite Learning Registry, and ticket archival were all bolted to `/harden-workflow --ticket` and all silently stopped the moment a legitimate second closure path appeared. The first two were relocated to guaranteed-execution points; the third sat undetected for six weeks because nobody enumerated the full set of things that path was carrying.

The structural recommendation is therefore not just "move TM-5" but **audit `/harden-workflow`'s ticket-mode steps as a class**: TM-5 and TM-6 were both housekeeping riders on a processing workflow, and both needed relocating. Any remaining TM-* step that performs suite-wide bookkeeping rather than workflow-specific hardening is a candidate for the same treatment and should be checked now, while the pattern is in view. More generally, when a pipeline forks, the correct audit is not "does the routing still work" but **"enumerate everything the old path was carrying, and re-home each item against its own true trigger condition."** Entry 4 stated that lesson correctly and this ticket is the evidence that stating it was not the same as completing it.

---
**Status**: **REMEDIATED (archival re-homed to `/secretary` Step 1.0.6, unconditional every session close; TM-5 preserved; `mv -n` no-clobber guard added — proven by live trial)**
**Verification**: **PASSED — live trial, 2026-07-26.** The `/secretary` invocation immediately following this remediation executed Step 1.0.6 as written. Result: **39 tickets archived**, `archive/` 24 → 63, 4 closed tickets (all genuinely under 7 days) and 5 open tickets correctly left in root, **zero collisions** — the post-run `find ... -mtime +7` re-check returned empty, confirming a clean sweep with nothing skipped. The predicted count matched the measured count exactly. See the Remediation Record below for the structural verification that preceded this, and the Live Trial Record appended after it.

---

## Remediation Record (2026-07-26) — built, structurally verified, live trial pending

```
REMEDIATION RECORD
  Ticket:            20260726_ticket-archival-orphaned_workflow.md
  Faulting workflow: /harden-workflow (orphaned step) -> remediated in /secretary
  Root cause fixed:  Archival was reachable only via /harden-workflow --ticket, a path the
                     two-path ticket model bypasses for every Substantive/Logic closure.
  Changes made:      claude-commands/secretary.md (v6->v7) —
                     - NEW Step 1.0.6 "Closed-ticket archival pass" in Phase 1, immediately
                       after 1.0.5, mirroring its structure/placement/rationale deliberately.
                       Runs unconditionally every /secretary invocation, suite or project.
                     - mv -n instead of bare mv (no-clobber; see Live verification below).
                     - Phase 7 Secretary Receipt gains a TICKET ARCHIVE: line, reported every
                       run including the no-op case, with a COLLISIONS SKIPPED field.
                     - STRICT RULE 21 (strict_rule_count 20->21): a step whose real trigger is
                       "a session ended" belongs to the workflow owning session boundaries.
                     - GLOSSARY term "Closed-ticket archival pass". last_hardened 2026-07-26,
                       content_hash sha256:073556aed6ba069b.
                     claude-commands/harden-workflow.md (v5->v6) —
                     - TM-5 PRESERVED and unchanged in behavior; gained a dated [NOTE]
                       recording the diagnosis, pointing to Step 1.0.6, and flagging the
                       mv -n difference for any future editor of that copy. No STRICT RULE
                       altered — removing TM-5 would strip STRICT RULE 18 of its referent
                       without a superseding replacement (/nodelete).
                     - last_hardened held at 2026-07-07 (annotation, not a hardening pass);
                       content_hash sha256:9f815d57af5567f6.
                     .changelogs/secretary.md + .changelogs/harden-workflow.md — entry 15 each
                       (both files use externalized Change Logs).
                     manifest/SUITE_PHYLOGENY.md — lineage entry appended.
  Tests:             487/487 passing, unchanged before and after. No new tests: this changed
                     workflow .md protocol surfaces, not Python. Verification is behavioral,
                     and was RUN rather than asserted — see below.
  Live verification: Step 1.0.6's command was executed verbatim (base path substituted only)
                     against a purpose-built sandbox fixture containing all five relevant
                     cases. Results, all correct:
                       - 2 closed tickets older than 7 days  -> ARCHIVED
                       - 1 closed ticket under 7 days        -> correctly LEFT in root
                       - 1 OPEN ticket                       -> correctly UNTOUCHED
                       - 1 NAME COLLISION (same filename already in archive/)
                           -> archived original SURVIVED intact ("ARCHIVED ORIGINAL - MUST
                              SURVIVE" still present), root copy left in place, nothing lost
                       - the three report lines produced correct counts (3 / 2 / 1)
                     The collision case was also run against bare mv as a control: it
                     silently overwrote the archived original with no error. That is what
                     mv -n prevents, and why the guard is not cosmetic.
  Linter:            lint_workflows.py -> CLEAN (0 CRITICAL, 0 WARNING) on secretary.md,
                     harden-workflow.md, and execute-build.md individually. Suite-wide
                     0 CRITICAL / 19 WARNING — unchanged from the SUITE_HEALTH.md baseline.
  Deferred:          (a) -mtime +7 keys off filesystem mtime, not the filename's YYYYMMDD.
                     Carried over verbatim from TM-5 rather than silently changed, since
                     altering age semantics is a separate decision from relocating a step.
                     (b) The Section 5 recommendation — audit /harden-workflow's remaining
                     TM-* steps as a class for the same orphaning — is NOT done. TM-5 and
                     TM-6 are both now re-homed; whether any other TM-* step is suite-wide
                     bookkeeping rather than workflow-specific hardening was not enumerated.
                     (c) Horizontal transfer of the mv -n guard to any other suite step that
                     relocates files by name into a shared destination — recorded in the
                     phylogeny entry, not enumerated.
  NOT RUN:           The archival itself. Deliberately left un-executed so the user's next
                     /secretary invocation is a genuine trial against the real 39-ticket
                     backlog. Running it here would have made that trial vacuous and would
                     have been this suite's own named failure — certifying a fix by a path
                     other than the one that must actually work.
```

**Why this ticket was OPEN rather than REMEDIATED at build time**: the fix was built and every mechanical property verified, but its governing claim — *"archival now happens because a session closed"* — is only proven when `/secretary` actually runs and archives the backlog. Marking it REMEDIATED on the strength of a sandbox run would have been precisely the Hallucinated Success pattern that this same session built `/execute-build` Step 6a to prevent. Closure was therefore withheld for the trial run. **That trial has now run — see below.**

---

## Live Trial Record (2026-07-26) — the verification the closure actually rests on

```
LIVE TRIAL — /secretary Phase 1, Step 1.0.6
  Executed:      the Step 1.0.6 command block verbatim, unmodified, from secretary.md
  Context:       a real /secretary session close, not a test harness — the trigger under test
                 IS "a session closed," so any other invocation path would have proven nothing

  BEFORE         archive/: 24        CLOSED_ in root: 43
  AFTER          archive/: 63        CLOSED_ in root: 4        open in root: 5
  MOVED          39 tickets

  Predicted 39 (measured at build time) / observed 39 — exact match.

  Collision re-check (post-run `find ... -name 'CLOSED_*' -mtime +7`): EMPTY.
    Per Step 1.0.6's own note, a residue here would have indicated a name collision that
    mv -n correctly refused. There was none — clean sweep, nothing skipped, nothing lost.

  Correctly NOT moved:
    - 4 closed tickets under 7 days (CLOSED_20260707_nested-tasks-md..., CLOSED_20260716_sentinel,
      CLOSED_20260722_phase-status-empty-phases-contract, CLOSED_20260726_execute-build)
    - all 5 open tickets (no CLOSED_ prefix)

  What this proves that the sandbox could not: the step is reachable on the path that matters.
  The sandbox proved the command's semantics; only a real session close proves the re-homing
  itself — which was the entire defect. The mechanism was never broken; being reachable was.
```

**One honest limitation of this trial**: it exercised the archival on the `/secretary` path, which is the fix. It did not re-exercise `/harden-workflow` TM-5's preserved copy, since ticket mode was not invoked this session. TM-5 is unchanged in behavior and was verified only by inspection, not execution — noted rather than claimed otherwise.

---
*Signed,*
**Claude Code (Opus 5)**
*(Creating Agent — session-diagnostic pass)*
