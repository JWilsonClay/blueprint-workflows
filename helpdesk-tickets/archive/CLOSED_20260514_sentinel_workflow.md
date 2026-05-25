# Helpdesk Ticket: Non-Neutral Self-Healing Templates in Doorway/Sentinel

**To**: Senior Architect of Workflows
**From**: Antigravity / Sentinel Session
**Date**: 2026-05-14
**Subject**: Doorway self-healing "clones" external project schemas into new workspaces via non-neutral templates.
**Urgency**: CRITICAL (Architectural)

---

## 1. Executive Summary
During the initialization of a new project (ccjacksonville), the `/sentinel` workflow detected missing governance files (MANIFEST.md, Architecture.md). It triggered a "self-healing" process that recreated these files from global templates. However, these templates contain hardcoded folder structures and absolute paths from an external project ("ContentFlow" / "langgraph-social-agent"). As a result, the new project was populated with an incorrect and misleading architectural schema.

## 2. Root Cause Analysis: "Structural Gap"
- **The How**: The `IntegrityManager.heal()` method reads a template file and writes it to the target workspace verbatim. 
- **The Why**: The templates provided in the global `scripts/doorway/templates/` directory are project-specific exports rather than generic blueprints. Additionally, the `heal()` logic lacks the variable substitution mechanism present in `create_readme()`, meaning even if the templates were parameterized, they would not be correctly populated.

## 3. Forensic Evidence
- **Faulting Template**: [MANIFEST.md.template](file:///home/jwils/.gemini/antigravity/global_workflows/scripts/doorway/templates/MANIFEST.md.template#L1-L41)
  *Evidence: Template contains hardcoded "ContentFlow Architecture" and paths to "/home/jwils/Public/langgraph-social-agent/".*
- **Faulting Logic**: [integrity.py](file:///home/jwils/.gemini/antigravity/global_workflows/scripts/doorway/integrity.py#L112-L118)
  *Evidence: The heal() method performs a raw atomic_write(target_path, template_content) without any string substitution.*
- **Faulting Template (Architecture)**: [Architecture.md.template](file:///home/jwils/.gemini/antigravity/global_workflows/scripts/doorway/templates/Architecture.md.template#L1-L41)
  *Evidence: Identical project-specific hardcoding as the Manifest template.*

## 4. Remediation: Parameterization and Skeleton Generation
1. [Surgical] Scrub global templates in `scripts/doorway/templates/` of all hardcoded "ContentFlow" or "langgraph-social-agent" references.
2. [Structural] Update `IntegrityManager.heal()` to support variable substitution (e.g., `{name}`, `{path}`, `{description}`) similar to `create_readme()`.
3. [Enhanced] Implement dynamic MANIFEST.md skeleton generation in `doorway.py` that reflects the *actual* folders found in the workspace rather than a static list.

## 5. Recommendation to Senior Architect
Update the Doorway Protocol specification to enforce **Strict Template Neutrality**. No template in the `global_workflows` substrate should contain hardcoded project names or absolute paths. Furthermore, the `IntegrityManager` should be hardened to ensure that all "healing" operations pass through a substitution filter to prevent raw cloning of stale architectural state.

---
**Status**: **OPEN**
**Verification**: PENDING (Requires scrubbing of global templates and update to integrity.py logic)

---
*Signed,*
**Antigravity**
*(Sovereign Coding Assistant)*

note from John: an agent already corrected a few of the templates, but we do need a comprehensive e2e look at the workflow to ensure it is functioning as intended.  The intention is that this workflow is executable from the global workflows workspace, and able to be ran in ANY workspace old or new, and comprehensively build out any and all documentaiton and file structures needed, among all the other intentions noted in the workflow already.  please discuss with me to ensure we are clear and I am not contradicting other things in the workflow.
---
**Status**: **REMEDIATED**
**Closed**: 2026-05-15
**Changes Made**:
- `integrity.py`: Added `_expand_template()` — dynamic workspace dir enumeration replaces `[DIRECTORY_LIST_PLACEHOLDER]` in all templates. `heal()` now calls it before every atomic_write.
- `sentinel/core.md`: Injected Phase 1.5 (Agent Breadcrumb Population) — closes the permanent-placeholder gap. Agent now reads, samples, generates compact agentic key:value summaries, and pushes them into READMEs via --auto-apply.
- `breadcrumb.py`: `propose()` now enumerates directory file inventory (names + count + subdirs) and writes it into the log entry as structural context for the LLM agent.
- `README.md.template`: Removed hardcoded `.blueprints` reference.
- **Architect Note addressed**: Two bugs fixed, not one. Ticket covered Bug #1 (template cloning). Bug #2 (permanent breadcrumb placeholders) was surfaced during halting discussion and remediated in the same pass.
