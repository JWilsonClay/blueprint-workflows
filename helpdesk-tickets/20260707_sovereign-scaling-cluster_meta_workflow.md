# Helpdesk Ticket: Sovereign Scaling Cluster — Verification-Spine Completion, Bloat Remediation, Doorway/README Remediation, and Execution Delegation Strategy

**To**: Senior Architect of Workflows (John Wilson)
**From**: Claude (session agent)
**Date**: 2026-07-07
**Subject**: Four-part strategy proposal covering (1) the stalled Verification-Spine Upgrade Campaign, (2) an evidence-based response to the Antigravity workflow-architectural-bloat findings — now including a verified Instruction Density Compression lever, (3) a Claude-designs/Gemini-executes token-economy delegation model, and (4) closing the gap between the Doorway Design Invariant this suite already declared and what its code actually does. User-reviewed once (2026-07-07); this revision incorporates that review. Some items below (marked ✅ DONE) were executed directly this session as authorized low-risk cleanup; the substantial construction work remains gated behind the user's separate execution approval.
**Urgency**: HIGH (Strategic — governs the shape of the next major cluster of work)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 0. Scope & Process Boundary (read first)

This ticket is a **strategy and design artifact**. A small number of low-risk, mechanical, immediately-reversible items were executed directly this session under the user's general cleanup authorization (marked ✅ DONE throughout, each with real evidence) — everything else, especially the substantial construction work in §2-5, remains gated behind a separate, explicit execution approval per the user's own stated process.

**Explicitly out of scope for this session to act on**: `helpdesk-tickets/20260707_workflow-architectural-bloat_workflow.md` and its supporting evidence remain a concurrent Antigravity/Gemini-research artifact under the user's own control. §3 responds substantively to it (including verifying and incorporating a user-pasted Gemini research appendix) but this ticket does not close, rename, or edit that ticket.

**User review incorporated (2026-07-07):** the user reviewed the prior revision of this ticket in full and recorded no material disagreement. Specific confirmations and corrections from that review are folded in throughout, and cited inline where they change a prior recommendation.

---

## 1. Executive Summary

Four threads, one underlying gap. The suite has no formal mechanism for distinguishing *judgment work that requires the most capable model* from *construction work that could run on a less expensive one* — today, by default, everything runs on Claude natively. That gap connects all four parts:

- **Part 2 (§2)**: A separate, still-open campaign (`implementation-plan.md` at repo root) has 9 pending and 2 deferred workflow-engine upgrades. Real, substantial, unstarted work — now being converted from its self-perpetuating QUEUE format into this ticket's governing `tasks.md`.
- **Part 3 (§3)**: A concurrent research ticket found real evidence of structural imbalance in Sovereign workflow files, and the user separately supplied a second, verified research thread from that same investigation — Grok workflows literally embed executable-looking pseudocode as their primary instruction medium. Both are real. Neither justifies a wholesale suite rewrite; both point to two narrow, targeted levers.
- **Part 4 (§4)**: The user's own proposed fix for the token-economy gap — Claude designs, a cheaper/less-scarce agent executes most construction — turns out to already be `/workstream --gemini`, a Sovereign-graded, already-built role the user had simply forgotten was there. The gap is not "build a new mechanism," it's "build a lighter single-engineer mode for it, then learn to use it."
- **Part 5 (§5)**: While investigating a user question about README breadcrumb cleanup, direct code inspection found that `doorway.py` already *declares* a design principle it never finished *enforcing* — README self-heal was still creating files everywhere by default, contradicting the module's own stated "Doorway Design Invariant." This is now fixed (✅ DONE, §5.1).

§6 proposes one sequenced plan across all four parts.

---

## 2. Part 1 — The Verification-Spine Campaign Is a Real, Unstarted Backlog

### 2.1 Finding

`implementation-plan.md` (repo root) is a self-perpetuating, QUEUE-table-driven campaign, distinct from a `tasks.md`-paired plan. Current state (`implementation-plan.md:66-99` as of this ticket's original filing):

| Status | Workflows | Count |
|---|---|---|
| DONE | `/focus-plan`, `/quality`, `/harden`, `/iterate-test`, `/receipt-check` | 5 |
| PENDING | `/redteam`(#3), `/execute-build`(#4), `/sentinel`(#5), `/continuous-verify`(#6), `/secretary`(#7), `/triage`(#8), `/investigate`(#9), `/helpdesk-tickets`(#10), `/harden-workflow`(#12) | 9 |
| DEFERRED | `/refactor`(#13), `/provenance`(#14) | 2 |
| EXCLUDED (correctly scoped out) | 18 workflows, reasoned individually | 18 |

Each pending item follows a fully-specified, ten-step "END-TO-END UPGRADE RECIPE" (`implementation-plan.md:109-137`) — mechanical enough to already resemble an executable checklist.

### 2.2 A finding the queue itself doesn't know yet

The QUEUE table was last touched 2026-06-02. Since then, the Sovereign Redesign Cluster hardened four PENDING-listed workflows (`/execute-build`, `/secretary`, `/triage`, `/harden-workflow`) through *other* means — ticket-driven fixes, not the campaign's own engine-extraction recipe. "PENDING" here means *never received the specific engine-extraction treatment*, not *un-hardened*. Re-running the campaign's own "Honest-Design Discipline" step against these four specifically is a real prerequisite, not busywork, since the files these would-be engines target have materially changed shape.

### 2.3 Recommendation (→ `tasks.md` Phases 4-5)

1. Re-run Honest-Design Discipline against the four workflows in §2.2 before building their engines.
2. Convert the QUEUE-table format to the standard `implementation-plan.md` + `tasks.md` pair (per `templates/plan/`). Each QUEUE row maps to one `tasks.md` Phase; the ten-step recipe maps to that phase's task checklist.
3. Prioritize `/execute-build`'s own engine-extraction ahead of its current #4 position — Part 4's delegation design builds directly on top of it.

### 2.4 Status Snapshot — [ADDED 2026-07-07, this session, closing this Part] **PART 1 COMPLETE**

All 9 PENDING workflows named in §2.1's table now have real, tested, read-only engines. Executed exactly as §2.3 recommended: `/execute-build` went first (`tasks.md` Phase 4.1-4.2), then `/secretary`/`/triage`/`/harden-workflow` (the remaining §2.2 re-verification targets, Phase 4.3-4.5), then the five originally-PENDING-but-not-materially-changed targets `/redteam`/`/sentinel`/`/continuous-verify`/`/investigate`/`/helpdesk-tickets` (Phase 5.1-5.5). Each got its own fresh Honest-Design Discipline pass per §2.3 item 1 — three found the seed assumption needed correcting (`/execute-build`'s reuse target had already been built elsewhere; `/redteam`'s "Ghost Logic collector" framing didn't survive re-application against an arbitrary-target-codebase constraint; `/sentinel`'s assumed "drift-delta layer" gap didn't exist at all), the rest confirmed and specified the original hint. 168 new tests (295 → 463), zero regressions, every touched file lint-CLEAN. Per-workflow evidence: `tasks.md` Phases 4-5, `docs/compression-staging/*-honest-design.md` (9 design docs), and 9 closed helpdesk tickets (`CLOSED_20260707_*-engine-gap_workflow.md`). This closes Part 1 (§2) of this ticket — Parts 2-4 (§3-§5) remain open, gated behind the separate execution approval §0 describes.

A retroactive data-integrity finding surfaced by the very last engine built (`/helpdesk-tickets`'s own Ticket Lifecycle Evidence Engine): all 9 of this session's own engine-gap tickets had left `Phylogeny Disposition: PENDING` despite `Status: REMEDIATED` (a live instance of the exact contradiction that engine was built to catch), and used prose evidence instead of the mandated citation format. Corrected same-day — see those 9 tickets' own `Phylogeny Disposition Note` fields and added citations.

---

## 3. Part 2 — The Bloat Ticket: Real Signal, Two Narrow Levers (Not a Rewrite)

### 3.1 What's real (verified directly, not accepted from the ticket's framing)

- Change Log and STRICT RULES genuinely consume a large, growing share of word count in mature files: `secretary.md` — 44.1% combined; `nodelete.md` — 35.8%. Append-only by design, re-read in full on every invocation — a genuine, monotonically-growing per-invocation token cost.
- **User-verified, 2026-07-07**: a second research thread from the same Gemini/Antigravity investigation, pasted into the bloat ticket (`20260707_workflow-architectural-bloat_workflow.md:190-289`) after this ticket's first draft, and independently spot-checked against the real source rather than trusted at face value: Grok's `execute-plan/SKILL.md` genuinely embeds a `while` loop over `ready_queue`/`in_progress` (verified: `~/.grok/bundled/skills/execute-plan/SKILL.md:440-466`), a `cascade_skip()` function definition (verified: `:787`), and a mathematical dependency-level formula `level(node) = ...` (verified: `:346-347`). These are not paraphrase or embellishment — they are the literal, verbatim content of the file. Grok's architecture treats the LLM as a compiler/interpreter of embedded pseudocode, not just a prose reader.

### 3.2 Where the ticket's causal story still overreaches (dissent stands, confirmed by user review)

Sovereign's mean word count (3998) is lower than Grok's (7479); Sovereign's structural conformity is far higher (~100% vs. 12-96%); the Imbalance Score metric structurally bakes in a penalty for the suite's own mandated Change Log/STRICT RULES sections; the N=5 Grok sample is a different task genre (multi-agent orchestration) from most single-agent Sovereign files. Full citations in the prior revision of this ticket, unchanged. **User confirmed 2026-07-07**: *"I cannot dissent to your Do not assessment. It pours factual water on the fire we thought was there."* No suite-wide rewrite to Grok-style pseudocode. That remains correct.

### 3.3 Recommendation — three targeted levers, not a redesign (→ `tasks.md` Phase 1-2)

1. **Change Log externalization.** Move each workflow's Change Log to **`.changelogs/<workflow-name>.md`** (dot-prefixed, per user correction 2026-07-07 — matches `.workflow_state/`, `.history/` convention), leaving a short pointer in the live file. `/nodelete`-compliant: relocated, never deleted.
2. **STRICT RULES gets no standalone fix — its fix is Part 1.** Converting prose-enforced rules into engine-enforced checks is the Verification-Spine campaign's entire purpose (`/harden`'s Grade Ceiling, `/iterate-test`'s Mock-Trap detector are the proven precedent). Finishing §2's backlog *is* the STRICT RULES bloat fix.
3. **Instruction Density Compression (new, from the verified §3.1 research) — the necessary-but-verbosely-communicated half of bloat, distinct from levers 1-2.** User's own framing, 2026-07-07: *"Bloat can be from two possibilities, one, unnecessary information, and two, necessary information communicated in a bloated methodology... Grok's workflows serve as a perfect example for how to condense meaningful instruction into token conscious format."*

   **The precise distinction (worked out with the user this session, since it determines where this lever may and may not be applied):** the Honest-Design Discipline's existing axis (mechanically-verifiable vs. irreducible-judgment) determines *where content lives* — a real script, or the model. Pseudocode density is a *different* axis — *how densely* whatever already lives with the model is communicated. It applies only to content that stays with the model: both judgment payloads and the control-flow that orchestrates them. A STRICT RULE like "discussion is not authorization" can be written as flowing prose or as `if not user.explicit_selection: HALT(...)` — both are the same instruction; the model still has to evaluate it either way; neither is a script. That's the legitimate, judgment-preserving compression this lever targets.

   **The boundary this lever must not cross (user explicitly invited dissent; this is it, confirmed correct on review):** the ability to *notate* something as pseudocode does not imply it's mechanically decidable. `if is_this_design_excellent(): proceed()` is exactly as syntactically valid as `if file_exists(path): proceed()` — the first calls a function that can never actually be implemented. Pseudocode notation *hides* a smuggled judgment call better than prose does, not worse (prose forces an honest "in the model's judgment..."; pseudocode can look deterministic when it isn't). The test for "should this become a real script" was never "can I write pseudocode for it" — it remains the original Mock-Trap test. Compression is legitimate only where it changes *how densely* something is phrased, never *what kind of decision* is being made.

   **Scope, precisely:** apply to STRICT RULES with clear IF/THEN/HALT shape and Phase control-flow/branching logic. Do **not** apply to GLOSSARY, "why we do this" prose, or Change Log narrative — compressing motivation and historical context into pseudocode destroys the value a fresh-context reader needs, and Grok's own files aren't 100% pseudocode either (their Rules/Setup sections remain substantially prose). Per-rule test before compressing: *does this change what's being asked, or only how densely it's phrased?* If the former, don't compress it — it likely belongs in lever 2 (a real engine) instead.

---

## 4. Part 3 — Execution Delegation: Claude Designs, Gemini Executes (revised after user review)

### 4.1 This is not a new idea — it's `/workstream`, which the user had simply forgotten existed

**User, 2026-07-07**: *"I may have to learn to use the workstreams workflow mechanic that was already built into the suite, I just forgot about it."* Confirmed: `/workstream` (Sovereign, v4) already defines `--gemini` as Workstream B's permanent role (`workstream.md:88`), with `/implementation-plan --workstreams`/`--audit --workstreams` as the design/audit machinery around it (Phase 6/7). The deeper mechanism — `docs/design-pillars/PILLAR_03_EXECUTION_DELEGATION_FORMULA.md`, a full delegation-adapter design — was deliberately left unbuilt in `execute-build.md` this session, gated behind the Agent Capability Gate specifically because of the $200 Grok Build overrun. Nothing here is new construction from zero; it's finishing and lightening what already exists.

### 4.2 Runtime decision — confirmed, now with a firmer reason than a cooldown

**User, 2026-07-07**: *"opencode no longer exists on the laptop, and grok build will be on hiatus for the foreseeable future... my trust in the xai plan was broken for now."* This upgrades the prior finding (a ~1-week interface-learning cooldown, partially elapsed) to an indefinite hold for a trust reason, not a scheduling one. **Decision, per user: Gemini/Antigravity is the execution partner. Grok Build work is not scheduled and should not be spent effort on beyond what's already flagged.** The asymmetry from the prior revision stands as context (Gemini has no CLI — Antigravity is an interactive app, so the handoff is necessarily human-mediated paste-and-return, not automatable; Gemini has no proven delegated-execution track record in this suite, unlike Grok's validated Videos-project run) — recorded for completeness, not to relitigate a decision the user has now made twice.

**User's own shorthand, 2026-07-07**: *"my desire right now will be to remain with the claude gemini claude workflow"* — confirms the exact three-leg shape already proposed: Claude designs → Gemini executes → Claude verifies.

### 4.3 Why the existing `/workstream` model needs a lighter mode, not a replacement

`/workstream` is built for **3 simultaneous parallel engineers** (Claude=A, Gemini=B, Grok=C) under a Grok-OpenCode PM plus a Grok-Web Architect — rotation formulas, cross-workstream conflict scans, a Diff Oracle. The user's ask is simpler and serial: one designer/reviewer, one primary builder. Its PM/Architect roles are also currently assumed to be Grok OpenCode — itself retired, which would reintroduce the exact Grok-dependency question §4.2 just resolved. A single-engineer mode avoids both problems.

### 4.4 Proposed design — now explicitly two-fold per user request (→ `tasks.md` Phase 6-7)

**User, 2026-07-07**: *"it sounds like a two fold methodology, a refinement/rebuild as proposed of the workstreams workflow, then a user training session so I can contextualize how to use workstreams properly, as I forgot about it immediately after building it."*

**Fold 1 — Build the single-engineer mode:**
1. Design leg (Claude, native, unchanged): `/design-orchestrator` → `/implementation-plan` produce `DESIGN_*.md`, `implementation-plan.md`, `tasks.md`. Already exists.
2. Execution leg (Gemini, new): extend `/workstream` Phase 0a and `/implementation-plan` Phase 6 to recognize a workstream design with only Workstream B populated (A and C explicitly DORMANT). Reuse the existing Pre-Flight Manifest, Engineer Brief, and Handoff Block mechanics verbatim — they don't depend on the 3-engineer count. Skip rotation, cross-workstream conflict scan, and PM/Architect ceremony.
3. Verification leg (Claude, native, unchanged): `/implementation-plan --audit --workstreams` (or a solo-mode variant) reuses the already-hardened Coverage Ledger audit to independently verify Gemini's output.
4. Safety carryover from the $200 lesson: bound each delegation to one phase/slice at a time — never "build the whole plan" unsupervised in one hop.

**Fold 2 — User training (new deliverable, explicitly requested, not previously scoped):**
5. Produce a standalone quick-reference (`docs/GEMINI_WORKSTREAM_GUIDE.md` or an extension of `/onboard`, already Sovereign-graded for "situation-aware startup brief") covering: exactly how to invoke `/workstream --gemini` in the new single-engineer mode, what the Engineer Brief / Handoff Block round-trip actually looks like end to end, and a worked example using the first real pilot from §6 item 5. This exists specifically so the mechanism doesn't get built and then forgotten a second time.

---

## 5. Part 4 — Doorway/README: A Declared Principle the Code Never Finished Enforcing

### 5.1 Finding, and the fix already executed this session (✅ DONE)

**User question, 2026-07-07**: *"I believe we have completely overhauled the doorway protocol under the sentinel workflow... I think the readme breadcrumb logic was retired. How do we design a cleanup one off to remove the readme's..."*

Investigated directly rather than assumed either way. Finding: **partially right, in an important and non-obvious way.** `doorway.py`'s own module docstring already declares a "Doorway Design Invariant" (added under Pillar 1, PR 01-06): *"Agent context is delivered by the engine [substrate_index.json], not by filesystem cardinality (N x README.md)."* A real `substrate_index.json` mechanism already exists (PR 01-01). But direct inspection of `integrity.py`'s `create_readme()` (pre-fix) showed the actual README-creation code path was still fully active by default, excluding only two hardcoded directories (`claude-commands`, `helpdesk-tickets/archive`) — the stated principle and the actual behavior had diverged. This explains the 20+ untracked breadcrumb READMEs still littering the workspace: the mechanism that creates them was never turned off, only patched for one narrower data-loss bug earlier this session (`CLOSED_20260705_doorway_lazy-scan-stale-readme_workflow.md`).

**Fixed this session, verified, not just designed:**
- `scripts/doorway/integrity.py`: `IntegrityManager` gains `autoheal_enabled: bool = False`; `create_readme()` now returns `False` immediately unless explicitly enabled. `heal()` (Architecture.md/MANIFEST.md self-repair) is untouched — this gate is README-specific.
- `scripts/doorway/doorway.py`: `DoorwayContextualizer` gains a `readme_autoheal` passthrough (default `False`), threaded explicitly to `IntegrityManager` rather than left implicit.
- `scripts/tests/test_doorway.py`: existing 4 tests updated to pass `readme_autoheal=True` explicitly (they test self-heal *regression* behavior specifically and need the real code path exercised to mean anything). New `TestReadmeAutohealDefaultOff` (2 tests) proves the new default directly: no README created, `missing_readme` still reported (unconditional in `auditor.py`), opting in still works.
- Full suite: 303/303 passing, including the 6 doorway tests.

This directly completes what Pillar 1 already declared as intended state — not a new architectural decision, a closed gap between stated principle and code.

### 5.2 What is genuinely still open (not done this session, correctly so)

The still-open, HIGH-urgency `helpdesk-tickets/20260705_sentinel-doorway-redesign_workflow.md` — filed during Grok Build's inaugural session — already diagnosed this exact class of problem and designed the fuller remediation: a `substrate_index.json`-centric, tiered zero-finding model, with `sentinel.md`'s own README-walk language (Phase 1.5) updated to match, plus `scanner.py`/`manifest.py`/`breadcrumb.py` changes. §5.1's fix is that ticket's Phase 0 prerequisite, done; the ticket's Phase 1-6 architecture is real, well-specified, substantial, and **not built** — appropriately folded into `tasks.md` as future work (§6, and a strong candidate for the Part 3 delegation pilot, since it's already fully specified). A provenance note is being appended to that ticket (not a closure) recording this partial progress.

### 5.3 Workspace and git-history cleanup — two tiers, only one executed now

**User asked for both:** (1) remove the breadcrumb READMEs from the workspace, and (2) remove them from git history.

- **Tier A — workspace + normal git removal (✅ DONE, safe, ordinary, reversible via `git revert`):** with §5.1's fix landed first (so nothing regenerates), untracked breadcrumb READMEs are deleted from the working tree and tracked ones (`scripts/README.md`, `scripts/doorway/README.md`, `helpdesk-tickets/README.md` and siblings — 8 files, confirmed via `git ls-files`) are `git rm`'d as part of this session's commit. This is completely ordinary version control, not history-rewriting.
- **Tier B — actual git-history purge (NOT done, flagged, needs its own explicit go-ahead):** `git log --all -- '**/README.md'` shows 8 historical commits touched a README.md file, some already pushed to the public GitHub remote. Fully removing that content from history (not just going forward) requires `git filter-repo` or equivalent, followed by a **force-push to a public repository** — a hard-to-reverse, shared-state-affecting action that breaks any existing local clones and is explicitly the category of action my own operating principles require separate, informed confirmation for, independent of the broad cleanup authorization already given. Two real options, not decided here: (a) accept that a handful of old commits retain README content — the working tree is clean going forward, which is what matters for day-to-day use; (b) proceed with the history rewrite, understanding the force-push and clone-breaking consequences. **This ticket recommends (a)** unless the user has a specific reason (e.g., accidentally-committed secrets, which these files do not contain) to warrant (b)'s cost. Recorded in `tasks.md` as an explicitly-gated, not-yet-authorized task either way.

---

## 6. Combined Sequencing (`tasks.md` is now the authoritative, checkable version of this section)

1. ✅ DONE — Doorway autoheal opt-in fix + regression tests (§5.1).
2. ✅ DONE — Workspace README cleanup, Tier A (§5.3).
3. Quick wins, low risk: `.changelogs/` externalization (§3.3.1); `lint_workflows.py --fix-hashes --write` mode (✅ DONE this session, resolves `20260704_lint-fix-hashes-gap`).
4. Container conversion: root `implementation-plan.md` → `tasks.md`-paired format (§2.3.2), re-running Honest-Design Discipline on the four workflows that changed shape (§2.2).
5. Re-prioritize within the converted queue: `/execute-build` engine-extraction first.
6. Build the single-engineer delegation mode (§4.4, Fold 1).
7. Produce the user training guide (§4.4, Fold 2).
8. First live pilot: run either a Verification-Spine backlog item or the doorway `substrate_index.json` architecture (§5.2) through the new Gemini delegation pattern — the latter is a strong candidate since it's already fully specified.

---

## 7. Risks

- **HIGH — repeating the $200 failure shape with a different runtime.** Mitigated by §4.4 item 4 (bounded per-phase delegation) — must not be skipped when built.
- **MEDIUM — Gemini delegation is unproven in this suite.** Mitigate by treating §6 item 8 as an explicit, small pilot, not the largest item.
- **MEDIUM — Force-push temptation on the README history question.** §5.3 Tier B is recommended against by default; treat any future request to proceed with it as requiring fresh, explicit confirmation, not inferred from this ticket's general cleanup authorization.
- **LOW — the bloat ticket and this one both exist, addressing overlapping ground.** No content conflict; user's call whether to cross-reference or close either.

---

## 8. What This Ticket's Design Sections (§2, §4 Fold 1, §5.2 Tier B) Explicitly Do Not Do

- Does not build the single-engineer `/workstream` mode, the doorway `substrate_index.json` architecture, or the `.changelogs/` migration across all 33 files — real, substantial construction work, correctly deferred to `tasks.md` for a future, separately-approved execution pass.
- Does not rewrite `implementation-plan.md`'s QUEUE-table content in place — see the archival note in `tasks.md` and `.history/archive/`.
- Does not touch `helpdesk-tickets/20260707_workflow-architectural-bloat_workflow.md`.
- Does not perform the git-history rewrite in §5.3 Tier B.

---

## 9. Open Ticket Disposition (scope-expansion authorization exercised this session)

Per explicit user authorization ("a few open tickets in the helpdesk... I will defer to you as an example of scope expansion opportunity I am authorizing you to decide on"):

| Ticket | Disposition | Reasoning |
|---|---|---|
| `20260704_lint-fix-hashes-gap_workflow.md` | **CLOSED this session** | `--write` mode built and tested (§6 item 3) — genuinely resolved, not administratively closed. |
| `20260705_opencode-to-grok-build-transition_workflow.md` | Stays OPEN | Its own text says re-open review only when Grok Build sees active use — §4.2 confirms that's further off than originally stated, not closer. |
| `20260705_sentinel-doorway-redesign_workflow.md` | Stays OPEN, provenance note appended | §5.1 closed its Phase 0 prerequisite; Phase 1-6 architecture genuinely remains unbuilt and is folded into `tasks.md`. Closing it now would be exactly the premature-closure failure this suite caught and corrected twice earlier this session. |
| `20260705_triage-session-handover_workflow.md` | **CLOSED this session** | Its one live recommendation (a `TRIAGE_RECEIPTS.md` persistence channel) is independently confirmed already built (`triage.md:426`, `.workflow_state/receipts/TRIAGE_RECEIPTS.md` exists on disk) — verified directly, not assumed from the ticket's own claim. Its handover content is fully consumed. |
| `20260707_nested-tasks-md-receipt-title-mismatch_workflow.md` | Stays OPEN | Unresolved, correctly so, per its own recommendation section — not touched by this cluster's scope. |
| `20260707_workflow-architectural-bloat_workflow.md` | Not touched | Remains under the user's own control per standing instruction. |
| `20260707_sovereign-scaling-cluster_meta_workflow.md` (this ticket) | Stays OPEN | Governing ticket for the cluster; closes when `tasks.md`'s phases are verified complete, mirroring the prior cluster's meta ticket. |

---

## 10. Fresh-Agent Pre-Read Map

1. This ticket, in full.
2. `implementation-plan.md` (repo root) — current state; note the archival pointer to `.history/archive/` if §2.3.2 has executed by the time you're reading this.
3. `tasks.md` (repo root) — the authoritative, checkable version of §6's sequencing.
4. `docs/design-pillars/PILLAR_03_EXECUTION_DELEGATION_FORMULA.md` §4 — the delegation pattern §4.4 adapts.
5. `claude-commands/workstream.md` and `claude-commands/implementation-plan.md` Phase 6/7 — existing multi-agent machinery being extended, not replaced.
6. `helpdesk-tickets/20260705_sentinel-doorway-redesign_workflow.md` — the fuller doorway architecture folded into `tasks.md`.
7. `scripts/doorway/integrity.py` + `scripts/doorway/doorway.py` — the autoheal opt-in fix (§5.1), already live.
8. `helpdesk-tickets/20260707_workflow-architectural-bloat_workflow.md` (including its user-appended Gemini research, lines 190-289) — the research §3 responds to and verifies.

---

## 11. Recommendation to Senior Architect

§2, §3, §4 Fold 1, and §5.2/§5.3 Tier B represent the remaining, substantial, not-yet-executed work — now expressed as the checkable `tasks.md` at repo root. On explicit approval, execution proceeds per §6's sequencing.

---
**Status**: **OPEN**
**Verification**: PENDING — user review incorporated 2026-07-07; awaiting approval to execute `tasks.md`.

---
*Signed,*
**Claude**
*(Session Agent — Senior Architect of Workflows role)*
