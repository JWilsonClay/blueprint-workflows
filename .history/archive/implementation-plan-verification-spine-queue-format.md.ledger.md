# Archival Ledger — implementation-plan.md (Verification-Spine Upgrade Campaign, QUEUE-table format)

Append-Only Ledger (`nodelete.md` Pillar 6). Entries accumulate; a prior entry is never edited or removed.

---

## 2026-07-07 — Superseded by tasks.md-paired format (Sovereign Scaling Cluster)

**Archived from:** `implementation-plan.md` (repo root), as it stood through the 2026-07-05 `/receipt-check` ITERATION LOG entry, immediately before this cluster's revision.

**Nature of this archival — read before assuming the standard gate applied:** this is **not** a Completion Marking archival under `/implementation-plan --audit`'s dual `phase_status.py` cross-reference (that mechanism verifies `tasks.md`-shaped `## Phase N` units against `BUILD_RECEIPTS.md`; this document was a self-perpetuating QUEUE table with no such units, and was never meant to be consumed by `phase_status.py`). This is a **supersession archival**, authorized directly by the user (`helpdesk-tickets/20260707_sovereign-scaling-cluster_meta_workflow.md`, §0: *"supersedes where necessary, quarantined where needed"*): the QUEUE-table *mechanism* (self-perpetuating BOOT PROTOCOL, one-upgrade-per-context loop) is superseded by the standard `implementation-plan.md` + `tasks.md` pair per `templates/plan/`. The underlying *work* the QUEUE table tracked is not complete — 9 items remain PENDING, 2 DEFERRED — and continues, now inside the new `tasks.md`. Archiving the container format here preserves the real historical engineering record (the five completed upgrades' ITERATION LOG entries) without losing it to an in-place overwrite, and without falsely implying the underlying work is done.

**Verification at archival time:** `manifest/SUITE_HEALTH.md` confirms the five DONE engines' real Sovereign grades and hardening dates (`/focus-plan` v3 2026-07-04, `/quality` v3 2026-05-25, `/harden` v3 (Std Ver 2 era), `/iterate-test` v3, `/receipt-check` v3 2026-07-05) — cross-checked against this file's own ITERATION LOG below, consistent.

**Archived content (verbatim, full file as it stood before this cluster's revision):**

```markdown
# Implementation Plan — Sovereign Verification-Spine Upgrade Campaign
### A self-perpetuating, context-resilient execution protocol. One large upgrade per context window.

> **START HERE — you are a fresh-context agent.** You have no memory of prior sessions. This document is your complete context. Do not look for hidden state. Read this whole file top to bottom, then follow the **BOOT PROTOCOL** below. Everything you need is here or in the two reference implementations it names.

---

## [INTENT] User Objective

> Upgrade the Sovereign Suite's verification workflows, one at a time, using a proven architectural pattern: **externalize each workflow's deterministic verification layer into a read-only, script-backed "engine," and keep the irreducible judgment in the model.** Two workflows are already done (`/focus-plan`, `/quality`) and serve as templates. A fresh agent must be able to load this plan, autonomously execute the next upgrade end-to-end, update this plan, suggest the next, and halt — so the user runs `/clear` and loops without losing a beat.
>
> The non-negotiable boundary: **never script irreducible judgment.** A script that pretends to assess quality, security excellence, or adversarial soundness is a Mock Trap / Grade Fraud. Engines verify *process receipts, structural facts, and mechanical evidence* — judgment stays with the model.
>
> Campaign started 2026-06-02. Marked /nodelete: this section may never be removed, only updated by explicit user instruction.

---

## ⟳ BOOT PROTOCOL (execute every fresh context, in order)

1. **Read this entire plan.** Internalize THE CONCEPT and the HONEST-DESIGN DISCIPLINE below.
2. **Read your behavioral frame:** the global frame is auto-loaded (faith context, no-praise directive, ambiguity protocol). Also skim `claude-commands/role.md` (you are the Senior Architect of Workflows).
3. **Read your two reference implementations** (these are your templates — do not skip):
   - `scripts/focus/` (engine) + `claude-commands/focus-plan.md` (v3 thin-rail workflow)
   - `scripts/quality/` (engine) + `claude-commands/quality.md` (v4 thin-rail workflow)
4. **Find the work:** open the **QUEUE** table. Take the **topmost `PENDING`** row. If there are no `PENDING` rows, first run **NEXT-WORKFLOW SELECTION** to append one, then take it.
5. **Execute the UPGRADE RECIPE on that one workflow only.** Do not batch. Do not do two.
6. **Update this plan:** set the row's status to `DONE`, and append a dated entry to the **ITERATION LOG**.
7. **Suggest the next** logical workflow (append it to the QUEUE as `PENDING` with a one-line rationale if it isn't already there).
8. **HALT** with a short report ending in the exact line: `READY FOR /clear — next: /<workflow>`. Then stop. The user will `/clear` and re-load this plan.

**You do exactly one upgrade per context.** Steps 5–8 are the whole job. If you run low on context mid-recipe, finish the current sub-step, write an honest `IN-PROGRESS` note into the ITERATION LOG with what remains, set the QUEUE row to `IN-PROGRESS`, and HALT — the next fresh agent resumes from your note.

---

## THE CONCEPT (what we are doing and why)

The suite's verification workflows historically enforced their core guarantees by **instruction** — they *asked* the agent to gather evidence and *trusted* it did. That is the weakest enforcement model; a capable model routes around the ceremony, and the guarantee (that a check actually happened) rests on nothing structural. The fix, proven twice:

- **Split each workflow into a deterministic half and a judgment half.**
- **Build the deterministic half as a read-only Python "engine"** under `scripts/<name>/`, modeled on `scripts/doorway/` (which already backs `/sentinel`). It reads the substrate, emits a structured JSON evidence report, and **writes nothing** to the workspace.
- **Reduce the workflow `.md` to a thin "verification rail"** that runs the engine and reasons over its output — keeping every judgment step intact.
- Because a *script* produced the evidence, the agent **cannot hallucinate it**. The anti-Hallucinated-Success / anti-Mock-Trap guarantee becomes architectural.

**The two reference cases differ in proportion — study both:**
- `/focus-plan` (v3): the deterministic half was the *bulk* (parse the plan, grep the substrate for anchors, separate production vs test matches). The engine carries most of the load.
- `/quality` (v4): quality is *irreducible judgment* — it cannot be scored by a script. So the engine verifies only the **process receipts** (witness-log validity, chain-tag completeness) and flags **mechanical smells** (one-directional, advisory). The judgment stayed 100% in the 7-step protocol. The engine is a *thin rail*, not a scorer.

Every workflow you upgrade sits somewhere on that spectrum. Your first real task each cycle is to **find where**, honestly.

---

## HONEST-DESIGN DISCIPLINE (the mandatory judgment step — do this before writing any engine code)

For the target workflow, answer in the ticket and the ITERATION LOG:

1. **What is mechanically verifiable here?** (file/symbol existence, receipt format, checklist items with deterministic signatures, import/call relationships, git facts, log presence.) → this is the engine.
2. **What is irreducible judgment?** (Is this output *excellent*? Is this design *sound*? Is this adversarial critique *complete*?) → this stays in the model, untouched.
3. **The Mock-Trap test:** if your proposed engine would have to *judge* (2) to produce its result, STOP. You are about to build a Mock Trap. Redesign it to verify (1) only, and make any heuristic signal **one-directional and advisory** (a finding means "likely defect"; the absence of a finding means *nothing* about quality — say so loudly in code, schema, and the workflow).

If a workflow turns out to have **no** meaningful deterministic layer, that is a finding: report it and recommend a surgical defect-fix instead of an engine. Do not manufacture an engine to fit the pattern. (None of the three queued workflows are in this category — each has a real deterministic layer, sketched below.)

---

## THE QUEUE (state machine — keep this table current)

| # | Workflow | Status | Engine = deterministic layer | Judgment stays | Named pattern made structural |
|---|----------|--------|------------------------------|----------------|-------------------------------|
| — | `/focus-plan` | **DONE** (v3, `scripts/focus/`) | plan parse + substrate grep + test-path split | intent, negative-space, HALT gate | Ghost Logic / Hallucinated Success |
| — | `/quality` | **DONE** (v4, `scripts/quality/`) | witness-ledger audit + chain-tag verify + smell lint | the 7-step quality verdict | (process receipts; judgment NOT scripted) |
| 1 | `/harden` | **DONE** (v3, `scripts/harden/`) | CWE signature scan + **grade ceiling computed from findings** | threat model, Sound-Effect-Execution, final grade (≤ ceiling) | **Grade Fraud** (made structural via one-directional ceiling) |
| 2 | `/iterate-test` | **DONE** (v3, `scripts/iterate/`) | Mock-Trap detector (AST): imported production symbols **patched** (behavior replaced) vs **called un-patched** + hardcoded-assertion tautology (Python-first) | PRIMARY-vs-INFRASTRUCTURE call + "does this test the real intelligence?" final verdict | **Mock Trap** (made structural via one-directional fidelity signal) |
| 3 | `/redteam` | **PENDING** | thin evidence rail: Ghost Logic collector (claimed behavior ↔ actual code + log evidence) | the 5-persona adversarial verdict | Ghost Logic / Hallucinated Success |
| 4 | `/execute-build` | **PENDING** | task-state machine validator: parse `tasks.md` phase/task markers, verify Build Receipt presence per completed phase, detect orphaned `[/]` tasks, check `phase_count` frontmatter coherence against the `.md` plan | the actual build decisions, phase ordering judgment, and HALT-or-proceed calls | **Orphaned Execution** (incomplete phase left open across context windows) |
| 5 | `/sentinel` | **PENDING** | doorway engine already backs this (`scripts/doorway/`); augment with a "drift delta" layer: compare `WORKFLOW_MANIFEST.md` declared suite state against live `lint_workflows.py` output and `dependency_graph.json` freshness | the architectural drift verdict and routing decision | **Context Erosion** / stale-state drift |
| 6 | `/continuous-verify` | **PENDING** | plan-alignment cross-checker (reuse `scripts/focus/` anchor_scanner): for each completed phase in `tasks.md`, verify a corresponding Build Receipt and Validation Receipt exist; emit a coverage gap matrix | the "does this implementation satisfy the intent" verdict | **Hallucinated Success** (phase marked complete with no verifiable artifact) |
| 7 | `/secretary` | **PENDING** | session-state collector: enumerate expected session artifacts (HANDOFF.md freshness, DevJournal last-entry delta, uncommitted file list, open ticket count, WORKSTREAM_STATUS.md last-update age), emit a closure-readiness JSON | the synthesis narrative, deferred-item judgment, and session quality assessment | **Ghost Logic** (session close with no traceable paper trail) |
| 8 | `/triage` | **PENDING** | trigger-matrix engine: for each Trigger Matrix row that already names a deterministic source (`lint_workflows.py --quiet`, `harden_audit.py --output-json`, `quality_audit.py --output-json`), wire a real subprocess call and compare against the instructional fallback; emit a structured evidence block the model reasons over | the priority assignment, intent-modifier elevation, and final recommendation text | **Hallucinated Success** (trigger evaluated shallowly without evidence) |
| 9 | `/investigate` | **PENDING** | read-only forensic anchoring: confirm the investigation perimeter files exist, parse git log for the cited commits/dates, enumerate claimed code locations (`file#Lnn` references) and verify they resolve, emit a "citation fidelity" report | the root-cause judgment, blame assignment, and remediation recommendation | **Ghost Logic** (investigation cites evidence that doesn't exist in substrate) |
| 10 | `/helpdesk-tickets` | **PENDING** | ticket lifecycle engine: scan `helpdesk-tickets/` for OPEN vs CLOSED_ prefix counts, validate ticket schema (required sections present), detect tickets older than N days without status change, emit a ticket-health JSON the workflow reasons over | the urgency ranking, remediation design, and resolution sign-off | **Context Erosion** (ticket left open across sessions, root cause forgotten) |
| 11 | `/receipt-check` | **DONE** (v3, `scripts/receipt/`) | receipt coverage engine: parses `tasks.md` (reusing `focus.phase_status.parse_tasks_md`), cross-references completed phases against BUILD/VALIDATION receipts by phase-name match and HARDEN receipts by a disclosed file-mention heuristic, reports Documented as existence-only (its real Phase/Stage value is a fixed constant, no per-phase key exists), computes gap %, wires Quality-Process via a direct `quality_audit.py` call | which gaps matter given project priorities, stale-harden flagging, Gap Summary narration | **Hallucinated Success** (receipt present but content never verified — made structural via mechanical phase-to-receipt matching) |
| 12 | `/harden-workflow` | **PENDING** | suite linter integration (already wired via `lint_workflows.py`): extend Phase 7d to call the linter as a subprocess from within the workflow, parse its JSON output, and emit a structured Degradation Check result per workflow; the engine already exists — the gap is that the workflow still calls it *instructionally* | the Sovereign grade decision, degradation verdict, and certificate content | **Grade Fraud** (linter called instructionally; agent can skip or misread output) |
| 13 | `/refactor` | **DEFERRED** | a real engine exists (import/call graph walk, LOC counter, `scripts/focus/anchor_scanner.py` reuse) but the shim-layer design and phase migration decisions are irreducibly architectural; engine scope is narrow (LOC threshold detection, test-coverage delta before/after) | the migration strategy, shim design, and phase sequencing | (lower stakes — refactors are scoped engagements, not continuous enforcement) |
| 14 | `/provenance` | **DEFERRED** | a git-walking engine is clean and buildable (`git log --follow --format=...`, `git blame` parsers); but provenance guards no active failure pattern and writes no receipt infrastructure — the deterministic layer would be all gain for no enforcement | the lineage interpretation, architectural intent attribution | (no active failure pattern guarded; build after #12 if appetite remains) |
| — | `/soc` | **EXCLUDED** | SOC is a pure judgment workflow (where to draw module boundaries is irreducibly architectural); LOC detection reused by `/refactor` engine covers its only deterministic signal | entire judgment | (deterministic signal already covered by `/refactor` engine entry; no separate engine justified) |
| — | `/deepcode` | **EXCLUDED** | code review quality is irreducible judgment (same class as `/quality`); the only deterministic layer would be LOC/complexity thresholds, already handled by `/triage`'s god-file trigger | entire judgment | (no unique deterministic layer not already covered elsewhere) |
| — | `/document` | **EXCLUDED** | journal entry presence (last-entry age) is already a `/triage` signal; the writing of a journal entry is synthesis judgment | entire judgment | (already covered as triage signal; no engine adds value) |
| — | `/retrospective` | **EXCLUDED** | retrospective is synthesis and pattern-recognition judgment; the only mechanically verifiable signal (PROCESS_LEARNINGS.md age) is already a `/triage` trigger | entire judgment | (already covered as triage signal) |
| — | `/divergence` | **EXCLUDED** | lateral thinking is constitutively irreducible judgment — scripting divergence produces the statistical median, the opposite of the workflow's purpose | entire workflow is judgment | (Mock Trap by definition — any engine here IS the trap) |
| — | `/gitclean` | **EXCLUDED** | git state facts (uncommitted files, commit count since squash) are already `/triage` signals; the actual squash/rebase decisions are judgment; Phase 8 graph-reconnection logic is high-stakes manual verification | graph-reconnection judgment and squash strategy | (signals already in triage; high-risk destructive operations should remain manually guided) |
| — | `/depreciate` | **EXCLUDED** | contradiction detection is judgment (what counts as irreconcilable?); the archive/supersede operation is manual by design | entire judgment | (the workflow IS the safety valve against automated deletion — scripting it inverts its purpose) |
| — | `/workstream` | **EXCLUDED** | multi-agent orchestration is judgment-dominant; Pre-Flight Manifest already runs deterministic bash checks; Diff Oracle already calls `git diff`; no new engine adds enforcement not already structural | PM oversight, escalation resolution, role activation | (already has more structural enforcement than most — marginal engine value) |
| — | `/implementation-plan` | **EXCLUDED** | plan generation is creative synthesis; verification of plan quality belongs to `/focus-plan` (already done); this workflow produces the artifact, not the verification | entire judgment | (the output is consumed by the engine ecosystem, not produced by it) |
| — | `/canvas` | **EXCLUDED** | canvas generation is visual synthesis from code structure; the only deterministic layer is file enumeration (already done by triage/deepcode); grade: Hardened, needs `/harden-workflow` structural pass before engine consideration | entire judgment | (structural hardening via `/harden-workflow` is the prerequisite, not an engine) |
| — | `/onboard` | **EXCLUDED** | onboard is read-only orientation synthesis; the observable signals it reads (git state, file presence) are already collected by `/triage`'s Phase 0; no enforcement gap | entire judgment | (read-only orientation tool; no failure pattern to make structural) |
| — | `/testpackage` | **EXCLUDED** | post-modularization QA is judgment-dominant (what tests to write, what coverage targets to set); the only deterministic signal (LOC/coverage delta) is already in the `/refactor` engine scope | entire judgment | (overlaps `/refactor` and `/iterate-test`; no unique deterministic layer) |
| — | `/nodelete` | **EXCLUDED** | behavioral modifier — the preservation discipline is applied by the model, cannot be externally verified without auditing every edit ever made | entire content is a behavioral directive | (behavioral modifier; enforcement is architectural at the git level, not engine level) |
| — | `/nodeleteshort` | **EXCLUDED** | compact form of `/nodelete`; same reasoning applies | same as `/nodelete` | (behavioral modifier) |
| — | `/role` | **EXCLUDED** | role definition file — no phases, no receipts, no enforcement logic | entire content is an identity declaration | (identity/context document; not in scope) |
| — | `/personality` | **EXCLUDED** | behavioral frame — faith context, no-praise directive; cannot and must not be scripted | entire content | (behavioral modifier; sacred in scope — must not be automated) |

**Per-workflow seed design (a starting hypothesis — VERIFY it against the actual `.md` before building; adjust honestly):**

- **`/harden`** — graded `Hardened`, *not* Sovereign (the hardening workflow isn't itself top-hardened). It has a ~19-item security checklist and a Diamond/Gold/Silver/Bronze grade. Many items are deterministic CWE signatures (hardcoded secrets, `eval`/`exec`, unsafe `subprocess`, path traversal, world-writable perms, missing input validation). The **grade is a computation currently rendered by judgment → Grade Fraud risk.** Engine: a read-only security scanner that checks the deterministic items and **computes the grade from real findings**; the agent adjudicates only genuinely ambiguous items. Writes/consumes `HARDEN_GRADES.md` (which `/receipt-check` reads). Highest stakes, cleanest fit — that is why it is #1.
- **`/iterate-test`** — the suite's flagship **Mock Trap** workflow, yet it leans on an *instructional* "Intelligence Bridge Declaration" (the agent attests the test reaches real intelligence). Engine: statically determine whether a test file actually imports/calls the production module it claims to validate, vs. only patching/mocking it. Reuse `scripts/focus/anchor_scanner.py`'s test-path classification. Scope **Python-first**; do not overpromise cross-language. Writes `VALIDATION_RECEIPTS.md`. Hardest engine — keep it honest and narrow.
- **`/redteam`** — Sovereign, 5 adversarial personas. Core is **irreducible judgment** (like `/quality`). Engine is a **thin rail only**: collect deterministic Ghost Logic evidence (a claimed behavior with no corresponding code or log line). **Never script the adversarial verdict.**

---

## END-TO-END UPGRADE RECIPE (run once per context, on one workflow)

This is the exact procedure executed for `/focus-plan` and `/quality`. Follow it.

**A. Investigate (read-only).** Read the target `claude-commands/<wf>.md` in full. Run the HONEST-DESIGN DISCIPLINE. Confirm the seed design or correct it. Find the real defects (look specifically for: self-description contradictions like "internalize all N rules" not matching `strict_rule_count`; `phase_count` wrong; phantom-mandatory files; filename mismatches; instructional-only enforcement of a verifiable guarantee). Cite evidence as `file#Lnn`.

**B. File a helpdesk ticket (OPEN).** Use the `/helpdesk-tickets` format. Filename `helpdesk-tickets/YYYYMMDD_<wf>_workflow.md` (today's date). Name the structural gap, ≥2 forensic citations, a workflow-level recommendation. Status `OPEN`. (Tickets are gitignored by repo convention — that is expected.)

**C. Build the engine** under `scripts/<wf-short>/`, modeled on `scripts/focus/` and `scripts/quality/`:
- `__init__.py` (docstring stating the read-only + honesty boundary), `_utils.py` (`safe_read`; `assert_within` if you walk paths — both already written in focus/quality, copy the pattern), the capability module(s), `reporter.py` (JSON + human), a `<cli>.py` orchestrator with `--workspace` / `--output-json` / `--quiet`, and `schema/<wf>_report.schema.json`.
- **Read-only on the workspace. Emit JSON to stdout. Write no files.**
- Any heuristic signal is **advisory + one-directional**, with the Mock-Trap disclaimer in code and schema.

**D. Tests.** `scripts/tests/test_<wf>.py`, `unittest` style (the suite runner is `unittest discover`, not pytest). Include: the core parse/verify cases, a negative control, and a **read-only invariant test** (snapshot `rglob('*')` before/after a run; assert equal). Run: `cd ~/blueprint-workflows/scripts && PYTHONPATH=. python3 -m unittest tests.test_<wf> -v`, then the full suite `./run_tests.sh`.
- **KNOWN pre-existing failure:** `tests.test_core.TestRefactorCore.test_import_patterns_python` (`'import foo' not found`) fails on untouched code. It is unrelated. Expect exactly this one failure in the full suite; do **not** investigate or "fix" it, and do not let it block you.

**E. Live-run the engine** against this workspace: `python3 ~/blueprint-workflows/scripts/<wf-short>/<cli>.py --workspace ~/blueprint-workflows ...`. Confirm it produces sane output and wrote nothing (no new dir, clean `git status` except your intended files). Fix any false positives you find (e.g., documentation *mentions* of a token vs. real tokens) and add a regression test — this happened in both reference builds.

**F. Harden the `.md` (under /nodelete).** Read the file in-conversation first (the Edit tool requires it). Inject a "Verification Rail" / "Execution Model" section that runs the engine; fix the defects from step A; **supersede** (don't delete) any contradicted STRICT RULE with a numbered replacement and a struck-through pointer; preserve all original content and the Change Log; append a new Change Log entry. Update frontmatter: bump `version`, set `last_hardened` to today, correct `strict_rule_count` and the "internalize all N" line to match, add the engine to `dependencies`. Keep every judgment step verbatim.

**G. Wire dependents (only if applicable).** If the engine produces a signal another workflow consumes, inject a real call (e.g., `/quality` wired into `/triage` and `/receipt-check`). `/nodelete` injections only — do not restructure. Read each file before editing it.

**H. Lint CLEAN.** For every `.md` you touched: `python3 ~/blueprint-workflows/scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows --file <wf>.md`. Require **0 CRITICAL, 0 WARNING** (INFO is acceptable linter noise). The lint reports the correct `content_hash` as `actual=…`; set the frontmatter `content_hash` to that value (it is computed over the body excluding frontmatter+changelog, so setting it does not re-invalidate). `phase_count` must equal the number of `## PHASE <digit>` headers (uppercase PHASE + digit — the linter's pattern). Re-lint to confirm CLEAN.

**I. Close the ticket.** `mv helpdesk-tickets/YYYYMMDD_<wf>_workflow.md helpdesk-tickets/CLOSED_YYYYMMDD_<wf>_workflow.md` (the rename IS the closure), and update its Status line to `REMEDIATED (...)` with the verification evidence. Confirm the `claude-commands/<wf>.md` symlink into `~/.claude/commands/` is intact.

**J. Update this plan + suggest next + HALT.** Set the QUEUE row to `DONE`. Append an ITERATION LOG entry. Ensure the next workflow is in the QUEUE as `PENDING`. Report concisely (what was built, defects fixed, tests, lint, ticket closed; note the known `test_core` failure). End with the literal line `READY FOR /clear — next: /<workflow>`.

**Gates that must all hold before you call an upgrade done:** engine is read-only (test proves it) · target tests green · full suite shows only the known `test_core` failure · every touched `.md` lints CLEAN · ticket closed · `/nodelete` preserved (judgment steps + Change Log intact) · symlink intact · this plan updated. **No git commits** unless the user explicitly asks (the user may commit between cycles themselves).

---

## CONVENTIONS & ENVIRONMENT (quick reference)

- Workspace root: `~/blueprint-workflows`. Commands: `claude-commands/<name>.md` (canonical) → symlinked to `~/.claude/commands/<name>.md`. Edit the canonical file only.
- Scripts: run with `PYTHONPATH=.` from `scripts/`. Existing engines: `scripts/doorway/` (template), `scripts/focus/`, `scripts/quality/`. Shared tests dir: `scripts/tests/`. Linter: `scripts/suite/lint_workflows.py`.
- Security primitives to mirror (already in `focus/_utils.py`): `safe_read` (bounded read, CWE-400), `assert_within` (path-traversal guard, CWE-22). Engines write nothing — no `atomic_write`/`safe_mkdir` needed.
- `/nodelete` discipline: inject/append; delete only what directly contradicts; supersede STRICT RULES with numbered replacements; never delete a Change Log entry.
- Helpdesk tickets are gitignored (`helpdesk-tickets/*workflow*.md`) — they live on disk only; that is intended.
- Behavioral frame: no praise unless functionally required; surface significant ambiguity as one question; faith context is foundational. (Auto-loaded globally; restated here for a fresh agent's certainty.)

---

## NEXT-WORKFLOW SELECTION (how to choose #4 and beyond, once the queue's PENDING rows are exhausted)

Rank remaining workflows by the **fit signature**: (a) a deterministic, high-stakes layer currently enforced by *instruction*; (b) it guards a **named failure pattern**; (c) it has **no existing `scripts/` backing**; (d) bonus if it writes/reads receipt infrastructure. Append the top candidate to the QUEUE as `PENDING` with a one-line cited rationale, then proceed normally.

**Pre-vetted runners-up (already scanned 2026-06-02):**
- `/execute-build` — has a real defect (`strict_rule_count: 0`) worth fixing, but its "engine" would mostly *reuse* `/focus-plan` + `/continuous-verify` rather than add new substance; the build itself is judgment. Medium fit.
- `/provenance` — a clean git-walking engine (decision lineage from `git log`/`blame`), but it gates nothing and guards no failure pattern. Lower stakes.
- `/secretary` — session-close orchestrator; a "session-state collector" engine could feed it, but much is synthesis/judgment.

**Architect note (optional, for whoever does #2/#3):** a shared substrate-analysis library is emerging — `focus/anchor_scanner.py` already does file/symbol grep + test-path classification, which `/harden` (CWE scans) and `/iterate-test` (import/call analysis) both need. Consider consolidating into `scripts/substrate/` instead of duplicating grep logic. Only do this if it does not balloon the single-context upgrade; per-workflow packages (as in focus/quality) are proven and acceptable.

---

## ITERATION LOG (append-only — newest at the bottom; one entry per completed or in-progress upgrade)

- **2026-06-02 — /focus-plan → v3 (DONE).** Built `scripts/focus/` (plan parser + read-only anchor scanner + reporter + CLI + schema, 18 tests incl. read-only invariant). Fixed filename mismatch (`implementation_plan.md`→`implementation-plan.md`), phantom Memory Ledger (STRICT RULE 13 demoted), `phase_count` 0→4. Old per-item ceremony preserved as Manual Fallback Mode. Ticket `CLOSED_20260602_focus-plan_workflow.md`. Lint CLEAN.
- **2026-06-02 — /quality → v4 (DONE).** Built `scripts/quality/` (ledger auditor + chain-tag verifier + one-directional smell linter + reporter + CLI + schema, 19 tests). Honest design: engine verifies *process receipts + mechanical smells*, never quality. Fixed "11 STRICT RULES"→17 (was contradicted by `strict_rule_count: 14`); made the trust-only witness/tag verifiable (RULES 15–17). Wired into `/triage` (deterministic P3 source) and `/receipt-check` (5th observability dimension). Ticket `CLOSED_20260602_quality_workflow.md`. Lint CLEAN on all three files.
- **2026-06-02 — /harden → v3 (DONE).** Built `scripts/harden/` (cwe_scanner + threat_classifier + grade_computer + reporter + CLI + JSON schema, 33 tests incl. the read-only invariant). Honest design: the engine detects deterministic CWE signatures and computes a **Grade Ceiling** that is *one-directional* — a firm CRITICAL/HIGH finding forbids a higher grade, but a clean scan certifies NOTHING (reading it as a Diamond is the Grade Fraud). Threat model, Sound-Effect-Execution, and the final grade (assigned ≤ ceiling) stay in the model. Made **Grade Fraud** structural: the grade now has a deterministic floor the agent cannot certify above. Live run caught 2 genuine `shell=True` CRITICALs (`workstream/verify.py:54`, `core/git_ops.py:110`) that instruction-based hardening had left — 0 false positives, confirmed read-only. Fixed frontmatter (`version` 2→3, `phase_count` 0→4, `strict_rule_count` 11→15, `grade` Hardened→Sovereign, engine→deps). Original Phases 0–3 preserved verbatim as the Manual / Judgment Protocol; STRICT RULES 12–15 added (1–11 untouched, none contradicted). Wired into `/triage` (deterministic `harden_audit.py` call mirroring the `lint_workflows.py --quiet` precedent). Ticket `CLOSED_20260602_harden_workflow.md`. Lint CLEAN on `harden.md` + `triage.md`. Full suite: only the known unrelated `test_core` failure.
- **2026-06-02 — /iterate-test → v3 (DONE).** Built `scripts/iterate/` (`mock_analyzer` AST engine + `bridge_classifier` + `reporter` + `iterate_audit` CLI + JSON schema, 27 tests incl. the read-only invariant). Honest design: the engine is a **Mock-Trap Detector** — it parses a test's AST (no execution) and reports which imported production symbols are **patched** (a *Patched-Subject*, behavior replaced by a mock) vs **called un-patched**, plus the hardcoded-assertion tautology (a `return_value`/`side_effect` literal echoed in an `assert ==` — the Step-4g / RULE-10 deficiency). Made **Mock Trap** structural: the Step-4b Intelligence Bridge Declaration — historically an unverified *attestation* — is now reconciled against read-only AST facts (Mute Witness enforcement). One-directional: a `MOCK_TRAP_CANDIDATE` *demands* the agent's PRIMARY-vs-INFRASTRUCTURE call (PRIMARY ⇒ FIDELITY HALT; INFRASTRUCTURE ⇒ valid mock) — the engine NEVER makes that call (scripting it would make the detector itself a Mock Trap), and a clean scan certifies NOTHING (a live-called test can still be a tautology / Sound Effect Execution). Live run analyzed 13 suite test files: 0 candidates, 0 false positives after an `__init__.py` package-marker exclusion fix (regression-tested); confirmed read-only; JSON validates against the schema. Fixed frontmatter (`version` 2→3, `grade` Hardened→Sovereign, `last_hardened`→2026-06-02, `strict_rule_count` 13→16, engine→`dependencies`; `phase_count` stays 7 — the Fidelity Rail uses non-`## PHASE` headers, so the original 7 phases are untouched). Original Phases 0–6 preserved verbatim as the judgment protocol the engine feeds; STRICT RULES 14–16 added (1–13 untouched, none contradicted). Wired into `/triage` (deterministic `iterate_audit.py --output-json` call mirroring the `harden_audit.py` precedent). Ticket `CLOSED_20260602_iterate-test_workflow.md`. Lint CLEAN on `iterate-test.md` + `triage.md`. Full suite: only the known unrelated `test_core` failure.
- **2026-07-05 — /receipt-check → v3 (DONE).** Resolved via `helpdesk-tickets/CLOSED_20260704_hallucinated-success-recurrence_workflow.md` (a registry-aggregate investigation that confirmed this campaign as the correct existing remediation vehicle, rather than inventing a parallel fix). Built `scripts/receipt/` (`coverage.py` + `reporter.py` + `receipt_audit.py` CLI + `_utils.py`, 15 tests incl. a live `quality_audit.py` subprocess test and the read-only invariant). Honest design, three matching keys used precisely because the four receipt files don't share one: BUILD/VALIDATION receipts matched by phase-name (reusing `focus.phase_status.parse_tasks_md` directly rather than re-deriving phase-boundary detection — first reuse of that parser outside `/focus-plan`, recorded in `SUITE_PHYLOGENY.md`); HARDEN matched by a disclosed file-mention heuristic (a phase naming no files reports `unverifiable_no_file_list`, never silently covered); DOCUMENTED reported existence-only, since `DOCS_RECEIPTS.md`'s real "Phase/Stage" value is a fixed constant ("Journal Update") in every entry this workspace has ever written, confirmed against the live file rather than assumed — no per-phase key exists to match at all. Quality-Process wired via a direct `quality_audit.py` subprocess call inside the same pass (previously a separate manual instruction the agent could skip). Reused `/focus-plan` v4's exact PENDING-is-not-a-gap distinction so a not-yet-built phase never counts against the gap percentage. Fixed frontmatter (`grade` Hardened→Sovereign, `version` 2→3, `dependencies`→`scripts/receipt/`). Original five-phase manual procedure preserved verbatim as Manual Fallback Mode; STRICT RULES 9–11 added (8→11, none contradicted). Ticket `CLOSED_20260704_hallucinated-success-recurrence_workflow.md`. Lint CLEAN on `receipt-check.md`. Full suite: only the known unrelated `test_core` failure.
- **2026-06-02 — Full Queue Enumeration (PLANNING, no build).** Reviewed all 33 workflow files in `claude-commands/`. Classified each by verification-spine fit signature: deterministic layer presence, failure pattern guarded, receipt infrastructure written. Result: 11 PENDING entries (entries #4–#12: `/execute-build`, `/sentinel`, `/continuous-verify`, `/secretary`, `/triage`, `/investigate`, `/helpdesk-tickets`, `/receipt-check`, `/harden-workflow`); 2 DEFERRED entries (#13–#14: `/refactor`, `/provenance`); 18 EXCLUDED entries (behavioral modifiers, pure-judgment workflows, and workflows whose deterministic signals are already covered by existing engines or `/triage`). Key design decisions: `/divergence` excluded as a Mock Trap by definition; `/gitclean` excluded due to high-stakes destructive operations that must remain manually guided; `/workstream` excluded because its Pre-Flight Manifest and Diff Oracle already provide more structural enforcement than a new engine would add; `/personality` excluded as sacred-scope behavioral frame. No code written. Queue is now complete from entry 1 through the full suite.
```

**Acceptance criteria for this archival:** the new `implementation-plan.md` (post-2026-07-07 revision) carries a pointer to this file; `tasks.md` (repo root) carries the same 9 PENDING + 2 DEFERRED items as real Phases, not silently dropped; the five DONE engines' historical engineering detail (the ITERATION LOG prose above) remains findable and intact, here.
