# Workspace-Level Divergence Findings — 2026-05-25
# Source: /divergence on ~/blueprint-workflows as a whole
# Status: ALL APPROVED — implementation planning in progress
# Context: 32 workflows, 400KB protocol text, 3 runtimes, 10-iteration field test complete

---

## Divergence #1 — The Living Specification (Workflow Linter)
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

## Divergence #2 — The Sovereign Onboarding Agent
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

## Divergence #3 — The Workflow Dependency Graph
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
