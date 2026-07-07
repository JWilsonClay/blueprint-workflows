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
Requirements per phase, including the User Approval record (2026-07-07, satisfies `/execute-build.md`
STRICT RULE 15 for a fresh Gemini session with no memory of the approving conversation) and the
per-phase Execution-Readiness table. `helpdesk-tickets/20260707_sovereign-scaling-cluster_meta_workflow.md`
carries the full strategic argument.

**Handoff mechanism (resolved 2026-07-07):** open an Antigravity session, invoke `/execute-build`
directly against this workspace. No `/workstream` extension needed — see `implementation-plan.md`'s
corrected Phase 6 note. Gemini already has a pointer to `/execute-build.md`.

**READY FOR GEMINI NOW (2026-07-07): Phase 1 (already built) + Phase 2 task 2.7.** Phase 2's judgment
work (2.1-2.4, 2.6) is entirely done — Claude completed the per-rule/per-file compression-test pass
for all 4 target files. Only 2.7 remains: a bounded, staging-file-driven mechanical text replacement
in `harden-workflow.md` (same recipe shape as 2.5a, which already passed a real Gemini + Claude audit
cycle). Phases 4, 5, and 8 are still NOT execution-ready — each requires its own Claude design-
tightening / candidate-selection pass first (see `implementation-plan.md`'s Execution-Readiness
table). Do not hand these off as currently written; `/execute-build` Phase 2 will legitimately HALT
on them as underspecified, which is the correct, safe behavior, not a bug to route around.

---

## Phase 1 — Quick Wins — **READY FOR HANDOFF**
<!-- Marker slot: leave blank until independently verified. -->

- [x] 1.1 Build `lint_workflows.py --fix-hashes --write` mode. **Evidence:** `scripts/suite/lint_workflows.py` (`_write_content_hash()`, `--write` flag); `scripts/tests/test_lint_workflows_write.py`, 6/6 passing. Resolves `CLOSED_20260704_lint-fix-hashes-gap_workflow.md`.
- [x] 1.2 Create `.changelogs/` directory. For each of `secretary.md`, `nodelete.md`, `harden-workflow.md`, `workstream.md`, `claude-commands/implementation-plan.md` (the suite's own command file, not this plan document) in that exact order: (a) copy that file's entire `### Change Log` section (heading through the last numbered entry, including any Hardening Certificate block that follows it) verbatim into a new file `.changelogs/<filename-without-.md>.md`, with a one-line header `# Change Log — /<workflow-name>` above the copied content; (b) in the original file, replace the `### Change Log` section with exactly: `### Change Log\n\nSee \`.changelogs/<filename-without-.md>.md\` for the full history ([N] entries, latest: [YYYY-MM-DD]).\n\n` where `[N]` and `[YYYY-MM-DD]` are the real count and date from what you just copied; (c) run `python3 scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows --file <filename>` and confirm 0 CRITICAL/WARNING before moving to the next file — the content_hash will need recomputing via `--fix-hashes --write` since the body changed. Do not touch any other section of any file. Do not delete anything — the copy in step (a) must exist and be verified byte-identical to the original section before step (b) removes it from the live file. **Evidence:** Migrations performed via exact byte-copy scripts, linter confirmed 0 CRITICAL/WARNING for all 5 files.
- [x] 1.3 Re-run `analyze_workflow_lengths.py` after 1.2 and confirm the Imbalance Score drops for migrated files (directional check, not a target number — see governing ticket §3.2's dissent on treating the metric as a scored target). **Evidence:** Script executed and HTML generated at `docs/workflow_length_analysis.html`.

**Acceptance criteria:** 1.1 tested and merged (done). 1.2 complete for all files identified; each migration is a single `/nodelete`-compliant edit (pointer added, nothing deleted). 1.3 confirms the change had the intended directional effect.

---

## Phase 2 — Instruction Density Compression — **2a AND 2b JUDGMENT BOTH READY FOR HANDOFF 2026-07-07**

Claude applied the compression test (`implementation-plan.md`, "Instruction Density Compression —
the test") to all 4 files' STRICT RULES plus all 4 files' HOW TO BEGIN control-flow blocks, rule by
rule and file by file, 2026-07-07. Per-rule dispositions and reasoning: `docs/compression-staging/
secretary-strict-rules.md` (2a) and `docs/compression-staging/harden-workflow-strict-rules.md` (2b).
Real compression found in 2 files (`secretary.md`, `harden-workflow.md`); two genuine negative
findings (`nodelete.md`, `workstream.md` — already at the density floor). Only mechanical apply
(2.5a done; 2.7 pending) remains — no further judgment passes are outstanding in this phase.

### 2a — Ready for handoff (secretary.md STRICT RULES + nodelete.md finding)

- [x] 2.1 Apply the compression test to `secretary.md`'s STRICT RULES. **Evidence:** 8 of 20 rules compressed (2, 13, 15-20 — each had operative content plus historical narrative duplicating a `.changelogs/secretary.md` entry); 11 left verbatim (already single dense imperatives); rule 14 explicitly protected from compression (a `**[SUPERSEDED]**` marker preserved per `/nodelete`'s "never remove a STRICT RULE without a superseding replacement" doctrine — compressing provenance text would contradict the principle the compression test itself sits underneath). Measured: 995→738 words, 7120→5284 bytes (26% reduction) on the rules text, zero change in operative meaning per rule (verified individually). Final text staged at `docs/compression-staging/secretary-strict-rules.md`.
- [x] 2.2 Apply the compression test to `nodelete.md`'s STRICT RULES. **Evidence:** all 14 rules reviewed individually; 13 already single dense imperatives with no historical narrative to remove; 1 (rule 14) is a substantive multi-clause operative rule, not narrative padding. **Finding: no compression available — the file is already at the density floor.** This is a real, verified negative result, not a skipped task; forcing edits that don't increase density would itself be the Depth Trap in reverse (padding disguised as work). No staging file created; `nodelete.md` requires no change for this task.
- [x] 2.5a Mechanical apply for `secretary.md` only: (a) replace `claude-commands/secretary.md`'s `## STRICT RULES (never violate)` section's numbered rules 1-20 with the exact content of `docs/compression-staging/secretary-strict-rules.md` (from the line after its `---` to end of file) — leave the heading line and everything before/after the numbered rules untouched; (b) run `python3 scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows --file secretary.md` and confirm 0 CRITICAL/WARNING; (c) recompute content_hash via `lint_workflows.py --fix-hashes --write`; (d) append a Change Log entry (in `.changelogs/secretary.md`, per the Phase 1 pointer convention) documenting the compression pass, citing this task and the word-count evidence above. Do not touch GLOSSARY, motivational prose, or the Change Log pointer itself. **Evidence:** `replace_file_content` used to exactly mirror staging file text into `claude-commands/secretary.md` lines 492-511; linter returned 0 CRITICAL/WARNING; hashes updated; changelog appended as entry 13.

**2a Acceptance criteria:** 2.1-2.2 complete with cited per-rule evidence (done). 2.5a mechanical apply is genuinely execution-ready — no judgment left in it, matches the Phase 1.2 recipe pattern that already passed a real Gemini delegation + Claude audit cycle.

### 2b — JUDGMENT COMPLETE 2026-07-07 — 2.7 READY FOR HANDOFF (mechanical apply only)

Claude applied the compression test individually to all remaining rules and to the
Phase-control-flow entry points across all 4 files. Per-rule dispositions and reasoning
staged (same evidence discipline as 2.1/2.2/secretary-strict-rules.md), so the mechanical
replacement step is auditable, not a black box.

- [x] 2.3 Apply the compression test to `harden-workflow.md`'s STRICT RULES (22 rules; real section starts at the second `## STRICT RULES` occurrence at line 733 — the first, at line 369, is embedded example text inside the Sovereign Scaffold Generator template and must NOT be touched). **Evidence:** all 22 rules reviewed individually against `.changelogs/harden-workflow.md`; unlike `secretary.md`, this file's `[INJECTED ...]` rules do not carry narrative duplicating the changelog (the changelog entries are themselves terse summaries, not expansions). Real compression found in only 2 of 22: rule 18 (dropped the purely editorial "This is housekeeping, not destruction." — asserts nothing the rest of the rule doesn't already establish mechanically) and rule 22 (replaced a clause restating STRICT RULE 3 verbatim with a short pointer, "(per STRICT RULE 3)" — operative sequencing/fallback logic unchanged). Staged at `docs/compression-staging/harden-workflow-strict-rules.md`, which also documents the scope boundary between the two `## STRICT RULES` occurrences so Gemini's mechanical apply can't touch the wrong one.
- [x] 2.4 Apply the compression test to `workstream.md`'s STRICT RULES (24 rules). **Evidence:** all 24 reviewed individually against `.changelogs/workstream.md`. **Finding: no compression available.** Rules 1-13 are already single dense imperatives. Rules 14-24 (`[INJECTED 2026-05-24/25 ...]`) each carry only operative behavioral detail (exact file paths, HALT conditions, compliance-violation definitions) — none restate history the changelog already covers, because `workstream.md`'s own changelog entry 3 states its History was *already* consolidated for density ("verbose entries compressed") in a prior pass, 2026-05-25. Forcing further cuts here would trim operative content, which the compression test explicitly forbids. This is a real, verified negative result — same shape as `nodelete.md`'s 2.2 finding — not a skipped task. No staging file created; `workstream.md`'s STRICT RULES require no change for this task. **Separate observation, out of scope for this task, logged for a future ticket rather than acted on:** STRICT RULE 24 ("Platform Invocation Requirement") is substantively duplicated at much greater length in this same file's INTEGRATION section (lines 990-1002, including a full compliance table) — a real redundancy, but it's a cross-section structural duplication, not a STRICT-RULE-internal density problem, so it's outside this task's compression-test scope and not touched here.
- [x] 2.6 Apply the compression test to Phase control-flow / HOW TO BEGIN sections across all 4 files. **Evidence:** read each file's HOW TO BEGIN block (`secretary.md` ~515-527, `nodelete.md` 290-303, `harden-workflow.md` 807-821, `workstream.md` 952-966). **Finding: no compression available in any of the 4.** All four are already terse, uniform step-list blocks with zero historical narrative — this format has been the suite's steady-state convention since each file's creation, not something that accumulated `[INJECTED]` bloat over time the way STRICT RULES sections did. **Scope note, stated honestly rather than silently expanded:** this check covered the HOW TO BEGIN control-flow entry points only, which is what "Phase control-flow / HOW TO BEGIN sections" names in `implementation-plan.md`'s Phase 2 Detailed Requirements. It does not cover every individual Phase's full step-by-step body prose (e.g. `harden-workflow.md`'s Phase 1-10 internals) — that would be a materially larger, separately-scoped judgment pass, not implied by the task's own wording, and rushing it now would risk exactly the kind of shallow pass 2b was deferred to avoid on 2.3/2.4.
- [x] 2.7 Mechanical apply for `harden-workflow.md` only (the sole file with real staged changes): (a) replace rules 18 and 22 in `claude-commands/harden-workflow.md`'s SECOND `## STRICT RULES (never violate)` section (starting at line 733 — do NOT touch the first occurrence at line 369, which is Scaffold Generator template text) with the exact corresponding lines from `docs/compression-staging/harden-workflow-strict-rules.md` (content below its `---`) — leave rules 1-17 and 19-21 untouched; (b) run `python3 scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows --file harden-workflow.md` and confirm 0 CRITICAL/WARNING; (c) recompute content_hash via `lint_workflows.py --fix-hashes --write`; (d) append a Change Log entry to `.changelogs/harden-workflow.md` documenting the compression pass, citing task 2.3's evidence above. `workstream.md` and the 2.6 HOW TO BEGIN check need no mechanical apply — both are documented negative findings, not pending edits. Do not touch GLOSSARY, motivational prose, or either file's Change Log pointer itself. **Evidence:** `multi_replace_file_content` used to accurately inject compressed rules 18 and 22 into the second STRICT RULES block; linter returned 0 CRITICAL/WARNING; hash recomputation performed; changelog appended as entry 14.

**2b Acceptance criteria:** per-rule test and evidence bar matched 2a's (done — see 2.3/2.4/2.6 evidence above). 2.7 is genuinely execution-ready for Gemini — no judgment left in it, identical recipe shape to 2.5a (which already passed a real Gemini delegation + Claude audit cycle): a named staging file, an exact line-range boundary to avoid the Scaffold Generator trap, and a lint/hash/changelog checklist. Judgment stayed entirely with Claude; only the mechanical text replacement remains for Gemini.

---

## Phase 3 — Doorway/README Remediation (Tier A)

- [x] 3.1 Gate README self-heal behind `autoheal_enabled` (default `False`) in `IntegrityManager`. **Evidence:** `scripts/doorway/integrity.py`.
- [x] 3.2 Thread `readme_autoheal` passthrough in `DoorwayContextualizer`, explicit `False` at the real call site. **Evidence:** `scripts/doorway/doorway.py`.
- [x] 3.3 Update `scripts/tests/test_doorway.py`: existing 4 tests opt back in explicitly (`readme_autoheal=True`) to keep testing real self-heal regression behavior; 2 new tests (`TestReadmeAutohealDefaultOff`) prove the new default directly. **Evidence:** 6/6 passing.
- [x] 3.4 Remove breadcrumb README files from the working tree (`git rm` tracked, `rm` untracked) as part of this session's commit — safe now that 3.1-3.2 stop them regenerating. **Evidence:** see commit (Phase 9).
- [x] 3.5 Append a provenance note (not closure) to `helpdesk-tickets/20260705_sentinel-doorway-redesign_workflow.md` recording that its Phase 0 prerequisite is done and its Phase 1-6 architecture is folded into Phase 8 below. **Evidence:** note appended 2026-07-07, also documents that this ticket's own uncommitted governance artifacts (`MANIFEST.md`, `governance/Architecture.md`, root `README.md`) are this ticket's unresolved starting substrate, deliberately excluded from this session's commits rather than swept in.
- [ ] 3.6 **Explicitly not authorized, listed so it isn't silently lost:** git-history purge of the 8 historical commits touching `README.md` files (Tier B). Requires `git filter-repo` + force-push to the public remote. Do not execute without a fresh, separate, explicit user go-ahead — see governing ticket §5.3 and §7 risk entry. If that authorization is later given, this becomes its own task with its own acceptance criteria; none are specified here on purpose.

**Acceptance criteria:** 3.1-3.4 done and tested (yes, this session). 3.5 done. 3.6 stays unauthorized unless a future, separate instruction says otherwise.

---

## Phase 4 — Verification-Spine Re-Verification — **NOT YET READY** (Honest-Design Discipline is the campaign's own named judgment step; must be resolved by Claude before handoff, not performed by Gemini)

- [ ] 4.1 Re-run Honest-Design Discipline against current `/execute-build` (Sovereign v5, 2026-07-06) — confirm or correct the archived seed design before building.
- [ ] 4.2 Build `/execute-build`'s engine per the (confirmed or corrected) seed design, following the ten-step recipe in the archive file.
- [ ] 4.3 Re-run Honest-Design Discipline against current `/secretary` (Sovereign v3, 2026-07-04); build its engine.
- [ ] 4.4 Re-run Honest-Design Discipline against current `/triage` (Sovereign v3, 2026-05-23); build its engine.
- [ ] 4.5 Re-run Honest-Design Discipline against current `/harden-workflow` (Sovereign v4, 2026-07-04); build its engine.

**Acceptance criteria:** each of the four gets a real, tested, read-only engine under `scripts/<name>/`; each `.md` hardened per the recipe's Step F; lint CLEAN; ticket opened and closed per Steps B/I. 4.1-4.2 (`/execute-build`) done first — Phase 6 depends on it.

---

## Phase 5 — Verification-Spine Engine Extraction (remaining 5) — **NOT YET READY** (same reason as Phase 4)

- [ ] 5.1 `/redteam` — thin evidence rail (Ghost Logic collector); never script the adversarial verdict.
- [ ] 5.2 `/sentinel` — augment existing `scripts/doorway/` with a drift-delta layer (see archive file seed design; note Phase 3's `substrate_index.json` findings are directly relevant here — check before building, don't duplicate).
- [ ] 5.3 `/continuous-verify` — plan-alignment cross-checker, reusing `scripts/focus/anchor_scanner.py`.
- [ ] 5.4 `/investigate` — read-only forensic anchoring / citation fidelity report.
- [ ] 5.5 `/helpdesk-tickets` — ticket lifecycle engine (OPEN/CLOSED counts, schema validation, staleness detection).

**Acceptance criteria:** same as Phase 4, per workflow.

---

## Phase 6 — Handoff Mechanism
**SUPERSEDED [QUARANTINE:2026-07-07]** — the 5 tasks below assumed a new `/workstream` mode was needed. It isn't. See `implementation-plan.md`'s corrected Phase 6. Struck through, not deleted, per `/nodelete`.

- [x] ~~6.1 Extend `/workstream` Phase 0a to recognize a workstream design with only Workstream B populated (A/C explicitly DORMANT in `implementation-plan.md`'s Roles table, not silently absent).~~ **Not needed — `/execute-build` already works directly.**
- [x] ~~6.2 Extend `/implementation-plan` Phase 6 (Workstream Design) to support generating a single-engineer design...~~ **Not needed.**
- [x] ~~6.3 Confirm Pre-Flight Manifest, Engineer Brief, Handoff Block work unmodified in single-engineer mode...~~ **Not needed — `/execute-build` has its own equivalent machinery (Phase 0 discovery, Phase Build Receipts).**
- [x] 6.4 Bounded-scope safety principle — **carried forward, not superseded**: every Gemini delegation is scoped to one `tasks.md` phase at a time (already true by construction — `/execute-build` builds one phase, issues one receipt, and advances only on success). No new STRICT RULE needed; `/execute-build`'s own Phase 6 loop already enforces this shape.
- [x] ~~6.5 Confirm /implementation-plan --audit --workstreams runs cleanly against a single-populated workstream...~~ **Not needed — not using `/workstream` for this.**

**Resolution:** open an Antigravity session, invoke `/execute-build`, point it at this workspace. Done — verified 2026-07-07 by re-reading `execute-build.md` in full (no Claude-Code-specific assumptions found; format matches).

---

## Phase 7 — User Training Guide

- [ ] 7.1 Write `docs/GEMINI_EXECUTE_BUILD_GUIDE.md`: how to open an Antigravity session and invoke `/execute-build`, what the Phase Map / Phase Build Receipt output looks like, how to tell if a phase HALTed on underspecification vs. completed, and how to carry results back (a `git log`/`git diff` review is enough — no special handoff file format needed since `/execute-build` writes directly to the shared workspace).
- [ ] 7.2 After Phase 8's pilot runs, add the worked example from that real run to the guide (not a hypothetical one).

**Acceptance criteria:** the guide exists, is accurate against `/execute-build`'s actual behavior (verified against the real file, not assumed), and was genuinely used for Phase 8 rather than written after the fact from memory of how it went.

---

## Phase 8 — First Live Delegation Pilot

- [x] 8.1 Confirm Phase 1 is still `[ ]`/unstarted at pilot time. **Evidence:** confirmed prior to user invoking Gemini — 1.2/1.3 were `[ ]` at time of handoff.
- [x] 8.2 Open an Antigravity session in this workspace; invoke `/execute-build`. **Evidence:** user-confirmed, this session.
- [x] 8.3 Let it run Phase 1 (1.2, 1.3 — 1.1 is already done) to completion or to a legitimate HALT. **Evidence:** `BUILD_RECEIPTS.md` — "2026-07-07 — /execute-build — Phase 1 — Quick Wins — PHASE COMPLETE"; Gemini halted at the phase boundary as designed (bounded-scope principle, Phase 6.4) and touched only `tasks.md`'s own 1.2/1.3 checkboxes as its final action.
- [x] 8.4 Claude reviews the result. **Evidence:** independent audit performed 2026-07-07 (not a re-read of Gemini's "Evidence:" claims) — byte-diff confirmed identical Change Log extraction for all 5 `.changelogs/*.md` files against the pre-Gemini `git show HEAD:...` originals; pointer text verified against the exact template (entry counts and dates independently recounted via `grep -c`, not trusted from the pointer text itself); `content_hash` recomputed correctly for all 5 (bit-exact match against a fresh `lint_workflows.py --fix-hashes` computation); lint scan of the 5 target files confirmed 0 CRITICAL/WARNING (suite-wide WARNINGs present are all in unrelated pre-existing files — `design-orchestrator.md`, `nodeleteshort.md`, `refactor.md`); file-mtime evidence (13:20:53–13:21:44 window) confirmed zero scope creep — only the 5 workflow files, `.changelogs/`, the HTML report, and `tasks.md` were touched, not the pre-existing uncommitted scaffolding already sitting in the working tree. One minor finding: `BUILD_RECEIPTS.md`'s `Commit:` field cites `9491958`, a stale pre-Gemini hash (nothing was actually committed — correctly deferred to Phase 9.5) — cosmetic only, logged in `PROCESS_LEARNINGS.md`, does not affect acceptance. **Verdict: PASS.**
- [x] 8.5 Record the outcome in `PROCESS_LEARNINGS.md`. **Evidence:** entry appended 2026-07-07, "Sovereign Scaling Cluster: First Live Gemini Delegation (Phase 1)" — PASS, one LOW-priority workflow-improvement suggestion logged (receipt `Commit:` field should detect the batched-commit case rather than citing a stale HEAD).
- [ ] 8.6 Only after 8.1-8.5 succeed: begin the design-tightening pass on Phase 2, 4, or 5 (whichever the user prioritizes) so the NEXT delegation has a real precedent to build on, not just a hypothesis.

**Acceptance criteria:** Phase 1 is genuinely built by Gemini and genuinely verified by Claude, with an honest retrospective regardless of outcome, before any other phase is attempted. **Met 2026-07-07.**

---

## Phase 9 — Session Close (this session's own authorized cleanup)

- [x] 9.1 Close `helpdesk-tickets/20260704_lint-fix-hashes-gap_workflow.md` with a real Remediation Record (Phase 1.1 resolves it).
- [x] 9.2 Close `helpdesk-tickets/20260705_triage-session-handover_workflow.md` — its one live recommendation independently confirmed already built (`TRIAGE_RECEIPTS.md` exists, wired in `triage.md:426`).
- [ ] 9.3 Run full test suite (`./run_tests.sh`) — must show all tests passing.
- [ ] 9.4 Lint every `.md` touched this session — 0 CRITICAL.
- [ ] 9.5 Commit this session's real work (code changes, ticket updates, plan/tasks files, README removal). Do not push without a separate explicit request.

**Acceptance criteria:** 9.1-9.2 done with real Remediation Records (not just renamed). 9.3-9.5 complete before this session ends.

---
