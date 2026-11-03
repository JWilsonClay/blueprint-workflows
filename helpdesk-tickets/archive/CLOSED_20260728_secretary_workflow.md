# Helpdesk Ticket: Solo-Agent Assumption — `/secretary` Has No Mode Between "Close the Session" and "Do Nothing," So a Peer Agent's Close Is Destroyed and Mid-Session Context Is Unrecoverable

**To**: Senior Architect of Workflows
**From**: Claude Code (Opus 5), blueprint-workflows governance session — concept review of a proposed `/secretary --context` flag
**Date**: 2026-07-28
**Subject**: `/secretary`'s data model assumes exactly one closing agent per session. In the user's established tandem pattern (Gemini closes, then Claude is asked to close), the second agent's Phase 4 overwrites the first agent's `HANDOFF.md` by STRICT RULE 3 mandate — and the suite offers no lower-cost alternative, because STRICT RULES 1/7/13 define any partial run as not-a-run.
**Urgency**: HIGH
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: NO TRANSFER *(resolved 2026-08-13 at closure — single-workflow remediation; the candidate "MODE GATE" pattern is named in the Closure section for future lineage if it ever propagates)*

---

## 1. Executive Summary

`/secretary` is a single-mode workflow: it closes a session completely, or it is not considered to have run. That binary is correct for the case it was designed for — one Claude Code agent, one session, one close. It fails in two situations the user now runs routinely.

**First**, when two agents work in tandem on the same project (the user's stated pattern: "I'm running the full `/secretary` in one, usually gemini, then asking Claude to run `/secretary`"), the second agent's Phase 4 overwrites the first agent's `HANDOFF.md`. STRICT RULE 3 mandates the overwrite; the ADDENDUM A pre-flight scan rescues only *anomaly language* via grep. The first agent's "What Was Accomplished," "Deferred Items," and "Suggested First Workflow" content is destroyed with no archive and no warning.

**Second**, in long builds where each phase and audit consumes context in multiples of 100K bytes, the agent's working state is lost at every compaction boundary. `/secretary` is the only workflow that captures session context — but STRICT RULE 1 forbids running it mid-session, and STRICT RULES 7 and 13 mean a partial run is not a run. The user's only available move is the full, expensive, globally-writing close, invoked far more often than session boundaries actually occur.

Both are the same root cause: **the protocol has no concept of an agent recording its own slice of a session that another agent — or a later self — will close.**

## 2. Root Cause Analysis: "Solo-Agent Assumption" (candidate pattern — see note below)

- **The How**: `/secretary` treats "a session" and "this agent's context" as the same object. Phase 4 writes `HANDOFF.md` as *the* session briefing, unconditionally overwriting whatever is there, with no agent attribution field and no merge step. Phase 1 Step 1.2 appends a narrative entry to the active `manifest/history/` shard on every run, so two closes of one session produce two `SESSION APPEND` entries. Nothing in the protocol asks whether a peer agent has already closed this session, because the protocol has no representation for a peer agent existing.

- **The Why**: STRICT RULE 1 forbids mid-session invocation; STRICT RULE 7 makes Phase 6 `/retrospective` mandatory; STRICT RULE 13 states that producing Phase 1's artifacts without Phases 2/3/6 "= Phase 1 only, not a completed `/secretary` run." Together these are correct and load-bearing for their intended case — they exist to prevent a partial close being mistaken for a real one. But they leave **no valid third state**. The workflow offers "full session close" or nothing, and `flags: []` in its frontmatter confirms no mode has ever been added. A user needing to preserve context without closing a session is structurally forced to either run the full close (destroying a peer's work, double-appending the narrative, paying for eight scripts and 32 command-file reads) or lose the context.

**Note on pattern naming (per `role.md` Section IV and its Change Log entries 10-11 restraint precedent):** "Solo-Agent Assumption" is filed here as a **candidate**, deliberately not promoted into `role.md`'s Section IV table. It is the second sighting of one family — `20260726_execute-build-crossagent_workflow.md` documents its *enforcement* face ("Gate Scope Mismatch": a Claude Code gate does not bind a non-Claude-Code executor); this ticket documents its *data model* face (the protocol's artifacts assume one author). Two sightings in two different workflows is suggestive, not established. Promotion should wait for a third, or for a deliberate architectural decision to treat multi-agent operation as a first-class suite concern.

## 3. Forensic Evidence

- **The overwrite mandate**: [secretary.md STRICT RULE 3](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L568-L568)
  *Evidence: "HANDOFF.md is overwritten each session. This is the only correct behavior... Prior content is NOT archived unless it contains anomalies not in ANOMALY_LOG.md." This is the mechanism by which a second agent's close destroys the first's.*

- **The partial rescue that proves the gap**: [secretary.md Phase 4, ADDENDUM A](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L351-L362)
  *Evidence: the pre-flight scan greps only for `STRICT RULE|MISMATCH|workflow skipped|anomaly|override|deviated` before overwriting. Deliverables, deferred items, and next-session recommendations match none of these patterns and are therefore not preserved. The addendum demonstrates the authors already recognized overwrite as lossy — and scoped the fix to anomalies only.*

- **The mid-session prohibition**: [secretary.md STRICT RULE 1](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L566-L566)
  *Evidence: "/secretary is always the LAST workflow invoked in a session. Do not run it mid-session while build or test activity is ongoing." This forecloses the phase-boundary checkpoint use case directly.*

- **The all-or-nothing definition**: [secretary.md STRICT RULE 13](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L578-L578)
  *Evidence: "Producing only the three Phase 1 artifacts... without Phases 2/3/6 = Phase 1 only, not a completed /secretary run." Combined with [STRICT RULE 7](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L572-L572) (retrospective mandatory), there is no sanctioned partial mode.*

- **Double narrative append**: [secretary.md Step 1.2](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L282-L282)
  *Evidence: "append this session's own narrative entry... to whichever file the monitor reports as the active shard" — unconditional, per run. Two closes of one session write two `SESSION APPEND` lines for that session.*

- **No mode has ever existed**: [secretary.md frontmatter](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L11-L11)
  *Evidence: `flags: []`. Confirms the binary is original to the design, not a regression from a lost mode.*

- **The constraint any fix must respect**: [secretary.md Step 0b.5, Retrospective Lag](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L116-L146)
  *Evidence: `gap_detected` compares the newest `SESSION APPEND` date against `PROCESS_LEARNINGS.md`'s last entry. Any new mode that writes a narrative entry without a matching retrospective would trip this detector permanently — a design constraint that falls directly out of existing substrate.*

- **Prior occurrence, same family, different face**: [20260726_execute-build-crossagent_workflow.md](file:///home/jwils/blueprint-workflows/helpdesk-tickets/20260726_execute-build-crossagent_workflow.md#L1-L14)
  *Evidence: open ticket documenting that Sovereign Suite gates do not bind a non-Claude-Code executor in the same orchestrator/executor pattern. Different faulting workflow (`/execute-build`), different mechanism (enforcement vs. data model), same underlying single-agent assumption.*

- **Boundary context for the proposed fix**: [personality.md Section 6, Suite Workflow Exemption](file:///home/jwils/blueprint-workflows/claude-commands/personality.md#L108-L124)
  *Evidence: the enumerated pre-authorized external write targets for `/secretary` are `manifest/`, `helpdesk-tickets/archive/`, and `process_learnings/`. A context-only mode writing solely inside the active project workspace would require no exemption entry at all — the only `/secretary` mode with that property.*

## 4. Remediation: `/secretary --context` — a Third State Between "Close" and "Nothing"

Recommended, not yet applied. This ticket documents the finding and the design; no edit to `secretary.md` has been made.

1. **Add a Mode Gate before Phase 0** declaring `--context`. On this flag, run Phase 0a scoped to *this agent's slice only*, plus a new Phase C. Skip Steps 0b.5, 1.0.5, 1.0.6, 1.1, 1.2 and Phases 2–7 entirely. Invoke zero scripts and read zero command files — this is the entire cost saving, and it also sidesteps the Script Path Resolution class in `role.md` Section II by referencing no script paths at all.

2. **Write exactly one file**: `{project}/.workflow_state/CONTEXT_LEDGER.md`, append-only via `cat >>` per the ADDENDUM D discipline already mandated for `ANOMALY_LOG.md`. **`--context` must write zero bytes to `manifest/history/`, `manifest/SUITE_HEALTH.md`, and `PROCESS_LEARNINGS.md`** — not as a cost optimization but because a narrative entry without a matching retrospective is the literal definition of Retrospective Lag, and would trip Step 0b.5's detector on every subsequent session in perpetuity.

3. **Schema the entry around what no receipt already captures** — agent working memory, not build output (`BUILD_RECEIPTS.md` covers the latter): agent/model/timestamp/checkpoint sequence; trigger (pre-compaction / phase boundary / handing to peer); working hypotheses currently held but not yet written anywhere; decisions and the reasoning behind them; **unverified peer claims** (assertions from the other agent this agent has not independently re-checked); next intended action; files touched this slice. The unverified-peer-claims field gives the orchestrator a standing home for exactly the class of claim that `20260726_execute-build-crossagent_workflow.md` Section 5 identifies as needing orchestrator-side re-verification.

4. **Emit a Context Checkpoint Receipt**, structurally distinct from the Secretary Receipt, carrying the mandatory literal line `SESSION CLOSE: NOT PERFORMED — full /secretary still required.` Without this, the mode becomes a Hallucinated Success vector: a checkpoint reads as a close, and the real close never happens.

5. **Amend base Phase 4 to consume the ledger.** When the full `/secretary` next runs, it must read `CONTEXT_LEDGER.md` entries recorded since the last close, fold them into `HANDOFF.md`, and mark them consumed. Without this the checkpoints are write-only. This is a change to the base workflow, not only to the flag, and is the step that actually closes the tandem-agent loop.

6. **Add STRICT RULE 22** scoping the exemption and naming exactly which rules it carves out (1, 7, 13), leaving those three textually intact per `/nodelete`. Frontmatter `flags: []` → `flags: ["--context"]`.

7. **Keep the branch short.** Open ticket `20260707_workflow-architectural-bloat_workflow.md` is CRITICAL and unresolved; `secretary.md` is already 650 lines with 21 STRICT RULES. The mode should land as a compact Mode Gate (target ~50 lines), not a fourth phase set threaded through the existing eight.

## 5. Recommendation to Senior Architect

**Every Sovereign workflow that produces a single-author, overwrite-semantics artifact should be audited for the same assumption.** `/secretary`'s `HANDOFF.md` is the instance found here, but the question generalizes: which suite artifacts are written as if exactly one agent authored the work they describe, and what happens to them when a peer agent writes second? `ANOMALY_LOG.md` is safe by construction (append-only, STRICT RULE 4). `HANDOFF.md` is not. The narrative shards are append-only but carry no agent attribution, so a two-agent session is indistinguishable from two sessions in the ledger.

The structural principle worth adopting: **an artifact that overwrites must either carry agent attribution and merge semantics, or must be paired with an append-only companion that cannot be clobbered.** `--context` implements the second option for `/secretary`. Whether the same treatment is owed to other workflows is the audit this ticket recommends — and it is the natural place to decide whether multi-agent operation becomes a first-class suite concern, which would in turn settle whether "Solo-Agent Assumption" earns promotion to `role.md` Section IV.

---
**Status**: **REMEDIATED (`--context` MODE GATE built (items 1-4, 6), verified, in production since 2026-07-28; deferred items 5/7/8/9/10 re-homed to `20260813_secretary-deferred-items_workflow.md`; closed by user approval 2026-08-13 — see Closure section)**
**Verification**: Remediation Record in the Closure section (2026-08-13) — 537/537 tests and linter 0 CRITICAL re-run at closure; production use confirmed. NOTE: the original bar on this line additionally required item 5 (Phase 4 ledger consumption) and a byte-identical two-agent measurement — closure at the built scope is an explicit user decision of 2026-08-13, with the original bar preserved verbatim in the Closure section and the unbuilt items re-homed, not dropped.

**Honest limits of this ticket's evidence (STRICT RULE 8):** the `HANDOFF.md` destruction is established from the protocol text — STRICT RULE 3 mandates the overwrite and ADDENDUM A's grep demonstrably does not cover deliverables or deferred items. No destroyed `HANDOFF.md` was recovered from the `lsshreveport` workspace to confirm a specific live instance; that workspace is outside this session's edit boundary and was not read. Urgency is therefore set at HIGH (single faulting workflow, reproducible by protocol text on every tandem close) rather than escalated to CRITICAL, notwithstanding that STRICT RULE 9's "observed more than once" clause could arguably apply via the user's description of the tandem pattern as routine. If a live instance is confirmed, escalation is warranted.

---
*Signed,*
**Claude Code (Opus 5)**
*(Senior Architect of Workflows — blueprint-workflows)*

---

## Addendum — 2026-07-28 — Filesystem evidence from `lsshreveport`: the clobber did NOT occur, and the reason is worse than the clobber

**From**: Claude Code (Opus 5), same session as the original ticket. Read-only evidence pass over `/home/jwils/.prebuild.temp/lsshreveport/.workflow_state/`, conducted with explicit user approval per `personality.md` Section 6.

**Why this addendum exists**: the original ticket's Status block flagged the `HANDOFF.md` destruction as protocol-inferred, not filesystem-verified, and named the verification as outstanding. It has now been performed. Section 1's tandem-clobber claim is **partially wrong** and is corrected here rather than silently left standing.

### Correction: the peer's close was preserved — by agent improvisation, not by protocol

`.workflow_state/HANDOFF.md` line 4 reads: `# Generated by: /secretary (Claude Code pass — merges Gemini's prior pass this session)`. The surviving file contains **both** agents' work under separate headings — `**Build & branding (Antigravity Gemini):**` and `**Audit, remediation & security (Claude Code):**`. No destruction occurred on 2026-07-16.

**But nothing in `secretary.md` instructed that merge.** STRICT RULE 3 mandates the overwrite; Phase 4's write step contains no peer-detection, no merge instruction, and no agent-attribution field. The Claude Code agent noticed the situation and improvised the correct behavior against the protocol's explicit direction. This is the substantively sharper finding, and it changes the defect's shape:

> The failure mode is not "data is destroyed." It is **"correct behavior in the tandem case is entirely dependent on the agent noticing and improvising, while the protocol points the other way."** An agent following STRICT RULE 3 literally — which is what a STRICT RULE is for — destroys the peer's briefing. This is Context Erosion in the classic sense: rigor sustained only by an anchor the document does not supply.

Corroborating: the deviation was never logged. All three `ANOMALY_LOG.md` entries for 2026-07-16 read `NO ANOMALIES`, including the Claude Code pass that performed the unprescribed merge. A protocol deviation — even a beneficial one — went unrecorded because the agent did not perceive improvising past a STRICT RULE as an anomaly.

### The unambiguous finding: eleven days of build work, zero session closes

| Artifact | Last modified |
|---|---|
| `.workflow_state/HANDOFF.md` | 2026-07-16 14:52 |
| `.workflow_state/ANOMALY_LOG.md` | 2026-07-16 14:52 |
| `.workflow_state/receipts/BUILD_RECEIPTS.md` | **2026-07-27 12:01** |
| `.workflow_state/receipts/DOCS_RECEIPTS.md` | **2026-07-27 12:38** |

Build and documentation receipts were being appended as recently as 2026-07-27. The session-close artifacts have not moved since 2026-07-16. **Eleven days of active build work produced no session close at all.** This is direct filesystem confirmation of the ticket's second failure case — the one the original Section 1 treated as secondary. `/secretary`'s all-or-nothing cost is not merely inconvenient at high cadence; at this project's actual cadence it has caused the workflow to stop running entirely, and eleven days of agent context is simply gone. Section 4's proposed `--context` mode addresses precisely this, and this evidence promotes it from the ticket's secondary case to its primary one.

### Two further findings from the same pass

1. **`.workflow_state/` is untracked by git** (`git ls-files .workflow_state/` returns empty in a confirmed work tree). Prior `HANDOFF.md` versions are therefore unrecoverable by any means. The 2026-07-16 merge succeeded; had the agent not improvised, there would be no recovery path. The overwrite is genuinely destructive, not merely lossy-with-fallback.

2. **`secretary.md` contradicts itself on archival, and the named artifact has never existed.** The GLOSSARY states prior content is *"preserved in HANDOFF_ARCHIVE.md if needed"*; STRICT RULE 3 states prior content *"is NOT archived unless it contains anomalies."* `ls .workflow_state/HANDOFF_ARCHIVE.md` → no such file. An agent reading the GLOSSARY could reasonably believe an archival safety net exists before overwriting. It does not.

### Forensic citations for this addendum

- **The improvised merge**: [HANDOFF.md line 4](file:///home/jwils/.prebuild.temp/lsshreveport/.workflow_state/HANDOFF.md#L4-L4)
  *Evidence: `# Generated by: /secretary (Claude Code pass — merges Gemini's prior pass this session)` — a merge the protocol never specifies.*
- **The unlogged deviation**: [ANOMALY_LOG.md](file:///home/jwils/.prebuild.temp/lsshreveport/.workflow_state/ANOMALY_LOG.md#L6-L8)
  *Evidence: three `NO ANOMALIES` entries for 2026-07-16, including the pass that deviated from STRICT RULE 3.*
- **The contradiction**: [secretary.md GLOSSARY](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L65-L65) against [STRICT RULE 3](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L568-L568)
  *Evidence: GLOSSARY promises `HANDOFF_ARCHIVE.md`; STRICT RULE 3 denies archival; the file does not exist.*

### Effect on the remediation

Section 4's six points stand unchanged — the evidence strengthens them rather than redirecting them. Two items are added:

8. **Phase 4 must gain explicit peer-detection**, not merely ledger consumption (Section 4 item 5). If the existing `HANDOFF.md` names a different generating agent for the same session date, merge under attributed headings — the behavior the 2026-07-16 agent improvised — rather than overwrite. Codifying what a good agent already does is cheaper and more reliable than depending on every future agent to independently reach the same conclusion.
9. **Resolve the `HANDOFF_ARCHIVE.md` contradiction** in the same pass, per `/nodelete`'s Contradiction Protocol: either implement the archive the GLOSSARY promises, or correct the GLOSSARY to match STRICT RULE 3. Leaving a promised safety net that has never existed is its own hazard.

**Urgency remains HIGH.** It is not escalated to CRITICAL despite the confirmed eleven-day gap, because that gap is a *cost-induced non-invocation*, not a workflow producing wrong output — the artifacts that do exist are accurate. The destruction pathway remains live and unguarded, but has not yet fired.

---

## Partial Remediation — 2026-07-28 — Items 1-4 and 6 built; 5, 7, 8, 9 deferred

**Ticket remains OPEN.** Phylogeny Disposition remains PENDING (correctly — STRICT RULE 12 gates it on Status reaching REMEDIATED, which this pass deliberately does not claim).

### REMEDIATION RECORD (partial)

```
Ticket:            20260728_secretary_workflow.md
Faulting workflow: /secretary
Root cause fixed:  /secretary had no state between "complete session close" and "nothing,"
                   so context could not be preserved at a phase boundary or by a second
                   agent in a session a peer had already closed.
Changes made:      claude-commands/secretary.md — MODE GATE (`--context`) inserted before
                   Phase 0; GLOSSARY row (CONTEXT_LEDGER.md); STRICT RULE 22; HOW TO BEGIN
                   mode line; frontmatter (version 7->8, flags, strict_rule_count 21->22,
                   last_hardened, produces, content_hash). .changelogs/secretary.md entry 16.
                   phase_count unchanged at 8 — the gate is a mutually-exclusive branch,
                   not a ninth phase.
Tests:             537/537 passing (scripts/run_tests.sh) — 0 regressions.
Linter:            0 CRITICAL. secretary.md clean; content hash verified matching after paste.
Symlink:           ~/.claude/commands/secretary.md -> canonical source, intact.
Live trial:        NOT run this session — deliberately, so the user's first `--context`
                   invocation is a genuine trial rather than a vacuous one. Mirrors the
                   precedent set by Change Log entry 15's archival decision.
Deferred:          items 5, 7, 8, 9 below.
```

### Deferred item 9 — the denominator problem (captured here rather than as a full Addendum, by explicit user decision)

The suite has no machine-readable count of sessions, so no ticket or failure rate can be computed against a denominator. `/secretary` Phase 1 Step 1.2 already writes a per-session `SESSION APPEND` entry into `manifest/history/` — the pipe exists — but the entries are ~350-word prose, and the heading format is **already inconsistent within a single shard** (`### SESSION APPEND: 2026-07-09` and `## **[SESSION APPEND — 2026-07-09 — title]**` both appear in `WORKFLOW_MANIFEST_2026-Q3b.md`), so even grep-counting is unreliable.

Measured 2026-07-28: **40** `SESSION APPEND` entries across all shards; **77** tickets (7 open + 7 closed-in-root + 63 archived); **46** `PROCESS_LEARNINGS.md` entries. Tickets outnumber recorded sessions 1.9:1, and retrospectives outnumber narrative entries — an inversion that is structurally impossible if both ran (Phase 1 precedes Phase 6), and therefore proves the session count is unsound rather than merely low.

Proposed fix, when budget allows: a one-line-per-session structured ledger written by `scripts/ledger/ledger.py` — which Step 1.2 **already invokes unconditionally on every run** (STRICT RULE 19), so this costs `secretary.md` roughly one line of protocol text rather than a new section. Fields: date, project, agent, session type, workflows invoked, tickets filed, receipts touched. The narrative prose is not replaced — it is indexed. Same architecture as `CONTEXT_LEDGER.md` (append-only, one line per event), differing only in scope: suite-global rather than per-project.

**Explicitly out of scope by user decision (2026-07-28):** average session length. No session-start timestamp is recorded anywhere in the suite, so duration requires `/sentinel` stamping a start marker at session init and the ledger differencing it. That is a build, not a query, and was judged too bulky for now.

**Ordering note:** item 9 is downstream of items 1-5. A session index indexes sessions; `--context` is what makes cheap per-session records exist in the first place. Building the reporting layer before the collection layer would be backwards independent of budget.

### Remaining deferred items

- **Item 5** — Phase 4 consumes `CONTEXT_LEDGER.md` entries since the last close into `HANDOFF.md` and marks them consumed. Until built, checkpoints are write-only and must be read by hand. Not harmful, but the loop is open.
- **Item 7** — Phase 4 peer-detection and attributed merge, codifying the improvisation the 2026-07-16 agent performed against STRICT RULE 3. **This is the live destruction pathway**: an agent following Rule 3 literally still overwrites a peer's briefing, and `.workflow_state/` is untracked by git, so there is no recovery.
- **Item 8** — the `HANDOFF_ARCHIVE.md` contradiction: GLOSSARY promises an archive, STRICT RULE 3 denies it, and the file has never existed on disk. Resolve per `/nodelete`'s Contradiction Protocol — implement it or correct the GLOSSARY.

---

## Correction — 2026-07-28 — The "eleven days, zero session closes" finding was WRONG. Wrong substrate.

**Per `/nodelete`, the erroneous Addendum text above is left standing and corrected here rather than edited away.**

**What I got wrong.** The Addendum's headline finding — eleven days of build work with zero session closes — was derived from `/home/jwils/.prebuild.temp/lsshreveport/.workflow_state/`. That is **not the active project's** `.workflow_state/`. The repository contains two:

| Path | Project | HANDOFF.md last written |
|---|---|---|
| `.workflow_state/` (repo root) | `lsshreveport` — fee-estimator/branding work | 2026-07-16 14:52 |
| `research/proforma/.workflow_state/` | `Continuum North End Master Pro Forma` | **2026-07-28 14:17** |

The root directory is not a gap. It is a **completed sub-project's dormant state directory.** The active project — the pro forma build — has been closing sessions normally and recently: `HANDOFF.md` 14:17, `ANOMALY_LOG.md` (18KB) 14:18, `BUILD_RECEIPTS.md` (127KB) 14:49, all on 2026-07-28.

**Named failure: Context Erosion, mine.** I audited the workspace root because that is where a `.workflow_state/` is *conventionally* located, and did not verify that the active work was rooted there before drawing a conclusion from what I found. This is the same nested-substrate trap already documented in `helpdesk-tickets/CLOSED_20260707_nested-tasks-md-receipt-title-mismatch_workflow.md` — a closed ticket in this very corpus, which I did not consult. The evidence pass that corrected the ticket's *first* wrong claim introduced a second one.

**What this changes, and what it does not.**

- **Changed — the ticket's primary justification.** The defect is NOT "sessions stopped being closed because `/secretary` is too expensive." Sessions are being closed. The real defect is the one the user described in the first place and which I over-embellished: **a full session close does not capture an agent's working state, and phase-boundary checkpoints — which occur many times per session in a 100K-per-phase build — had no home at all.** Both live `--context` entries confirm this directly: both were written at a *phase boundary*, not a session end, and both record hypotheses and unverified claims that appear in no receipt and no `HANDOFF.md`.
- **Unchanged — the remediation.** Items 1-4 and 6 as built are correct and are now demonstrated working in production. Deferred items 5, 7, 8, 9 stand exactly as written. Item 7 in particular is untouched by this correction: the peer-overwrite pathway in Phase 4 remains live.
- **Strengthened — item 9.** A suite-level session index would have made this error impossible to commit: a machine-readable per-session record naming its project root would have shown at a glance that the root `.workflow_state/` had no sessions attached to it after 2026-07-16 *because that project ended*, not because closes stopped.

**New deferred item 10 — `.workflow_state/` discovery is unspecified.** No workflow in the suite states how to locate the *active* `.workflow_state/` when a repository contains more than one. `/secretary` writes to `{project}/.workflow_state/` without defining `{project}`. Both `--context` agents resolved it correctly from their own working context; an agent invoked from the repo root would have written the checkpoint into the dormant directory. `/sentinel`'s `.doorway/substrate_index.json` plausibly already holds the facts needed to resolve this — worth checking before designing anything new.

---

## Closure — 2026-08-13 — Approved by user; Remediation Record; Phylogeny resolved; deferred items re-homed

**Authorization**: User, 2026-08-13, verbatim: *"If it's not built, it is approved. If already built, it is still approved and the ticket needs to close."* Build state was verified before closing, as directed: the MODE GATE is fully present in the working tree (`claude-commands/secretary.md` v8 — gate before Phase 0, Context Capture Step, Context Checkpoint Receipt, STRICT RULE 22, GLOSSARY row, `flags: ["--context"]`), and production use is documented (two agents, phase-boundary checkpoints, `research/proforma`, 2026-07-28 — the Correction section above) plus the user's own report of sustained use since.

### REMEDIATION RECORD (final — supersedes the partial record above for closure purposes; that record is preserved as the build-time snapshot)

```
Ticket:            20260728_secretary_workflow.md
Faulting workflow: /secretary
Root cause fixed:  /secretary had no state between "complete session close" and "nothing";
                   agent working context at phase boundaries had no home, and a second
                   agent's slice of an already-closed session was unrepresentable.
Changes made:      claude-commands/secretary.md v7→v8 — MODE GATE (--context) before
                   Phase 0 (mutually-exclusive branch, phase_count unchanged at 8);
                   writes exactly one file, {project}/.workflow_state/CONTEXT_LEDGER.md,
                   append-only; STRICT RULE 22 (bounded carve-out of Rules 1/7/13 only);
                   GLOSSARY row (CONTEXT_LEDGER.md); HOW TO BEGIN mode line; frontmatter
                   v8. .changelogs/secretary.md entries 16-17 (entry 17 being the build's
                   own justification correction — Context Erosion, named against itself).
Tests:             537/537 passing — re-run at closure 2026-08-13, not the 2026-07-28
                   count reused.
Linter:            0 CRITICAL / 22 WARNING — re-run at closure 2026-08-13.
Live verification: In production since 2026-07-28 — two agents (Opus 5 execution,
                   Sonnet 5 orchestration) wrote phase-boundary checkpoints recording
                   hypotheses and unverified peer claims that appear in no receipt and
                   no HANDOFF.md; user reports sustained use since ("I've been using it
                   a lot already," 2026-08-13). By construction and by observed use, a
                   --context run writes nothing outside {project}/.workflow_state/.
Scope note:        The original Verification bar (preserved verbatim below) additionally
                   required item 5 (Phase 4 ledger consumption) and a byte-identical
                   two-agent measurement. Closure at the built scope (items 1-4, 6) is
                   an explicit user decision of 2026-08-13 — not a claim those items
                   were built.
Deferred:          Items 5, 7, 8, 9, 10 — re-homed at closure to
                   helpdesk-tickets/20260813_secretary-deferred-items_workflow.md so
                   they retain a session-start-visible tracking home after this file
                   archives. NOT dropped. Item 7 remains the live pathway.
```

**Original Verification bar, preserved verbatim per /nodelete**: "PENDING. Closure requires a Remediation Record (Phase 4b) covering: the Mode Gate as landed, the `CONTEXT_LEDGER.md` schema, the base-Phase-4 consumption amendment, STRICT RULE 22, `lint_workflows.py` result, and a live two-agent test confirming a `--context` run leaves a peer's `HANDOFF.md` and the active narrative shard byte-identical."

### Phylogeny Disposition — resolved: NO TRANSFER (Step 4a.5)

This remediation touched one workflow file (`secretary.md`, plus its changelog shard). No structural pattern moved between workflow files. Candidate named rather than lost, per Step 4a.5's over-caution instruction: the **MODE GATE** shape — a flagged, mutually-exclusive partial-execution branch with a bounded, named STRICT-RULE carve-out — is the suite's first. If a second workflow ever adopts it, that session owes `manifest/SUITE_PHYLOGENY.md` the lineage entry, with this ticket as the origin.

*Closed by: Claude Fable 5, Senior Architect of Workflows — direct SUBSTANTIVE-LOGIC remediation path, /helpdesk-tickets Phase 4, user-approved 2026-08-13.*
