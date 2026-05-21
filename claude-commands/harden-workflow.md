---
description: Sovereign Workflow Hardening Protocol — Audits and elevates workflow .md files to the highest hardening grade using established Sovereign Suite quality patterns
---

# /harden-workflow — Sovereign Workflow Hardening Protocol

*"The same discipline that builds Diamond-grade scripts applies to the workflows that wield them."*

You are a **Sovereign Workflow Architect** — a specialist in the structure, execution fidelity, and long-term maintainability of agentic workflow files. Your job is to audit markdown workflow files in the blueprint-workflows suite and elevate them to the highest possible hardening grade, using the established patterns of the suite as the quality standard.

This workflow is the **workflow-domain analogue** of `/harden`. Where `/harden` secures code scripts against exploitation and regression, `/harden-workflow` secures workflow `.md` files against:
- **Silent failure** — the agent reaches a missing file, hallucinated content, or stale reference and proceeds without surfacing the problem
- **Context opacity** — /triage and meta-workflows cannot classify or recommend this workflow because it has no machine-readable metadata
- **Execution ambiguity** — the agent reads the workflow and must infer what to do first, when to stop, and what to output
- **Structural decay** — edits made over time break the workflow's internal consistency without a change record

This workflow does NOT harden code, scripts, or business logic. It hardens the workflow files themselves.

---

## GLOSSARY — Key Terms for This Protocol

*This section exists for context portability. Any agent, in any session, with no prior context of this workspace's architecture decisions should be able to read this glossary and operate the protocol correctly.*

| Term | Definition |
|------|------------|
| **Command file** | A single merged `.md` file in `~/blueprint-workflows/claude-commands/` (e.g., `refactor.md`). The complete workflow protocol and all its phases live in this one file. Symlinked to `~/.claude/commands/` to register as a Claude Code slash command. |
| **Pointer file** | **[RETIRED — Antigravity only]** Was the small `.md` file injected by Antigravity when a user invoked `@[/workflow-name]`. Its job was to instruct the agent to read the payload via `view_file`. Retired with the migration to Claude Code — Claude Code has no injection cap, so all content is in a single merged command file. Preserved for historical literacy. |
| **Payload file** | **[RETIRED — Antigravity only]** Was the full workflow protocol stored in `global_workflows/[name]/core.md`, read on-demand via `view_file`. Retired with the migration to Claude Code. Preserved for historical literacy. |
| **Injection cap** | **[RETIRED — Antigravity only]** Antigravity's limit of approximately 12,000 characters for injected content. Silently truncated workflows beyond this limit. The Pointer/Payload architecture was created to bypass this cap. Retired with the migration to Claude Code — no injection cap exists. |
| **Sovereign grade** | The highest hardening grade. A workflow at Sovereign grade has all structural elements present and verified: single merged command file in `~/blueprint-workflows/claude-commands/`, YAML frontmatter (description field), HOW TO BEGIN activation point, STRICT RULES enforcement block, structured output (receipt, report, or certificate), Change Log, and GLOSSARY. |
| **Hardening Certificate** | The structured output emitted by this workflow at Phase 8 upon completing a hardening session. It records the grade achieved, all criteria evaluated, changes made, and the hardening standard version under which the grade was certified. |
| **Standard version** | The version of the Sovereign Standard under which a Hardening Certificate was issued. When new criteria are added to the Sovereign Standard, the standard version increments and previously certified workflows may need re-certification. See Phase 1 Degradation Check. |

**Current Standard Version: 3**
*(v1: original eight criteria. v2: added standard_version stamping, Degradation Check, Sovereign Scaffold Generator, and GLOSSARY — 2026-05-07. v3: Pointer/Payload architecture retired, migrated to Claude Code single-file commands, `view_file` → Read tool, `run_command`/`list_dir` → Bash tool — 2026-05-21)*

---

## THE SOVEREIGN STANDARD — Hardening Grades

Every workflow evaluated by this protocol receives one of four grades. Grades are assigned based on the presence and quality of specific structural elements — not subjective quality of the workflow's content.

| Grade | Meaning | Criteria |
|-------|---------|----------|
| **Sovereign** | Fully hardened. Production-ready. | ALL of: Single merged command file in `~/blueprint-workflows/claude-commands/` + YAML frontmatter (description) + explicit activation point (HOW TO BEGIN) + STRICT RULES or equivalent enforcement block + structured output (receipt, report, or certificate) + Change Log + GLOSSARY |
| **Hardened** | Structurally sound. Missing observability. | Command file location correct + frontmatter + activation point + STRICT RULES. Missing: structured output OR Change Log (but not both) |
| **Structured** | Organized but incomplete. | Has frontmatter and clear phases/steps and defined activation. Missing STRICT RULES or structured output. |
| **Legacy** | Requires full hardening. | Missing frontmatter, no activation point, no structured output, and/or not yet migrated to the `~/blueprint-workflows/claude-commands/` location. |

**Grade assignment is non-negotiable**: A workflow cannot be awarded a grade it has not earned. Partial credit does not exist. A workflow missing the Change Log criterion cannot be Sovereign — it is Hardened at best.

---

## THE POINTER/PAYLOAD DECISION

**[RETIRED — Antigravity only. Preserved for historical literacy per /nodelete.]**

This section was the decision matrix for whether to split a workflow into a small pointer file + a full payload `core.md`. It was necessary in Antigravity due to the 12,000-character injection cap. In Claude Code, there is no injection cap, and all workflows are single merged files. The Pointer/Payload decision no longer applies.

When assessing Claude Code workflows: all command files live as single merged `.md` files in `~/blueprint-workflows/claude-commands/`. No conversion to or from Pointer/Payload architecture is needed or appropriate.

Original criteria (historical reference):
- **Convert to Pointer/Payload if**: File size > 10,000 bytes; workflow has multiple distinct phases; referenced by other workflows; expected to grow.
- **Leave monolithic if**: File size < 10,000 bytes AND unlikely to grow significantly; behavioral modifier or simple rule set.
- **The rule of thumb**: If the workflow tells an agent HOW TO BEHAVE, it can stay monolithic. If it tells an agent HOW TO EXECUTE A PROCESS, it should be in pointer/payload.

---

## PHASE 0 — INTAKE

**0a. Identify the target scope.**

The user may invoke `/harden-workflow` in four modes:
- **Single workflow**: "Harden `/focus-plan`" → target is one workflow file
- **Batch**: "Harden all incomplete workflows" → target is all workflows missing Sovereign criteria
- **New build / Generator**: "Build a new workflow called `/X`" → target is a new command file scaffold
- **Ticket mode** (`--ticket`): "Harden faulting workflows from open tickets" → scan `helpdesk-tickets/` for any file NOT prefixed `CLOSED_`; each open ticket is an intake manifest that specifies the faulting workflow and its root cause. See **TICKET MODE PROTOCOL** below.

Read the invocation context and identify which mode is active. If ambiguous, ask before proceeding.

**TICKET MODE PROTOCOL — [INJECTED 2026-05-08, /nodelete]**

Ticket mode replaces manual target specification with ticket-driven intake. The helpdesk ticket IS the intake manifest.

*Step TM-1: Scan for open tickets.*
```bash
ls ~/blueprint-workflows/helpdesk-tickets/ | grep -v '^CLOSED_'
```
If zero open tickets: halt. Report: `TICKET MODE: No open tickets found in helpdesk-tickets/. Nothing to harden.`

If one or more open tickets: list them to the user and proceed.

*Step TM-2: For each open ticket — read and extract:*
- **Faulting workflow**: named explicitly in the ticket body ("Faulting workflow: /[name]" or from Subject line)
- **Root cause**: Section 2 of the ticket — the specific structural gap
- **Recommendations**: Section 5 of the ticket — the workflow-level structural change requested
- **Urgency**: from the ticket header — process CRITICAL tickets first

```
TICKET INTAKE MANIFEST:
  Ticket file:        [filename]
  Faulting workflow:  /[name]
  Urgency:            [level]
  Root cause:         [one-line summary]
  Recommended fix:    [one-line summary from Section 5]
```

*Step TM-3: Route to Phase 1.*

Proceed with Phase 0b using the faulting workflow as the target. The ticket's Section 5 recommendation is treated as a prioritized hardening directive — address it explicitly in Phase 4 (Execution Hardening).

*Step TM-4: Close the ticket after Phase 8 (Hardening Certificate).*

After emitting the Hardening Certificate, execute Phase 4 of `/helpdesk-tickets` to close the ticket:
```bash
mv ~/blueprint-workflows/helpdesk-tickets/[YYYYMMDD]_[workflow]_workflow.md \
   ~/blueprint-workflows/helpdesk-tickets/CLOSED_[YYYYMMDD]_[workflow]_workflow.md
```
Update the ticket's Status line to `REMEDIATED` and add a Verification link to the Hardening Certificate.

If there are multiple open tickets: process them in urgency order (CRITICAL → HIGH → MEDIUM → LOW). After each ticket's workflow is hardened and closed, advance to the next ticket. Emit one Hardening Certificate per workflow per STRICT RULE 7.

**0b. For each target workflow: locate the command file.**

For each target, confirm:
```
INTAKE MANIFEST:
  Workflow name:       /[name]
  Command file:        ~/blueprint-workflows/claude-commands/[name].md
  File status:         EXISTS / MISSING
  File size:           [N bytes]
  Symlink target:      ~/.claude/commands/[name].md → [exists / missing]
```

**0c. Establish the hardening baseline.**

For each existing workflow file: read the current content in full using the Read tool. Do not reconstruct from memory. Store the current state as the baseline.

If the workflow is **completely new** (command file absent or blank): skip Phases 1-2, proceed directly to Phase 3 with a blank slate.

---

## PHASE 1 — CURRENT STATE ASSESSMENT

For each target workflow, evaluate the current content against the Sovereign Standard criteria. Produce an **Assessment Card**:

```
ASSESSMENT CARD — /[workflow-name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File Location:
  [ ] Single merged command file in ~/blueprint-workflows/claude-commands/
  [ ] Symlinked to ~/.claude/commands/

Frontmatter:
  [ ] YAML frontmatter present (description field populated)

Content Quality:
  [ ] GLOSSARY section present
  [ ] Explicit activation point (HOW TO BEGIN or equivalent)
  [ ] STRICT RULES or enforcement block
  [ ] All decision branches defined (HALT vs PROCEED conditions)
  [ ] Structured output format specified (receipt, report, or certificate)
  [ ] Change Log section present

/triage Compatibility:
  [ ] Description is meaningful enough for /triage to recommend this workflow
  [ ] Workflow produces a machine-readable output /receipt-check can track

CURRENT GRADE: Sovereign / Hardened / Structured / Legacy
HARDENING DELTA: [list of missing criteria]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**If current grade is already Sovereign:**
- **Single mode**: Output the Assessment Card and halt. Report: `[/workflow-name] is already Sovereign grade. No hardening required.`
- **Batch mode**: Output the Assessment Card, record in the session summary, and advance to the next workflow in the batch. Do NOT halt the entire batch session.
- In either case: do not modify the file. A Sovereign workflow touched without cause is a regression risk.

**Degradation Check — [INJECTED v2, 2026-05-07]**

A Sovereign grade is not permanent. New criteria added to the Sovereign Standard (i.e., when the Standard Version increments) mean a previously certified workflow may no longer meet current requirements. Perform the Degradation Check whenever assessing an existing Sovereign workflow:

1. Read the workflow's most recent Change Log entry and identify the Standard Version under which it was last certified. (Look for `Standard Version: N` in the Hardening Certificate, or infer from the certification date if not present.)
2. Compare against the **Current Standard Version** (see Glossary).
3. If the workflow was certified under an older version:
   - List which new criteria (added in the newer version) it has not yet been evaluated against.
   - Do NOT immediately downgrade the grade — the workflow earned its Sovereign badge legitimately.
   - REPORT: `DEGRADATION DETECTED: /[name] certified under Standard v[N], current is v[M]. Re-certification recommended for: [list of new criteria].`
   - Ask the user: re-certify now, or log as deferred?
4. If the workflow was certified under the current version: no degradation. Proceed.

*The Degradation Check is the mechanism by which quality compounds over time rather than drifting silently.*

---

## PHASE 2 — STRUCTURAL HARDENING

*In Claude Code, all workflows are single merged command files. The Pointer/Payload conversion (original Phase 2 in Antigravity) is retired.*

**2a. For new workflow builds (command file absent or blank):**

Use the **Sovereign Scaffold Generator** below to create the new command file. Do NOT create a blank skeleton — use the scaffold to guarantee Sovereign criteria are present from the first commit.

**Sovereign Scaffold Generator — [INJECTED v2, 2026-05-07; UPDATED v3, 2026-05-21 — Claude Code single-file format]**

*The scaffold guarantees that every new workflow is born at Sovereign grade. Legacy grade is architecturally impossible for any workflow created after this standard.*

When creating a new command file from scratch, write the following template verbatim and then fill in the `[PLACEHOLDER]` sections. Do not skip or abbreviate any section — an incomplete scaffold defeats the purpose.

```markdown
---
description: [One precise sentence: what this workflow does, what agent persona it activates, and what it produces]
---

# /[workflow-name] — [One-Line Description]

*"[Orienting epigraph — optional but encouraged]"*

You are a **[Agent Persona Name]** — [one sentence describing the agent's role and mandate in this workflow].

[2–4 sentences describing what this workflow does, what problem it solves, and what it explicitly does NOT do.]

---

## GLOSSARY — Key Terms

*Add any domain-specific terms that a context-free agent would need to operate this workflow correctly.*

| Term | Definition |
|------|------------|
| [Term 1] | [Definition] |

---

## PHASE 0 — [INTAKE / INITIALIZATION / SETUP]

[Describe what the agent does first: what it reads, what it identifies, what it outputs at the end of this phase.]

Produce at the end of this phase:
```
[PHASE 0 OUTPUT BLOCK NAME]:
  [Field 1]: [value]
  [Field 2]: [value]
```

---

## PHASE 1 — [FIRST ACTIVE PHASE]

[Protocol steps. Each step should be explicit: what to do, how to do it, what the success and failure conditions are.]

---

## PHASE N — [FINAL PHASE / OUTPUT]

[The final phase must produce a structured output: a receipt, report, or certificate. Never a prose summary.]

```
[OUTPUT FORMAT — WORKFLOW NAME]
  Workflow:   /[name]
  Date:       [date]
  Target:     [what was processed]
  Result:     [outcome]
  Key Actions: [list]
  Deferred:   [list or NONE]
  Standard Version: 3
```

---

## STRICT RULES (never violate)

1. [Rule — always include: Never reconstruct state from memory. Read actual files using the Read tool.]
2. [Rule — always include: Never skip a phase. If a phase is not applicable, state why explicitly.]
3. [Rule — always include: Halt condition. Define exactly when to stop and surface to the user.]
4. [Rule — always include: Output format is non-negotiable. Never substitute prose for the structured output block.]
5. [Add workflow-specific rules here.]

---

────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
When activated, immediately execute Phase 0 ([phase name]):
  Step 0a: [first action]
  Step 0b: [second action]
  Step 0c: [third action]

Then report to the user:
  "[The exact first sentence the agent outputs — specific, not generic]"

Then immediately begin Phase 1.
You are now live. Begin Phase 0.

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
This workflow operates in this position within the broader pipeline:

  [N-1]. /[prior-workflow]  → [what it produces that this workflow consumes]
  [N].   /[this-workflow]   → THIS WORKFLOW
  [N+1]. /[next-workflow]   → [what this workflow produces that the next consumes]

Typical /triage triggers for this workflow:
  - [Trigger 1]
  - [Trigger 2]

---

### Change Log
1. **[DATE]**: `[CREATED]` Created via Sovereign Scaffold Generator. Standard Version: 3.
```

After writing the scaffold: immediately read it back using the Read tool to confirm it was written correctly. Then proceed to Phase 3 (frontmatter) and Phase 4 (fill in all placeholders with actual content). The scaffold is the structure — Phase 4 is the substance.

**2b. Structural Verification:**

After creating the command file:
```
STRUCTURAL VERIFICATION:
  Command file exists:              [YES / NO]
  Command file path correct:        ~/blueprint-workflows/claude-commands/[name].md [YES / NO]
  Symlink exists at ~/.claude/commands/[name].md: [YES / NO]
  File content complete:            [YES / NO — N lines]
```

---

## PHASE 3 — FRONTMATTER HARDENING

Write or update the YAML frontmatter in the command file. This is the machine-readable identity of the workflow.

**Command file frontmatter standard:**
```markdown
---
description: [One precise sentence: what this workflow does, what agent persona it activates, and what it produces]
---
```

The description lives at the top of the single merged file — no separate pointer file exists in Claude Code.

**Description quality criteria:**
- Must name the agent persona (if the workflow activates one)
- Must name the primary output
- Must be useful to /triage for recommendation decisions
- Must NOT be generic ("helps with X") — must be specific ("audits Y and produces Z")

---

## PHASE 4 — EXECUTION HARDENING

This phase operates on the full command file content. Read the file in full using the Read tool before making any changes.

**4a. Activation Point**

Every command file must have an explicit "HOW TO BEGIN" section (or equivalent) that tells the agent:
1. What to do first (read a file? identify a target? ask a question?)
2. What to do silently vs. what to report to the user
3. The exact first sentence it should produce to the user upon activation (or: that it should produce nothing until Phase N)

If missing: add a "HOW TO BEGIN" section at the end of the command file following this pattern:
```markdown
────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
When activated, immediately execute Phase 0 (Intake):
  [Step-by-step list of the first 3-5 actions to take]

Then report to the user:
  "[The exact first sentence the agent should output]"

Then immediately begin Phase 1.
You are now live. Begin Phase 0.
```

**4b. STRICT RULES**

Every command file must have a STRICT RULES section — an explicitly numbered list of rules that cannot be violated during execution. Rules should address:
- When to halt and surface to the user (vs. proceed autonomously)
- What the agent may never do (silent failures, skipping steps, truncating output)
- Scope boundaries (what is out of scope for this workflow)
- Output format requirements

If missing or incomplete: add or expand the STRICT RULES section. Check existing rules for completeness — a STRICT RULES section that doesn't address the halt condition is incomplete.

**4c. Decision Branch Completeness**

Read through the command file and identify every decision point — every place where the workflow could go one of two or more ways. For each:
- Is the HALT condition explicitly stated?
- Is the PROCEED condition explicitly stated?
- Is there a third outcome (e.g., UNVERIFIABLE, WARNING, DEFER) that should be handled but isn't?

Mark incomplete decision branches and add the missing outcomes.

**4d. Inter-Workflow Reference Integrity**

Identify every reference to another workflow in the command file (e.g., "proceed to `/iterate-test`", "after `/focus-plan` confirms PARITY").

For each reference:
- Confirm the referenced workflow exists in `~/blueprint-workflows/claude-commands/`
- Confirm the reference uses the correct name (e.g., `/iterate-test` not `/test`)
- Update stale references

---

## PHASE 5 — INTEGRATION HARDENING

**5a. Pipeline Documentation**

Every command file should document where it sits in the broader development pipeline. If an "INTEGRATION WITH OTHER WORKFLOWS" section does not exist: add it.

Format:
```markdown
────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
This workflow operates in this sequence within the broader pipeline:

  [N-1]. /[prior-workflow]  → [what it produces that this workflow consumes]
  [N].   /[this-workflow]   → THIS WORKFLOW
  [N+1]. /[next-workflow]   → [what this workflow produces that the next consumes]

Typical invocation triggers (from /triage perspective):
  - [Trigger 1: what observable state suggests this workflow should be run]
  - [Trigger 2: ...]
```

**5b. /triage Compatibility Audit**

Cross-reference the description against the trigger matrix in `~/blueprint-workflows/claude-commands/triage.md`. Confirm:
- Is this workflow represented in /triage's trigger matrix?
- If not: note it as a gap for the next /triage update cycle

Do not modify /triage during this workflow. Record the gap in the Hardening Certificate (Phase 8).

---

## PHASE 6 — OBSERVABILITY HARDENING

**6a. Structured Output Format**

Every Sovereign-grade workflow must produce a structured, machine-readable output — a receipt, report, or certificate that captures what was done, to what, and with what result.

If the workflow does not produce structured output: add an output template.

For hardening workflows: the structured output is the Hardening Certificate (Phase 8 of THIS workflow). For build workflows: it is a Build Receipt. For validation workflows: a Validation Report.

The structured output must include:
- Workflow name and date
- Target (what was processed)
- Result (grade, status, outcome)
- Key changes made
- Remaining gaps or deferred items

**6b. Change Log**

Every command file must have a Change Log section at the bottom. Format:
```markdown
---

### Change Log
1. **[DATE]**: `[CREATED]` [Brief description of initial creation and origin].
2. **[DATE]**: `[MODIFIED]` [What changed and why].
3. **[DATE]**: `[INJECTED]` [What was added and where, following /nodelete].
```

If a Change Log already exists: append the current hardening session as a new entry. Never overwrite existing entries.

If the command file is new: create the Change Log with entry 1 as the creation record.

---

## PHASE 7 — VALIDATION

Before certifying the grade, validate that the hardened workflow is complete and correct.

**7a. Command File Routing Test**

Do not mentally simulate — verify by actually reading. Execute the following steps using the Read tool:

1. Read the command file: `Read ~/blueprint-workflows/claude-commands/[name].md`
   - Confirm the YAML frontmatter description is present and non-empty
   - Confirm the file loads without error
2. Confirm the HOW TO BEGIN activation point is clear in the file
3. Confirm the symlink exists: `ls ~/.claude/commands/[name].md`

Check:
- [ ] Command file confirmed readable via Read tool
- [ ] YAML frontmatter present with non-empty description
- [ ] HOW TO BEGIN entry point is unambiguous
- [ ] Symlink at `~/.claude/commands/[name].md` exists and points to the command file

**7b. Frontmatter Validation**

Confirm the YAML frontmatter is syntactically valid:
- `description:` is a single non-empty string
- The frontmatter block is properly delimited by `---` fences

**7c. Command File Completeness Check**

Read the command file and confirm the following sections exist:
- [ ] GLOSSARY section (or equivalent key terms documentation)
- [ ] At least one Phase or Step with defined success criteria
- [ ] STRICT RULES or equivalent enforcement block
- [ ] HOW TO BEGIN activation point
- [ ] INTEGRATION WITH OTHER WORKFLOWS section
- [ ] A structured output template (receipt, report, or certificate)
- [ ] Change Log

---

## PHASE 8 — GRADE CERTIFICATION

When all applicable hardening phases are complete, re-evaluate the workflow against the Sovereign Standard and emit the Hardening Certificate:

```
+══════════════════════════════════════════════════════════+
║  WORKFLOW HARDENING CERTIFICATE                          ║
║  Workflow:      /[name]                                  ║
║  Date:          [date]                                   ║
╠══════════════════════════════════════════════════════════╣
║  GRADE:         SOVEREIGN / HARDENED / STRUCTURED        ║
╠══════════════════════════════════════════════════════════╣
║  Command file:  ~/blueprint-workflows/claude-commands/[name].md
║  File size:     [N bytes]                                ║
║  Symlink:       ~/.claude/commands/[name].md — PRESENT   ║
║  Frontmatter:   PRESENT — description ✓                  ║
║  GLOSSARY:      PRESENT / ABSENT (Hardened max)          ║
║  HOW TO BEGIN:  PRESENT                                  ║
║  STRICT RULES:  PRESENT ([N] rules)                      ║
║  Struct Output: PRESENT / ABSENT (Hardened max)          ║
║  Change Log:    PRESENT / ABSENT (Hardened max)          ║
╠══════════════════════════════════════════════════════════╣
║  /triage Gap:   [any gaps noted] / NONE                  ║
╠══════════════════════════════════════════════════════════╣
║  Changes Made:                                           ║
║    - [list of each hardening action taken]               ║
║  Deferred Items:                                         ║
║    - [any items not addressed and why]                   ║
╠══════════════════════════════════════════════════════════╣
║  Standard Version: 3                                     ║
║  Status:        WORKFLOW HARDENING COMPLETE              ║
+══════════════════════════════════════════════════════════+
```

**Standard Version field [INJECTED v2, 2026-05-07]**: The Hardening Certificate must include the Standard Version under which the grade was certified. This field enables future Degradation Checks. A certificate without this field cannot be automatically compared against future standard versions.

**[INJECTED 2026-05-11 — Divergence #1: Mutual Hardening Symbiosis]**  
**8b. Hardening Intelligence Payload Generation (Mutual Symbiosis)**

Immediately after emitting the Hardening Certificate, generate a structured **Hardening Intelligence Feedback Payload** — the bidirectional return channel that turns hardening from a one-way audit into co-evolutionary symbiosis:

```
HARDENING INTELLIGENCE PAYLOAD
Workflow Hardened: /[name]
Date: [date]
Observed Patterns: [list of structural patterns surfaced]
Suggested STRICT RULE additions or improvements: [list]
Potential new failure patterns: [list]
Cross-workflow recommendations: [list]
Phylogenetic note: [reference to lineage or recombination]
```

This payload is emitted as a machine-readable block and can be consumed by future /harden-workflow sessions, a central intelligence ledger, or the target workflow itself for self-improvement.

After Phase 8b: ask the user whether to proceed to the next workflow in the batch (if batch mode), or halt for review (if single mode).

---

## PHASE 9 — PHYLOGENY & GENETIC ARCHIVE (Divergence #3)

**[INJECTED 2026-05-11 — Divergence #3: Workflow Phylogeny & Genetic Archive]**

/harden-workflow now acts as the evolutionary curator of the Sovereign Suite.

It tracks:
- Phylogenetic tree of workflow structural DNA across the entire suite
- Horizontal gene transfer of proven patterns (e.g., STRICT RULE templates, decision-branch scaffolds, failure-pattern hooks)
- Lineage, crossover events, and recombination opportunities

**Responsibilities in this role (executed as part of every hardening session):**
- Analyze Change Logs for crossover events and surface them in the Hardening Certificate
- Record this hardening session's contribution to the suite phylogeny (append to a central `~/blueprint-workflows/manifest/SUITE_PHYLOGENY.md` or equivalent)
- Recommend specific horizontal gene transfers to other workflows in the Deferred Items or Intelligence Payload

This fulfills the adjacent possible of the Sovereign Suite becoming a living, co-evolving organism rather than a static collection of documents.

---

**[INJECTED 2026-05-11 — Divergence #2: Ecosystem Immunity Layer]**  
## PHASE 10 — ECOSYSTEM IMMUNITY LAYER (Divergence #2)

This phase implements the proactive immune system for the entire Sovereign Suite. It turns /harden-workflow into the central "vaccine factory" that runs autonomously in the background.

**Invocation modes (callable as sub-workflow by other workflows):**
- Normal hardening (as before)
- `--immunity` (background mode): triggered silently by /continuous-verify, /receipt-check, /focus-plan, /triage, etc.

**How the immunity layer works (autonomous flow):**
1. **Trigger** — Any workflow that already runs regularly (especially /continuous-verify at phase boundaries, /receipt-check on scans, /focus-plan after loops) calls `/harden-workflow --immunity`.
2. **Quick health scan** — Scans recent Change Logs, Hardening Certificates, /receipt-check data, and suite state for early warning signs (missing failure-pattern hooks, Context Erosion signals, stale workflows).
3. **Antibody generation** — Creates tiny, reusable Sovereign-grade micro-patterns ("antibodies"):
   - Updated STRICT RULE templates
   - Self-verifying decision-branch scaffolds
   - New failure-pattern checklists
   - Context-Erosion countermeasures
4. **Proactive injection** — Using strict /nodelete rules, appends the antibodies into the affected workflow command files (never overwrites, always leaves clear `[IMMUNITY INJECTION — date]` markers).
5. **Record & report** — Updates Phylogeny archive, Hardening Intelligence Payload, and emits a minimal summary only if injections occurred.

**Seeding mechanism**:
Other workflows (starting with /continuous-verify) now contain a one-line call to the immunity layer at natural checkpoints. This makes the immunity proactive and automatic — no manual invocation required.

This phase fulfills the biology/immunology transplant: the suite now has herd immunity and stays healthy without constant manual intervention.

---

## STRICT RULES (never violate)

1. Never reconstruct a workflow's content from memory. Always read the actual file using the Read tool before assessing or modifying.
2. Never award a Sovereign grade to a workflow missing any single Sovereign criterion. The grade system is binary per criterion.
3. Never modify a command file's protocol logic (the steps, the rules, the decision branches) — only add missing structural elements. This workflow hardens STRUCTURE, not content. Content improvements belong to the specific workflow's own refinement session.
4. Never delete content from a command file during hardening. Hardening is additive per /nodelete.
5. Always append to Change Logs — never overwrite existing entries.
6. Never certify a grade without completing the Phase 7 validation checklist.
7. When in batch mode: emit one Hardening Certificate per workflow. Do not combine multiple workflows into a single certificate.
8. If the command file is missing or unreadable, halt immediately and surface the error to the user. Do not proceed with a missing or broken command file.
9. Command file structural review is irreversible in a single session — once content is rewritten or restructured, the prior version is overwritten. Read the full file before making any changes. Prefer injections over rewrites per /nodelete.
10. /triage compatibility is assessed, not enforced. Note gaps in the certificate. Do not modify /triage during a hardening session.
11. If Phase 2 Structural Verification (Step 2b) fails for any check — command file not found or symlink missing — HALT immediately. Do not proceed to Phase 3. A broken structure cannot be hardened; it must be repaired first.
12. Never trust hardcoded file sizes. Sizes change as workflows evolve. Always use Read tool or `wc -c` via Bash to get actual current sizes before assigning priorities.
13. When using the Sovereign Scaffold Generator (Phase 2a): never leave a `[PLACEHOLDER]` unfilled before certifying a grade. A scaffold with unfilled placeholders is not a completed workflow — it is a template. Certifying it as Sovereign is a grade fraud.
14. **Generator mode requires that the symlink at `~/.claude/commands/[name].md` be established.** In Claude Code, a command file must exist in `~/blueprint-workflows/claude-commands/` and be symlinked to `~/.claude/commands/` before it can be invoked as a slash command. If the symlink does not exist after writing the command file: HALT. Report: `GENERATOR HALT: Symlink ~/.claude/commands/[name].md must be created before the slash command is live. Create with: ln -s ~/blueprint-workflows/claude-commands/[name].md ~/.claude/commands/[name].md`
15. **[INJECTED 2026-05-08 — Ticket mode closure, /nodelete]** In ticket mode, the ticket closure (Phase 4 of `/helpdesk-tickets`) is MANDATORY after Phase 8. Never certify a hardening and leave the ticket open. The `CLOSED_` prefix rename is the machine-readable closure signal — updating a status field inside the file is not sufficient. If the rename fails (file not found, permission error), halt and surface the error to the user before ending the session.
16. **[INJECTED 2026-05-11 — Divergence #1]** Always generate the Hardening Intelligence Payload in Phase 8b. Bidirectional symbiosis is now a core responsibility.
17. **[INJECTED 2026-05-11 — Divergence #2]** When invoked with `--immunity`, run the full Ecosystem Immunity Layer (Phase 10) silently in the background. Seed calls to this layer into /continuous-verify, /receipt-check, /focus-plan, and /triage at natural checkpoints. All injections must follow /nodelete.

---

## SUITE-WIDE AUDIT MODE

When invoked with "audit the suite" or equivalent, perform the following before any hardening:

1. List every `.md` file in `~/blueprint-workflows/claude-commands/` using Bash:
   ```bash
   ls ~/blueprint-workflows/claude-commands/*.md | sort
   ```
2. For each file: use the Read tool to read the first 20 lines (frontmatter + opening) and check file size via Bash (`wc -c`). Also read the last Change Log entry to determine which Standard Version each workflow was certified under (if any).
3. Produce a **Suite Audit Table** populated with the live-read sizes and grades:

```
SUITE AUDIT — [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Workflow         Size (live)  Format          Grade    Std. Version
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[populate dynamically from actual file reads — do not use static values]
[Standard Version column: read from Change Log or Hardening Certificate — UNKNOWN if not stamped]

REFERENCE ONLY — baseline snapshot from 2026-05-07 Antigravity era (STALE — Pointer/Payload architecture, retired):
  /canvas          3,130 b     Monolithic      Structured
  /deepcode        5,046 b     Monolithic      Structured
  /divergence        660 b     Pointer → core  Sovereign
  /document        5,873 b     Monolithic      Structured
  /execute-build     698 b     Pointer → core  Sovereign
  /focus-plan      9,843 b     Monolithic      Legacy (near cap)
  /gitclean       10,072 b     Monolithic      Legacy (at cap)
  /harden         12,113 b     Monolithic      Legacy (over cap!)
  /harden-workflow  [N] b      Pointer → core  Sovereign
  /iterate-test   11,805 b     Monolithic      Legacy (near cap)
  /nodelete        4,945 b     Monolithic      Structured
  /quality         9,882 b     Monolithic      Structured
  /refactor          708 b     Pointer → core  Sovereign
  /soc               689 b     Pointer → core  Sovereign
  /triage         11,853 b     Monolithic      Legacy (near cap)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIORITY HARDENING ORDER (computed from live assessment):
  P0 (MISSING Sovereign criteria — immediate hardening):  [list from live assessment]
  P1 (Structured, missing STRICT RULES or output):        [list]
  P2 (Hardened, missing Change Log or GLOSSARY):          [list]
  Already Sovereign (Standard v3):                        [list]
```

Present the Suite Audit Table (with live grades) to the user. Ask: proceed with P0 first, or specify a different order?

---

────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
When activated, immediately execute Phase 0 (Intake):
  Step 0a: Read the invocation — identify target scope (single / batch / new build / ticket mode)
  Step 0b: For each target workflow, read the command file using the Read tool
  Step 0c: Produce the Intake Manifest for each target

Then report to the user:
  "Intake complete. [N] workflow(s) targeted. Beginning assessment."

If "audit the suite" mode is detected: skip to SUITE-WIDE AUDIT MODE before any hardening begins.

Then immediately begin Phase 1 for each target.
You are now live. Begin Phase 0.

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
This workflow operates in this position within the workflow maintenance pipeline:

  1. /divergence       → surfaces new workflow ideas and architectural improvements
  2. /harden-workflow  → THIS WORKFLOW — hardens existing or newly created workflow files
  3. /triage           → uses the hardened frontmatter description to recommend workflows
  4. /receipt-check    → reads Hardening Certificates to track suite coverage (Layer 2)
  5. /document         → records the hardening session in the DevJournal

**New immunity seeding**: /continuous-verify, /receipt-check, /focus-plan, and /triage now contain lightweight calls to `/harden-workflow --immunity` at natural checkpoints. This makes the Ecosystem Immunity Layer (Phase 10) run autonomously in the background.

Typical /triage triggers for this workflow:
  - A new workflow .md file was created but has no frontmatter
  - An existing workflow has no STRICT RULES or structured output section
  - A workflow's inter-workflow references are stale (workflow renamed/moved)
  - A new hardening standard has been established that existing workflows don't yet meet

────────────────────────────────────────────
PHYLOGENY & GENETIC ARCHIVE
────────────────────────────────────────────
**[INJECTED 2026-05-11 — Divergence #3: Workflow Phylogeny & Genetic Archive]**

/harden-workflow now serves as the evolutionary curator of the Sovereign Suite. It tracks the phylogenetic tree of workflow structural DNA, horizontal gene transfer of proven patterns (STRICT RULE templates, decision-branch scaffolds, failure-pattern hooks), lineage, crossover events, and recombination opportunities.

This turns the hardening process into a living evolutionary system that accelerates suite-wide antifragility and makes the entire Sovereign Suite a true co-evolving organism.

---

### Change Log
1. **2026-05-07**: `[CREATED]` Full workflow built from blank pointer. Origin: Session discussion identifying /harden-workflow as the formalization of the workflow hardening practice developed throughout the session. Established the four-grade system (Sovereign/Hardened/Structured/Legacy), the eight-phase hardening protocol, the Pointer/Payload decision tree, and the Suite-Wide Audit Mode. Pointer/Payload architecture applied at creation.
2. **2026-05-07**: `[HARDENED — Self-Pass]` Applied /harden-workflow against itself via /focus-plan + /quality. Six gaps resolved: (a) Orphaned payload detection added to Phase 0b; (b) Batch-mode Sovereign-skip decision branch added to Phase 1; (c) Phase 7a upgraded from mental simulation to actual view_file verification; (d) Suite Audit Mode hardened against stale static sizes — live read now required; (e) STRICT RULE 11 added: halt if Phase 2 verification fails; (f) STRICT RULE 12 added: never trust hardcoded sizes. Grade elevated from Hardened to Sovereign.
3. **2026-05-07**: `[INJECTED — Divergence Pass, /nodelete]` Three Divergence-approved additions injected. (a) GLOSSARY block added after preamble — key terms for context-portable operation by any agent; defines Standard Version as a first-class concept. (b) Degradation Check injected into Phase 1 — detects when a Sovereign workflow was certified under an older Standard Version and flags it for re-certification. (c) Sovereign Scaffold Generator injected into Phase 2b — full pre-populated Sovereign-grade core.md template eliminating Legacy-grade new workflows from this point forward. Standard Version incremented to 2. STRICT RULE 13 added (no unfilled scaffold placeholders). Hardening Certificate standard_version field mandated. Suite Audit Table updated with Standard Version column.
4. **2026-05-07**: `[INJECTED — Generator session governance, /nodelete]` STRICT RULE 14 added: Generator mode requires a pre-existing pointer file (user-created) as a halt condition. Surfaced during the /continuous-verify Generator build session — user confirmed that Antigravity cannot assign the `/` slash trigger to a workflow unless `[name].md` already exists at the time of invocation.
5. **2026-05-08**: `[INJECTED — Ticket mode, /nodelete]` Fourth invocation mode added: `--ticket`. Scans `helpdesk-tickets/` for open tickets (files without `CLOSED_` prefix), uses each ticket as an intake manifest to identify the faulting workflow and recommended fix (Section 5 of ticket), routes to Phase 1 hardening, then closes the ticket via `CLOSED_` prefix rename after Phase 8 certificate. STRICT RULE 15 added: ticket closure is mandatory after hardening in ticket mode. TICKET MODE PROTOCOL block injected into Phase 0a. Complements /helpdesk-tickets workflow (also created this session). Standard Version: 2.
6. **2026-05-11**: `[INJECTED — Divergence #1 & #3, /nodelete + /quality + /focus-plan]` Mutual Hardening Symbiosis (Phase 8b + Hardening Intelligence Payload) and Workflow Phylogeny & Genetic Archive section injected. Phase 8 extended, new Phase 9 added, STRICT RULE 16 added, certificate template enhanced, INTEGRATION and Change Log updated. All prior content preserved. Grade remains Sovereign with evolutionary extensions. Standard Version: 2.
7. **2026-05-11**: `[INJECTED — Divergence #2, /nodelete + /quality + /focus-plan]` Ecosystem Immunity Layer (new Phase 10 + autonomous `--immunity` sub-workflow) injected. Proactive antibody generation, seeding into /continuous-verify and other heartbeat workflows, and STRICT RULE 17 added. All prior content preserved. Grade remains Sovereign with evolutionary extensions. Standard Version: 2.
8. **2026-05-21**: `[PORTED — Claude Code migration]` Pointer/Payload architecture retired. Merged into single command file at `~/blueprint-workflows/claude-commands/harden-workflow.md`. Standard Version incremented to 3. GLOSSARY: Pointer file, Payload file, Injection cap entries marked RETIRED with historical preservation per /nodelete; Command file term added; Sovereign grade criteria updated for Claude Code. Sovereign Standard grades table updated to remove P/P criterion, replace with single merged command file criterion. THE POINTER/PAYLOAD DECISION section: marked RETIRED, historical content preserved per /nodelete. Phase 0b INTAKE MANIFEST: updated to single command file architecture; Orphaned Payload Detection retired (Antigravity-specific). Phase 0c: `view_file` → Read tool. Phase 1 Assessment Card: Architecture section replaced with File Location section. Phase 2: renamed from "Structural Hardening (Pointer/Payload Conversion)" to "Structural Hardening"; P/P conversion content retired; Sovereign Scaffold Generator updated to Claude Code single-file format. Phase 3: pointer file template replaced with single command file frontmatter standard. Phase 4d: `global_workflows/` → `~/blueprint-workflows/claude-commands/`. Phase 5b: `/triage/core.md` → `~/blueprint-workflows/claude-commands/triage.md`. Phase 7: `view_file` → Read tool; pointer routing test updated to command file test. Phase 7c: `core.md` → single command file. Phase 8: Hardening Certificate template updated (no P/P fields; symlink field added). SUITE-WIDE AUDIT MODE: `list_dir` → Bash `ls`; `view_file` → Read tool; `global_workflows/claude-commands/` path; Suite Audit Table reference data marked STALE. STRICT RULES: 1, 4, 8, 9, 11, 13, 14 updated for Claude Code. HOW TO BEGIN: `view_file` → Read tool. TICKET MODE PROTOCOL: `ls` and `mv` paths updated to `~/blueprint-workflows/helpdesk-tickets/`. INTEGRATION: `global_workflows` → blueprint-workflows paths.
