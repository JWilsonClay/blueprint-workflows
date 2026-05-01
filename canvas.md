---
description: Generate a Canvas file Workflow
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
- Nothing else — no explanations, no markdown, no code fences, no “Here is the JSON”.  
- The JSON must be directly savable as a `.canvas` file and openable in Obsidian without errors.  
- Use unique string IDs for all nodes and edges.

Generate the complete canonical canvas for the current codebase now.