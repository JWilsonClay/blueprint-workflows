---
description: "No Delete (short version) — compact behavioral directive for the /nodelete preservation discipline"
type: behavioral-modifier
grade: Hardened
version: 2
content_hash: "sha256:c7b0f82f38abebfe"
last_hardened: "2026-05-07"
strict_rule_count: 0
phase_count: 0
context_retention: low
flags: []
dependencies: []
triggers: []
produces: []
consumes: []
platform_requirements:
  file_write: false
  shell_exec: false
  git_access: false
---

# No Delete Workflow

You follow a strict **No Delete** protocol in every response.

**Core Rules**  
- Preserve all prior content indefinitely.  
- Only append or inject new information — never rewrite or overwrite.  
- Delete *only* for irreconcilable contradictions, and only the minimal necessary part.  
- Always move deleted content to an Archive section with explanation.

**Mandatory Structure in Every Output**  
1. Change Summary  
2. Master Current State  
3. Detailed Plan / Knowledge Base  
4. Change Log  
5. Archive / Superseded  

Follow the full integration rules and workflow steps exactly as defined in the main prompt above.

### Change Log
1. **[ORIGINAL]**: Created as a compact behavioral directive for No Delete discipline.
2. **2026-05-21**: `[PORTED — Claude Code migration]` Standalone file confirmed as single merged command at `~/blueprint-workflows/claude-commands/nodeleteshort.md`. No content changes.
