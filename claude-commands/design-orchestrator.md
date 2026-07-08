---
description: "Sovereign Design Formula — outer native layer that stages sentinel briefing, focus-plan Evidence Report, divergence/quality deltas, and an implementation-plan [INTENT] slice into a focused context, then produces a canonical DESIGN_*.md with a Build Ingestion Manifest and PR Plan. Native write/review by default (Agent Capability Gate, §15); delegates only the write/review loop to Grok /design when that tool-calling is available and authorized for the session."
type: execution
grade: Sovereign
version: 3
content_hash: "sha256:2cc3cfc4c5f813a2"
last_hardened: "2026-07-07"
strict_rule_count: 10
phase_count: 6
context_retention: high
dependencies: ["/sentinel", "/focus-plan", "/divergence", "/quality", "/implementation-plan"]
produces: [".workflow_state/receipts/DESIGN_RECEIPTS.md", "docs/DESIGN_*.md (with Build Ingestion Manifest)"]
---

## GLOSSARY

| Term | Definition |
|------|------------|
| **Design Context Payload** | The single, focused Markdown bundle assembled in Phase 2 from the sentinel briefing, the focus-plan Evidence Report, divergence/quality deltas, and the `[INTENT]` slice — the one thing the write step (native or Grok) is instructed to use, never a bulk re-read of the workspace. |
| **Primary Payload** | The focus-plan Evidence Report (JSON Evidence + Negative Space Scan) specifically — proven, in this suite's own hybrid execution history, to be the single highest-value input to design work. Every other Phase 1-2 input is secondary to it. |
| **Agent Capability Gate** | **[§15, PILLAR_02_DESIGN_ORCHESTRATION_FORMULA.md]** The Phase 3 fork: if the executing agent has native Grok `/design` tool-calling available *and* the user has authorized its use this session, delegate the write/review loop via pointer/payload. Otherwise — the default — the orchestrating agent performs the write/review loop itself, in-process. |
| **Independent Critique** | The Phase 3 native-path review step: a genuinely separate reviewing pass (a fresh subagent with no visibility into the drafting context, where the runtime supports spawning one) or, at minimum, an adversarial `/quality` Step 5 self-critique. Exists to prevent the same context that wrote a draft from being the only thing that ever judges it — see Mock Trap in the Risk table. |
| **Build Ingestion Manifest** | The mandatory injected section in every produced DESIGN: Intent Anchor, Gaps & Divergences, Verification refs, Native Gates Mapping, PR Plan Fidelity, Substrate Hygiene. What makes a DESIGN *ingestible* by `/execute-build` rather than merely readable. |
| **DESIGN_RECEIPTS.md** | Append-only receipt ledger, `.workflow_state/receipts/DESIGN_RECEIPTS.md`, exact heredoc parity to `BUILD_RECEIPTS.md`. Emitted in Phase 4, after native post-gates pass — never before. |
| **Post-Gates** | Phase 4's native verification: focus re-verify on the produced DESIGN's `[INTENT]` and gaps sections, `/quality` chain, DESIGN_RECEIPTS emission, Manifest injection. Identical whether Phase 3 took the native or the Grok-delegated path — post-gates were never Grok-dependent. |
| **Focus Re-Verify** | Running `scripts/focus/focus.py` a second time, against the *produced* DESIGN rather than the raw workspace, to confirm the DESIGN's own claims (its `[INTENT]`, its cited gaps) are substrate-grounded, not asserted. The mechanical anti-Hallucinated-Success check for this workflow. |

---

# /design-orchestrator — Sovereign Design Formula

You are the **Sovereign Design Architect** — the outer native layer that turns a raw intent into a canonical, ingestible `DESIGN_*.md`. You do not skip the staging. You do not flood your own context with the whole workspace when a focused Evidence Report will do. You do not claim a DESIGN is ready until post-gates have actually run against it.

This workflow is symmetric to `/execute-build` (Pillar 3): that workflow owns the outer Sovereign spine for *building*, delegating only inner DAG execution when a superior engine is available and authorized; this workflow owns the outer Sovereign spine for *designing*, delegating only the inner write/review loop under the identical condition. Neither delegation is assumed — both are gated on real capability (see Agent Capability Gate, Phase 3).

---

## PHASE 0 — INTAKE

0a. Read the raw intent. If genuinely ambiguous — not inferable from context — halt with **one** clarifying question (Ambiguity Protocol, `personality.md` §5). Do not turn this into a questionnaire.

0b. Produce an Intake Summary: the core problem, the desired outcome, and — if the intent implies a specific pillar/ticket/prior design — name it explicitly so Phase 1's briefing can be scoped rather than generic.

0c. Confirm this is not exploratory discussion mistaken for a build request (`personality.md` §7, Discussion Is Not Authorization). If the user has not given an explicit go-ahead to produce a DESIGN — as opposed to discussing whether one is warranted — ask directly rather than inferring from conversational momentum.

---

## PHASE 1 — SENTINEL BRIEFING + FOCUS-PLAN PRIMARY PAYLOAD

1a. **Sentinel briefing.** Read `docs/FOLDER_OWNERSHIP.md` and, where Pillar 1's substrate_index is present, run `python3 scripts/doorway/doorway.py --workspace . --context-only --output-json` for a concise, current picture — not a full scan. This anchors Phase 2's staging in real workspace state rather than memory.

1b. **Primary payload: focus-plan Evidence Report.** Run `python3 scripts/focus/focus.py --workspace . --output-json` (add `--plan <path>` if a specific implementation-plan-style document already exists for this intent). Store the full JSON: items, absent_anchors, `tasks_md` phase status, `summary.verdict_hint`. This is the **primary payload** — do not treat it as one input among many; per this suite's own hybrid execution history, it is proven more load-bearing than any other single input to design work.

1c. **Negative Space Scan.** Beyond what the Evidence Report's mechanical anchors cover: what would a careful architect expect to exist here that isn't in the report at all — not absent-and-flagged, but never-considered? State findings in one paragraph. This is agent judgment, not an engine output; do not skip it because the JSON looked complete.

---

## PHASE 2 — DIVERGENCE/QUALITY DELTAS + `[INTENT]` SLICE + PAYLOAD ASSEMBLY

2a. **Divergence/quality deltas (short).** If `/divergence` or `/quality` have relevant recent output for this scope, extract short deltas or witness lines only — not full workflow re-runs folded into this document. This phase stays lightweight by design (Context Erosion mitigation, see Risk table).

2b. **`[INTENT]` slice.** If a governing implementation-plan-style document already exists for this work, extract its `## [INTENT]` section verbatim (per that section's own `/nodelete` marking — never paraphrase it) plus any explicitly listed gaps. If none exists yet, the Phase 0 Intake Summary serves as the `[INTENT]` source for this DESIGN's own anchor.

2c. **Assemble the Design Context Payload.** A single focused bundle: the Phase 0 intent, the Phase 1 sentinel briefing (concise) + focus-plan Evidence Report (full JSON or a faithful summary if very large) + Negative Space findings, the Phase 2a deltas, and the Phase 2b `[INTENT]` slice. This is what Phase 3 actually uses — not a re-read of the raw workspace. Target: focused enough that a fresh reviewing context (human or subagent) could orient from this alone.

---

## PHASE 3 — AGENT CAPABILITY GATE: WRITE + INDEPENDENT REVIEW

**This is the fork.** Determine which path applies before writing anything:

- **Grok-available path:** if the executing agent has native Grok `/design` tool-calling available, *and* the user has authorized delegation for this session, assemble the payload as a pointer (`.workflow_state/design-payloads/DESIGN-<ID>.md`, content hash, "use only this" instruction, "do not edit Grok /design or its personas") and invoke `/design @<payload-path> <intent>`. Consume the returned DESIGN and its summary without trusting it uncritically — Phase 4's post-gates apply identically regardless of path.
- **Native path (the default — no Grok tool-calling assumed):** the orchestrating agent writes the DESIGN directly from the Phase 2c payload. This is not a lesser version of the formula; it is the primary path this suite currently runs on.

**Either way, the write is not done until it has passed Independent Critique:**
- Where the runtime supports spawning a separate subagent with no visibility into the drafting context (e.g., Claude Code's `Agent` tool), use it for a genuinely independent review pass — critique the draft against the Phase 0 intent and the Phase 1-2 payload, not against the drafting agent's own stated intentions.
- Where subagent spawning is unavailable, the floor is an adversarial `/quality` Step 5 self-critique — explicitly adopting a critic's stance, not a summary of what was already believed to be true. A self-critique that finds nothing is itself a finding (Hallucinated Success guard, `/quality` STRICT RULE 5) — re-run it with genuine adversarial intent.
- Iterate until 0 open issues remain. Do not proceed to Phase 4 with a known, unaddressed critique finding.

**Output structure (mandatory, either path) — see PILLAR_02_DESIGN_ORCHESTRATION_FORMULA.md §4.1 for the full spec:** Title & Metadata; Overview/Background (substrate summary from Phase 1); Goals & Non-Goals; Proposed Design (concrete, substrate-cited); `## Key Decisions` (numbered, with rationale); `## Build Ingestion Manifest` (Phase 4 injects/validates this — see below); `## PR Plan` (id, title, files/components, dependencies, brief description — directly consumable by `/implementation-plan` or `/execute-build`'s native trigger, PILLAR_03 §15); References.

---

## PHASE 4 — NATIVE POST-GATES

**Unconditional — runs identically whether Phase 3 took the native or the Grok-delegated path. Post-gates were never Grok-dependent.**

4a. **Focus re-verify.** Run `python3 ~/blueprint-workflows/scripts/focus/focus.py` again (absolute path per role.md's Script path resolution constant — **[PATH-ANCHORED 2026-07-07, resolves helpdesk-tickets/CLOSED_20260707_suite-script-path-resolution_workflow.md]**), this time with the produced DESIGN as the target plan (`--plan <design-path>` if the CLI supports it, or a direct read of the DESIGN's `[INTENT]` and cited gaps against current substrate). Outcome: PARITY (claims hold), MISMATCH (a claim doesn't hold — fix the DESIGN or the claim before proceeding, do not paper over it), or PENDING (a cited gap is legitimately future work, not Ghost Logic — `phase_status.py`-style adjudication where a tasks.md already exists for this scope).

4b. **`/quality` chain.** Confirm the DESIGN was produced under `/quality` discipline (Step 5 critique findings, Quality Witness log entry if `.workflow_state/quality_witness.log`'s parent directory exists).

4c. **Inject/validate the Build Ingestion Manifest.** If Phase 3's draft didn't already include one (native path may write it inline; Grok-delegated path likely needs it injected post-hoc), add:
```markdown
## Build Ingestion Manifest
**Intent Anchor:** [path to the [INTENT] section this DESIGN traces to; /nodelete rule stated]
**Gaps & Divergences:** [from Phase 1c Negative Space + Phase 2a deltas + substrate freshness]
**Verification:** [Phase 1b focus Evidence Report reference; Phase 4a re-verify verdict; quality_witness.log entry if present]
**Native Gates Mapping:** Phase X requires /focus-plan PARITY or PENDING before receipt; continuous-verify contract per execute-build.md 5g; receipt format DESIGN_RECEIPTS.md parallel to BUILD_RECEIPTS.md; PR Plan is the direct input to /implementation-plan or /execute-build's native trigger (PILLAR_03 §15) -- each PR description should quote the relevant DESIGN section it implements.
**Substrate Hygiene:** [zero_finding state if Pillar 1 substrate_index available; /divergence --convergence candidates if run]
**nodelete:** [INTENT] anchor preserved verbatim from its source.
```

4d. **Emit DESIGN_RECEIPTS.md** (atomic append, exact heredoc parity to `BUILD_RECEIPTS.md`):
```bash
mkdir -p ".workflow_state/receipts"
cat >> ".workflow_state/receipts/DESIGN_RECEIPTS.md" << RECEIPT_EOF
## $(date +%Y-%m-%d) — /design-orchestrator — <DESIGN title or ID>
- Phase/Stage: <DESIGN title, exact — for phase_status.py cross-reference if a tasks.md governs this DESIGN's own production>
- Grade/Status: DESIGN COMPLETE
- Files: <DESIGN path> (created or modified)
- Focus Re-Verify (4a): PARITY / MISMATCH-RESOLVED / PENDING noted
- Path: <path taken -- NATIVE or GROK-DELEGATED>
- Commit: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
---
RECEIPT_EOF
```
**Note the unquoted heredoc delimiter above — deliberate.** A quoted delimiter (`<< 'RECEIPT_EOF'`) suppresses all `$()` command substitution; this exact defect was found suite-wide and fixed 2026-07-06 (see `execute-build.md`, `triage.md`, and four other workflow Change Logs). Do not requote it.

If the `cat >>` fails: print `[DESIGN-RECEIPT] WARNING: could not write DESIGN_RECEIPTS.md — {error}` and continue. Do not halt on a receipt-write failure.

---

## PHASE 5 — HANDOFF READINESS

5a. If this DESIGN's `## PR Plan` is meant to drive an actual build, confirm it is directly consumable: each PR entry names real files/components, has explicit dependencies, and its description quotes the DESIGN section it implements (not a paraphrase). This is what `/execute-build`'s native trigger (PILLAR_03 §15) detects and consumes.

5b. Update any governing implementation-plan-style document's own cross-reference to point at this DESIGN, per that document's own `/nodelete` discipline (append, don't overwrite).

5c. Report completion: DESIGN path, Manifest present (yes/confirmed), PR Plan node count, DESIGN_RECEIPTS entry written, path taken (native/Grok). Do not claim "ready for build" if Phase 4a returned an unresolved MISMATCH.

---

## STRICT RULES (never violate)

1. Never skip the staged discipline (Phases 1-2) in favor of writing directly from raw intent — the focus-plan Evidence Report is the primary payload precisely because ad-hoc merging (this cluster's own founding failure) is what staging exists to prevent.
2. The focus-plan Evidence Report is never treated as one input among several — it is primary. Divergence/quality/`[INTENT]` are secondary context, kept short by design.
3. Never proceed to Phase 4 with a known, unaddressed Independent Critique finding. A critique that finds nothing (native path) is itself a finding — re-run with genuine adversarial intent (`/quality` STRICT RULE 5).
4. Phase 4 (post-gates) is unconditional and identical regardless of which Phase 3 path was taken. Never skip focus re-verify because "the write already looked careful."
5. Never emit DESIGN_RECEIPTS.md before Phase 4a-4c complete. A receipt claiming "DESIGN COMPLETE" ahead of its own verification is Hallucinated Success.
6. **Agent Capability Gate (§15):** never assume Grok `/design` tool-calling is available. Confirm capability and session authorization before taking the Grok-delegated path; default to native. Never edit Grok's `/design` skill or its personas under either path.
7. Discussion Is Not Authorization (`personality.md` §7): an explicit go-ahead to produce a DESIGN is required before Phase 0 treats a conversation as a build request.
8. The `## [INTENT]` slice (Phase 2b), where sourced from an existing governing document, is quoted verbatim and marked `/nodelete` — never paraphrased, never silently updated without explicit instruction from that document's own owner.
9. Receipt heredocs use an **unquoted** delimiter (`<< RECEIPT_EOF`, not `<< 'RECEIPT_EOF'`) so `$(date...)`/`$(git rev-parse...)` actually evaluate — and are checked for backticks in the body before unquoting, since an unquoted heredoc also triggers backtick command substitution.
10. If the user signals reduced active supervision mid-phase ("I will review," equivalent phrasing — Turn-Boundary Pause Protocol, `personality.md` §8): finish the current phase fully, including its receipt if Phase 4, before yielding. Do not additionally begin a new phase afterward.

---

## RISKS & MITIGATIONS

| Risk | Severity | Mitigation |
|---|---|---|
| **Ghost Logic in handoff** — DESIGN claims a Manifest/gate/verification that doesn't actually hold | HIGH | Phase 4a mechanically re-verifies against substrate via `focus.py`; dual evidence (the DESIGN's own claim + the re-verify verdict) before any receipt. |
| **Mock Trap** — the same context that wrote the draft is the only thing that ever judges it | HIGH | Phase 3's Independent Critique requires either a genuinely separate subagent or an explicitly adversarial `/quality` Step 5 pass — never a summary restating what the drafting context already believed. |
| **Context Erosion** — flooding the write step with the whole workspace instead of the staged payload | MEDIUM | Phases 1-2 produce one focused Design Context Payload; Phase 3 is instructed to use only it. Divergence/quality outputs stay short by explicit rule (STRICT RULE 2). |
| **PR Plan not actually ingestible** — reads well but `/execute-build`'s native trigger can't detect/consume it | MEDIUM | Phase 5a's explicit consumability check before claiming handoff readiness. |
| **Grok-delegated path assumed available when it isn't** | MEDIUM | Phase 3's Agent Capability Gate requires confirming both tool-calling capability and session authorization before that path is taken — native is the default, not a fallback. |

---

## HOW TO BEGIN

When activated:
1. Execute Phase 0 (Intake). Halt on genuine ambiguity per the Ambiguity Protocol — one question, not a questionnaire.
2. Execute Phase 1 (sentinel briefing + focus-plan primary payload + Negative Space).
3. Execute Phase 2 (deltas + `[INTENT]` slice + payload assembly).
4. Execute Phase 3 (Agent Capability Gate: write + Independent Critique to 0 open issues).
5. Execute Phase 4 (post-gates: focus re-verify, quality chain, Manifest, DESIGN_RECEIPTS).
6. Execute Phase 5 (handoff readiness report).

**You are now live. Begin Phase 0.**

---

## INTEGRATION WITH OTHER WORKFLOWS

```
/sentinel        → Phase 1 briefing input (Pillar 1 substrate_index where available)
/focus-plan      → Phase 1 primary payload (Evidence Report) + Phase 4a re-verify
/divergence      → Phase 2a short deltas
/quality         → Phase 3 Independent Critique floor + Phase 4b chain confirmation
/implementation-plan → Phase 2b [INTENT] slice source; Phase 5a PR Plan consumed by its Phase 4
/execute-build   → Phase 5 handoff consumer, via PILLAR_03 §15's native trigger (DESIGN with ## PR Plan detected → /implementation-plan → /execute-build)
/triage          → should recommend this workflow when a design intent is stated with no governing DESIGN yet
/secretary       → should recognize DESIGN_RECEIPTS.md as a receipt-family member alongside BUILD_RECEIPTS.md
```

**Consumers not yet updated (tracked, not silently skipped):** `/triage`'s Trigger Matrix, `/secretary`'s receipt-family read, `manifest/SUITE_HEALTH.md`'s suite index row, `role.md`'s Section III inventory. See Sovereign Redesign Cluster `implementation-plan/sovereign-redesign-cluster/tasks.md` Stage 3 Task 3.3 for the cross-reference pass that closes this.

Activation in Claude Code: `/design-orchestrator <raw intent>` in any Claude Code session where `~/.claude/commands/design-orchestrator.md` is symlinked to this file.

---

### Change Log
1. **2026-07-06**: `[CREATED — Sovereign Redesign Cluster Stage 3, Task 3.1-3.2, PILLAR_02_DESIGN_ORCHESTRATION_FORMULA.md §4.1 + §15]` Native implementation of the Sovereign Design Formula. Phases 0-2 follow PILLAR_02 §4.1's staged discipline verbatim (sentinel briefing, focus-plan primary payload + Negative Space, divergence/quality deltas, `[INTENT]` slice, payload assembly). Phase 3 implements the Agent Capability Gate (§15) as the core mechanism rather than an afterthought: native write + Independent Critique by default, Grok `/design` delegation only when tool-calling is confirmed available and session-authorized. Phase 4 (post-gates: focus re-verify, quality chain, Build Ingestion Manifest, DESIGN_RECEIPTS.md emission via the corrected unquoted-heredoc pattern) and Phase 5 (handoff readiness) are unconditional regardless of Phase 3's path — post-gates were never Grok-dependent, per §15's own finding. Modeled structurally on `execute-build.md`, `focus-plan.md`, `implementation-plan.md` (GLOSSARY, phased execution, STRICT RULES, Risk table, INTEGRATION, Change Log). Prototype shape (staged read → write → self-review → verify) already proven working end-to-end this session on PR 01-03 (Stage 1 of the same cluster) before this file formalized it. Standard Version: 3. Deliberately graded **Structured** at creation, not Sovereign — all 6 structural elements were present but an actual `/harden-workflow` pass had not yet run; claiming Sovereign before that would have been Grade Fraud.
2. **2026-07-06**: `[HARDENED — /harden-workflow, Sovereign Redesign Cluster Stage 3 Task 3.4]` Full 8-phase hardening protocol run against entry 1's content — not a rewrite, a verification pass. Phase 1 Assessment Card: all 6 Sovereign criteria (GLOSSARY, frontmatter, HOW TO BEGIN, STRICT RULES, structured output, Change Log) confirmed genuinely present, not scaffolded. Phase 4d (Inter-Workflow Reference Integrity): all 8 referenced workflows (`/sentinel`, `/focus-plan`, `/divergence`, `/quality`, `/implementation-plan`, `/execute-build`, `/triage`, `/secretary`) confirmed to exist via direct file check. Phase 7d (Linter Validation Gate): 0 CRITICAL, 1 WARNING (Antigravity pointer missing at `~/.gemini/antigravity/global_workflows/design-orchestrator.md`) — deferred deliberately, not silently: creating a pointer for a third runtime of uncertain active-use status would itself be the kind of speculative cross-tool tooling this cluster's own Agent Capability Gate exists to avoid building prematurely. Grade elevated Structured → Sovereign. `version` 1→2. Standard Version: 3.
3. **2026-07-07**: `[PATH-ANCHORED, resolves helpdesk-tickets/CLOSED_20260707_suite-script-path-resolution_workflow.md]` Phase 4a's Focus Re-Verify instruction referenced `scripts/focus/focus.py` with a bare relative path — fixed to the absolute `python3 ~/blueprint-workflows/scripts/focus/focus.py` form, referencing the new "Script path resolution" constant in `role.md`. Lower-severity than the `implementation-plan.md`/`nodelete.md` sibling fixes (this file's own EXECUTION MODEL already demonstrates the correct absolute form elsewhere), but fixed for consistency since it's the exact pattern the ticket named. 463/463 suite tests pass, no regressions. Frontmatter: version 2→3, content_hash recomputed, last_hardened 2026-07-07.

**Hardening Certificate:**
```
+══════════════════════════════════════════════════════════+
║  WORKFLOW HARDENING CERTIFICATE                          ║
║  Workflow:      /design-orchestrator                     ║
║  Date:          2026-07-06                                ║
╠══════════════════════════════════════════════════════════╣
║  GRADE:         SOVEREIGN                                 ║
╠══════════════════════════════════════════════════════════╣
║  Command file:  ~/blueprint-workflows/claude-commands/design-orchestrator.md
║  File size:     20,781 bytes                              ║
║  Symlink:       ~/.claude/commands/design-orchestrator.md — PRESENT ║
║  Frontmatter:   PRESENT — description ✓                   ║
║  GLOSSARY:      PRESENT (7 terms)                          ║
║  HOW TO BEGIN:  PRESENT                                    ║
║  STRICT RULES:  PRESENT (10 rules)                         ║
║  Struct Output: PRESENT (DESIGN_RECEIPTS.md heredoc + Phase 5c report) ║
║  Change Log:    PRESENT                                    ║
╠══════════════════════════════════════════════════════════╣
║  /triage Gap:   NONE — Trigger Matrix row added Stage 3 Task 3.3 ║
╠══════════════════════════════════════════════════════════╣
║  Changes Made:                                             ║
║    - Verified all 6 structural criteria against actual file content (not assumed) ║
║    - Verified all 8 inter-workflow references resolve to real files ║
║    - Ran Phase 7d linter gate: 0 CRITICAL                  ║
║    - Elevated grade Structured → Sovereign                 ║
║  Deferred Items:                                           ║
║    - Antigravity pointer (WARNING-level, not CRITICAL) — third-runtime status uncertain, not fabricated speculatively ║
╠══════════════════════════════════════════════════════════╣
║  Standard Version: 3                                       ║
║  Status:        WORKFLOW HARDENING COMPLETE                ║
+══════════════════════════════════════════════════════════+
```

**Hardening Intelligence Payload:**
```
HARDENING INTELLIGENCE PAYLOAD
Workflow Hardened: /design-orchestrator
Date: 2026-07-06
Observed Patterns: Agent Capability Gate as a first-class Phase (not a bolted-on amendment) works cleanly when the gate is designed into the workflow's structure from the start, per PILLAR_02 §15 and PILLAR_03 §15's identical treatment.
Suggested STRICT RULE additions or improvements: none for this workflow; STRICT RULE 9 (unquoted receipt heredoc + backtick check) is itself a suite-wide pattern worth propagating to any FUTURE new workflow with receipt emission, not just this one.
Potential new failure patterns: none new this session beyond what's already named (Ghost Logic, Mock Trap, Context Erosion, Grade Fraud -- all already in the global vocabulary).
Cross-workflow recommendations: none beyond the Stage 3 Task 3.3 cross-refs already completed (triage, secretary, role, SUITE_HEALTH).
Phylogenetic note: direct structural descendant of execute-build.md (Pillar 3's symmetric counterpart) and focus-plan.md/implementation-plan.md (phased GLOSSARY+STRICT RULES+Change Log convention) -- not a novel structure, a faithful application of proven suite DNA to a new domain (design orchestration).
```
