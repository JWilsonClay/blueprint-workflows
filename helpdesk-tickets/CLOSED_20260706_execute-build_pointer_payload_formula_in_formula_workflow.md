# Helpdesk Ticket: Native /execute-build Lacks Pointer/Payload Delegation to Grok /execute-plan (Formula-in-a-Formula Architecture)

**To**: Senior Architect of Workflows
**From**: Grok (Videos workspace, post-397b6602 execute-plan execution + native /implementation-plan --audit + direct discussion)
**Date**: 2026-07-06
**Subject**: Structural gap: native execute-build has no defined adapter/pointer-payload contract to delegate to superior Grok execute-plan engine while preserving Sovereign verification spine; creates redundancy, potential drift, and handoff Ghost Logic in large transitions
**Urgency**: CRITICAL (Architectural)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: `CONFIRMED — lineage entry` — see Hardening Certificate below. **[RESOLVED 2026-07-07]**

---

## 1. Executive Summary

In the current session, the full approved `docs/DESIGN_Complete_Videos_Pipeline.md` (containing the re-sequenced research engine + 4 Gaps/synthesis + close path) was successfully executed using Grok's native `/execute-plan` skill. This produced:
- A 15-node PR DAG (pr-1 research DB through pr-15 synthesis integration + receipts).
- Worktree-isolated subagents with implementer/reviewer personas.
- Mandatory review-fix loops driven to explicit 0 open issues (multiple rounds on pr-2, pr-4, pr-14, pr-15).
- Strict adherence to Subagent Worktree Protocol (fetch --no-tags, commit_sha authoritative via cat-file, worktree teardown before ref mutation).
- State persisted in `/tmp/grok-exec-plan-397b6602.json`.
- Stack assembly (plain-git mode) with range cherry-picks.
- Detailed per-PR appends to `.workflow_state/receipts/BUILD_RECEIPTS.md`.
- Final artifacts (VIDEO_SCRIPT, CONTENT_PLAN, etc.) matching DESIGN verbatim language for narration, timestamps, "minimal manual effort" list, short-form priority, etc.

Immediately afterward, the native `/implementation-plan --audit` (Phase 5 adversarial post-execution with Coverage Ledger) was invoked on the same work. It was dynamically adapted (per user authorization) because the native flow assumes `/execute-build` + `tasks.md`, but the actual execution used Grok execute-plan. The audit produced a high-fidelity report (89/100, 0 critical weaknesses, 4 minor notes on scope expansion in final fix, ephemeral /tmp state, generated artifacts in diff, residual broad except) and persisted it.

During the subsequent direct discussion of the experience, a clear, high-impact structural gap was identified and agreed upon with zero dissent:

The native Sovereign `/execute-build` (the phase-driven builder centered on `tasks.md` checkboxes, `implementation-plan.md` anchors, and the full verification spine) and Grok's `/execute-plan` (the DAG executor with superior isolation, review discipline, git protocol, and stack assembly) contain overlapping concepts (review-fix, fidelity, receipts, anti-drift) but also contradictions in plan representation, execution ownership, and state. There is **no defined mechanism** inside native execute-build for:
- Detecting a DESIGN-driven phase.
- Emitting a "pointer/payload" (modeled on the existing multi-runtime pointer system: one canonical payload, multiple delivery mechanisms).
- Delegating the core construction work to execute-plan.
- Consuming the engine's outputs (state JSON, appended receipts, branches).
- Resuming to layer the *native* Sovereign post-build gates (`/focus-plan`, embedded `/continuous-verify`, `/quality` chain, substrate hygiene via `/divergence`, exact canonical BUILD_RECEIPT format, `tasks.md` checkbox update, `/nodelete` discipline, etc.).

This is the "formula in a formula" or `execute-build-revised(execute-plan)` pattern. Execute-plan is not to be edited (it is the superior engine for its domain). The outer native layer must provide the Sovereign contract while delegating the inner execution.

The user explicitly anticipates this as a **huge transition**. Copious, high-fidelity, evidence-dense documentation is required now to prevent Context Erosion, Ghost Logic in the handoff layer, or loss of the pointer architecture's intent during implementation. /quality has been applied to this ticket: every assertion is cited, the root cause is phrased as a missing scaffold element, the recommendation is workflow-level, and the ticket is self-contained for future agents.

Without this adapter layer, continued hybrid usage will either duplicate effort (re-implementing review loops, git handling, isolation inside native execute-build) or silently drop Sovereign guarantees (bypassing native gates and receipt formats).

## 2. Root Cause Analysis: "Missing Delegation Adapter and Pointer/Payload Contract in Native execute-build"

**Failure class**: Structural Gap (with secondary risk of Context Erosion in handoffs and Ghost Logic if delegation is attempted ad-hoc without receipts).

- **The How**: 
  - When a user (as occurred) approves a DESIGN with `## PR Plan` section and invokes `/execute-plan @docs/DESIGN_Complete_Videos_Pipeline.md with /quality`, the native execute-build is entirely bypassed for the implementation work.
  - The native workflow's Phase 0–build loop assumes it will perform (or directly orchestrate) the code changes, verification, and receipt emission itself.
  - There is no branch, no "if DESIGN PR Plan present" decision point, no payload emission step, no delegation contract, and no consumption step that would allow execute-build to:
    1. Do its irreplaceable pre-work (intent anchoring from implementation-plan.md, /focus-plan gate, Phase Map update).
    2. Hand off a precise slice + native instructions via pointer/payload.
    3. Let execute-plan own the subagent worktrees, persona review-fix to 0 open, worktree protocol, cherry-pick stack assembly.
    4. Resume, run native post-gates (continuous-verify, quality, harden where applicable, divergence hygiene), emit the *exact* canonical Phase Build Receipt format expected by receipt-check / secretary / manifest, and mark the tasks.md checkbox.
  - Result observed in practice: successful execution via one path + manual adaptation of audit on the other. No automated, receipted, auditable composition.

- **The Why** (the structural gap in the faulting workflow):
  The `execute-build.md` (and its supporting GLOSSARY, phase definitions, STRICT RULES, and integration points with focus-plan/continuous-verify/quality/nodelete) defines only a direct, self-contained implementation rail. It lacks:
  - Any "Delegation" or "External Engine Adapter" phase/step.
  - A defined pointer/payload format and handoff contract (despite the suite already having a mature "one canonical payload, multiple pointer systems" pattern for multi-runtime: Claude Code symlinks, Grok OpenCode pointers, Antigravity pointers — all pointing at canonical claude-commands/*.md).
  - Explicit rules for preserving native verification spine elements as the *outer* layer while delegating the inner execution engine.
  - Consumption logic for execute-plan's artifacts (/tmp/grok-exec-plan-*.json state, per-PR BUILD_RECEIPTS appends, branch state).
  - Safeguards against duplicating concepts already superior in execute-plan (worktree isolation, mandatory independent reviewer, Subagent Worktree Protocol, DAG linearization + range cherry-pick stack assembly).

  This is exactly the class of missing scaffold that the pointer architecture was invented to solve in other contexts, and that the verification spine (focus-plan pre-gate + continuous-verify + receipts) was invented to enforce. The gap was latent until a user actually exercised the superior engine on a real DESIGN and then tried to close the loop with native tools.

## 3. Forensic Evidence

All citations are direct, current-session or canonical files with line ranges where possible. More than the minimum of 2 are provided for copious documentation of this high-impact transition.

- **[execute-build protocol definition]** [text](file:///home/jwils/blueprint-workflows/claude-commands/execute-build.md#1-100)
  *Evidence: Frontmatter and Phase 0/1 describe the rigid tasks.md-driven loop, Phase Map, Build Audit including continuous-verify gate, Phase Build Receipt emission. No mention of delegation, external engines, pointer/payload, or execute-plan. This is the "self-contained rail" that must become the outer adapter.*

- **[Grok execute-plan superiority and protocol]** [text](file:///home/jwils/.grok/bundled/skills/execute-plan/SKILL.md#1-80)
  *Evidence: Description, Subagent Worktree Protocol (Rules 1-3 on fetch without refspec, commit_sha authority, worktree teardown), persona injection, review-fix until 0 open, state file in /tmp, stack assembly (plain-git/Graphite), orchestrator owns git. These are the capabilities native execute-build should delegate to rather than duplicate.*

- **[Actual DESIGN executed via execute-plan]** [text](file:///home/jwils/Videos/docs/DESIGN_Complete_Videos_Pipeline.md#1-50)
  *Evidence: The authoritative source containing the ## PR Plan DAG (15 nodes), research engine + 4 Gaps, production vision, "current unbuilt items only" constraint, short-form priority, narration architecture, "minimal manual effort" list. This is what was successfully executed by execute-plan (397b6602) and audited natively.*

- **[Execution state and receipts from the run]** [text](file:///tmp/grok-exec-plan-397b6602.json#1-50)
  *Evidence: Linearized order, all pr-1..pr-15 status (pr-15 completed with review_rounds=2, commit 448d2e1... after fixes), user_instructions matching the invocation. Also cross-referenced in .workflow_state/receipts/BUILD_RECEIPTS.md (entries for pr-11 through pr-15 showing 0 open after review-fix, verbatim DESIGN fidelity claims, verification steps).*

- **[Existing pointer architecture (model to reuse)]** [text](file:///home/jwils/blueprint-workflows/DevJournal.md#12-70)
  *Evidence: Detailed history of "one canonical payload, multiple pointer systems" for Claude Code (symlinks in ~/.claude/commands/), Grok OpenCode (pointer files in ~/.opencode/commands/), Antigravity (pointers in ~/.gemini/antigravity/global_workflows/). Explicitly retired bulk-load to prevent Context Erosion. "Both runtimes now share one canonical payload per command." This pattern is the direct precedent for the proposed "pointer payload to execute-plan" handoff.*

- **[Global frame and Sovereign context]** [text](file:///home/jwils/Videos/CLAUDE.md#1-100) and [text](file:///home/jwils/.claude/CLAUDE.md#1-50)
  *Evidence: Commands location symlinks, pointer history, no-praise, biblical lens, ambiguity protocol, /nodelete, failure pattern vocabulary (Mock Trap, Ghost Logic, Context Erosion, Hallucinated Success, Grade Fraud). These must be preserved as the outer invariants in any revised execute-build(execute-plan) composition.*

- **[Recent audit adaptation in practice]** [text](file:///home/jwils/blueprint-workflows/implementation-plan/audits/20260706-1030-Videos-397b6602.md#1-50)
  *Evidence: The native --audit was run post-execute-plan and had to be "dynamically altered" because native assumes execute-build + tasks.md. Produced Coverage Ledger on the 33-file changeset, 89/100 score, explicit notes on the hybrid usage. Proves both the success of the current hybrid and the friction of the missing adapter.*

- **[Subagent Worktree Protocol and state discipline in execute-plan]** [text](file:///home/jwils/.grok/bundled/skills/execute-plan/SKILL.md#30-60)
  *Evidence: The exact rules that make execute-plan superior and that a native wrapper must respect (never edit these). Also the tool-call discipline and persona prepending.*

Additional context from session: User explicitly stated "I have zero dissent on everything you just mentioned", "huge transition", "your context here and now is key and vital", "use copious notes", " /quality applied to documenting the ticket."

## 4. Remediation: Introduce Pointer/Payload Delegation Adapter in Native execute-build (Formula-in-a-Formula)

1. Revise `/home/jwils/blueprint-workflows/claude-commands/execute-build.md` (and any core.md if present) to add a new "Delegation / External Engine Adapter" step or sub-phase inside the per-phase build loop. Triggered when the phase references a DESIGN containing a ## PR Plan section or when user intent explicitly delegates.

2. Define a standard, minimal pointer/payload artifact (e.g., a sidecar `EXECUTE_PLAN_PAYLOAD-<phase>.md` or a dedicated section in the DESIGN or a new convention under .workflow_state/). Contents at minimum: pointer to the DESIGN, slice of PRs or tasks for this phase, native instructions string (e.g., "respect /quality, current unbuilt only, produce canonical BUILD_RECEIPT, layer focus-plan/continuous-verify/quality gates on return, update tasks.md").

3. In the revised execute-build:
   - Perform all irreplaceable pre-delegation Sovereign work (Phase 0 discovery, intent anchor from implementation-plan.md, /focus-plan gate, drift check, Phase Map preparation).
   - Emit the payload.
   - Document the exact invocation: user (or thin wrapper) runs `/execute-plan @DESIGN... --instructions "<payload content>"` (or equivalent).
   - On resumption (explicit or via state detection): consume execute-plan outputs (/tmp/grok-exec-plan-*.json for status/commits, appended entries in BUILD_RECEIPTS.md, branch state).
   - Execute the full native post-build gates: /continuous-verify (5g), substrate hygiene (/divergence), quality chain, harden where applicable, exact canonical Phase Build Receipt emission (with links to the delegated work), tasks.md checkbox update.
   - Enforce no direct editing of the delegated engine.

4. Model the payload/pointer mechanics explicitly on the existing multi-runtime pointer system (see DevJournal citations). One canonical source of truth; the payload is the "delivery instruction + native customization" layer.

5. Add STRICT RULES: 
   - Never edit execute-plan or its SKILL.md.
   - Every delegation must produce traceable receipts on both sides.
   - Handoff must not create Ghost Logic (the outer layer must be able to reconstruct that the inner engine actually ran the intelligence).
   - Preserve "current unbuilt items only", /quality, naming-irrelevance where user-declared, etc.

6. Update related Sovereign docs for the new pattern: GLOSSARY in execute-build and implementation-plan.md, role.md (Senior Architect of Workflows), perhaps a small example in the Videos workspace or a test case. Produce a "Transition Notes" appendix in the revised workflow.

7. Because this is a huge transition, the first implementation should be done under /quality + this ticket + subsequent /harden-workflow --ticket. Prototype the payload format and handoff in this workspace (Videos) using the existing DESIGN as the canonical example.

8. After changes, re-run native /implementation-plan --audit and/or /receipt-check to validate.

## 5. Recommendation to Senior Architect

Add to the native `/execute-build` workflow (and the supporting Sovereign verification spine) a first-class "External Engine Delegation Adapter using Pointer/Payload" mechanism.

The revised execute-build shall act as the outer Sovereign "formula" (owning intent anchoring, Phase Map / tasks.md state, pre-gates from /focus-plan, embedded /continuous-verify, post-gates including /quality chain / divergence hygiene / exact canonical BUILD_RECEIPTS format / nodelete discipline / turn-boundary pause protocol).

It shall delegate only the core DAG execution, worktree-isolated subagent implementation + mandatory reviewer loops to 0 open, Subagent Worktree Protocol, state machine, and Git stack assembly to Grok `/execute-plan` (or future equivalent superior engines) when the source of truth is a DESIGN document containing a ## PR Plan section.

Define and document:
- The pointer/payload format and contract (modeled on the existing multi-runtime "one canonical payload" architecture).
- Exact pre-delegation and post-delegation responsibilities.
- Receipt parity and handoff audit requirements to prevent Ghost Logic or Context Erosion.
- STRICT RULES prohibiting editing of the delegated engine and requiring explicit user authorization for the delegation path.

This eliminates redundancy (no need to re-implement isolation/review/git-stack inside native execute-build), respects the engineering superiority of execute-plan in its domain, and preserves every native Sovereign guarantee as the non-negotiable outer layer.

Apply /quality, copious documentation, and /harden-workflow --ticket to the revised execute-build.md. Update the manifest/SUITE_PHYLOGENY.md if this pattern propagates (as it likely will). Treat this as a high-priority architectural evolution given the anticipated size of the transition.

## 6. Hardening Certificate ([ADDED] 2026-07-07, by Claude Code, Sovereign Redesign Cluster follow-up)

**Read this section before trusting §4's remediation plan as still current — it is not, for a specific, important, well-evidenced reason.**

This ticket's own root cause — "native execute-build has no defined mechanism for handling a DESIGN-driven phase while preserving the Sovereign verification spine" — **is closed.** The specific *mechanism* §4 prescribed to close it — a pointer/payload adapter whose primary purpose is delegating core execution to Grok `/execute-plan` — **was not built, and should not be**, for a reason this ticket could not have known at filing time: continued heavy reliance on Grok tool-calling as the *primary* execution path is what caused this cluster's own execution agent to terminate mid-build days later, on real, unbudgeted API cost (~$200 across two workspaces — see `helpdesk-tickets/CLOSED_20260706_sovereign-redesign-cluster_meta_workflow.md`'s "Build Attempt, Termination, Recovery" section). The user's own explicit, direct response to that incident — *"we keep the design as is with one caveat, we use a pass for every agent that is not Grok... allows non grok agents to continue through the workflow"* — reversed this ticket's own architectural default.

What was actually built (the **Native Execution Trigger**, `execute-build.md` Phase 0a + GLOSSARY, and the **Agent Capability Gate**, `PILLAR_03_EXECUTION_DELEGATION_FORMULA.md` §15) solves the same underlying problem from the opposite direction: native (non-Grok) execution of a DESIGN-driven phase is the **default**, exercised twice end-to-end this cluster with zero Grok involvement (PR 05-04, PR 06-02 — real backlog items, not synthetic demos). A Grok-delegated path — closer in shape to what this ticket originally asked for — remains *available*, but gated behind confirmed tool-calling capability and explicit session authorization, never assumed, per §15's own text. This ticket's specific pointer/payload artifact, its consumption-of-execute-plan-outputs step, and its "the outer layer must be able to reconstruct that the inner engine actually ran the intelligence" requirement are all real, good engineering asks — they were simply built for the gated, optional path rather than the default one, and have not been implemented in that reduced form as of this closure. **This is a deliberate scope reduction, not an oversight — recorded here so a future agent does not read "CLOSED" as "built exactly as specified."**

```
+══════════════════════════════════════════════════════════+
║  WORKFLOW HARDENING CERTIFICATE                          ║
║  Workflow:      /execute-build                            ║
║  Date:          2026-07-07                                ║
╠══════════════════════════════════════════════════════════╣
║  GRADE:         SOVEREIGN (pre-existing, unchanged)       ║
╠══════════════════════════════════════════════════════════╣
║  Command file:  ~/blueprint-workflows/claude-commands/execute-build.md
║  Symlink:       ~/.claude/commands/execute-build.md — PRESENT
║  Frontmatter:   PRESENT — version 5, strict_rule_count 18
║  GLOSSARY:      PRESENT (Native Execution Trigger added, Stage 4)
║  HOW TO BEGIN:  PRESENT
║  STRICT RULES:  PRESENT (18 rules; #17-18 are this ticket's own gates —
║                 never assume Grok availability; traceable provenance for
║                 the native handoff, the Ghost-Logic guard this ticket
║                 explicitly asked for, built for the native path instead
║                 of the Grok-delegation path)
║  Struct Output: PRESENT (Phase Build Receipt, exact canonical format,
║                 unchanged by this ticket's work — it was already correct)
║  Change Log:    PRESENT (entry 10, dated 2026-07-06)
╠══════════════════════════════════════════════════════════╣
║  /triage Gap:   NONE                                      ║
╠══════════════════════════════════════════════════════════╣
║  Changes Made (Sovereign Redesign Cluster Stage 4, prior to this closure pass):
║    - Native Execution Trigger (Phase 0a): detects a DESIGN with ## PR Plan
║      when <TASKS_FILE> is absent, runs /implementation-plan against it,
║      continues Phase 0-7 unmodified. Exercised twice, real items, zero
║      Grok involvement.
║    - Agent Capability Gate (PILLAR_03 §15): native is default; Grok path
║      requires confirmed capability + session authorization, never assumed.
║      This IS the ticket's own requested "adapter" concept, inverted:
║      instead of an adapter that routes TO Grok by default, it is a gate
║      that routes AWAY from Grok by default.
║    - STRICT RULES 17-18: traceable provenance for the native handoff
║      (which DESIGN + which /implementation-plan run produced a given
║      tasks.md), addressing this ticket's own Ghost-Logic concern for the
║      path that was actually built.
║  NOT Built (deliberate, see explanation above, not an oversight):
║    - Pointer/payload artifact format for Grok /execute-plan consumption.
║    - Consumption logic for /tmp/grok-exec-plan-*.json state, per-PR
║      receipt parsing from a Grok-executed DAG.
║    - The "formula-in-a-formula" composition where native wraps Grok as
║      the default inner engine.
╠══════════════════════════════════════════════════════════╣
║  Standard Version: 3                                       ║
║  Status:        WORKFLOW HARDENING COMPLETE (scope reduced, documented)
+══════════════════════════════════════════════════════════+
```

**Phylogeny Disposition**: `CONFIRMED — lineage entry` — `manifest/SUITE_PHYLOGENY.md`'s Sovereign Redesign Cluster entry already documents the Agent Capability Gate's propagation across PILLAR_02/PILLAR_03; this ticket is one of that transfer's two origin points (the companion design-formula ticket is the other).

**If a future session decides to build the Grok-delegation path this ticket originally specified** (now correctly understood as the *optional*, gated path, not the default): §4 items 2-3 of this ticket (the payload artifact format, the consumption logic) remain a good starting specification and are not superseded by anything built this cluster — only the "delegate by default" framing in §4 item 1 and the Recommendation (§5) is.

---
**Status**: **REMEDIATED (underlying structural gap closed via the opposite architectural default than originally specified — see Hardening Certificate above for the full, honest account of what changed and why)**
**Verification**: Hardening Certificate above. Full evidence trail: `.workflow_state/receipts/BUILD_RECEIPTS.md` Stage 4/6 entries, `helpdesk-tickets/CLOSED_20260706_sovereign-redesign-cluster_meta_workflow.md`'s own Closure Record and "Build Attempt, Termination, Recovery" section.

---
*Originally filed by Grok (Videos workspace session, pre-termination). Closed by Claude Code, 2026-07-07 — native path, no Grok involved in this closure, which is itself the point.*

---
*Signed,*
**Grok**
*(Agent operating in /home/jwils/Videos with full access to both native Sovereign commands and Grok bundled skills; author of the preceding analysis with zero user dissent)*
