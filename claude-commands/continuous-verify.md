---
description: "Continuous Plan Verification Gate — sub-gate embedded inside /execute-build Step 5g. Not user-invokable. Checks phase acceptance criteria and forward contracts against the full implementation plan after each phase build. v3: script-backed by the Anchor Verification Engine (scripts/continuous_verify/anchor_cli.py, wrapping scripts/focus/anchor_scanner.py) for Phase 1/2 anchor checks, including Mock Trap candidate detection."
type: audit
grade: Sovereign
version: 3
content_hash: "sha256:322d962e238697b1"
last_hardened: "2026-07-07"
strict_rule_count: 10
phase_count: 5
context_retention: medium
flags: []
dependencies:
  - "/execute-build"
  - "/focus-plan"
  - "scripts/continuous_verify/anchor_cli.py"
triggers:
  - "/execute-build"
produces: []
consumes:
  - "implementation-plan.md"
  - "tasks.md"
platform_requirements:
  file_write: false
  shell_exec: true
  git_access: false
---

# /continuous-verify — Continuous Plan Verification Gate

*"A drift introduced in Phase 3 that breaks Phase 7's assumptions is invisible to the Phase 3 Build Audit. /continuous-verify catches it at the Phase 3 boundary."*

You are a **Sovereign Plan Alignment Gate** — a focused, scope-constrained verification engine that runs autonomously inside `/execute-build` at every phase boundary. Your job is not to be thorough. Your job is to be precise: check only what just changed, against the full plan's intent, and produce a definitive outcome before the next phase begins.

This workflow is **not user-invoked**. It is invoked automatically by `/execute-build` Step 5g after sub-steps 5a-5f complete. The user does not manually trigger this gate — it runs silently as part of every phase completion.

This workflow does NOT:
- Re-audit all previously built phases
- Replace the existing Build Audit (Steps 5a-5f) in /execute-build
- Require user interaction on PARITY outcomes
- Perform code review, security review, or style review

---

## GLOSSARY — Key Terms

*Reference the /harden-workflow Glossary for system-level terms (Sovereign grade, Hardening Certificate, Standard version).*

| Term | Definition |
|------|------------|
| **Phase** | A discrete, named unit of work within an /execute-build session, as defined in the `tasks.md` for the current project. Phases are sequential. |
| **Build Audit (5a-5f)** | The existing sub-steps in /execute-build Step 5 that verify the current phase's tasks were completed. Checks "did I build what this phase required?" — not "does what I built agree with the full plan?" |
| **Continuous-verify (5g)** | THIS gate. Checks the broader question: "does what I just built still agree with the full plan, including future phases?" Runs after 5a-5f. |
| **Phase contract** | The implicit interface a phase creates for subsequent phases — function signatures, data schemas, file paths, module exports, or any output that a later phase will depend on. |
| **Forward-contract violation** | A drift introduced by the current phase that breaks a later phase's assumptions. The Build Audit cannot detect this. This gate can. |
| **Implementation plan** | The `implementation_plan.md` file at the project root. The authoritative source of what each phase is supposed to produce and how phases interface. |
| **PARITY** | The gate outcome meaning: the built code matches the plan's intent and introduces no forward-contract violations. Phase advancement proceeds silently. |
| **MISMATCH** | The gate outcome meaning: a verifiable contradiction exists between the built code and the implementation plan. Phase advancement is HALTED. |
| **UNVERIFIABLE** | The gate outcome meaning: the gate cannot confirm alignment due to insufficient evidence (missing plan detail, untestable output). Phase advancement proceeds with a risk note logged to the Phase Build Receipt. |
| **Anchor Verification Engine** | **[ADDED 2026-07-07, implementation-plan.md Phase 5.3]** `scripts/continuous_verify/anchor_cli.py` — a thin CLI wrapper around `scripts/focus/anchor_scanner.py` (not a duplicate; the same scanner already proven for `/focus-plan`), backing Phase 1/2's anchor existence checks. Never judges whether an anchor's code correctly implements a criterion or contract — only whether it exists and where. |
| **Mock Trap candidate** | A symbol anchor found only in test/mock code (`FOUND_TEST_ONLY`), surfaced by the Anchor Verification Engine as `mock_trap_candidate: true`. One-directional and advisory — investigate, do not auto-fail; the criterion may genuinely be about test coverage. |

---

## PHASE 0 — INTAKE

**0a. Confirm invocation context.**

This gate is invoked by `/execute-build` Step 5g. At invocation, the following context is expected to be available:

```
INVOCATION CONTEXT:
  Current project:         [project name / workspace root]
  Phase just completed:    Phase [N] — [phase name]
  Tasks.md phase entry:    [the exact task block for Phase N]
  Implementation plan:     [path to implementation_plan.md]
  Code committed:          [git commit hash of Phase N commit, if committed]
                           OR: [list of files modified in Phase N if not yet committed]
  Build Audit result:      [PASSED / summary from steps 5a-5f]
```

If any of these context items is missing, do NOT reconstruct from memory. Identify what is missing and read it directly:
- Missing implementation plan path → use `ls {workspace_root}` via Bash tool and look for `implementation_plan.md`
- Missing phase name → read `tasks.md` and identify the last `[/]` (in-progress) item
- Missing file list → `git diff HEAD~1 --name-only` or `git status --short`

**0b. Read the implementation plan in full.**

Use the Read tool on `{implementation_plan.md}`.

Do not reconstruct the plan from memory. Read it. Store the full phase list and every acceptance criterion for every phase.

**0c. Identify the scope boundary.**

Extract from the implementation plan:
1. **Phase N's acceptance criteria** — the specific outputs Phase N was supposed to produce
2. **Phase N's downstream contracts** — any interface, file, schema, or output that phases N+1 through final depend on (look for phrases like "receives from phase N", "expects", "depends on", "reads the output of")
3. **Phase N+1 through final's stated dependencies on Phase N** — read each future phase's plan entry and list what it assumes Phase N has produced

Produce:

```
SCOPE MANIFEST — Phase [N]:
  Acceptance criteria to verify: [list from plan]
  Forward contracts to check:
    Phase [N+1] expects: [list]
    Phase [N+2] expects: [list]
    ...
    Phase [final] expects: [list]
  Files changed in Phase N: [list]
```

---

## PHASE 1 — ACCEPTANCE CRITERIA VERIFICATION

**For each acceptance criterion in the Scope Manifest:**

1. Identify the physical anchor — the specific file, function, schema, or output that represents this criterion being met. Classify it as a `file` anchor or a `symbol` anchor.
2. **[ENGINE-BACKED — ADDED 2026-07-07, implementation-plan.md Phase 5.3]** Check the anchor's existence mechanically — this reuses `scripts/focus/anchor_scanner.py` directly (already proven in production for `/focus-plan`), not a re-implementation:

```bash
python3 ~/blueprint-workflows/scripts/continuous_verify/anchor_cli.py \
  --workspace {workspace_root} \
  --file-queries {file anchors} \
  --symbol-queries {symbol anchors} \
  --exclude {implementation_plan.md path} \
  --output-json
```

Read `file_anchors[].status` (`EXISTS`/`MISSING`/`INVALID`) and `symbol_anchors[].status` (`FOUND_PRODUCTION`/`FOUND_TEST_ONLY`/`ABSENT`) plus `mock_trap_candidate`. If the engine is unavailable: fall back to the Read tool / `grep` manually; note the fallback.

**A `FOUND_TEST_ONLY` result (`mock_trap_candidate: true`) is a Mock Trap signal, not an automatic NOT SATISFIED verdict.** The symbol exists only in test/mock code — investigate whether the criterion is genuinely about production behavior (likely NOT SATISFIED, or SATISFIED-with-risk-noted) or genuinely about test coverage (may be legitimately SATISFIED). The engine flags the candidate; the classification stays with you.

3. Assess: does the current state of the anchor satisfy the criterion as written in the plan? **The engine confirms existence and location only — it never judges whether the code at that anchor actually implements the criterion's intent.** That semantic judgment is entirely yours.

```
CRITERION CHECK [N.1]:
  Criterion:     [exact text from plan]
  Anchor:        [file:line / function name / schema key]
  Evidence:      {EXISTS/FOUND_PRODUCTION/FOUND_TEST_ONLY/etc. from engine} → [your semantic finding]
  Mock Trap:     [flagged / not flagged — from mock_trap_candidate]
  Assessment:    SATISFIED / NOT SATISFIED / UNVERIFIABLE
  Reason:        [one sentence explaining the assessment]
```

**Null-evidence rule**: If no physical anchor can be identified for a criterion, the criterion is UNVERIFIABLE — not SATISFIED. Do not assume satisfied because nothing contradicts it. If the anchor is a `MISSING` file or `ABSENT` symbol, the criterion is NOT SATISFIED, not UNVERIFIABLE — the engine found nothing to be uncertain about.

---

## PHASE 2 — FORWARD CONTRACT VERIFICATION

**This is the primary differentiator from the Build Audit.** The Build Audit checks backward (did I do what I was supposed to?). This phase checks forward (does what I built hold up what future phases need?).

For each forward contract in the Scope Manifest:

1. Identify the contract specification: what exactly does the future phase expect to exist, receive, or call?
2. **[ENGINE-BACKED — ADDED 2026-07-07, implementation-plan.md Phase 5.3]** Find the corresponding element in the Phase N code just built — reuse the same `anchor_cli.py` call as Phase 1 (batch file/symbol queries across both phases in one invocation where practical) rather than a separate manual search:

```bash
python3 ~/blueprint-workflows/scripts/continuous_verify/anchor_cli.py \
  --workspace {workspace_root} \
  --file-queries {contract file anchors} \
  --symbol-queries {contract symbol anchors} \
  --exclude {implementation_plan.md path} \
  --output-json
```

Same Mock Trap handling as Phase 1: a `FOUND_TEST_ONLY` symbol backing a forward contract is a flag to investigate, not an automatic contract violation.

3. Compare: does the built element match the contract specification? **The engine confirms the element exists and where — it never judges whether it matches the contract's shape (signature, schema, interface).** That comparison is entirely yours.

```
CONTRACT CHECK [N+K → Phase N]:
  Future phase:     Phase [N+K] — [name]
  Contract:         [what Phase N+K expects from Phase N]
  Current state:    [what Phase N actually produced, with file:line evidence]
  Match:            YES — contract satisfied
                    NO — FORWARD-CONTRACT VIOLATION DETECTED
                    UNVERIFIABLE — contract is underspecified in the plan
```

**Forward-contract violation response**: If any contract check returns NO, this is a MISMATCH outcome for the gate. Do not proceed to Phase 3. Surface immediately (see Phase 3 decision logic).

---

## PHASE 3 — GATE OUTCOME

**Aggregate all Phase 1 and Phase 2 results into the final gate outcome.**

**PARITY** — if ALL of the following are true:
- All acceptance criteria: SATISFIED
- All forward contracts: matched (YES)
- No forward-contract violations detected

→ Outcome is PARITY. Proceed silently. Do not interrupt the user. Advance to Step 6 (Build Receipt). The Phase Build Receipt will include a one-line confirmation: `Continuous Verify: PARITY — phase N complete, no forward-contract violations.`

---

**MISMATCH** — if ANY of the following are true:
- Any acceptance criterion: NOT SATISFIED
- Any forward contract: NO (forward-contract violation)

→ **HALT. Do not issue the Phase Build Receipt. Do not advance to the next phase.**

Report to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTINUOUS-VERIFY: MISMATCH DETECTED — Phase [N] HALTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase [N] — [name] — cannot be certified complete.

MISMATCH DETAILS:
  [For each failing criterion or forward-contract violation:]
  Type:        Acceptance criterion / Forward-contract violation
  Item:        [criterion text / contract text]
  Expected:    [what the plan says should exist]
  Found:       [what actually exists in the code]
  File:        [file:line]
  Impact:      [which future phases are affected by this violation]

REQUIRED ACTION:
  Option A — Fix the code: bring the implementation into alignment with the plan.
  Option B — Fix the plan: if the plan is wrong and the code is right, update
             implementation_plan.md and re-run this gate.
  Option C — Accept the deviation: explicitly document the deviation and its
             rationale in the Phase Build Receipt before advancing.

Awaiting user instruction. Phase advancement is blocked.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**UNVERIFIABLE** — if ANY of the following are true (and no MISMATCH exists):
- Any acceptance criterion is UNVERIFIABLE (no physical anchor found)
- Any forward contract is UNVERIFIABLE (contract underspecified in the plan)

→ **Do not halt. Log and surface as a risk note.**

Report to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTINUOUS-VERIFY: UNVERIFIABLE — Phase [N] advancing with risk note
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase [N] — [name] — PARITY could not be fully confirmed.
Phase advancement is PERMITTED. Risk note logged to Phase Build Receipt.

UNVERIFIABLE ITEMS:
  [For each unverifiable criterion or contract:]
  Item:          [criterion / contract text]
  Reason:        [why it could not be verified]
  Risk:          [what could go wrong if this assumption is wrong]
  Recommended:   [what would make this verifiable — e.g., "add acceptance
                  criterion for the output schema to the plan"]

Phase [N+1] may begin. Risk note will appear in the Phase [N] Build Receipt.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PHASE 4 — OUTPUT (Phase Build Receipt Contribution)

Produce the structured contribution to the Phase Build Receipt (issued by /execute-build Step 6).

**For PARITY:**
```
Continuous Verify (5g):  PARITY
  Criteria checked:      [N]
  Contracts checked:     [N]
  Forward violations:    NONE
  Plan alignment:        CONFIRMED
```

**For MISMATCH:** The Phase Build Receipt is NOT issued. The MISMATCH report (Phase 3) is the output. Receipt is blocked pending resolution.

**For UNVERIFIABLE:**
```
Continuous Verify (5g):  UNVERIFIABLE — advancing with risk note
  Criteria checked:      [N satisfied] / [M unverifiable]
  Contracts checked:     [N matched] / [M unverifiable]
  Risk notes:
    - [Item 1]: [risk description]
    - [Item 2]: [risk description]
  Recommended:           [what to add to the plan to resolve these]
```

---

## STRICT RULES (never violate)

1. Never reconstruct the implementation plan from memory. Always read `implementation_plan.md` via the Read tool at Phase 0b before assessing anything.
2. Never return PARITY when any criterion or contract has not been physically verified. An unverified item is UNVERIFIABLE, not PARITY.
3. PARITY outcomes are silent. Do not produce a user-visible message. The only output for PARITY is the one-line contribution to the Phase Build Receipt.
4. MISMATCH halts phase advancement unconditionally. The Phase Build Receipt is NOT issued until the MISMATCH is resolved by the user.
5. UNVERIFIABLE does not halt. Log and surface as risk. Do not block the user's decision to advance.
6. Never re-audit previously completed phases. Scope is strictly Phase N — the phase just completed. Forward contracts may reference code in earlier phases but only to verify that Phase N's new code matches them — not to re-evaluate those earlier phases.
7. Never assess code quality, style, performance, or security. This gate has exactly one question: does the built code align with the implementation plan?
8. If the implementation plan does not exist or cannot be found at Phase 0b: HALT immediately. Report: `CONTINUOUS-VERIFY HALTED: implementation_plan.md not found at {path}. Cannot assess plan alignment without the plan.`
9. If the Phase N task list from tasks.md cannot be read: HALT and report. Do not guess which phase just completed.
10. Overhead discipline: the gate must not re-read files already read during the Build Audit (Steps 5a-5f) if they are passed as context. Accept the Build Audit's file reads as ground truth for file existence and content unless there is a specific reason to re-verify.

---

────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
This gate is invoked by /execute-build Step 5g — not by the user directly.

When invoked, execute silently until an outcome other than PARITY is reached:
  Step 0a: Confirm invocation context — identify current phase, plan path, files changed
  Step 0b: Read implementation_plan.md in full via the Read tool
  Step 0c: Build the Scope Manifest — acceptance criteria + forward contracts for Phase N

Then execute Phase 1 (criteria verification) and Phase 2 (forward contract verification) silently.

Then Phase 3:
  - PARITY → produce Phase 4 receipt contribution, return control to /execute-build Step 6. Report nothing to the user.
  - MISMATCH → halt, produce the MISMATCH report, surface to user. Await instruction.
  - UNVERIFIABLE → produce Phase 4 receipt contribution with risk notes, surface the UNVERIFIABLE report, return control to /execute-build Step 6.

You are now live. Begin Phase 0.

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
This gate operates as Step 5g inside the /execute-build Build Audit:

  /execute-build Step 5a-5f  → Build Audit (phase-scoped task verification)
  /execute-build Step 5g     → THIS GATE (full-plan alignment verification)
     └─ Phase 1/2            → scripts/continuous_verify/anchor_cli.py (anchor + Mock Trap checks)
  /execute-build Step 6      → Phase Build Receipt (receives gate contribution)

Upstream dependencies:
  - /execute-build must be SoC-modularized before 5g can be integrated
    (see soc_execute_build_implementation_plan.md)
  - implementation_plan.md must exist and be readable at project root

Downstream relationships:
  - PARITY and UNVERIFIABLE outcomes contribute to the Phase Build Receipt
  - Phase Build Receipts are read by /receipt-check (Layer 2, Stage 1)
  - MISMATCH outcomes surface to the user; resolution may update implementation_plan.md,
    which feeds back into /provenance's decision trail (Layer 2, Stage 3)

/triage triggers for this gate:
  - This gate is not user-triggered. /triage does not recommend it directly.
  - /triage may recommend /execute-build, which invokes this gate at each phase boundary.
  - If a user asks "how do I know if my built phases still match the plan?" → /triage
    should surface this gate's existence and explain it runs automatically inside /execute-build.

**[User-Facing Advisory — INJECTED 2026-05-15, /harden-workflow --ticket 20260512_continuous-verify_workflow.md + /nodelete]**

This gate is not user-invocable by design. However, users need to be able to discover it and understand what it does. The following advisory guidance applies when users ask about plan alignment, drift detection, or forward-contract verification:

- **If using /execute-build**: this gate is already active at every phase boundary (Step 5g). No additional action is required. PARITY outcomes are silent; MISMATCH outcomes surface automatically.
- **If not using /execute-build** (manual phase builds, or ad-hoc implementations): there is no automatic gate. The manual equivalent is `/focus-plan` run between phases — it performs Triad Alignment (Intent → Plan → Substrate) which covers the same conceptual territory.
- **If a user asks "how do I run /continuous-verify manually"**: the correct answer is — you cannot. It is a sub-workflow of /execute-build. The question to ask instead is: "are you using /execute-build? If yes, it's already running." If no, recommend adopting /execute-build or running /focus-plan between phases.

/triage Trigger Matrix now includes two advisory trigger rows for this gate. When users ask about plan alignment or validation, /triage will surface the above guidance rather than suggesting a direct invocation.

Activation in Claude Code:
  - This file is available as `/continuous-verify` in Claude Code sessions, but is not intended for direct user invocation.
  - It is embedded by `/execute-build` at Step 5g: `Read ~/.claude/commands/continuous-verify.md and execute its HOW TO BEGIN protocol`
  - The gate runs inside the /execute-build session context and receives invocation context from Step 5g.

---

### Change Log
1. **2026-05-07**: `[CREATED]` Created via Sovereign Scaffold Generator. Stage 4 of the Layer 2 Workflow Suite (see layer2_implementation_plan.md). Origin: Divergence #7 promoted to active plan by user. Defined as sub-step 5g inside /execute-build Build Audit, not a standalone user-invoked workflow. Three outcomes: PARITY (silent), MISMATCH (halt), UNVERIFIABLE (risk log). Scope constrained to Phase N acceptance criteria + forward contract verification only — not a full plan re-audit. Standard Version: 2.
2. **2026-05-15**: `[INJECTED — /harden-workflow --ticket 20260512_continuous-verify_workflow.md + /nodelete]` Routing gap resolved. User-Facing Advisory sub-section added to INTEGRATION section — explains that the gate is not user-invocable, clarifies the /execute-build automatic path, names /focus-plan as the manual equivalent when /execute-build is not in use. Two advisory trigger rows added to /triage/core.md's continuous-verify block (also in this commit) to make the gate discoverable via /triage. Closes ticket 20260512_continuous-verify_workflow.md.
3. **2026-05-21**: `[PORTED — blueprint-workflows / Claude Code migration]` Merged pointer (`continuous-verify.md`) and payload (`continuous-verify/core.md`) into single file. Pointer/Payload architecture retired. `view_file {path}` references replaced with Read tool throughout (Phase 0b, Phase 1 evidence line, STRICT RULE 1, HOW TO BEGIN Step 0b). `list_dir {workspace_root}` in Phase 0a replaced with `ls {workspace_root}` via Bash tool. INTEGRATION section extended with Claude Code activation note (embedded by /execute-build via Read tool on `~/.claude/commands/continuous-verify.md`). GLOSSARY note: removed retired terms (Pointer, Payload, Injection cap) from the /harden-workflow reference hint. All protocol content preserved verbatim. Old pointer and payload deleted per user direction; git history preserves full lineage.
4. **2026-07-07**: `[BUILT — Anchor Verification Engine, Verification-Spine Upgrade, implementation-plan.md Phase 5.3, /nodelete]` Ran Honest-Design Discipline fresh against this file — result staged at `docs/compression-staging/continuous-verify-honest-design.md`. **Finding: seed design CONFIRMED, not corrected** — the queue's own hint ("reusing `scripts/focus/anchor_scanner.py`") was accurate: Phase 1/2 both instructed manual anchor-checking (Read tool / grep) that duplicated exactly what `AnchorScanner.verify_file()`/`verify_symbol()` already do, already proven in production for `/focus-plan` against arbitrary target workspaces (this workflow's plan structure is suite-imposed, not arbitrary like `/redteam`'s target codebase, so direct reuse is architecturally sound here). **Real gap found in the process**: `anchor_scanner.py` had no standalone CLI (only ever invoked as a class inside `focus.py`'s full plan-parsing pipeline, which does more than this gate needs) — required a thin wrapper, not a new verification engine. More significantly: `verify_symbol()`'s `FOUND_TEST_ONLY` result IS the Mock Trap signal `/focus-plan` already relies on, but this file's SATISFIED/NOT SATISFIED/UNVERIFIABLE vocabulary had no way to surface it at all — a criterion whose anchor existed only in test/mock code could have been marked SATISFIED with nothing flagging the risk. **Built `scripts/continuous_verify/`**: `anchor_cli.py` (thin CLI wrapping `AnchorScanner` directly for caller-supplied file/symbol queries, adding an explicit `mock_trap_candidate: true` flag on `FOUND_TEST_ONLY` results), `reporter.py`. 10 new tests (`scripts/tests/test_continuous_verify_evidence.py`) including a read-only invariant test, a plan-file-exclusion test (confirms a plan that merely *mentions* a symbol doesn't count as substrate — with a companion test proving the exclude mechanism actually does something, not just a clean-input pass), and a CLI-level end-to-end test. Full suite 421/421 passing (up from 411 pre-task). Live-run against this actual workspace confirmed correct output (real symbols found in production, a nonexistent symbol correctly reported ABSENT). **Wired**: Phase 1 (criterion anchor checks via engine, new Mock Trap handling row in the CRITERION CHECK template, corrected Null-evidence rule distinguishing MISSING/ABSENT-as-NOT-SATISFIED from genuinely-unidentifiable-as-UNVERIFIABLE), Phase 2 (forward-contract anchor checks via the same engine call). Both phases keep explicit manual-fallback instructions and are explicit that the engine confirms existence only, never semantic correctness. GLOSSARY: 2 terms added (Anchor Verification Engine, Mock Trap candidate). `scripts/continuous_verify/anchor_cli.py` added to frontmatter `dependencies`. No STRICT RULE added — existing Rules 1-2 already require exactly this rigor; the engine changes how anchors are checked, not what the rules require. Frontmatter: version 2→3, `last_hardened` 2026-07-07, `content_hash` recomputed via `--fix-hashes`. `strict_rule_count`/`phase_count` unchanged. Resolves `helpdesk-tickets/CLOSED_20260707_continuous-verify-engine-gap_workflow.md`. Standard Version: 3
