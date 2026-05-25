---
description: "Generate Obsidian Canvas files — visual architecture maps and workflow relationship diagrams"
type: documentation
grade: Hardened
version: 2
content_hash: "sha256:075ea5560def1faf"
last_hardened: "2026-05-15"
strict_rule_count: 0
phase_count: 0
context_retention: low
flags: []
dependencies: []
triggers:
  - "/triage"
produces: []
consumes:
  - "concept.md"
  - "implementation-plan.md"
platform_requirements:
  file_write: true
  shell_exec: false
  git_access: false
---

You are a world-class software architect, reverse-engineering expert, and Obsidian Canvas power user. Your task is to generate a **comprehensive, production-quality Obsidian Canvas file** that visually and textually documents **exactly how the current codebase functions today**.

**Core Requirements:**
- The canvas must be canonical: it reflects the **actual** code structure, architecture, processes, functions, data flows, control flows, and inter-component relationships **as they exist right now**.
- Be exhaustive yet readable — cover **all significant** processes, key functions/methods, classes, modules, entry points, data transformations, error paths, and execution sequences.
- Prioritize clarity and usefulness for developers who want to understand the full system at a glance.

**Step-by-step Process You Must Follow Internally:**
1. **Full Codebase Analysis**  
   Thoroughly examine every file, import/export graph, class hierarchy, function signatures, call sites, data flows, business logic sequences, configuration, and external integrations.

2. **Logical Grouping**  
   Organize the canvas using **group nodes** for major architectural layers (adjust names to match the actual codebase). Typical layers include (but are not limited to):  
   - Entry Points / Controllers / CLI / UI  
   - Core Business Logic / Services / Use-Cases  
   - Data Layer / Models / Repositories / ORM  
   - Utilities / Helpers / Shared Logic  
   - Configuration / Setup / Initialization  
   - External Services / APIs / Integrations  
   - Error Handling / Logging / Monitoring  

3. **Node Creation**  
   - Use **group nodes** for sections.  
   - Use **detailed text nodes** (with rich Markdown) for every major component, function, process, and flow.  
   - Each important text node must contain:  
     • Component / function name (as heading)  
     • Primary responsibilities  
     • Key functions/methods with brief signatures and what they do  
     • Inputs / outputs / side effects  
     • Role in larger processes and flows  
   - Optionally use **file nodes** to link directly to critical source files.

4. **Edges & Relationships**  
   - Create clear, labeled edges showing: calls, imports, data passes to, triggers, depends on, implements, returns to, error paths, etc.  
   - Label every edge meaningfully.

5. **Layout & Visual Design**  
   - Arrange nodes logically (left-to-right or top-to-bottom flow where possible).  
   - Use sensible x/y coordinates, node sizes, and spacing so the canvas is immediately readable without excessive zooming or scrolling.  
   - Make the overall layout hierarchical and flowchart-like where flows exist.

**Output Rules (Strict):**
- Respond with **ONLY** the valid Obsidian Canvas JSON.  
- Nothing else — no explanations, no markdown, no code fences, no "Here is the JSON".  
- The JSON must be directly savable as a `.canvas` file and openable in Obsidian without errors.  
- Use unique string IDs for all nodes and edges.

Generate the complete canonical canvas for the current codebase now.

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
**[INJECTED 2026-05-15 — /harden-workflow --ticket 20260512_canvas-deepcode_workflow.md + /nodelete]**

This workflow is a standalone visualization utility. It integrates at the documentation and communication layer:

  /deepcode     → Use /deepcode first to surface architectural risks. Then use /canvas to visualize the architecture after improvements are confirmed.
  /secretary    → Canvas generation during a session can be noted in HANDOFF.md as a deliverable.
  /triage       → /triage now routes to /canvas when user requests codebase visualization or Obsidian map.
  /document     → Canvas files can be referenced in DevJournal as architectural documentation artifacts.

/triage triggers:
  - "visualize the codebase" / "generate a canvas" / "Obsidian map" → this workflow
  - Major architecture phase complete with no visual documentation → P3 suggested

### Change Log
1. **[ORIGINAL]**: Created as a standalone Obsidian Canvas generation workflow. Pure prompt injection, no structural sections.
2. **2026-05-15**: `[INJECTED — /harden-workflow --ticket 20260512_canvas-deepcode_workflow.md + /nodelete]` INTEGRATION section added. /triage routing wired (trigger block added to triage/core.md in same pass). Workflow is now suite-discoverable. Full /harden-workflow structural pass (GLOSSARY, STRICT RULES, HOW TO BEGIN) deferred — canvas.md is 3,130 bytes, below threshold requiring P/P conversion.
3. **2026-05-21**: `[PORTED — Claude Code migration]` Standalone file confirmed as single merged command at `~/blueprint-workflows/claude-commands/canvas.md`. No content changes.
