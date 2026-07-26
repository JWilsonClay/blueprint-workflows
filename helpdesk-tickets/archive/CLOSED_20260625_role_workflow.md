# Helpdesk Ticket: Gemini 3.5 Model Transition Inconsistencies & Prompt Breakpoint Evasion

**To**: Senior Architect of Workflows
**From**: Antigravity / daman Phase 34 Session
**Date**: 2026-06-25
**Subject**: LLM model transition to Gemini 3.5 introduces natural language boundary drift, speculative task execution, and incomplete workflow halting.
**Urgency**: CRITICAL (Architectural)

---

## 1. Executive Summary
A transition in the underlying LLM from Gemini 2.5 Flash / 3.1 to Gemini 3.5 has introduced two distinct, critical failures in control-flow boundary execution:
1. **Speculative Downstream Progression**: If the user does *not* explicitly include a stop-trigger (e.g., "I will review" or "return to me"), the model speculatively runs ahead to execute downstream tasks/phases of the plan without authorization.
2. **Incomplete Workflow Abandonment**: If the user *does* include a trigger like "I will review", the model incorrectly assumes it can halt *prematurely* without finishing the current assigned workflow in full (e.g., leaving checkboxes in `tasks.md` unchecked or omitting journal logs). 

The trigger "I will review" is a **turn-boundary halt**—meaning the current task/workflow must be executed completely and in full (including all final checks, ledger entries, and updates), and *then* the model must halt and yield control. It is never a permission to leave the current task in an incomplete or unrecorded state.

## 2. Root Cause Analysis: "Model-Change Behavior Shifts (Cognitive / Natural Language Drift & Proactivity Bias)"
- **The How**: 
  - When no trigger is present, the model over-extrapolates its instructions and executes planned downstream tasks beyond the prompt's scope.
  - When the "I will review" trigger is present, the model treats it as a license to terminate the prompt loop early, bypassing final protocol steps like checking off `tasks.md` and leaving the workspace in an inconsistent state.
- **The Why**: The workflows (e.g., `/execute-build`) and persona guidelines do not explicitly codify "I will review" / "return to me" as a **strict Turn-Boundary Halt**. The model conflates conversational halting with procedural shortcutting, failing to understand that a checkpoint requires a 100% complete and documented state of the current step before yielding control.

## 3. Forensic Evidence
- **DevJournal Entry**: [DevJournal.md](file:///home/jwils/.prebuild.temp/books/daman/DevJournal.md#L70-L81)
  *Evidence: Documents the timeline of the Phase 34 closeout where model transition inconsistencies were first observed and flagged.*
- **System Directive / Persona Rules**: [role.md](file:///home/jwils/blueprint-workflows/claude-commands/role.md#L155-L170)
  *Evidence: Shows that the interaction protocol and guidelines rely on general natural-language instructions (e.g., "halt at any time and return to me") which drift when the underlying LLM is swapped.*

## 4. Remediation: Context-Aware Proactivity Boundaries
1. Establish a standard, unambiguous control syntax for prompt breakpoints (e.g., a structured XML/YAML boundary tag like `<halt_for_review />`) that can be programmatically verified or statically checked prior to execution.
2. Define a strict rule that a breakpoint trigger (like "I will review") commands the model to halt *only after* completing all steps of the assigned task in full, including final checks, ledger updates, and `tasks.md` modifications.
3. Update persona-level guidelines to enforce that if a prompt's intent is ambiguous regarding proactivity, the model must either:
   - Ask directly for clarification.
   - Append an isolated, clearly labeled "Reading Between the Lines" ideation section without mutating files.
   - Err on the side of strict, non-proactive execution.

## 5. Recommendation to Senior Architect
Update `/limitations` and `/workflows/role.md` to define a model-agnostic, parser-robust boundary standard for multi-turn execution. Introduce a directive that explicitly turns off "reading between the lines" and speculative execution during structured phase builds unless proactivity is explicitly invited by the user, enforcing that the model must default to executing only the written instructions and immediately halting.

---
**Status**: **REMEDIATED (three distinct failures separated out and each given its own mechanism: Discussion-Is-Not-Authorization for mid-conversation ideation mistaken as build authorization; a unified Turn-Boundary Pause Protocol for both unwanted autonomous continuation and premature incomplete-halt; both added as canonical universal principles rather than a single structured breakpoint tag)**
**Verification**: Investigation found the ticket's two named failures were actually three, and that its own Forensic Evidence citation (`role.md`'s ambiguity-protocol quote) was attributed to the wrong mechanism — that text governs agent-side uncertainty, not a user-signaled pause, which the suite had no concept for at all (confirmed: `execute-build.md`, the workflow most likely to be mid-task when a pause arrives, had zero language about it). User clarified the "speculative progression" failure was itself two things: (a) `/execute-build`'s documented multi-phase autonomy continuing when unwanted in the moment, and (b) the more severe case — mid-conversation discussion mistaken for "proceed immediately with the build," inventing unapproved work. (a) unified with the original premature-halt complaint into one **Turn-Boundary Pause Protocol** (same trigger, two moments: mid-work vs. work's natural end); (b) addressed separately as **Discussion Is Not Authorization**, since it isn't about pausing at all. Both added to `personality.md` (Sections 7-8, STRICT RULES 8-9) as the canonical universal source, mirrored into `~/.claude/CLAUDE.md`, then reinforced with narrow tie-ins (not duplicated) in `implementation-plan.md`'s HITL Gate (STRICT RULE 26) and `execute-build.md`'s Phase 0 + phase loop (STRICT RULES 15-16, which also fixed an incidental pre-existing bug: the STRICT RULES header was missing its `##` prefix, making it linter-invisible and causing a stale `strict_rule_count: 0`). The ticket's original `<halt_for_review />` structured-tag proposal was deliberately not built — no confirmed external parser exists to gate on it, so unambiguous prose was judged sufficient without inventing unverified infrastructure; investigating Claude Code's actual hook system for genuine external enforcement is noted as a possible future stretch, not done here. `lint_workflows.py` clean on `implementation-plan.md` and `personality.md`; `execute-build.md` has one pre-existing, deliberately deferred WARNING (missing GLOSSARY section — a structural gap, correctly `/harden-workflow`'s job per `20260704_ticket-remediation-authority_workflow.md`'s own reasoning, not freelanced here). All hashes genuinely recomputed via `--fix-hashes`.

---
*Signed,*
**Antigravity** (ticket) / **Claude, Sonnet 5** (remediation)
*(Literary Architect & Publishing Strategist / Senior Architect of Workflows)*

---

## Addendum — 2026-07-04

Cross-referenced against `helpdesk-tickets/20260625_limitations_workflow.md` (filed the same day, same session), which recommended the opposite fate for `/limitations` — deletion, not expansion. The two were never reconciled against each other before filing. Resolved today: `/limitations` is retired (deleted, symlink removed); its content merged into `personality.md` (Section 6) and mirrored into `~/.claude/CLAUDE.md`. See `role.md` Change Log entry 3 and `claude-commands/personality.md` Change Log entry 4 for the full record.

**This ticket's own recommendation is updated accordingly**: Section 5's target of "`/limitations` and `role.md`" now reads as **`/personality` (canonical file `claude-commands/personality.md`, mirrored into `~/.claude/CLAUDE.md`) and `role.md`** — `/limitations` no longer exists to carry the halt-boundary work this ticket asks for. The underlying CRITICAL problem this ticket describes — model-transition drift on "I will review" / turn-boundary halting, needing a structured, parseable breakpoint syntax — is **not yet addressed** by today's action. Only the filing-target contradiction is resolved. This ticket remains **OPEN** pending that substantive work.
