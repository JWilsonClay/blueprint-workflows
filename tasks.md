# tasks.md — Sovereign Scaling Cluster (Active — only uncompleted items carry real weight)

**Note:** Units marked `**COMPLETED [ARCHIVE:YYYY-MM-DD]**` below have been independently
verified by `/implementation-plan --audit`'s Completion Marking sub-pass (dual cross-reference
against `scripts/focus/phase_status.py` + `.workflow_state/receipts/BUILD_RECEIPTS.md` — never
checkbox state alone). No phase here carries that marker yet — this plan was authored directly,
not yet executed through `/execute-build`, so no such marker would be honest. Task-level `[x]`
below reflects real, directly-verified completion (tests passing, live-run evidence cited) done
this session; it is evidence for a future audit pass, not a substitute for one.

**Checkbox states:** `[ ]` not started · `[/]` in progress · `[x]` complete (with cited evidence).

**Companion documents:** `implementation-plan.md` (repo root) carries the rationale and Detailed
Requirements per phase. `helpdesk-tickets/20260707_sovereign-scaling-cluster_meta_workflow.md`
carries the full strategic argument. This file is the checkable driver `/execute-build` and a
Gemini delegate both read.

---

## Phase 1 — Quick Wins
<!-- Marker slot: leave blank until independently verified. -->

- [x] 1.1 Build `lint_workflows.py --fix-hashes --write` mode. **Evidence:** `scripts/suite/lint_workflows.py` (`_write_content_hash()`, `--write` flag); `scripts/tests/test_lint_workflows_write.py`, 6/6 passing. Resolves `CLOSED_20260704_lint-fix-hashes-gap_workflow.md`.
- [ ] 1.2 Create `.changelogs/` directory convention and migrate Change Log sections exceeding ~10% of total word count (per `scripts/suite/analyze_workflow_lengths.py` output) to `.changelogs/<workflow-name>.md`, leaving a short pointer in the live file. Candidates in priority order: `secretary.md` (44.1% combined w/ STRICT RULES), `nodelete.md` (35.8%), `harden-workflow.md` (two Change Log sections), `workstream.md`, `implementation-plan.md` (this suite's own command file, not this plan document).
- [ ] 1.3 Re-run `analyze_workflow_lengths.py` after 1.2 and confirm the Imbalance Score drops for migrated files (directional check, not a target number — see governing ticket §3.2's dissent on treating the metric as a scored target).

**Acceptance criteria:** 1.1 tested and merged (done). 1.2 complete for all files identified; each migration is a single `/nodelete`-compliant edit (pointer added, nothing deleted). 1.3 confirms the change had the intended directional effect.

---

## Phase 2 — Instruction Density Compression

- [ ] 2.1 Apply the compression test (`implementation-plan.md`, "Instruction Density Compression" section) to `secretary.md`'s STRICT RULES and Phase control-flow.
- [ ] 2.2 Same for `nodelete.md`.
- [ ] 2.3 Same for `harden-workflow.md`.
- [ ] 2.4 Same for `workstream.md`.
- [ ] 2.5 Lint CLEAN on every file touched (`lint_workflows.py --file <name>`, 0 CRITICAL/WARNING).

**Acceptance criteria:** each compressed rule/phase is verified against the per-rule test before and after (does it change *what*, or only *how densely*); GLOSSARY/prose/Change Log sections are untouched; lint CLEAN; a genuine word-count reduction is observable in the STRICT RULES/Phase sections specifically.

---

## Phase 3 — Doorway/README Remediation (Tier A)

- [x] 3.1 Gate README self-heal behind `autoheal_enabled` (default `False`) in `IntegrityManager`. **Evidence:** `scripts/doorway/integrity.py`.
- [x] 3.2 Thread `readme_autoheal` passthrough in `DoorwayContextualizer`, explicit `False` at the real call site. **Evidence:** `scripts/doorway/doorway.py`.
- [x] 3.3 Update `scripts/tests/test_doorway.py`: existing 4 tests opt back in explicitly (`readme_autoheal=True`) to keep testing real self-heal regression behavior; 2 new tests (`TestReadmeAutohealDefaultOff`) prove the new default directly. **Evidence:** 6/6 passing.
- [x] 3.4 Remove breadcrumb README files from the working tree (`git rm` tracked, `rm` untracked) as part of this session's commit — safe now that 3.1-3.2 stop them regenerating. **Evidence:** see commit (Phase 9).
- [ ] 3.5 Append a provenance note (not closure) to `helpdesk-tickets/20260705_sentinel-doorway-redesign_workflow.md` recording that its Phase 0 prerequisite is done and its Phase 1-6 architecture is folded into Phase 8 below.
- [ ] 3.6 **Explicitly not authorized, listed so it isn't silently lost:** git-history purge of the 8 historical commits touching `README.md` files (Tier B). Requires `git filter-repo` + force-push to the public remote. Do not execute without a fresh, separate, explicit user go-ahead — see governing ticket §5.3 and §7 risk entry. If that authorization is later given, this becomes its own task with its own acceptance criteria; none are specified here on purpose.

**Acceptance criteria:** 3.1-3.4 done and tested (yes, this session). 3.5 done. 3.6 stays unauthorized unless a future, separate instruction says otherwise.

---

## Phase 4 — Verification-Spine Re-Verification (4 workflows whose shape changed since 2026-06-02)

- [ ] 4.1 Re-run Honest-Design Discipline against current `/execute-build` (Sovereign v5, 2026-07-06) — confirm or correct the archived seed design before building.
- [ ] 4.2 Build `/execute-build`'s engine per the (confirmed or corrected) seed design, following the ten-step recipe in the archive file.
- [ ] 4.3 Re-run Honest-Design Discipline against current `/secretary` (Sovereign v3, 2026-07-04); build its engine.
- [ ] 4.4 Re-run Honest-Design Discipline against current `/triage` (Sovereign v3, 2026-05-23); build its engine.
- [ ] 4.5 Re-run Honest-Design Discipline against current `/harden-workflow` (Sovereign v4, 2026-07-04); build its engine.

**Acceptance criteria:** each of the four gets a real, tested, read-only engine under `scripts/<name>/`; each `.md` hardened per the recipe's Step F; lint CLEAN; ticket opened and closed per Steps B/I. 4.1-4.2 (`/execute-build`) done first — Phase 6 depends on it.

---

## Phase 5 — Verification-Spine Engine Extraction (remaining 5)

- [ ] 5.1 `/redteam` — thin evidence rail (Ghost Logic collector); never script the adversarial verdict.
- [ ] 5.2 `/sentinel` — augment existing `scripts/doorway/` with a drift-delta layer (see archive file seed design; note Phase 3's `substrate_index.json` findings are directly relevant here — check before building, don't duplicate).
- [ ] 5.3 `/continuous-verify` — plan-alignment cross-checker, reusing `scripts/focus/anchor_scanner.py`.
- [ ] 5.4 `/investigate` — read-only forensic anchoring / citation fidelity report.
- [ ] 5.5 `/helpdesk-tickets` — ticket lifecycle engine (OPEN/CLOSED counts, schema validation, staleness detection).

**Acceptance criteria:** same as Phase 4, per workflow.

---

## Phase 6 — Single-Engineer `/workstream` Mode (Delegation Fold 1)

- [ ] 6.1 Extend `/workstream` Phase 0a to recognize a workstream design with only Workstream B populated (A/C explicitly DORMANT in `implementation-plan.md`'s Roles table, not silently absent).
- [ ] 6.2 Extend `/implementation-plan` Phase 6 (Workstream Design) to support generating a single-engineer design; skip rotation formula, cross-workstream conflict scan, PM/Architect ceremony when in this mode.
- [ ] 6.3 Confirm Pre-Flight Manifest, Engineer Brief, Handoff Block work unmodified in single-engineer mode (they shouldn't need changes — verify, don't assume).
- [ ] 6.4 Add the bounded-scope safety rule explicitly: single-engineer delegations MUST be scoped to one phase/slice, never an entire multi-phase plan in one hop. STRICT RULE addition to `/workstream`, citing the $200 Grok Build incident as the named precedent.
- [ ] 6.5 Confirm `/implementation-plan --audit --workstreams` (or a solo-mode variant) runs cleanly against a single-populated workstream — verify the Coverage Ledger audit doesn't assume 3 workstreams exist.

**Acceptance criteria:** a real (even if trivial/synthetic) single-engineer workstream design + execution + audit cycle completes end-to-end before Phase 8's real pilot is attempted.

---

## Phase 7 — User Training Guide (Delegation Fold 2)

- [ ] 7.1 Write `docs/GEMINI_WORKSTREAM_GUIDE.md`: invocation steps for `/workstream --gemini` in single-engineer mode, the Engineer Brief / Handoff Block round-trip explained end to end for a human operator (not just an agent).
- [ ] 7.2 After Phase 8's pilot runs, add the worked example from that real run to the guide (not a hypothetical one).

**Acceptance criteria:** the guide exists, is accurate against Phase 6's actual built behavior (not aspirational), and was genuinely used for Phase 8 rather than written after the fact from memory of how it went.

---

## Phase 8 — First Live Delegation Pilot

- [ ] 8.1 Select the doorway `substrate_index.json` architecture (`helpdesk-tickets/20260705_sentinel-doorway-redesign_workflow.md`, Phase 1-4) as the pilot target, or confirm a different, comparably well-specified and appropriately-small candidate.
- [ ] 8.2 Claude produces the design/plan artifacts for the pilot slice (already largely done — that ticket has a JSON schema draft and verification checklist).
- [ ] 8.3 Hand off to Gemini via the Phase 6 mechanism, one bounded slice.
- [ ] 8.4 Claude runs the Coverage Ledger audit on the returned work before accepting it.
- [ ] 8.5 Record the outcome (PASS/CONCERNS/FAIL, what worked, what didn't) in `PROCESS_LEARNINGS.md` — this is the pattern's first real test and the suite's own retrospective discipline applies to it same as anything else.

**Acceptance criteria:** one real, bounded unit of work is genuinely built by Gemini and genuinely verified by Claude, with an honest retrospective regardless of outcome.

---

## Phase 9 — Session Close (this session's own authorized cleanup)

- [x] 9.1 Close `helpdesk-tickets/20260704_lint-fix-hashes-gap_workflow.md` with a real Remediation Record (Phase 1.1 resolves it).
- [x] 9.2 Close `helpdesk-tickets/20260705_triage-session-handover_workflow.md` — its one live recommendation independently confirmed already built (`TRIAGE_RECEIPTS.md` exists, wired in `triage.md:426`).
- [ ] 9.3 Run full test suite (`./run_tests.sh`) — must show all tests passing.
- [ ] 9.4 Lint every `.md` touched this session — 0 CRITICAL.
- [ ] 9.5 Commit this session's real work (code changes, ticket updates, plan/tasks files, README removal). Do not push without a separate explicit request.

**Acceptance criteria:** 9.1-9.2 done with real Remediation Records (not just renamed). 9.3-9.5 complete before this session ends.

---
