# Helpdesk Ticket: Pillar 6 Archival Leaves No Resolvability Convention for `phase_status.py` — Archived-But-Verified Phases Become Indistinguishable From Ghost Logic

**To**: Senior Architect of Workflows
**From**: Claude Code session (research/proforma workspace)
**Date**: 2026-07-29
**Subject**: `/nodelete`'s Pillar 6 (Archival Mode) removes a phase's `### Phase N` section from the live `tasks.md` once it graduates off the active surface, but leaves `scripts/focus/phase_status.py` with no mechanism to still resolve that phase — the engine's read side has no counterpart to Pillar 6's write side, so an archived-but-genuinely-complete phase reports identically to a phase that never existed.
**Urgency**: CRITICAL (Architectural)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

`phase_status.py` is the shared mechanical spine consumed by three separate workflows — `/focus-plan`'s PENDING/MISMATCH adjudication, `/implementation-plan --audit`'s Completion Marking sub-pass, and (by shared match-key convention) `/execute-build`'s own receipt writer. All three depend on a phase's `### Phase N` header still being present in the live `tasks.md` to resolve anything about it. `/nodelete`'s own Pillar 6 (Archival Mode) exists specifically to graduate completed, non-contradicted history off that live surface — and does so correctly, moving the content verbatim into a `.history/archive/tasks.md.ledger.md` file. The gap: nothing in either workflow provides a way for `phase_status.py` to still resolve an archived phase as "genuinely complete, moved" rather than "not found." The two features were each built correctly in isolation and never reconciled against each other. Confirmed live in `research/proforma`: a single commit (`c6ec846`, Phase 55's own build) archived Phases 14, 45, 47-54 — roughly 900 lines — and `phase_status.py` now resolves zero of them, identically to how it would resolve a phase number that was never used.

## 2. Root Cause Analysis: "Archival Blind Spot — A Write-Side Feature With No Read-Side Counterpart"

This is a new failure shape, related to but distinct from Ghost Logic: Ghost Logic is a plan claiming work that was never done; this is the mirror case at the *tooling* layer — genuinely-done, genuinely-verified work that a script can no longer see, for a reason that has nothing to do with whether the work happened. Also distinct from the already-tracked `helpdesk-tickets/20260707_phase-status-campaign-header-scope_workflow.md` (still open): that ticket's root cause is `_PHASE_TITLE_RE`'s narrow *pattern-matching scope* failing against unusually-shaped headers that are still physically present in `tasks.md`. This ticket's root cause is architectural absence — the content is not merely unmatched, it has been correctly, deliberately *removed* from the file `phase_status.py` reads, by a different workflow's own by-design behavior.

- **The How**: `/nodelete`'s Pillar 6 archival moves a phase's full `### Phase N` section (including any `BUILD OUTCOME` sub-section) out of the live `tasks.md` into `.history/archive/tasks.md.ledger.md`, verbatim, as intended. `phase_status.py`'s `parse_tasks_md()` only ever reads the live `tasks.md` it is pointed at — it has no parameter, fallback, or secondary-source concept for a companion archive file. Once a phase's header is gone from the live file, every consumer downstream reports the same signal a phase that was never planned would produce: `not_started`/`no_checkboxes`, no receipt cross-reference possible.
- **The Why**: Neither workflow's own design ever modeled the other's output as an input. `/nodelete` Pillar 6 was built around the verification gate for *whether* to archive (independently confirmed complete via `phase_status.py` itself, ironically — a unit must already resolve `found_complete` before Pillar 6 will move it) — but never asked what happens to that same unit's resolvability *afterward*. `phase_status.py` was built around a single-file, single-pass parsing contract with no notion that its own source file's completeness could legitimately shrink over time by design, not by defect. The result: the one gate (`/focus-plan`'s PENDING vs. MISMATCH adjudication, GLOSSARY) that exists specifically to tell "legitimately not-yet-built" apart from "claimed done and isn't there" has no third bucket for "was done, was verified, was correctly archived" — it can only fall through to MISMATCH-eligible territory or silent invisibility, neither of which is the true state.

## 3. Forensic Evidence

- **`phase_status.py` has no archive-awareness anywhere in its 526 lines**: [phase_status.py](file:///home/jwils/blueprint-workflows/scripts/focus/phase_status.py#L1-L526)
  *Evidence: `grep -n "archive\|ledger" scripts/focus/phase_status.py` returns exactly 3 matches — two are docstring citations of an unrelated, already-closed ticket (`helpdesk-tickets/CLOSED_20260708_plan-archive-pipeline-design_workflow.md`, about header-annotation stripping, not archival resolvability) at lines 142 and 332, and the third (line 377) is an unrelated comment about `BUILD_RECEIPTS.md` being "a workspace-wide ledger, not per-plan." No code path reads `.history/archive/` or any equivalent secondary source.*

- **`research/proforma/tasks.md`'s own live phase sequence shows the gap directly**: [tasks.md](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/tasks.md#L96-L144)
  *Evidence: Phase 22's header at line 96 is immediately followed by Phase 44's header at line 144 — Phases 23 through 43 (previously built, real work) are simply absent from this file today, by design, per prior archival passes. Phase 44 (line 144) is immediately followed by Phase 46 (line 256) — Phase 45 is likewise absent. `phase_status.py` cannot resolve any of them from this file, regardless of whether they were ever completed.*

- **The archived content genuinely exists and is intact — this is a visibility regression, not a data-loss violation**: [tasks.md.ledger.md](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/.history/archive/tasks.md.ledger.md#L1226-L1251)
  *Evidence: `### Phase 14` at line 1226 and `### Phase 45` at line 1251 (Phase 47 at line 1401) are all present, verbatim, in the archive file — confirming Pillar 6 did its own job correctly. The defect is entirely on the read side.*

- **Independently confirmed and named by this session's own Phase 55 adversarial audit, `CRIT-01`**: [20260729-1037-proforma-phase55.md](file:///home/jwils/blueprint-workflows/implementation-plan/audits/20260729-1037-proforma-phase55.md#L17)
  *Evidence: "this commit silently strips the `### Phase 14`, `### Phase 45`, `### Phase 47` through `### Phase 54` header sections... from the live, tool-scanned file — independently confirmed via `phase_status.py --workspace research/proforma`, which resolves 10 phase entries post-commit and contains no entry whose title starts `Phase 45:`, `Phase 47:`, or `Phase 54:`... this is not a `/nodelete` data-loss violation, it is an undisclosed tooling-visibility regression."*

- **The project's own receipt made a false completeness claim about exactly this regression, because no tooling existed to check it properly**: [BUILD_RECEIPTS.md](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/BUILD_RECEIPTS.md#L1395)
  *Evidence: the Phase 55 receipt's "5b Risk Resolution" section asserts `phase_status.py` "still resolves Phase 44 and Phase 46 as `found_complete` after the edit, confirming no receipt-parse regression" — true for the two phases it happened to check, and silent on the eight it didn't, because there was no standing mechanism prompting the check to cover archived phases specifically. A human or agent relying on this receipt's own self-report would have no way to know the regression existed.*

- **A per-project workaround was required in lieu of a suite-level fix, confirming this cannot be solved once and reused**: [tasks.md, Fix 217](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/tasks.md#L1643)
  *Evidence: `research/proforma`'s own drafted remediation (Phase 59, Fix 217) has to invent an ad-hoc "restore machine-resolvable stub entries... without duplicating the full archived content back" mechanism from scratch, because no suite-level convention exists to reuse. Every future project that follows Pillar 6's own archival guidance will hit the identical gap and have to re-invent the same fix.*

## 4. Remediation: Give `phase_status.py` (or Pillar 6) a Standing Archived-Phase Resolvability Convention

Not yet applied — recommendation only:
1. Extend `phase_status.py`'s parsing contract to optionally consult a project's archive file(s) (e.g., `.history/archive/tasks.md.ledger.md`, or a configurable path) as a secondary source, surfacing a distinct status — e.g. `archived_complete` — separate from `not_started`/`complete`/`in_progress`, so `/focus-plan`'s Sovereign Gate and `/implementation-plan`'s Completion Marking sub-pass can both treat it as neither PENDING nor MISMATCH but as its own, correctly-adjudicated fourth outcome.
2. Alternatively (or additionally), have `/nodelete` Pillar 6 leave behind a minimal, machine-resolvable stub at the original phase's location — a canonical `### Phase N: Title` header plus a one-line `**ARCHIVED [DATE]** — see .history/archive/... ` pointer, satisfying `phase_status.py`'s existing parsing contract without needing to change the engine at all. This is the lower-risk option (no engine change, only a Pillar 6 output-format addition) and is what `research/proforma`'s Fix 217 is independently attempting to retrofit by hand.
3. Whichever direction is chosen, add a regression test exercising the full loop: archive a phase via Pillar 6 → confirm `phase_status.py` still resolves it as a distinct, correctly-labeled state, not silent absence.

## 5. Recommendation to Senior Architect

Treat `phase_status.py` and `/nodelete` Pillar 6 as two halves of one contract, not two independently-correct features — every future change to either should be checked against the other's assumptions before being considered complete. More generally: any workflow that *removes* content from a file another workflow's engine depends on for resolution should be required, at design time, to state explicitly what that engine now sees in its place — "nothing" is never an acceptable answer for content that was true and verified. This is the general failure class worth naming in the suite's own vocabulary alongside Ghost Logic and Mock Trap: call it an **Archival Blind Spot** — a structurally-correct removal that an unrelated verification engine cannot distinguish from the thing it exists to catch.

---
**Status**: **OPEN**
**Verification**: PENDING — no remediation applied yet.

---
*Signed,*
**Claude Code**
*(Creating Agent — research/proforma session)*

---

## Addendum — 2026-07-30: The Gap Escalated From Partial to Total, and Option 2's Stub Convention Is Now Structurally Unavailable

**Filed by**: Claude Code session (research/proforma workspace), one day after the original ticket.
**Why an addendum and not a new ticket**: STRICT RULE 7 — this is the same failure this ticket already documents, in a more severe form. Two *genuinely distinct* Pillar 6 failures found in the same session were filed separately as `20260730_nodelete_workflow.md`.

### What changed

On 2026-07-30 the user authorized a **full** `/nodelete --archive` of `research/proforma` — all 19 remaining phases across both `tasks.md` and `implementation-plan.md`, with the explicitly stated target end-state of "zero phase and task information" on the active surfaces. The archival executed correctly: gate cleared 19/19, content moved verbatim and byte-verified before any strip, Dual-Surface parity confirmed.

The resulting engine state is worse than the one this ticket was filed against:

```
phase_status.py --workspace research/proforma --output-json
  → found: True, receipts_file_found: True, structure_recognized: False, phases: []
```

The original ticket documented a *partial* blind spot — 10 phases invisible while 9 remained resolvable, so `structure_recognized` stayed `True` and the file still looked healthy. A full archival collapses that into `structure_recognized: False`, which [`phase_status.py`'s own docstring](file:///home/jwils/blueprint-workflows/scripts/focus/phase_status.py#L52-L58) instructs consuming workflows to treat as *"structure not recognized"* — a parse failure — **not** as "no phases exist." A correctly, completely archived project is now mechanically indistinguishable from a corrupted or unparseable `tasks.md`.

### Why this matters for the remediation options already on the table

The original Section 4 offered Option 2 — have Pillar 6 leave a minimal machine-resolvable stub behind — as "the lower-risk option (no engine change, only a Pillar 6 output-format addition)." **That option is structurally unavailable in the full-archival case.** Any stub sufficient for `phase_status.py` to resolve a phase is, by definition, phase information on the active surface — the exact thing a full archival exists to remove. The two requirements are in direct conflict, and nothing in Pillar 6 acknowledges the conflict or tells an agent which one wins.

This was confronted live and left undecided rather than guessed: the archival proceeded, the break was surfaced to the user under Pillar 4's Intent-Mismatch Gate, and the three candidate dispositions (accept the ambiguity / retain a titles-only index / fix the engine to distinguish the two states) were put to the user rather than resolved by the executing session.

- **The live archived surface**: [tasks.md](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/tasks.md#L1-L25)
  *Evidence: 61 lines remain — a title block, the four STANDING RULES, and the deliberately-retained `[UNNUMBERED — Closing Phase]` section, which was refused by the gate as drafted-only and correctly left active. Zero `### Phase N:` headers, zero checkboxes.*
- **The content, intact, in its Append-Only destination**: [.history/archive/tasks.md.ledger.md](file:///home/jwils/.prebuild.temp/lsshreveport/research/proforma/.history/archive/tasks.md.ledger.md#L2093)
  *Evidence: the 2026-07-30 entry, 2,254 lines byte-verified against the extraction before the active surface was touched. As with the original ticket: this remains a visibility regression, not a data-loss violation.*
- **Fix 217's stub convention, now itself archived**: the per-project workaround cited at the original Section 3's final bullet was folded into this archival along with everything else — confirming the original ticket's own point that a per-project retrofit cannot survive as a reusable convention.

### Revised recommendation

Option 1 (engine-side archive awareness, with a distinct `archived_complete` status) is now the **only** option that covers both the partial and total cases. Option 2 should be recorded as viable for partial archival only, and explicitly ruled out for full archival. A third requirement should be added to Section 4: `phase_status.py` must distinguish *"no phases, because all were archived"* from *"no phases, because parsing failed"* — today both emit `structure_recognized: False`, and only one of them is a defect.

**Urgency**: unchanged at CRITICAL (Architectural), and now additionally satisfying STRICT RULE 9's "observed more than once" criterion in its own right.
