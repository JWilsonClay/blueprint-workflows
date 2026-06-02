# Workspace-Level Divergence Findings — 2026-05-25
# Source: /divergence on ~/blueprint-workflows as a whole
# Status: ALL APPROVED — implementation planning in progress
# Context: 32 workflows, 400KB protocol text, 3 runtimes, 10-iteration field test complete

---

## Divergence #1 — The Living Specification (Workflow Linter) [COMPLETED]
**Vector:** Inversion — workflows as testable codebase
**Status:** APPROVED — first implementation priority
**Nuance from user:** Explore non-human-readable mechanisms for machine verification

### Core Idea
`scripts/suite/lint_workflows.py` — a protocol linter that treats .md workflow files as source code and verifies internal consistency, cross-references, structural requirements, and STRICT RULE integrity.

### Basic Checks (human-readable content scanning)
- Every cross-workflow reference (`/workstream`, `/implementation-plan`, etc.) resolves to an actual file in `claude-commands/`
- Every GLOSSARY term is used in the workflow body (orphan term detection)
- STRICT RULE numbering is sequential (no gaps, no duplicates after injection sessions)
- Every `### Change Log` entry has a date in `YYYY-MM-DD` format
- STRICT RULES that reference phases (e.g., "Phase 7d") — verify that phase exists in the same file
- Frontmatter `description:` is present, non-empty, and syntactically valid YAML
- HOW TO BEGIN section exists
- INTEGRATION section exists
- Symlink at `~/.claude/commands/<name>.md` exists and points correctly
- File size tracking — flag files exceeding 50KB

### Non-Human-Readable Mechanisms (user's nuance — EXPAND)
The user asked: "are there portions that don't need to be human-readable? What could exist to aid lint_workflows.py?"

**Frontmatter expansion possibilities:**
Current frontmatter is minimal:
```yaml
---
description: "one line"
---
```

Could expand to include machine-readable metadata:
```yaml
---
description: "one line"
version: 3
grade: Sovereign
last_hardened: 2026-05-25
content_hash: sha256:abc123...
dependencies:
  - /implementation-plan
  - /workstream
  - /triage
triggers:
  - /triage
  - /secretary
produces:
  - .workflow_state/handoffs/WORKSTREAM_*.md
  - .workflow_state/PM_OVERSIGHT_REPORT_*.md
consumes:
  - implementation-plan.md
  - WORKSTREAM_STATUS.md
  - DECISIONS.md
type: execution | behavioral-modifier | meta | audit | documentation
strict_rule_count: 24
phase_count: 5
flags:
  - --claude
  - --gemini
  - --grok
  - --pm
---
```

**Content hashing for verification:**
- `content_hash: sha256:...` in frontmatter — computed from the workflow body (excluding frontmatter itself and Change Log)
- The linter computes the hash and compares — if mismatch, the workflow was modified without updating the hash
- This catches "silent edits" — changes made outside of /harden-workflow that bypass the Change Log
- Hash would be updated by /harden-workflow at the end of every hardening session

**Inline machine-readable markers:**
- `<!-- PHASE:2.5 -->` before each phase heading — the linter counts and validates phase sequencing without parsing markdown headers
- `<!-- STRICT_RULE:14 -->` before each rule — the linter validates numbering mechanically
- `<!-- XREF:/implementation-plan -->` on cross-reference lines — explicit machine-readable link that the linter validates
- `<!-- DEPRECATED:2026-05-24 -->` on retired content — the linter can report how much deprecated content remains

**Workflow type classification:**
| Type | Examples | Linter behavior |
|------|---------|-----------------|
| `execution` | /workstream, /execute-build, /soc | Must have phases, structured output, STRICT RULES |
| `behavioral-modifier` | /quality, /personality, /nodelete | Must have STRICT RULES, no phases required |
| `meta` | /harden-workflow, /triage, /secretary | Must reference other workflows, must have INTEGRATION |
| `audit` | /investigate, /redteam, /receipt-check | Must produce structured output, must be read-only |
| `documentation` | /document, /retrospective, /provenance | Must have append-only discipline |

The type determines which structural checks the linter applies — a behavioral modifier doesn't need phases, but an execution workflow does.

### Script Architecture
```
scripts/suite/
  lint_workflows.py     # CLI entry point
  checks/
    frontmatter.py      # YAML validation + hash verification
    structure.py        # Phase/STRICT RULE/GLOSSARY/HOW TO BEGIN presence
    references.py       # Cross-workflow reference resolution
    consistency.py      # STRICT RULE numbering, term usage, phase references
    symlinks.py         # Symlink validation for all 3 runtimes
  __init__.py
```

Invocation:
```bash
python ~/blueprint-workflows/scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows
python ~/blueprint-workflows/scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows --fix-hashes  # recompute content hashes
python ~/blueprint-workflows/scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows --file workstream.md  # single file
```

### Governance Integration
- /harden-workflow: run linter after every hardening session before emitting certificate
- /triage: trigger when linter hasn't been run in 14+ days
- Pre-commit hook potential: run linter before every git commit to blueprint-workflows
- This IS the governance layer for the governance layer

### Open Questions
- How much frontmatter expansion is worth the maintenance cost? Every new field must be kept current.
- Should content hashes include or exclude the Change Log? (Excluding means the hash only changes when protocol content changes, not when history is appended.)
- Should the linter produce a structured report file or just stdout? (Report file enables /triage to read it.)
- Should non-human-readable markers (HTML comments) be injected into existing workflows now, or only into newly created/hardened workflows going forward?

---

## Divergence #2 — The Sovereign Onboarding Agent [COMPLETED]
**Vector:** Future User — graduated entry path
**Status:** APPROVED — DEFERRED to after #1 and #3
**Location:** TODO list — build after linter and dependency graph exist

### Core Idea
`/onboard` workflow — a single command that reads workspace state and produces a 2-page situation-aware startup brief for any new agent or human entering the workspace for the first time.

### What It Would Produce
```
ONBOARD BRIEF — [workspace name] — [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKSPACE TYPE: [governance / project / hybrid]
KEY FILES: [the 3-5 files to read first]
STANDARD PIPELINE: [the workflow sequence for this workspace type]
ACTIVE STATE: [from /triage — what needs attention now]
FAILURE PATTERNS: [from registry — what to watch for]
DO FIRST: [the single most important action]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Dependencies
- Depends on Divergence #3 (dependency graph) to know which workflows matter for this workspace
- Depends on Divergence #4 (failure pattern registry) to include pattern literacy
- Build AFTER these two exist

### Open Questions
- Should /onboard be part of /sentinel (session-init monitor) or standalone?
- Should it detect "first time in this workspace" automatically, or be user-invoked?

---

## Divergence #3 — The Workflow Dependency Graph [COMPLETED]
**Vector:** Scale distortion — what breaks at 64 workflows
**Status:** APPROVED — second implementation priority (after linter)
**User nuance:** How is it invoked? Who references it? What references it? Must be autonomous.

### Core Idea
A machine-readable dependency graph mapping every workflow's inputs, outputs, triggers, and cross-references. Generated automatically, updated by /harden-workflow.

### File: `manifest/DEPENDENCY_GRAPH.md` (human-readable) + `manifest/dependency_graph.json` (machine-readable)

### Graph Structure (per workflow)
```json
{
  "/workstream": {
    "reads": ["implementation-plan.md", "WORKSTREAM_STATUS.md", "DECISIONS.md", "concept.md"],
    "writes": [".workflow_state/handoffs/WORKSTREAM_*.md", ".workflow_state/PM_OVERSIGHT_REPORT_*.md", "ITERATION_LEDGER.md"],
    "triggers": ["/implementation-plan --audit --workstreams"],
    "triggered_by": ["/triage", "/implementation-plan --workstreams"],
    "references": ["/implementation-plan", "/helpdesk-tickets", "/retrospective"],
    "referenced_by": ["/triage", "/implementation-plan"],
    "type": "execution",
    "flags": ["--claude", "--gemini", "--grok", "--pm"]
  }
}
```

### Who References It (Autonomous Integration)
| Consumer | How It Uses the Graph | Trigger |
|----------|----------------------|---------|
| `/harden-workflow` | After hardening workflow X, check graph for all workflows that reference X → flag them for potential re-certification | Every hardening session |
| `lint_workflows.py` | Validate cross-references against graph — catch orphan references and broken links | Every linter run |
| `/triage` | When recommending a workflow, note its dependencies ("run /focus-plan before /execute-build") | Every triage scan |
| `/divergence` | Use the graph to identify isolated workflows (no inbound references = candidate for divergence or retirement) | On demand |
| `/onboard` (future) | Read graph to determine which workflows matter for the current workspace | On demand |
| `/canvas` | Export graph as visual architecture diagram | On demand |

### Generation Mechanism
Two options:
1. **Script-generated:** `lint_workflows.py --generate-graph` scans all workflow files, parses INTEGRATION sections and cross-references, outputs `dependency_graph.json`
2. **Frontmatter-declared:** each workflow declares its dependencies in expanded frontmatter (see Divergence #1), the graph is assembled from frontmatter

**Recommendation:** Both. Frontmatter is the declaration (what the workflow SAYS it depends on). Script scan is the verification (what it ACTUALLY references). Mismatches are linter findings.

### Autonomous Update Protocol
- `lint_workflows.py` regenerates the graph on every run
- `/harden-workflow` runs the linter (and thus regenerates the graph) after every hardening session
- The graph is always current because the linter is run frequently
- If the graph is stale (not regenerated in 14+ days), /triage flags it

### Open Questions
- Should the graph be committed to git, or generated on-the-fly each time?
- Should the JSON be in `manifest/` (alongside WORKFLOW_MANIFEST.md) or in `.workflow_state/`?
- How granular should the "references" be? Per-workflow, per-phase, or per-STRICT-RULE?

---

## Divergence #4 — The Failure Pattern Registry
**Vector:** Domain transplant — immunology antibody library
**Status:** APPROVED — implementation after linter and graph
**User nuance:** What workflow references it? How does it become context-aware autonomously?

### Core Idea
`manifest/FAILURE_PATTERN_REGISTRY.md` — a single-source catalog of every named failure pattern, its definition, observed instances, countermeasures, detection methods, and validation status.

### Registry Format (per pattern)
```markdown
## [Pattern Name]
**Definition:** [one-line signature]
**First Observed:** [date, project, iteration]
**Recurrences:** [list with dates and projects]
**Countermeasure:** [which workflow, which rule, which mechanism]
**Detection Method:** [how /triage or /investigate finds it]
**Validated:** [YES — recurrence prevented / NO — untested / PARTIAL — reduced but not eliminated]
**References:** [which workflows mention this pattern in their STRICT RULES or GLOSSARY]
```

### Current Patterns to Consolidate
| Pattern | Currently Documented In | Countermeasure |
|---------|------------------------|----------------|
| Mock Trap | CLAUDE.md, role.md, /iterate-test | /iterate-test Step 4b Intelligence Bridge |
| Context Erosion | CLAUDE.md, role.md, PROCESS_LEARNINGS | Forced Context Refresh, pointer architecture |
| Hallucinated Success | CLAUDE.md, role.md, /redteam | Diff Oracle, Quality Witness |
| Ghost Logic | CLAUDE.md, role.md, /redteam | /redteam Phase 5 ForensicAuditor |
| Sound Effect Execution | CLAUDE.md, role.md, /iterate-test | /iterate-test GLOSSARY |
| Calibration Gaming | PROCESS_LEARNINGS (2026-05-25) | Remove calibration from agent-facing instructions |
| Grade Fraud | role.md, /harden-workflow | /harden-workflow STRICT RULE 13 |
| Platform Architecture as Failure Vector | PROCESS_LEARNINGS (2026-05-25) | Platform Invocation Requirement |

### Who References It (Autonomous Integration)
| Consumer | How It Uses the Registry | Trigger |
|----------|------------------------|---------|
| `/triage` Phase 0g | Failure pattern surface scan — currently checks git messages for keywords. Enhanced: check against registry patterns for more precise matching. | Every triage scan |
| `/investigate` | When investigating failures, cross-reference against registry for known pattern matching. "Does this match a known pattern?" becomes a lookup, not a discovery. | Every investigation |
| `/redteam` | Use registry as the adversarial checklist — verify each pattern's countermeasure is active in the target workspace. | Every red team audit |
| `/retrospective` Phase 3 | Pattern identification currently reads PROCESS_LEARNINGS.md. Enhanced: also read registry for recurrence checking. | Every retrospective |
| `/harden-workflow` Phase 10 | Ecosystem Immunity Layer draws antibodies from the registry — currently undefined source. Registry becomes the formal antibody library. | Every immunity scan |
| `/onboard` (future) | Include top 5 most-recurrent patterns in the onboarding brief as "failure literacy." | On demand |
| `~/.claude/CLAUDE.md` | Currently contains the failure pattern table. Could be simplified to: "see ~/blueprint-workflows/manifest/FAILURE_PATTERN_REGISTRY.md for full definitions." | Session start |

### Autonomous Update Protocol
- `/retrospective` Phase 3: when a new pattern is identified or a recurrence is documented, append to the registry (not just PROCESS_LEARNINGS.md)
- `/harden-workflow --ticket`: when a ticket's root cause matches a registry pattern, link the ticket to the pattern entry
- The registry is append-only for pattern definitions. Countermeasure and validation fields are updated as fixes are deployed and tested.

### Open Questions
- Should the registry live in `manifest/` (alongside the workflow manifest) or at the workspace root?
- Should CLAUDE.md's failure pattern table be replaced with a pointer to the registry, or kept as a summary with the registry as the full reference?
- Should each pattern have a unique ID (FP-001, FP-002) for cross-referencing in tickets and STRICT RULES?

---

## Synthesis: Implementation Order

1. **Divergence #1 (Linter)** — first, because it's the foundation. The linter validates everything else. It also generates the dependency graph (Divergence #3).
2. **Divergence #3 (Dependency Graph)** — second, generated by the linter. Once the graph exists, /harden-workflow and /triage can reference it.
3. **Divergence #4 (Failure Pattern Registry)** — third, consolidation of existing content. Referenced by /triage, /investigate, /retrospective, /redteam.
4. **Divergence #2 (Onboarding)** — last, because it depends on all three above to produce a useful brief.

## V2 Frontmatter Deferred Items (Access on next metadata upgrade)

**[DEFERRED 2026-05-25 — Frontmatter Divergence D2/D3/D4 partial]**

The following fields were approved but deferred to v2 to keep the initial schema manageable. When the v1 schema is stable and the linter is operational, implement these:

1. **`injection_history`** — Structured list of injection sessions (date, source, items_added). Detects injection-without-validation drift. Source: Frontmatter Divergence #2 (Injection Lineage Chain).
2. **`last_validated`** — Date of most recent holistic validation (distinct from `last_hardened`). Source: Frontmatter Divergence #2.
3. **`total_injections`** — Count of injection sessions. Linter flags >10 injections without re-validation. Source: Frontmatter Divergence #2.
4. **`token_estimate`** — Approximate token cost to read + execute. Requires measurement. Source: Frontmatter Divergence #3 (Agent Comprehension).
5. **`phase_depth`** — Maximum sub-step nesting depth. Higher = more context retention needed. Source: Frontmatter Divergence #3.
6. **`invocation_modes`** — Full structured mode definitions with flag combinations and phase routing. Enables auto-generated help and /triage exact recommendations. Source: Frontmatter Divergence #4 (Invocation Signature).

**Autonomous access:** `/harden-workflow` should check this section when upgrading frontmatter schemas. `/triage` should flag this section when the v1 linter has been operational for 30+ days without v2 implementation.

---

## Meta-Observation: Sovereign Self-Governance

The suite has reached the complexity threshold where it needs the same infrastructure it provides to its projects:
- **Linter** = `/harden` for workflows (automated quality verification)
- **Dependency Graph** = file ownership boundaries for workflows (impact analysis)
- **Failure Pattern Registry** = Diff Oracle for process failures (ground truth lookup)
- **Onboarding** = Pre-Execution Mandate for human newcomers (context refresh)

The tools exist. They just haven't been turned inward.

---

## Divergence #5 — The Workflow Health Dashboard (Gap Analysis Pass 2)
**Vector:** Inversion — machine-readable data exists but no human-readable synthesis
**Status:** APPROVED — ON HOLD
**Source:** /divergence gap analysis, 2026-05-25 (second pass after full hardening session)

### Core Idea
A `lint_workflows.py --dashboard` mode that produces a single-page visual summary synthesizing all governance data: suite health score, workflow count by grade/type, dependency graph as ASCII, top linter findings, platform coverage status, stale hash/checkpoint alerts, quality witness accumulation, and iteration trend data.

### Why It Matters
The suite now has rich machine-readable data (dependency_graph.json, v1 frontmatter, HARDEN_GRADES.md, quality_witness.log, ITERATION_LEDGER.md) but no composite view. The user must run 3+ tools and mentally compose the results. A dashboard gives "suite health in one glance" from one command.

### Implementation Notes
- New mode in `lint_workflows.py` — reads existing data sources, produces formatted terminal output
- Data sources: frontmatter (grade/type counts), dependency_graph.json (edge counts, orphan detection), HARDEN_GRADES.md (script coverage), linter findings (CRITICAL/WARNING counts), quality_witness.log (entry count + review status)
- Output: structured ASCII dashboard, ~40 lines, scannable in 15 seconds
- Complexity: LOW-MEDIUM (aggregation of existing data, no new collection)

### Prerequisites
None — all data sources already exist. Can be built independently.

---

## Divergence #6 — The Workflow Test Runner (Gap Analysis Pass 2)
**Vector:** Constraint removal — workflows are untestable → workflows are testable
**Status:** APPROVED — ON HOLD
**Source:** /divergence gap analysis, 2026-05-25 (second pass)

### Core Idea
`scripts/suite/test_workflows.py` — behavioral smoke tests that invoke each workflow in a sandboxed context and verify the output contains expected structural markers (section headers, required fields, format compliance). Treats workflows as programs with entry points, not just documents to read.

### Why It Matters
The adversarial audit identified behavioral testing as the biggest verification gap. The linter checks structure (does the file HAVE the right sections?). The test runner checks behavior (does the workflow PRODUCE the right output when invoked?). A frontmatter change that breaks YAML parsing in a way the linter doesn't catch would only surface when a user tries to invoke the workflow. The test runner catches it proactively.

### Implementation Notes
- Define "expected output markers" per workflow type: execution workflows produce structured output blocks, behavioral modifiers produce nothing (silent activation), meta workflows produce reports
- Sandbox: run each workflow with a minimal synthetic workspace (temp directory with concept.md, tasks.md stubs)
- Verify: HOW TO BEGIN parses correctly, Phase 0 runs without error, structured output template appears in output
- NOT full execution — activation verification only. 5-10 seconds per workflow, not minutes.
- Complexity: MEDIUM-HIGH (requires defining expected behavior per type, building sandboxed execution)

### Prerequisites
- Linter frontmatter `type` field (DONE — all 33 workflows have type classification)
- Understanding of which workflows are safe to invoke in a sandbox (read-only workflows = safe; execution workflows = need mock targets)

---

## Divergence #7 — The Cross-Session Memory Bridge (Gap Analysis Pass 2)
**Vector:** Future User — agent starting session #100
**Status:** APPROVED — ON HOLD
**Source:** /divergence gap analysis, 2026-05-25 (second pass)

### Core Idea
A lightweight `SESSION_PRIORS.md` file per workspace (or a section in CLAUDE.md) capturing the top 5-10 operational lessons learned from the most recent sessions. Updated by /secretary at session close. Read by /onboard or /sentinel at session start. The bridge between "what we learned" and "what the next agent does differently."

### Why It Matters
PROCESS_LEARNINGS.md is cross-project institutional memory (narrative, appended by /retrospective). HANDOFF.md is per-session state (overwritten each session). Neither provides per-workspace operational intelligence that persists across sessions. The gap: an agent starting session #100 doesn't know what agents in sessions #95-99 learned about this specific workspace's quirks, patterns, and gotchas.

This is the macro version of Context Erosion — across sessions, not within them. Forced Context Refresh solves within-session. The Memory Bridge solves across-session.

### Implementation Notes
- File: `{workspace}/.workflow_state/SESSION_PRIORS.md` — append-only, top-N format
- Updated by: /secretary Phase 4 — extracts 1-3 key operational lessons from the session and appends
- Read by: /onboard Phase 1 (if present) and /sentinel Phase 2 (if present)
- Format: structured entries with date, lesson, and "applies when" context
- Max size: 50 entries. After 50, oldest entries are archived (not deleted) to keep the file scannable.
- The Failure Pattern Registry (Divergence #4, approved, unbuilt) would be a component of this — failure patterns are the failure-specific subset of cross-session memory. Building the Memory Bridge as the broader container would naturally house the registry.
- Complexity: LOW (small addition to /secretary; small read step in /onboard and /sentinel)

### Prerequisites
- /onboard (DONE — built this session)
- /secretary (DONE — already operational)
- /sentinel (DONE — already operational)

---

## Implementation Priority (all approved divergences)

| Priority | Divergence | Status | Depends On |
|----------|-----------|--------|------------|
| 1 | #1 Linter | ✅ COMPLETE | — |
| 2 | #3 Dependency Graph | ✅ COMPLETE (as dependency_graph.json) | #1 |
| 3 | #2 Onboarding | ✅ COMPLETE (/onboard built) | #1, #3 |
| 4 | #4 Failure Pattern Registry | ON HOLD | — (consolidation task) |
| 5 | #5 Health Dashboard | ON HOLD | #1 (linter exists) |
| 6 | #7 Memory Bridge | ON HOLD | #2 (/onboard), /secretary |
| 7 | #6 Test Runner | ON HOLD | #1 (linter type classification) |

Frontmatter divergences (Platform Compatibility, Injection Lineage, Comprehension Estimate, Invocation Signature) are tracked in the V2 Frontmatter Deferred Items section above.
