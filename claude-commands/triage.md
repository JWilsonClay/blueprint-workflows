---
description: "The Triage Desk — reads workspace state, recommends which workflows to run. Optional intent passed as argument after the command. v4: script-backed by the Triage Evidence Engine (scripts/triage/triage_audit.py) for task/phase state, receipt coverage, and Trigger Matrix completeness."
type: meta
grade: Sovereign
version: 5
content_hash: "sha256:278e975809809b79"
last_hardened: "2026-07-07"
strict_rule_count: 11
phase_count: 3
context_retention: medium
flags: []
dependencies:
  - "/harden-workflow"
  - "/workstream"
  - "/implementation-plan"
  - "/quality"
  - "scripts/triage/triage_audit.py"
triggers:
  - "/sentinel"
  - "/harden-workflow"
produces:
  - ".workflow_state/receipts/TRIAGE_RECEIPTS.md"
consumes:
  - "tasks.md"
  - "implementation-plan.md"
  - "WORKSTREAM_STATUS.md"
  - "DECISIONS.md"
  - ".workflow_state/receipts/*"
  - ".workflow_state/quality_witness.log"
platform_requirements:
  file_write: false
  shell_exec: true
  git_access: true
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
| **TRIAGE_RECEIPTS.md** | Append-only triage report ledger (P5). Written by /triage using identical `cat >>` + heredoc header style as BUILD_RECEIPTS.md (## DATE — /triage — ...). Emitted on handover signal. Consumed by /secretary and SUITE_HEALTH. |
| **God-file** | A script file exceeding 500 LOC. Signals Separation of Concerns debt. Triggers `/soc` and `/refactor`. |
| **LOC** | Lines of code. Measured via `wc -l`. |
| **Orphaned in-progress task** | A task marked `[/]` in `tasks.md` — started in a prior session, not completed, not reset to pending. Signals a broken execution boundary. |
| **Triage Clear** | The valid output when no triggers fire. Not an absence of work — positive confirmation that state signals are green across all evaluated workflows. |
| **Failure pattern** | A named class of agent failure documented in the Sovereign Suite. Relevant patterns for /triage: Hallucinated Success, Context Erosion, Ghost Logic. See Finding hooks in Phase 1. |
| **Hallucinated Success** | Agent reports a workflow as complete or unnecessary without verifiable evidence. In /triage context: recommending "NO ACTION NEEDED" for a workflow without actually evaluating its triggers. |
| **Context Erosion** | Triage analysis becomes less rigorous over a long session — triggers evaluated shallowly, evidence becomes vague. Countermeasure: re-read STRICT RULES before producing the report. |
| **Triage Evidence Engine** | **[ADDED 2026-07-07, implementation-plan.md Phase 4.5]** `scripts/triage/triage_audit.py` — the read-only mechanical layer behind Phase 0b/0c (task/phase state and receipt coverage, via direct reuse of `scripts/focus/phase_status.py` and `scripts/receipt/coverage.py` — not duplicated) and the Phase 2 Trigger Matrix Completeness Gate. Reports facts only — checkbox tallies, receipt presence, workflow-name presence in report text — never whether a trigger was evaluated with genuine rigor or which priority a finding deserves. Architectural sibling of `scripts/build/` and `scripts/secretary/`. |

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

**0b. Tasks & Plan State** **[ENGINE-BACKED — ADDED 2026-07-07, implementation-plan.md Phase 4.5]**

The checkbox tally and orphaned-in-progress detection are mechanical facts — get them from the engine rather than hand-counting (this reuses `scripts/focus/phase_status.py` directly, not a new parser):

```bash
python3 ~/blueprint-workflows/scripts/triage/triage_audit.py --workspace . --output-json
```

Read `phase_status.phases` from the JSON — each phase's checkbox tally and derived `status` (`in_progress` IS the orphaned-in-progress signal). If the engine is unavailable: fall back to reading `tasks.md` directly and counting `[ ]`/`[/]`/`[x]` by eye; note the fallback in the report.

- Does `implementation_plan.md` exist? Note its last-modified timestamp.
- Is `implementation_plan.md` newer than the last known verification activity?

**0c. Receipt State** **[ENGINE-BACKED — ADDED 2026-07-07, implementation-plan.md Phase 4.5]**

Receipt-file presence is a mechanical fact — the same `triage_audit.py` call above also returns `receipt_coverage` (reusing `scripts/receipt/coverage.py` directly, the same engine `/receipt-check` already uses):

Read `receipt_coverage.receipt_files_present` from the JSON — `build`/`validation`/`harden`/`docs`/`design`/`triage` booleans. If `tasks_md_found: false` or the engine is unavailable: fall back to manually checking `.workflow_state/receipts/` for each receipt file; note the fallback in the report.

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

**[INJECTED 2026-05-23] 0h. Multi-Agent Workstream State**
Check for multi-agent workstream infrastructure:
- Does `WORKSTREAM_STATUS.md` exist? If yes, read it — note status of each workstream (A, B, C) and last updated timestamps.
- Does `DECISIONS.md` exist? If yes, check for any entries tagged `**Escalation:** PENDING`.
- Does `implementation-plan.md` contain workstream definitions? (Look for "Workstream A", "Workstream B", "Workstream C" sections with task lists.)
- Store findings as `<WORKSTREAM_STATE>` for use in Phase 1 trigger evaluation.

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
| **[v3 — 2026-06-02 — deterministic call]** Run `python3 ~/blueprint-workflows/scripts/harden/harden_audit.py --workspace . --output-json` — a firm CRITICAL (`verdict_hint: BLOCKED`) in any non-test script → P0; a firm HIGH or a `requires_confirmation` credential candidate (`verdict_hint: FINDINGS`) → P1. Actual finding evidence, not just receipt absence (mirrors the `lint_workflows.py --quiet` precedent for `/harden-workflow`). | P0 / P1 | → P0 if intent is "push"/"staging"/"release" |

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
| **[v3 — 2026-06-02 — deterministic call]** Run `python3 ~/blueprint-workflows/scripts/iterate/iterate_audit.py --workspace . --output-json` — a `MOCK_TRAP_CANDIDATE` (`verdict_hint: FINDINGS`) in a test for a stage built/modified in the last 7 days → P1; a `HARDCODED_ASSERTION` smell → P2. Actual finding evidence, not just receipt absence (mirrors the `harden_audit.py` and `lint_workflows.py --quiet` precedents). The PRIMARY/INFRASTRUCTURE call stays with /iterate-test Step 4b — the engine never makes it. | P1 / P2 | → P0 if intent is "push"/"staging"/"release" |

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

**`/investigate`** **[INJECTED 2026-07-07, resolves helpdesk-tickets/CLOSED_20260707_triage-missing-investigate-row_workflow.md]**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| `<FAILURE_SIGNALS>` contains evidence of unexplained behavior with no root cause on record | P2 | → P1 if intent is "debug" or "figure out" |
| Journal or commit messages describe an error, wrong output, or unexpected state with no corresponding investigation report | P2 | |
| Intent phrasing matches "something is broken and I don't know why," "walk me through what happened," or "don't fix it yet, just tell me what's wrong" | P1 (intent-driven) | |
| Intent phrasing matches "treat this like a crime scene" (explicit invocation) | P0 (intent-driven) | |

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
| `dependency_graph.json` in `manifest/` is older than 14 days (stale governance data) | P2 | → P1 if intent includes "governance" or "lint" |
| Run `lint_workflows.py --quiet` — if CRITICAL > 0, recommend immediate `/harden-workflow` on affected workflows | P0 | |

**`/quality` (audit trigger)** **[INJECTED 2026-05-25]**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| `.workflow_state/quality_witness.log` exists AND has 25+ entries with no `## REVIEWED`/`[REVIEWED]` marker after the last 25 — **[v4 wiring 2026-06-02]** deterministic source: `python3 ~/blueprint-workflows/scripts/quality/quality_audit.py --workspace . --output-json` → `ledger.audit_trigger == "P3"` (replaces hand-counting) | P3 | → P2 if intent includes "audit" or "quality" |
| `.workflow_state/quality_witness.log` exists AND has entries showing `findings=0` for 5+ consecutive outputs | P2 | Potential Hallucinated Success in self-critique — review quality protocol compliance |
| Intent includes "quality audit" or "review quality" | P2 (intent-driven) | |

**`/design-orchestrator`** **[INJECTED 2026-07-06, Sovereign Redesign Cluster Stage 3, PILLAR_02 PR 02-06]**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| Stated design intent (new feature, redesign, architectural change) with no governing DESIGN_*.md and no implementation-plan.md yet | P1 | → P0 if intent is "design" or "architect" or "plan the approach" |
| A prior ad-hoc DESIGN exists with no Build Ingestion Manifest section (pre-dates this workflow) | P3 | Retrofit optional, not required — /execute-build's native trigger only needs a `## PR Plan`, not a full Manifest |
| Intent includes "design" or "architect this" | P1 (intent-driven) | |

**`/implementation-plan`** **[INJECTED 2026-05-23]**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| No `implementation-plan.md` in project root AND `concept.md` exists AND intent includes "plan" or "implement" | P1 (intent-driven) | |
| `implementation-plan.md` exists but is stale (last modified > 14 days) AND active development ongoing | P3 | |
| Intent includes "plan", "strategy", or "design the approach" | P2 (intent-driven) | |

**`/implementation-plan --workstreams`** **[INJECTED 2026-05-23]**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| `concept.md` exists but `implementation-plan.md` has no workstream definitions (no Workstream A/B/C sections) | P2 | → P1 if intent is "start workstreams" or "design workstreams" |
| `<WORKSTREAM_STATE>` shows all three workstreams COMPLETE AND PM audit done (audit pointer present in implementation-plan.md) — next iteration needed | P2 | |
| Intent includes "design workstreams" or "plan workstreams" or "new iteration" | P1 (intent-driven) | |
| Architect Directive pasted by user with no corresponding workstream definitions in implementation-plan.md | P0 | |

**`/workstream`** **[INJECTED 2026-05-23]**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| `implementation-plan.md` has workstream definitions AND `<WORKSTREAM_STATE>` shows NOT STARTED for one or more workstreams | P1 | → P0 if intent is "execute" or "start building" |
| `<WORKSTREAM_STATE>` shows BLOCKED for any workstream with no PENDING escalation in DECISIONS.md | P1 | |
| `<WORKSTREAM_STATE>` shows IN PROGRESS but last updated > 3 days ago for any workstream | P2 | |
| Intent includes "execute workstreams" or "start workstreams" with workstream definitions present | P0 (intent-driven) | |

**`/implementation-plan --audit --workstreams`** **[INJECTED 2026-05-23]**
| Trigger | Priority | Intent Modifier |
|---------|----------|-----------------|
| `<WORKSTREAM_STATE>` shows all three workstreams COMPLETE | P1 | → P0 if intent is "audit" or "review work" |
| `<WORKSTREAM_STATE>` shows two or more workstreams COMPLETE, one IN PROGRESS for 3+ days | P2 | |
| `<WORKSTREAM_STATE>` shows PENDING escalations in DECISIONS.md with all workstreams COMPLETE | P0 | |
| Intent includes "audit workstreams" or "review all work" or "PM review" | P1 (intent-driven) | |

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

**[ENGINE-BACKED — ADDED 2026-07-07, implementation-plan.md Phase 4.5]** Trigger Matrix Completeness Gate — after drafting the report above, before presenting it to the user, confirm mechanically that every Trigger Matrix workflow is actually mentioned (STRICT RULES 3 and 9 both name this as the same guarantee, restated a third time by Phase 1's own "Completeness requirement" — this gate is the structural backing all three already ask for):

```bash
python3 ~/blueprint-workflows/scripts/triage/triage_audit.py --workspace . --report-text "{DRAFT_REPORT_TEXT}" --output-json
```

Read `completeness.missing_from_report` from the JSON. If non-empty: the draft is incomplete — add the missing workflow(s) to "NO ACTION NEEDED" (with genuine trigger evaluation, not a rubber-stamp addition to pass the check) or to RECOMMENDATIONS if a trigger genuinely fires, before presenting the report. If the engine is unavailable: fall back to manually cross-checking the report against the Trigger Matrix's block headers below; note the fallback in the report.

**What this gate does NOT verify, stated honestly**: mechanical presence of a workflow's name in the report text is not proof its triggers were evaluated with genuine rigor — a name could still be pasted into "NO ACTION NEEDED" without real evaluation. This gate closes the narrower, purely mechanical failure STRICT RULES 3/9 actually describe (a workflow silently missing from the report entirely), not the deeper judgment failure of a shallow evaluation. Do not read a `missing_from_report: []` result as proof of rigor — only as proof of mention.

**[STAGE 1a — TRIAGE_RECEIPTS.md writer — INJECTED 2026-07-06, pr-05-02, PILLAR_05, /nodelete]**
After emitting the Triage Report to chat, persist a verbatim report block using atomic append (exact heredoc parity to BUILD_RECEIPTS in execute-build.md:350). Use workspace root for the receipts dir. This implements triage handover persistence (P5 / P1 cross; on user signals like "wrap up", "handover", "close session", "end", "reset", "finish" in SESSION_INTENT or at session end; always safe to emit as the triage report itself is the handover record).

```bash
mkdir -p ".workflow_state/receipts"
cat >> ".workflow_state/receipts/TRIAGE_RECEIPTS.md" << RECEIPT_EOF
## $(date +%Y-%m-%d) — /triage — REPORT
- Phase/Stage: TRIAGE
- Grade/Status: REPORT ISSUED
- Files: N/A
- Commit: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
---
RECEIPT_EOF
```
If `cat >>` fails: print `[TRIAGE-RECEIPT] WARNING: could not write TRIAGE_RECEIPTS.md — {error}` and continue. Do not halt triage.

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
     └─ Phase 0b/0c → scripts/triage/triage_audit.py (task/phase state via phase_status.py, receipt coverage via coverage.py)
     └─ Phase 2      → scripts/triage/triage_audit.py (Trigger Matrix Completeness Gate)
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
6. **2026-05-25**: `[INJECTED — Quality Witness audit trigger, /nodelete]` New `/quality` audit trigger block added to Trigger Matrix. Fires P3 when `.workflow_state/quality_witness.log` accumulates 25+ unreviewed entries. Fires P2 when 5+ consecutive `findings=0` entries detected (potential Hallucinated Success in self-critique). Enables autonomous quality audit discovery without user remembering to check. Standard Version: 3.
7. **2026-05-23**: `[INJECTED — Multi-Agent Workstream Orchestration triggers, /nodelete]` Four new Trigger Matrix blocks added: `/implementation-plan` (base command — was absent from matrix entirely), `/implementation-plan --workstreams` (workstream design triggers), `/workstream` (workstream execution triggers), `/implementation-plan --audit --workstreams` (workstream audit triggers). Phase 0h added: Multi-Agent Workstream State collection step — reads `WORKSTREAM_STATUS.md`, `DECISIONS.md`, and checks `implementation-plan.md` for workstream definitions, stores as `<WORKSTREAM_STATE>`. All existing content preserved per /nodelete. Standard Version: 3.
8. **2026-06-02**: `[INJECTED — /quality Option-F wiring, /nodelete]` The `/quality` P3 audit trigger now names its deterministic source: `scripts/quality/quality_audit.py --workspace . --output-json` → `ledger.audit_trigger == "P3"`, replacing the hand-count heuristic (the engine recognizes both `## REVIEWED` and `[REVIEWED]` reset markers). All prior trigger wording preserved per /nodelete. Standard Version: 3.
9. **2026-06-02**: `[INJECTED — /iterate-test Mock-Trap Detector wiring (Verification-Spine Campaign), /nodelete]` The `/iterate-test` Trigger Matrix block gains a deterministic-call row: `scripts/iterate/iterate_audit.py --workspace . --output-json` — a `MOCK_TRAP_CANDIDATE` (`verdict_hint: FINDINGS`) in a recently-built stage's test promotes the recommendation from receipt-absence to actual-finding evidence (P1; `HARDCODED_ASSERTION` → P2), mirroring the existing `harden_audit.py` and `lint_workflows.py --quiet` precedents. One-directional: the engine surfaces candidates; the PRIMARY/INFRASTRUCTURE classification stays with /iterate-test Step 4b. All prior trigger wording preserved per /nodelete. Standard Version: 3.
10. **2026-07-06**: `[INJECTED — pr-05-02, PILLAR_05, /nodelete]` Added TRIAGE_RECEIPTS.md emission (atomic cat >> heredoc after report, matching BUILD_RECEIPTS format exactly). Added GLOSSARY entry, frontmatter produces, Phase 0 consumption read of TRIAGE_RECEIPTS.md. Implements triage persistence + handover record per PILLAR_05 §4.5. Smallest additive change; no overwrite.
11. **2026-07-06**: `[FIXED — receipt heredoc evaluation, Sovereign Redesign Cluster Stage 2, /nodelete]` The STAGE 1a `TRIAGE_RECEIPTS.md` writer (added in entry 10, same day) used a quoted heredoc delimiter (`<< 'RECEIPT_EOF'`), which suppresses ALL `$()` command substitution inside the block. Discovered live the first time this pattern was actually exercised end-to-end: `$(date +%Y-%m-%d)` and `$(git rev-parse --short HEAD ...)` were never evaluated, and the resulting `TRIAGE_RECEIPTS.md` entry contained the literal shell syntax as text instead of a real date/commit hash. Fixed by unquoting the delimiter (`<< RECEIPT_EOF`); confirmed no backticks exist in the receipt body (unquoting a heredoc also enables backtick command substitution, a second failure mode if present — checked, absent). Verified with a live re-run producing a correctly-evaluated entry. The same defect, from the identical documented pattern, was found in and fixed for `execute-build.md`'s BUILD_RECEIPTS writer, `document.md`, `soc.md`, `harden.md`, and `iterate-test.md` — see their own Change Logs. `HARDEN_GRADES.md`'s and `DOCS_RECEIPTS.md`'s existing entries were checked and do not carry the defect (prior agents evidently pre-substituted real values by hand rather than relying on live evaluation) — this session's own first `BUILD_RECEIPTS.md` and `TRIAGE_RECEIPTS.md` entries are the first real instances of the bug actually manifesting in a persisted file, corrected in place via appended, dated notes per /nodelete.
12. **2026-07-06**: `[INJECTED — Sovereign Redesign Cluster Stage 3, PILLAR_02 PR 02-06, /nodelete]` Added a Trigger Matrix block for `/design-orchestrator`: fires P1 (P0 if intent names "design"/"architect") when a stated design intent has no governing DESIGN_*.md or implementation-plan.md yet. Pairs with the workflow's own creation this same stage.
13. **2026-07-07**: `[BUILT — Triage Evidence Engine, Verification-Spine Upgrade, implementation-plan.md Phase 4.4-4.5, /nodelete]` Ran Honest-Design Discipline fresh against this file — result staged at `docs/compression-staging/triage-honest-design.md`. **Finding**: `/triage` already reuses three existing engines directly in its Trigger Matrix (`harden_audit.py`, `iterate_audit.py`, `quality_audit.py`) plus `lint_workflows.py --quiet` — confirmed as a working precedent, no correction needed there. Two Phase 0 steps duplicated engine logic that exists elsewhere: 0b hand-counted what `scripts/focus/phase_status.py` already computes; 0c hand-checked what `scripts/receipt/coverage.py`'s `compute_coverage()` already computes. Neither needed new code — pure wiring. One genuinely new mechanical check: **Trigger Matrix completeness**, directly defending STRICT RULES 3 and 9 (both independently state the same guarantee — omitting a workflow from the report is Hallucinated Success) and Phase 1's own injected "Completeness requirement," which restates it a third time. **Built `scripts/triage/`**: a read-only engine (`matrix_completeness.py` — `extract_matrix_workflows()` regex-parses `triage.md`'s own `### Trigger Matrix` block headers, scoped to that section only; `check_report_completeness()` reports which matrix workflows are absent from a given report text as a pure set-difference; `reporter.py`; `triage_audit.py` CLI, which also directly imports and calls `phase_status.build_phase_status_report()` and `receipt.coverage.compute_coverage()` rather than re-parsing either). 13 new tests (`scripts/tests/test_triage_evidence.py`) including a read-only invariant test; caught and fixed a real regex bug during test-writing — the `/quality` header's annotation ("(audit trigger)") sits INSIDE the same bold span as the name, so the closing `**` does not immediately follow the name's backtick the way plain headers' does; the original regex required exactly that, silently missing every annotated header. Fixed by dropping the trailing `**` requirement, anchoring only on "line starts with `**` immediately followed by a backtick-wrapped name." Full suite 355/355 passing (up from 342 pre-task). Live-run against this actual `triage.md` confirmed correct extraction (25 distinct workflow entries, correctly distinguishing flagged variants like `/implementation-plan --workstreams` from the bare `/implementation-plan` row, correctly deduping `/focus-plan`'s two annotated blocks to one entry). **Wired**: Phase 0b (task/phase state via engine), Phase 0c (receipt state via engine), and a new Trigger Matrix Completeness Gate in Phase 2 (before the report is presented) — each keeps an explicit manual-fallback instruction and an explicit, honest statement of what the completeness gate does NOT verify (mechanical presence of a name is not proof of genuine trigger-evaluation rigor). GLOSSARY term added (Triage Evidence Engine). `scripts/triage/triage_audit.py` added to frontmatter `dependencies`. No STRICT RULE added — existing Rules 3/9 already require the guarantee this engine backs; the engine changes how completeness is confirmed, not what the rules require. Frontmatter: version 3→4, `last_hardened` 2026-07-07, `content_hash` recomputed via `--fix-hashes`. `strict_rule_count` unchanged at 11. Resolves `helpdesk-tickets/CLOSED_20260707_triage-engine-gap_workflow.md`.
14. **2026-07-07**: `[ADDED — /investigate Trigger Matrix row, resolves helpdesk-tickets/CLOSED_20260707_triage-missing-investigate-row_workflow.md]` `investigate.md`'s own INTEGRATION section declared 7 `/triage triggers` conditions, but no reciprocal row existed in this file's Trigger Matrix — a one-directional documentation gap: `/investigate` believed it was triage-routed, `/triage` had never actually been taught to route to it. Added a `/investigate` block (after `/redteam`) translating the 7 declared conditions into 4 trigger rows: two mechanical (`<FAILURE_SIGNALS>` evidence of unexplained behavior; journal/commit evidence of an unresolved error) and two intent-driven (general "something's broken"/"walk me through" phrasing at P1; the explicit "treat this like a crime scene" invocation phrase at P0, matching `/investigate`'s own stated explicit-invocation semantics). Verified via `scripts/triage/matrix_completeness.py`'s `extract_matrix_workflows()`: `/investigate` now present, 26 distinct entries (up from 25). Frontmatter: version 4→5, content_hash recomputed, last_hardened 2026-07-07.
