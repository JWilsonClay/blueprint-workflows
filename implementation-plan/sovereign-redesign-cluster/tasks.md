# tasks.md — Sovereign Redesign Cluster (Remaining Native-Path Scope)

**Read first:** `implementation-plan.md` in this same directory (the `[INTENT]`, Part 1, and Part 2 this file executes against). Do not begin Stage 1 without having read it.
**Consumed by:** `/execute-build`, pointed explicitly at this file (not the repo-root `implementation-plan.md`/`tasks.md`, which belong to a separate, unrelated campaign).
**Checkbox states:** `[ ]` not started · `[/]` in progress · `[x]` complete (requires a Phase Build Receipt in `.workflow_state/receipts/BUILD_RECEIPTS.md`).

---

## Stage 0 — Verify Recovered Foundation

**Read before starting:** `docs/DESIGN_Sovereign_Redesign_Cluster_Canonical.md` "Post-Canonical" section.
**Dependencies:** none — this is the entry point.

- [x] 0.1 Run `cd scripts && ./run_tests.sh` — confirm 238/238 passing (or note and investigate any drift from this baseline before proceeding).
- [x] 0.2 Run `python3 scripts/suite/lint_workflows.py --workspace . --quiet` — confirm 0 CRITICAL. **Found + fixed 2 incidental stale content_hash gaps (secretary.md, triage.md) not caught during recovery.**
- [x] 0.3 Run `git log --oneline 7712074..HEAD` — confirm the 13 expected commits (10 recovered + 1 test/hash fix + 1 pillar-docs commit + 1 capability-gate-amendment commit) are present, or note what's changed since and why. **20 commits present (recovery + capability-gate + cross-refs + this plan's own generation + this stage's hash fix); all accounted for.**

**Acceptance criteria:** all three checks pass or any deviation is explained in the Phase Build Receipt before Stage 1 begins.

---

## Stage 1 — Prototype Pass (prove the native pipeline shape before building scaffolding around it)

**Read before starting:** `docs/design-pillars/PILLAR_01_CONTEXT_SESSION_INITIALIZATION.md` (for PR 01-03's original scope), `PILLAR_02_DESIGN_ORCHESTRATION_FORMULA.md` §15, `PILLAR_03_EXECUTION_DELEGATION_FORMULA.md` §15.
**Dependencies:** Stage 0.

- [x] 1.1 Write a small, real DESIGN document for PR 01-03 (Manifest + integrity retarget + materialize, per `PILLAR_01`'s own scoping) — natively: no delegation, no payload emission. Must contain a `## [INTENT]` anchor, a `## Build Ingestion Manifest`, and a `## PR Plan`. Self-review or subagent-review to zero open issues before treating it as final (Mock Trap guard — see `implementation-plan.md` Risk table). **Done: `docs/DESIGN_PR_01_03_Manifest_Index_Retarget.md`, self-reviewed (2 critiques found + resolved in the DESIGN's own Review Pass). Also found integrity.py's half of PR 01-03 already satisfied by PR 01-00 — recorded, not re-done.**
- [x] 1.2 Run `/implementation-plan` against that DESIGN's `## PR Plan` to produce a small, real `tasks.md` scoped to just PR 01-03 (a *different* tasks.md from this one — a nested prototype artifact; note its path in the Phase Build Receipt). Since the DESIGN's `## PR Plan` already reflects a decision made in Task 1.1, this run may treat Phase 0-3 (intake/investigation/6-options/HITL gate) as satisfied by the DESIGN itself and go directly to Phase 4's two-part plan — running a fresh 6-option HITL gate on top of an already-decided PR Plan would be redundant. This shortcut is exactly what Stage 4 formalizes as the native trigger. **Done: `.workflow_state/pr-01-03-tasks.md`.**
- [x] 1.3 Run `/execute-build` on that prototype `tasks.md` — actually implement PR 01-03. This is real, useful backlog work, not throwaway code. **Done: `manifest.py`/`doorway.py` retargeted, verified live against this real workspace's own MANIFEST.md, 239/239 tests (1 new, real not mocked). Commit `de82e10`.**
- [x] 1.4 Run `scripts/focus/phase_status.py` against the resulting tasks.md + `BUILD_RECEIPTS.md` — confirm it reports this phase as COMPLETE, not PENDING or ghost. This is the exact data shape Stage 5 (Pillar 4) will depend on — prove it now, cheaply. **Found + fixed a real gap: `build_phase_status_report()` hardcoded workspace-root-relative tasks.md lookup with no override, would have failed against this very cluster's own non-root tasks.md. Added an additive `tasks_md_path` parameter (backward-compatible default), tested. Also found my own Stage 0 receipt didn't use the exact phase title `phase_status.py` requires for its match — corrected via an appended, correctly-formatted entry (original preserved per /nodelete). Re-verified: Stage 0 now correctly resolves `checkbox_status=complete` + `receipt_status=found_complete`.**
- [x] 1.5 Dry-run check only (do not archive): confirm `nodelete.md` Pillar 6's stated archival gate (receipt + phase_status cross-ref) *would* accept this phase as a valid candidate once a completion marker exists — no marker exists yet (Pillar 4 isn't built), so this is a read of the existing gate logic against the new evidence, not an actual archive action. **Confirmed: nodelete.md's gate checks `_COMPLETE_STATUSES = {"phase complete", "project build complete"}` against phase_status.py's output — exact match against Stage 0's corrected receipt. No archive action taken (correctly — Pillar 4 doesn't exist yet to inject markers, and nothing was asked to be archived).**
- [x] 1.6 Write a short findings note (in the Phase Build Receipt) on whether the native P2-style write/review, P3-style native execute, and P4-relevant data shape actually cohered end to end. Any friction found here gets fixed now, before Stages 3-5 build permanent scaffolding around this same shape. **See Phase Build Receipt below and BUILD_RECEIPTS.md entry. Summary: the pipeline coheres. Two real, small, unrelated gaps were found and fixed (phase_status.py's path assumption; receipt-title exactness) — both were latent before this stage, surfaced only because Stage 1 exercised real data end to end. Zero Grok dependency at any point. Going forward, Stages 2-7 must write BUILD_RECEIPTS.md `Phase/Stage:` values as the exact tasks.md phase title, nothing appended.**

**Acceptance criteria:** PR 01-03 is genuinely implemented and tested (real closed backlog item, not scaffolding); `phase_status.py` confirms COMPLETE against real data; findings note exists and any friction is either fixed or explicitly deferred with a filed helpdesk ticket.

---

## Stage 2 — Close Out Remaining Pillar 1 / Pillar 5 Backlog

**Read before starting:** `PILLAR_01` (for PR 01-06 scope), `PILLAR_05_TOOLING_LINTING_RUNTIME_GOVERNANCE.md` (for PR 05-03/05-04 scope).
**Dependencies:** Stage 1 (uses its findings note if any surfaced).

- [x] 2.1 PR 01-06 equivalent: role.md / `~/.claude/CLAUDE.md` cross-refs / `docs/FOLDER_OWNERSHIP.md` / `manifest/SUITE_HEALTH.md` / `process_learnings/PROCESS_LEARNINGS.md` updates + the "Doorway Design Invariant" statement, per `PILLAR_01`'s own spec. **Diff-verify every edit against the file's pre-edit content before committing** — this session's own near-miss (a silent merge truncation of a 661-line file) is the concrete reason this check is explicit, not assumed. **Done: Invariant now stated verbatim in 4 places (sentinel.md already had it; role.md, doorway.py docstring, PROCESS_LEARNINGS.md added). `manifest/SUITE_HEALTH.md` supersession correctly deferred to Stage 7 (Task 7.4) — "post-close" per PILLAR_01's own spec.**
- [x] 2.2 PR 05-03 equivalent: complete the receipt family beyond the skeleton `c1d49e6` landed — DESIGN_RECEIPTS and TRIAGE_RECEIPTS emission wired end-to-end (not just `coverage.py` constants), matching the exact heredoc parity `BUILD_RECEIPTS.md` already uses. **Done, with a significant finding: TRIAGE_RECEIPTS emission (triage.md) was code-complete but never exercised — running it for real to verify found a suite-wide bug (quoted heredoc delimiter suppresses ALL `$()` substitution, so every receipt-writing convention in the suite — 6 workflow files — would silently write literal `$(date...)`/`$(git rev-parse...)` text instead of real values). Fixed in all 6 files, verified live, 2 already-written broken entries corrected via appended notes per /nodelete. DESIGN_RECEIPTS emission correctly remains Stage 3's job (Task 3.2 already covers it) — coverage.py's consumption side is generic and ready, only the emitter (design-orchestrator.md) doesn't exist yet.**
- [x] 2.3 PR 05-04 equivalent: linter robustness + real test coverage for the Pillar 1/5 changes recovered this session, beyond the two gaps this session already patched (`test_suite_checks.py`, `role.md` hash). **Done: new `scripts/tests/test_doorway_auditor.py` (6 tests) — direct unit coverage for the Tier 1 `ownership_incomplete` gate (PR 01-02) and `build_substrate_index()` (PR 01-01), neither of which had a dedicated persisted test before (only "manual unit simulations" noted in the original commit messages). Named, deferred gap (not silently skipped): Option C's auto-escalation trigger (doorway.py) still has no dedicated test — verifying it properly requires simulating incremental-scan carry-over state precisely, judged out of proportion for this stage; still only manually verified per the original pr-01-00 commit message. Worth a helpdesk ticket if it ever misfires.**

**Acceptance criteria:** full test suite still green, lint still 0 CRITICAL, every edited file diffed against its pre-edit version and confirmed intentional (no silent truncation).

---

## Stage 3 — Build Pillar 2 Native Path (Design Orchestration)

**Read before starting:** `PILLAR_02_DESIGN_ORCHESTRATION_FORMULA.md` in full, especially §15.
**Dependencies:** Stage 1 (reuses the proven shape from Task 1.1).

- [x] 3.1 Create `claude-commands/design-orchestrator.md`, Phases 0-2 per `PILLAR_02` §4.1: intake, sentinel + focus primary payload assembly, divergence/quality + `[INTENT]` + payload assembly — using the exact shape already proven working in Stage 1 Task 1.1, not a fresh design. **Done.**
- [x] 3.2 Phases 3-5 per the §15 native path: the orchestrating agent performs the write/review loop itself — independent critique to zero open issues, concretely via a fresh subagent (e.g. Claude Code's Agent tool, `subagent_type: general-purpose` or `Plan`) that has not seen the draft's authoring context, so the review is genuinely independent rather than the same context critiquing itself; adversarial self-critique using `/quality` Step 5 is the floor when subagent spawning isn't available — then native post-gates (focus re-verify, `/quality` chain, DESIGN_RECEIPTS emission, Manifest injection). **Done.**
- [x] 3.3 Integration points per `PILLAR_02` PR 02-06: triage/secretary/SUITE_HEALTH/role/sentinel cross-refs. **Done: triage (Trigger Matrix row), secretary (DESIGN_RECEIPTS consumption), role.md (inventory), SUITE_HEALTH.md (new row). sentinel.md deliberately not touched — its routing map is scoped to drift signals, not design-intent signals (already correctly in triage.md).**
- [x] 3.4 Harden `design-orchestrator.md` (`/harden-workflow`) and run an adversarial audit against it. **Done: genuine 8-phase hardening pass (not a rubber stamp) — Phase 1 verified all 6 structural criteria present against actual content; Phase 4d confirmed all 8 inter-workflow references resolve to real files; Phase 7d linter gate 0 CRITICAL. Grade legitimately elevated Structured → Sovereign, with the full honest sequence preserved in the file's own Change Log (created at Structured, certified to Sovereign in a separate, later entry — never claimed prematurely).**

**Acceptance criteria:** `design-orchestrator.md` exists, is Sovereign-graded, linter-clean; a DESIGN produced through it (can reuse Stage 1's or a new one) passes native post-gates with a real DESIGN_RECEIPTS.md entry. **First three criteria met. The fourth (a DESIGN produced through design-orchestrator.md's own native path with a real DESIGN_RECEIPTS.md entry) is Stage 4's own end-to-end verification (Task 4.4) — the workflow exists and is certified, but hasn't yet been exercised on a real design intent the way Stage 1 exercised PR 01-03 through the build side.**

---

## Stage 4 — Build Pillar 3 Native Path (Execution Glue)

**Read before starting:** `PILLAR_03_EXECUTION_DELEGATION_FORMULA.md` in full, especially §15.
**Dependencies:** Stage 3 for the DESIGN-producing workflow to exist formally; the *target shape* it consumes was already proven in Stage 1 without waiting on Stage 3.

- [x] 4.1 Document the native trigger directly in `execute-build.md`: detect a DESIGN with `## PR Plan` → run `/implementation-plan` against it to produce a real `tasks.md` → run `/execute-build`'s existing Phase 0-7 loop on it, unmodified. This is glue and documentation, **not new execution machinery** — the engine already exists and was exercised in Stage 1. **Done: Native Execution Trigger added to Phase 0a + GLOSSARY term; `version` 4→5, `strict_rule_count` unaffected by this task alone (see 4.2).**
- [x] 4.2 Add STRICT RULES to `execute-build.md` per `PILLAR_03` §4.4/§15 intent: traceable receipts, no Ghost Logic in the native handoff (i.e., the tasks.md generation step must be auditable — which `/implementation-plan` run produced which tasks.md, cross-referenced in the Build Log). **Done: STRICT RULES 17 (never assume Grok tool-calling availability, native is default) + 18 (traceable provenance in Build Log — the Ghost-Logic guard for this trigger) added; `strict_rule_count` 16→18. Also added the matching HITL-gate exception to `implementation-plan.md` Phase 3 (DESIGN-driven invocation may skip straight to Phase 4), `version` 4→5 there too.**
- [x] 4.3 Integration points per `PILLAR_03` PR 03-06: triage/secretary/SUITE_HEALTH/role/sentinel/focus-plan/implementation-plan cross-refs. **Done: `execute-build` cross-referenced in `triage.md`, `secretary.md`, `role.md` (verified live via grep, not assumed from memory).**
- [x] 4.4 Harden + verify: run the full DESIGN → tasks.md → execute-build chain end to end on a real (not the Stage 1 prototype, a *new* one) small item, confirming the documented trigger actually works, not just reads well. **Done: PR 05-04 (suite_checks.py test coverage) run through the full real chain — `docs/DESIGN_PR_05_04_Suite_Checks_Test_Coverage.md` (via `/design-orchestrator`'s native path) → `.workflow_state/pr-05-04-tasks.md` (via the Native Execution Trigger, Phase 0-3 satisfied by the DESIGN per the new `implementation-plan.md` exception) → `/execute-build`'s Phase 0-7 loop, all 11 tasks complete, 272/272 tests passing, 0 CRITICAL lint. The trigger held up under real friction, not just a clean read: a genuine bug surfaced in `check_glossary_usage` and was named via ticket rather than silently patched (per this DESIGN's own Acceptance Criterion 3); separately, while committing that ticket, discovered and fixed a real repo-wide gap (`.gitignore` itself was never tracked, silently excluding `process_learnings/PROCESS_LEARNINGS.md` and 22 of 25 root-level helpdesk tickets from git history, verified via `git ls-tree` set-diff against the pre-fix parent commit) — see `helpdesk-tickets/20260706_gitignore-untracked-self-and-ledgers_workflow.md`, commit `66313dd`.**

**Acceptance criteria:** `execute-build.md` carries the documented trigger; a second, independent end-to-end run (DESIGN → tasks.md → build) succeeds with a canonical Phase Build Receipt. **Met — see Task 4.4 Phase Build Receipt below.**

---

## Stage 5 — Build Pillar 4 (Post-Build Hygiene, Archival, Marking)

**Read before starting:** `PILLAR_04_POST_BUILD_HYGIENE_ARCHIVAL_NODELETE.md` in full.
**Dependencies:** Stage 1 (provides the first real completed phase to mark), `nodelete.md` Pillar 6 and `scripts/focus/phase_status.py` (pre-existing, unmodified — do not alter either while building this stage; Pillar 4 consumes them, it does not own them).

- [ ] 5.1 Add the Completion Marking sub-pass to `/implementation-plan --audit` (after the existing Coverage Ledger step): cross-reference `phase_status.py` output + `BUILD_RECEIPTS.md` + any prior audit; inject `**COMPLETED [ARCHIVE:YYYY-MM-DD]**` or `**SUPERSEDED [QUARANTINE:YYYY-MM-DD]**` markers *only* where independently verified — refuse to mark on any Ghost Logic signal.
- [ ] 5.2 Canonical templates: `templates/plan/tasks.md.template` and `templates/plan/implementation-plan.md.template`, with marker slots and a "forward items only" convention, per `docs/DESIGN_Plan_Tasks_Format_and_Sentinel_Populator.md` (superseded-but-precedent, per the canonical's own Decision section).
- [ ] 5.3 Populator script `scripts/plan/ensure_plan_templates.py` — idempotent, `--workspace`-parameterized, matching the convention of every other script in `scripts/`.
- [ ] 5.4 Sentinel integration: "Plan & Tasks Format Check" as a new sentinel phase step, per `PILLAR_04`'s spec.
- [ ] 5.5 **Verification against real data, not a fabricated example:** run the new Completion Marking sub-pass against Stage 1's already-completed PR 01-03 phase. Confirm it correctly injects `**COMPLETED [ARCHIVE:...]**` retroactively. This is the single most important acceptance check in this stage — it proves the marking logic against ground truth this plan itself produced, not a hypothetical.

**Acceptance criteria:** Stage 1's PR 01-03 phase is correctly marked by the new sub-pass; templates + populator exist and are tested; sentinel's new check runs cleanly on this workspace.

---

## Stage 6 — Cross-Cutting Integration Finish

**Read before starting:** `PILLAR_05_TOOLING_LINTING_RUNTIME_GOVERNANCE.md` remaining PR scope (05-05, 05-06).
**Dependencies:** Stages 2-5 (integrates their outputs).

- [ ] 6.1 Remaining P5 items: meta closure prep (05-05 equivalent — assemble the Phylogeny/Remediation Record scaffolding used in Stage 7).
- [ ] 6.2 End-to-end cluster verification (05-06 equivalent): run the full pipeline for real — sentinel briefing → native design (Stage 3) → native build (Stage 4) → hygiene marking (Stage 5) → `nodelete --archive` on a genuinely new, real target (not reusing Stage 1's prototype again) — the complete loop this whole cluster exists to enable.
- [ ] 6.3 Sweep all remaining INTEGRATION/Change Log appends across workflows touched anywhere in Stages 1-6 that haven't yet been cross-referenced (triage.md, secretary.md, role.md, sentinel.md, focus-plan.md, DevJournal.md, manifest/SUITE_HEALTH.md).
- [ ] 6.4 Full suite verification: `run_tests.sh` green, linter 0 CRITICAL, `/receipt-check` coverage gap at or better than pre-Stage-1 baseline.
- [ ] 6.5 **Diff-verify every file touched in this stage against its pre-edit content** before committing (same discipline as Stage 2.1, for the same reason).

**Acceptance criteria:** the full sentinel→design→build→hygiene→archive loop completes successfully on a real target; all cross-references land; suite is green.

---

## Stage 7 — Meta Closure

**Read before starting:** `claude-commands/helpdesk-tickets.md` Phase 4 (Phylogeny Disposition, Remediation Record, closure protocol) in full.
**Dependencies:** Stage 6.

- [ ] 7.1 Resolve Phylogeny Disposition for the meta-ticket: `NO TRANSFER` or a `SUITE_PHYLOGENY.md` entry, per protocol.
- [ ] 7.2 Attach a Remediation Record (if any element of this cluster is ultimately classified SUBSTANTIVE-LOGIC) or Hardening Certificate (STRUCTURAL) — per the fork this suite's own protocol already uses.
- [ ] 7.3 Rename `helpdesk-tickets/20260706_sovereign-redesign-cluster_meta_workflow.md` → `CLOSED_20260706_sovereign-redesign-cluster_meta_workflow.md`.
- [ ] 7.4 Supersede any still-open SUITE_HEALTH advisories this cluster resolves.
- [ ] 7.5 Append to `process_learnings/PROCESS_LEARNINGS.md` — including this session's own lessons (Grok Build's real cost surprised the user; a "successful" git merge silently truncated real content and needed line-by-line re-verification to catch) as named, reusable lessons, not just cluster-specific notes.
- [ ] 7.6 Run `/secretary` + `/retrospective` for full session close.

**Acceptance criteria:** meta-ticket is `CLOSED_`, Phylogeny resolved, Remediation Record/Hardening Certificate attached, PROCESS_LEARNINGS updated, `/secretary` close completed with a clean HANDOFF.md.

---

**Full cluster complete when Stage 7's acceptance criteria all pass.** No stage may be marked `[x]` without its Phase Build Receipt on file.
