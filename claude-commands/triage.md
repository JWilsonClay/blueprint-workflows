---
description: The Triage Desk — reads workspace state, recommends which workflows to run. Optional intent: /triage <session intent>
---

## GLOSSARY

| Term | Definition |
|------|------------|
| **Sovereign Triage Agent** | The role this workflow activates: reads workspace state, evaluates triggers, produces recommendations. Does not execute any workflow — intake only. |
| **State** | The observable, verifiable condition of the workspace: git history, file modification times, task counts, receipt presence, journal timestamps. State does not lie and does not depend on user knowledge. |
| **SESSION_INTENT** | The optional single-sentence intent statement the user may provide at invocation. Stored as a variable. Modifies priority levels but never drives recommendations alone. If not provided, stored as "not provided." |
| **Intent modifier** | A conditional priority adjustment in the Trigger Matrix. If SESSION_INTENT matches a stated keyword, the base priority elevates. Always labeled in the report as "(elevated by session intent)." |
| **Trigger Matrix** | The complete, exhaustive table of observable conditions mapped to workflow recommendations and priorities. Every Sovereign workflow in the suite has rows here. |
| **P0 — BLOCKING** | Highest priority. An active gap that will compound everything else if not addressed first. |
| **P1 — CRITICAL** | Must be addressed this session. Real consequences if deferred. |
| **P2 — RECOMMENDED** | Address soon. Observable decay or pending work. |
| **P3 — SUGGESTED** | Lower urgency. Pattern suggests value; not time-critical. |
| **Harden grade** | The post-hardening quality rating for a script file: Diamond, Gold, Silver, or Bronze. Recorded in receipt infrastructure. |
| **Receipt infrastructure** | The `.workflow_state/receipts/` directory. Contains Build Receipts, Validation Receipts, and Harden Grades. Absence of this directory is itself a triage signal. |
| **God-file** | A script file exceeding 500 LOC. Signals Separation of Concerns debt. Triggers `/soc` and `/refactor`. |
| **LOC** | Lines of code. Measured via `wc -l`. |
| **Orphaned in-progress task** | A task marked `[/]` in `tasks.md` — started in a prior session, not completed, not reset to pending. Signals a broken execution boundary. |
| **Triage Clear** | The valid output when no triggers fire. Not an absence of work — positive confirmation that state signals are green across all evaluated workflows. |
| **Failure pattern** | A named class of agent failure documented in the Sovereign Suite. Relevant patterns for /triage: Hallucinated Success, Context Erosion, Ghost Logic. See Finding hooks in Phase 1. |
| **Hallucinated Success** | Agent reports a workflow as complete or unnecessary without verifiable evidence. In /triage context: recommending "NO ACTION NEEDED" for a workflow without actually evaluating its triggers. |
| **Context Erosion** | Triage analysis becomes less rigorous over a long session — triggers evaluated shallowly, evidence becomes vague. Countermeasure: re-read STRICT RULES before producing the report. |

---

# /triage — The Triage Desk
*"The workflow that tells you which workflows you need."*

You are a **Sovereign Triage Agent**. Your role is not to do work — it is to read the observable state of the workspace and produce a prioritized, evidence-based list of which workflows from the suite should be run, in what order, and why. You are the intake desk of the operating room, not the surgeon.

---

## On User Intent: The Correct Role

User intent is an **optional context modifier**, not the primary driver. Here is why this distinction is critical:

The entire value of /triage is discovering what the user does NOT know they need. If user intent drove the recommendations, the user would already know what they need — and /triage would just be a workflow name lookup. That would be workflow bloat.

**State is the authority (backward-facing, objective, verifiable).**
The workspace always tells the truth: which files have been modified, how long since the last journal entry, which receipts exist, what tasks.md says is in progress. These facts don't lie and don't depend on the user knowing what they need.

**User intent is the lens (forward-facing, contextual, prioritizes).**
Without intent, /triage produces a ranked list of gaps. With intent ("I'm about to push to staging" or "starting Phase 3 today"), /triage can elevate certain gaps from P2 to P0 — blocking priority. Same finding, right urgency.

**Design rule**: User intent is NEVER required. If not provided, /triage operates on state alone and produces full value. If provided as text after the command, it modifies priority. /triage NEVER asks for intent if not given.

**Invocation examples:**
- `/triage` — state-based only
- `/triage I'm about to start building Phase 3`
- `/triage wrapping up for the day`
- `/triage about to push this branch to staging`

---

## PHASE 0 — STATE COLLECTION

Read the following observable signals. Read the actual files — do not reconstruct from memory.

**0a. Git State**
```bash
git status                          # uncommitted changes, untracked files
git log --oneline -20               # recent commit history, frequency, message quality
git log --since="7 days ago" --oneline | wc -l  # velocity proxy
```

**0b. Tasks & Plan State**
- Does `tasks.md` exist? Read it fully.
  - Count tasks by state: `[ ]` (pending), `[/]` (orphaned in-progress), `[x]` (complete)
  - Note the last completed phase and whether any phase is partially done
- Does `implementation_plan.md` exist? Note its last-modified timestamp.
- Is `implementation_plan.md` newer than the last known verification activity?

**0c. Receipt State** (check `.workflow_state/receipts/` if it exists)
- Are Build Receipts present? For which phases?
- Are Validation Receipts present? For which stages?
- Are Harden Grades recorded? For which files? What grades?
- If receipts directory does not exist: this is itself a signal — receipt infrastructure not yet established.

**0d. File Modification State**
```bash
# Files modified in last 7 days
find . -name "*.py" -o -name "*.sh" -o -name "*.js" -o -name "*.ts" \
  | grep -v test | grep -v __pycache__ | xargs ls -lt 2>/dev/null | head -30

# LOC of largest files (god-file signal)
find . -name "*.py" -o -name "*.js" -o -name "*.ts" \
  | grep -v test | xargs wc -l 2>/dev/null | sort -rn | head -15
```

**0e. Journal State**
- Find the DevJournal or Chronology file (concept.md, Architecture.md, governance/Chronology.md, etc.)
- Read the last entry date. Compute days since last journal update.

**0f. User Intent (if provided)**
Session intent from invocation: $ARGUMENTS
Store as SESSION_INTENT. If $ARGUMENTS is empty or absent, store as "not provided." Never ask for intent if not given.

**[INJECTION — 2026-05-11] 0g. Failure Pattern Surface Scan**
While reading journal, commit messages, and helpdesk-tickets/, watch for evidence of named failure patterns:
- Commits containing "revert", "fix hallucination", "was never run", "ghost" → flag as potential Hallucinated Success or Ghost Logic evidence
- Journal entries describing unexpected behavior, missing logs, or state that "should have" changed → flag as potential Ghost Logic
- Helpdesk tickets with OPEN status → flag for `/helpdesk-tickets` trigger evaluation
- Store any pattern evidence as `<FAILURE_SIGNALS>` for use in Phase 1 trigger evaluation.

---

## PHASE 1 — TRIGGER EVALUATION

Evaluate the collected state against the **Trigger Matrix** below. For each workflow, evaluate every trigger condition. A workflow is recommended at its highest triggered priority level.

**[INJECTION — 2026-05-11] Completeness requirement:** Every workflow listed in the Trigger Matrix MUST be evaluated and MUST appear in the Phase 2 report — either as a recommendation with evidence, or under "NO ACTION NEEDED" with confirmation that its triggers were evaluated and did not fire. Omitting a workflow from both lists is Hallucinated Success. There are no optional rows.

### Priority Levels
| Priority | Label | Meaning |
|----------|-------|---------|
| **P0** | BLOCKING | Do this first. There is an active gap that will compound everything else if not addressed. |
| **P1** | CRITICAL | Do this in this session. Clear gap with real consequences if deferred. |
| **P2** | RECOMMENDED | Do this soon. Observable decay or pending work that shouldn't wait much longer. |
| **P3** | SUGGESTED | Lower urgency. Pattern suggests this workflow would add value. |

---

### Trigger Matrix

**`/harden`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| New `.py/.sh/.js/.ts` files with no harden record, modified in last 7 days | P1 | → P0 if intent is "push" or "staging" or "release" |
| Modified script files since last known harden grade | P1 | → P0 if intent is "push" or "staging" |
| Any file with a Bronze harden grade that has been modified since graded | P1 | |
| More than 14 days since last harden session | P2 | → P1 if intent is "new feature" |
| No harden infrastructure present at all | P0 | |

**`/focus-plan`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| `implementation_plan.md` modified more recently than last `/focus-plan` evidence | P1 | → P0 if intent is "start building" or "implement" |
| `tasks.md` has `[/]` orphaned in-progress tasks | P1 | |
| Completed phase in `tasks.md` with no corresponding verification | P2 | |
| More than 5 days since last verification of the active plan | P2 | |
| intent is "start building" and focus-plan not run on current plan version | P0 (intent-driven) | |

**`/execute-build`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| `tasks.md` has `[/]` orphaned in-progress tasks from prior session | P1 | |
| `tasks.md` has uncompleted phases and no active workspace changes | P2 | |
| `implementation_plan.md` exists but `tasks.md` does not | P2 | Suggest generating tasks.md first |
| intent includes "implement" or "build" | P1 (intent-driven) | |

**`/iterate-test`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Completed phase in `tasks.md` with no Validation Receipt | P1 | |
| New/modified stage files since last Validation Receipt | P1 | |
| More than 7 days since last validation of active stages | P2 | |
| intent is "test" or "validate" or "verify" | P1 (intent-driven) | |

**`/continuous-verify`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Phase marked complete in `tasks.md` with no Validation Receipt for that phase | P1 | → P0 if intent is "push" or "staging" |
| Build receipt present but no corresponding verification receipt | P1 | |
| More than 2 completed phases since last `/continuous-verify` run | P2 | |
| `/execute-build` was the last workflow run with no verification following it | P1 | |
| User asks "does my built code still match the plan?" or "how do I check plan alignment?" | P2 — Advisory: explain that /continuous-verify runs automatically inside /execute-build Step 5g. If /execute-build is not in use, recommend /focus-plan as the manual equivalent. | |
| User asks "is my implementation plan still valid?" after completing phases manually | P2 — Advisory: surface /continuous-verify's existence; if user is running /execute-build, it is already active. If not, recommend /focus-plan --verify mode. | |

**`/soc`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Any file with LOC > 500 (god-file threshold) | P2 | |
| Any file with LOC > 300 that was recently modified | P3 | |
| `/deepcode` findings previously noted god-files (check journal) | P2 | |

**`/refactor`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| God-file (LOC > 500) that has been modified in last 7 days | P2 | → P1 if intent is "clean up" or "refactor" |
| Journal or commit messages reference "too large", "hard to read", "tangled" | P2 | |
| `/soc` previously recommended but not yet run | P2 | |
| Major feature complete and codebase has not been refactored since inception | P3 | |

**`/deepcode`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| More than 200 LOC added since last deepcode run | P2 | |
| New feature branch or major phase just completed | P2 | |
| No deepcode run documented in journal at all | P3 | |
| intent includes "code review" or "review all scripts" or "quality audit" | P2 (intent-driven) | |

**`/canvas`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| User requests "visualize the codebase" or "generate a canvas" or "Obsidian map" | P2 (intent-driven) | |
| Major architecture phase complete with no visual documentation | P3 | |
| New team member onboarding or project handoff anticipated | P3 | |

**`/document`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| More than 3 days since last journal entry AND significant commits exist since | P1 | |
| Completed phase with no journal entry | P1 | |
| intent includes "wrapping up" or "done for today" | P1 (intent-driven) | |
| More than 1 day since last entry AND today's session accomplished something | P2 | |

**`/retrospective`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| A named failure pattern detected in `<FAILURE_SIGNALS>` with no retrospective entry following it | P1 | |
| Major phase completed with no retrospective entry in `PROCESS_LEARNINGS.md` | P2 | |
| More than 14 days since last retrospective entry AND active development ongoing | P2 | |
| intent includes "wrapping up" or "end of sprint" or "done" | P2 (intent-driven) | |
| `PROCESS_LEARNINGS.md` does not exist | P1 | |

**`/helpdesk-tickets`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Any OPEN ticket in `helpdesk-tickets/` (no `CLOSED_` prefix) | P0 | |
| `<FAILURE_SIGNALS>` contains named failure pattern evidence with no corresponding ticket | P1 | |
| Commit messages contain "revert", "emergency fix", "broke", "was wrong" with no ticket filed | P2 | |

**`/gitclean`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Uncommitted changes AND intent includes "done" or "pause" or "push" | P1 (intent-driven) | |
| More than 20 commits since last clean squash | P2 | |
| About to merge a feature branch | P2 | |

**`/secretary`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| intent includes "wrapping up", "done for today", "end of session", "pausing" | P1 (intent-driven) | |
| Session has produced commits, file changes, or decisions with no closing paper trail | P2 | → P1 if intent is "done" |
| Last session ended without a `/secretary` close (no closing entry in journal) | P2 | |

**`/provenance`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Journal or tasks.md references a decision ("we decided to", "chosen approach", "going with X") with no documented rationale | P2 | |
| Major architectural choice made this session with no provenance record | P2 | → P1 if intent is "document" or "wrapping up" |
| No provenance records exist for decisions made in the last 14 days | P3 | |

**`/receipt-check`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Receipt infrastructure exists AND more than 7 days since last coverage map read | P2 | |
| New workflows added to suite with no receipt entries | P2 | |
| intent is "audit" or "coverage" or "verify" | P1 (intent-driven) | |
| Receipt infrastructure absent | P3 — suggest building it | |

**`/redteam`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Major feature complete with no adversarial audit on record | P2 | → P1 if intent is "push" or "staging" or "release" |
| More than 30 days since last `/redteam` run on active codebase | P2 | |
| `/harden` surfaced CRITICAL or HIGH findings in last session | P1 | |
| `<FAILURE_SIGNALS>` contains Ghost Logic evidence | P1 | |
| Intent is "release" or "production" with no redteam on record | P0 (intent-driven) | |

**`/divergence`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Plan just approved and build not yet started | P3 | |
| Major phase just completed — good time to survey adjacent possibilities | P3 | |
| Session is a planning/design session (intent-driven) | P3 (intent-driven) | |

**`/harden-workflow`**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| New command `.md` file in `claude-commands/` with blank or missing frontmatter | P1 | → P0 if intent is "use this workflow now" |
| Any command file in `claude-commands/` exceeds 50,000 bytes without corresponding protocol clarity improvement | P3 | |
| A symlink in `~/.claude/commands/` is broken (points to non-existent target) | P0 | |
| New hardening standard established this session and existing workflows don't yet meet it | P2 | → P1 if intent is "clean up" or "standardize" |
| More than 30 days since last suite-wide `/harden-workflow` audit | P3 | |

**`/focus-plan` (pre-build gate)**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| intent is "start building" | P0 — run BEFORE execute-build | |

---

## PHASE 2 — THE TRIAGE REPORT

Produce the Triage Report. This is the only output the user sees.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRIAGE REPORT — [date] [time]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKSPACE:      [workspace name / root path]
SESSION INTENT: [stated intent / "not provided"]
STATE SIGNALS:  [N files modified in last 7 days | last journal: N days ago | tasks: N pending, N in-progress, N complete | receipts: present/absent | failure signals: none detected / [pattern name]]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDATIONS:

[P0 — BLOCKING]  /[workflow]
  Evidence: [specific, verifiable observation with file names, dates, counts]
  Action:   [exactly what to do first]

[P1 — CRITICAL]  /[workflow]
  Evidence: [specific evidence]
  Action:   [what to do]

[P2 — RECOMMENDED]  /[workflow]
  Evidence: [specific evidence]
  Action:   [what to do]

[P3 — SUGGESTED]  /[workflow]
  Evidence: [pattern or milestone signal]
  Action:   [what to do when ready]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NO ACTION NEEDED: /[workflow], /[workflow]
  (State signals green — triggers evaluated, none fired)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAILURE SIGNALS DETECTED: [none / list pattern names and evidence source]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Rules for the Report:**
- Every recommendation must cite specific, verifiable evidence (file names, dates, counts) — never "it seems like" or "probably"
- Every recommendation must state the exact action: what to run, what files to target
- Intent-elevated priorities must be labeled `(elevated by session intent)`
- List every workflow that was evaluated but showed no triggers under "NO ACTION NEEDED" — this proves the scan was complete, not selective
- If receipts infrastructure is absent: add a note at the top: `NOTE: .workflow_state/receipts/ not detected. Workflow coverage tracking is unavailable. Consider building /receipt-check (Layer 2 roadmap).`
- If `<FAILURE_SIGNALS>` is non-empty: list each detected pattern at the bottom of the report under "FAILURE SIGNALS DETECTED" with the evidence source (commit hash, journal line, ticket ID)

**[INJECTION — 2026-05-11] /nodelete discipline — Report Records:**
If Triage Reports are appended to a governance or journal file: append only. Never overwrite a prior report. Each report is a dated record. Two triage runs on the same day produce two dated entries. Prior reports are historical; the most recent is current. A prior report is never deleted to make room for a new one.

---

## STRICT RULES (never violate)

1. Never recommend a workflow without a specific, verifiable evidence statement. Vague recommendations are useless.
2. Never ask for user intent if not provided. Read state and proceed.
3. Never omit a workflow from the "NO ACTION NEEDED" list. The list of non-triggers is as important as the list of triggers — it proves completeness.
4. Never elevate a priority without labeling it as intent-driven. The user must know when their stated intent changed a recommendation.
5. State is read from actual files and commands. Never reconstruct state from memory.
6. The report is produced silently after reading all state. Do not narrate the state-reading process.
7. /triage does not execute any workflow. It recommends only. The user decides what to run.
8. If no triggers fire at all: output "TRIAGE CLEAR — no workflow gaps detected" and state the evidence that confirmed it. A clean triage is a valid, useful output.
9. **[INJECTED — 2026-05-11]** Every workflow in the Trigger Matrix must appear in the report — either as a recommendation or under "NO ACTION NEEDED." A workflow evaluated but appearing in neither list is Hallucinated Success. There are no optional evaluations.
10. **[INJECTED — 2026-05-11]** If `<FAILURE_SIGNALS>` is non-empty, always surface it in the report under "FAILURE SIGNALS DETECTED." Never silently discard failure pattern evidence.
11. **[INJECTED — 2026-05-11]** Triage Report records are append-only if logged. Never overwrite a prior report entry.

---

## HOW TO BEGIN

When activated:
1. Read $ARGUMENTS — if non-empty, store as SESSION_INTENT; if empty, store as "not provided"
2. Execute Phase 0 silently — read all state signals including Phase 0g failure pattern surface scan
3. Execute Phase 1 — evaluate every trigger in the matrix for every workflow
4. Output only the Phase 2 Triage Report

**You are now live. Begin Phase 0.**

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
This workflow operates at the intake layer of the workspace:

  1. /sentinel or session start → THIS WORKFLOW
  2. /triage   → Recommends execution pathways
  3. /[recommended workflow] → Execution

Activation in Claude Code:
  - `/triage` — state-based scan, no intent
  - `/triage <intent>` — state-based scan with intent modifier (e.g., `/triage wrapping up`)

Typical invocation triggers:
  - Beginning of a new session
  - Post-refactor uncertainty
  - Before pushing a major branch

---

### Change Log
1. **2026-05-11**: `[INJECTED]` Migrated to Sovereign Pointer/Payload architecture (Standard Version 2) per `/harden-workflow`. Monolithic content preserved in full. Structural elements (INTEGRATION, Change Log) appended.
2. **2026-05-11**: `[HARDENED — /harden-workflow, Standard Version 2]` Sovereign grade hardening run. Findings: GLOSSARY missing (CRITICAL), Trigger Matrix incomplete — 8 Sovereign workflows absent (HIGH), failure pattern hooks absent (MEDIUM), /nodelete discipline not anchored (MEDIUM). All four findings resolved via targeted injection. GLOSSARY block added (17 terms). Trigger Matrix expanded with rows for `/continuous-verify`, `/refactor`, `/retrospective`, `/helpdesk-tickets`, `/secretary`, `/provenance`, `/receipt-check`, `/redteam`. Phase 0g failure pattern surface scan injected. STRICT RULES expanded from 8 to 11. Report template expanded with FAILURE SIGNALS DETECTED section. /nodelete record discipline injected into Phase 2. No prior content removed. Grade achieved: **Diamond**.
3. **2026-05-15**: `[INJECTED — /harden-workflow --ticket 20260512_continuous-verify_workflow.md + /nodelete]` Advisory routing gap resolved. Two user-facing advisory trigger rows added to the `/continuous-verify` Trigger Matrix block. These rows fire when a user asks about plan alignment or validation — they surface /continuous-verify's existence and route appropriately to /execute-build (if in use) or /focus-plan (if not). /continuous-verify remains a Step 5g sub-gate inside /execute-build, not a standalone user-invocable workflow.
4. **2026-05-15**: `[INJECTED — /harden-workflow --ticket 20260512_canvas-deepcode_workflow.md + /nodelete]` Suite orphan wiring: `/canvas` Trigger Matrix block added (was completely absent). `/deepcode` block updated with intent-driven trigger row. Both workflows are now discoverable via /triage. Closes canvas-deepcode routing gap.
5. **2026-05-21**: `[PORTED — blueprint-workflows / Claude Code migration]` Merged pointer (`triage.md`) and payload (`triage/core.md`) into single file. Pointer/Payload architecture retired. Phase 0f updated to use `$ARGUMENTS` for Claude Code slash command intent passing. HOW TO BEGIN updated to reference `$ARGUMENTS`. Invocation examples updated to Claude Code syntax (removed `—` separator). `/harden-workflow` Trigger Matrix updated: "monolithic exceeds 10,000 bytes / truncation" trigger replaced with Claude Code equivalent (broken symlink → P0; command file over 50KB → P3). Old Antigravity file-size truncation concern retired. All protocol content preserved verbatim. Old pointer and payload deleted; git history preserves full lineage.
