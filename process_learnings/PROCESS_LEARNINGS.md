# PROCESS_LEARNINGS.md — Global Workflow Institutional Memory
# Location: /home/jwils/.gemini/antigravity/global_workflows/process_learnings/PROCESS_LEARNINGS.md
# Append-only. Each entry is one /retrospective session.
---

## 2026-05-07 — JWilsonClay/langgraph-social-agent — Sovereign Hardening Phase 5-7

### Session Summary
- Boundary: Phases 5, 6, and 7 of the Sovereign Identity Pipeline (Acoustic, Apoptosis, GHOST).
- Goal: Achieve Diamond-Hardened systemic integrity and synthetic chaos testing.
- Outcome: ACHIEVED. All three phases built and verified via Chaos Run.
- Workflows used: /execute-build, /focus-plan, /quality, /nodelete, /secretary
- Workflows skipped (unjustified): NONE
- Regressions: NONE detected.
- Key decisions: Implementation of "Acoustic" monitoring via syscall snapshots; "Apoptosis" via physical unlinking of state pickles on illegal transitions; "GHOST" fuzzing via randomized header injection.

### Problem Log
- NO PROBLEMS DETECTED. The use of /focus-plan and /quality ensured zero-drift implementation.

### Pattern Observations
- **FIRST ENTRY**: High correlation between /focus-plan usage and zero-regression outcomes in complex substrate modifications.
- **Pattern**: Manual verification via synthetic "Burns" is effective but requires the receipt infrastructure to be fully operational for automated observability.

### Workflow Improvement Suggestion
- **Problem observed**: Lack of automated receipt generation in Layer 1 workflows hinders Layer 2 observability (/receipt-check).
- **Proposed change**: /execute-build — Add a mandatory Step 6b that writes a standardized JSON/MD receipt to .workflow_state/receipts/.
- **Change type**: New Step
- **Priority**: HIGH
- **Rationale**: Enables /receipt-check to produce actual coverage maps instead of "NOT INITIALIZED" reports.

### Cross-Project Insight
- The "Biological Integrity" pattern (Acoustic Audit + Physical Apoptosis) is highly applicable to any long-running agentic substrate where environmental drift or state corruption is a risk.

---

## 2026-05-07 — JWilsonClay/langgraph-social-agent — Sovereign Session Documentation & Close

### Session Summary
- Boundary: Finalization of Phases 5-7, update of WORKFLOW_MANIFEST.md, production of HANDOFF.md, and initialization of DevJournal.md.
- Goal: Close the Sovereign Identity Pipeline build session with 100% paper trail compliance.
- Outcome: ACHIEVED. All three metadata artifacts (Manifest, Handoff, Anomaly Log) and the DevJournal created/updated.
- Workflows used: /secretary, /document, /retrospective, /focus-plan, /quality
- Workflows skipped (unjustified): NONE
- Regressions: NONE
- Key decisions: Initialized the global WORKFLOW_MANIFEST.md to track suite health (Score: 50%); established the .workflow_state directory as the sovereign repository for session metadata.

### Problem Log
- NO PROBLEMS DETECTED.

### Pattern Observations
- **Pattern**: The /secretary workflow serves as a powerful "Context Anchor" for the next agent, effectively mitigating the "Context Drift" that occurs between disparate agentic sessions.
- **Pattern**: Layer 2 observability (via /receipt-check) remains "NOT INITIALIZED" until Layer 1 workflows are updated to write structured receipts.

### Workflow Improvement Suggestion
- **Problem observed**: Manual detection of session boundaries in /retrospective is error-prone.
- **Proposed change**: /secretary — Modify Phase 5 to automatically pass the `ea5c384..HEAD` commit range (or equivalent session delta) to /retrospective.
- **Change type**: Modified Step
- **Priority**: MEDIUM
- **Rationale**: Automates the intake phase of the retrospective, ensuring high-fidelity data extraction without user intervention.

### Cross-Project Insight
- The use of a centralized `WORKFLOW_MANIFEST.md` provides a necessary meta-layer of quality control, allowing users to see at a glance which protocols are production-ready (Sovereign) vs. legacy.

---

## 2026-05-07 — JWilsonClay/langgraph-social-agent — Sovereign Session Documentation & Close

### Session Summary
- Boundary: Finalization of Phases 5-7, update of WORKFLOW_MANIFEST.md, production of HANDOFF.md, and initialization of DevJournal.md.
- Goal: Close the Sovereign Identity Pipeline build session with 100% paper trail compliance.
- Outcome: ACHIEVED. All three metadata artifacts (Manifest, Handoff, Anomaly Log) and the DevJournal created/updated.
- Workflows used: /secretary, /document, /retrospective, /focus-plan, /quality
- Workflows skipped (unjustified): NONE
- Regressions: NONE
- Key decisions: Initialized the global WORKFLOW_MANIFEST.md to track suite health (Score: 50%); established the .workflow_state directory as the sovereign repository for session metadata.

### Problem Log
- NO PROBLEMS DETECTED.

### Pattern Observations
- **Pattern**: The /secretary workflow serves as a powerful "Context Anchor" for the next agent, effectively mitigating the "Context Drift" that occurs between disparate agentic sessions.
- **Pattern**: Layer 2 observability (via /receipt-check) remains "NOT INITIALIZED" until Layer 1 workflows are updated to write structured receipts.

### Workflow Improvement Suggestion
- **Problem observed**: Manual detection of session boundaries in /retrospective is error-prone.
- **Proposed change**: /secretary — Modify Phase 5 to automatically pass the `ea5c384..HEAD` commit range (or equivalent session delta) to /retrospective.
- **Change type**: Modified Step
- **Priority**: MEDIUM
- **Rationale**: Automates the intake phase of the retrospective, ensuring high-fidelity data extraction without user intervention.

### Cross-Project Insight
- The use of a centralized `WORKFLOW_MANIFEST.md` provides a necessary meta-layer of quality control, allowing users to see at a glance which protocols are production-ready (Sovereign) vs. legacy.

---
## 2026-05-08 -- SoC & Hardening Logic Efficiency

### Learnings
- **Modularization Velocity**: Moving to a decoupled app structure early in the project life-cycle significantly simplifies the hardening process by isolating attack surfaces.
- **Signal Gaps**: Automated lead scoring via signals is elegant but requires robust mocking in unit tests to prevent environment-specific client failures (e.g., Groq/Httpx).
- **Validation-at-Source**: Enforcing `full_clean()` in model `save()` hooks provides a 'Diamond Hardened' data layer that catches edge cases (like empty descriptions) before they hit the database.

### Workflow Improvements
- **testpackage Integration**: The /testpackage workflow should explicitly recommend mocking external intelligence bridges as a Phase 1 dependency check.

---

## 2026-05-08 — JWilsonClay/nelson_neighbor — SoC Modularization & Diamond Hardening

### Session Summary
- Boundary: 2026-05-08 session (SoC Refactor through Test Package completion).
- Goal: Execute "Diamond Hardened" SoC refactor and regression verification via Test Package.
- Outcome: ACHIEVED. Monolith decoupled into 5 apps; 17 CVEs patched; 12/12 tests PASSING.
- Workflows used: /soc, /harden, /testpackage, /focus-plan, /quality, /secretary, /document, /receipt-check
- Workflows skipped (unjustified): NONE
- Regressions: 2 (Integration failures resolved during test package construction).
- Key decisions: Decoupled core/models.py into dedicated domain apps; enforced full_clean() on save() for data integrity; established a 3-tier testing lattice (Unit/Integration/Smoke).

### Problem Log
- **Integration FAILURES**: seo_context_processor registration and portfolio rendering loop missing in initial refactor. Resolved via iterative verification.
- **Dependency BUG**: Groq/Httpx incompatibility detected. Resolved via robust signal mocking in test suite.

### Pattern Observations
- **Pattern**: **Early Decoupling Velocity**. Performing SoC refactoring before deep security hardening simplifies the audit by narrowing the attack surface per-file.
- **Pattern**: **Mock-First Intelligence**. High correlation between external AI API instability and CI/CD flakes; mocking is mandatory for "Diamond" test status.

### Workflow Improvement Suggestion
- **Problem observed**: Manual prioritization of high-risk (network-facing) files during hardening is inconsistent.
- **Proposed change**: /harden — Add Phase 1b: "Attack Surface Registry" to automatically categorize files by network/privileged/data risk before the hardening loop.
- **Change type**: New Step
- **Priority**: MEDIUM
- **Rationale**: Ensures the most critical vulnerabilities are addressed first in long-running hardening sessions.

### Cross-Project Insight
- The "Diamond Substrate" pattern (Hardening + SoC + Mocked Testing) provides a portable baseline for any agentic web application requiring high reliability and security.

---

## 2026-05-09 — JWilsonClay/nelson_neighbor — Sovereign Red-Team Hardening Finalization

### Session Summary
- Boundary: Phases 9-11 of the Red-Team Audit (Forensic Audit through Social Stress).
- Goal: Finalize the Diamond Hardened status of the AI Dispatcher and Governance layers.
- Outcome: ACHIEVED. Authentic validation completed after HOT reconstruction.
- Workflows used: /redteam, /iterate-test, /quality, /secretary, /document, /focus-plan, /retrospective
- Workflows skipped (unjustified): NONE
- Regressions: 1 (Fidelity Failure identified in mock-based testing).
- Key decisions: Reverted mock-based success for Phases 10/11; implemented the "Intent Anchor" protocol; executed HOT simulations where the Substrate defends against real adversarial AI.

### Problem Log
- **THE MOCK TRAP**: Discovered that standard "efficient" unit-testing patterns (mocking LLM calls) create a false sense of security in AI audits. The test was passing but the logic was never hit. Resolved via HOT re-runs.

### Pattern Observations
- **Pattern**: **Context Erosion**. Without physical intent anchors in the task manifest, agents will default to "Sound Effect" mocks over "Espresso" execution.
- **Pattern**: **Adversarial Co-Evolution**. Local LiteRT (Gemma 4) provides a zero-cost, high-fidelity playground for stress-testing personality and conversion gates.

### Workflow Improvement Suggestion
- **Problem observed**: /iterate-test Step 4 currently allows for the use of intelligence mocks without warning.
- **Proposed change**: /iterate-test — Add Step 4g: "Fidelity Check." Force the agent to declare if it is mocking the intelligence being tested or if it is executing a "Hot" run.
- **Change type**: New Step / Guardrail
- **Priority**: CRITICAL
- **Rationale**: Prevents the "Hallucinated Success" mode in all future AI-substrate audits.

### Cross-Project Insight
- The "Intent Anchor" protocol (embedding the "How" inside the "What") is the only reliable way to prevent context drift in long-running agentic development cycles.

---


## 2026-05-13 — email_inbox — Sovereign Scraper Registry Implementation

### Session Summary
- Boundary: implementation_plan.md SoC Refactor
- Goal: Stabilize email archival engine via modular registry-controlled scraping architecture.
- Outcome: ACHIEVED. Burn resumed.
- Workflows used: [/investigate, /implementation-plan, /execute-build, /soc, /harden, /secretary]
- Workflows skipped (unjustified): NONE
- Regressions: 1 (Connection Refused due to Mock context default)
- Key decisions: Decoupled technical kind extractors from domain names.

### Problem Log
- **Infrastructure Context Lag**: High-volume burns fail when the environment defaults to Mock context instead of Live mode. 
- **Circular Import in Scraper**: Detected a circular import in the headless scraper service (`boss_level.py` loop). 

### Pattern Observations
- **Pattern**: **Resilience Boundary Efficiency**. Wrapping site-specific logic in a decorator (ResilienceGate) is the most effective way to prevent regression-induced engine apoptosis in high-volume pipelines.
- **Pattern**: **Configuration Drift**. Workspace data/config.yaml often becomes stale when moving between different LLM providers (LiteRT vs. Ollama).

### Workflow Improvement Suggestion
- **Problem observed**: Engine stalls or fails when run in a new terminal without explicit mode flags.
- **Proposed change**: /focus-plan — Add a "Substrate Connectivity" check that pings required endpoints (IMAP, LLM, Redis) before approving an implementation plan.
- **Change type**: New Check/Stage
- **Priority**: MEDIUM
- **Rationale**: Prevents session-start stall loops and configuration mismatches.

### Cross-Project Insight
- Standardizing extraction modules by "Technical Kind" (technical architecture) rather than "Target Name" (domain) drastically reduces logic duplication across different agentic tools.

## 2026-05-13 — email_inbox — Recovery Burn Stabilization & Forensic Audit

### Session Summary
- Boundary: Stabilization and resumption of the 1,000-email recovery burn.
- Goal: Resolve race conditions, harden registry telemetry, and initiate full background ingestion.
- Outcome: ACHIEVED. Burn active (PID 2214544) with 100% success rate on current batch.
- Workflows used: /investigate, /quality, /focus-plan, /execute-build, /secretary, /retrospective
- Workflows skipped (unjustified): NONE
- Regressions: 1 (Double-process race condition detected and resolved).
- Key decisions: Terminated redundant burn process; removed 10-tray safety throttle; implemented `ResilienceGate` structured telemetry.

### Problem Log
- **THE DOUBLE BURN**: Discovered that concurrent execution of the same ingestion script causes fatal `FileNotFoundError` race conditions on shared state pickles. Resolved via process cull and PID audit.
- **TELEMETRY GAP**: Legacy scraper failures were "silent" or caused engine crashes. Resolved via `ResilienceGate` which converts crashes into logged payload metadata.

### Pattern Observations
- **Pattern**: **Concurrency Lock Dependency**. Background "burn" scripts require a filesystem lock or a singleton guard to prevent accidental dual-execution during long-running sessions.
- **Pattern**: **Incremental Trust**. Hardcoding a `:10` tray limit for initial verification provides a necessary "State Handshake" before committing to a full-scale ingestion.

### Workflow Improvement Suggestion
- **Problem observed**: Background processes are difficult to track across disparate terminal sessions without centralized PID management.
- **Proposed change**: /execute-build — Add a "Background Orchestrator" step that writes the PID and log path of long-running tasks to `.workflow_state/ACTIVE_PROCESSES.json`.
- **Change type**: New Artifact/Management
- **Priority**: MEDIUM
- **Rationale**: Enables future agents to detect and manage background tasks (burns, tests, mirrors) without manual forensic investigation.

### Cross-Project Insight
- The use of **Structured Telemetry** (`{"success": bool, "data": dict, "error": str}`) is the only way to maintain forensic integrity in multi-layered scraper registries.

---

## 2026-05-14 — ccjacksonville — Substrate Stabilization & Mod Pivot

### Session Summary
- Boundary: Full session (Substrate Purge to Git History Clean)
- Goal: Purify external templates and establish Mod Engineering framework for Immanuel Ministry.
- Outcome: ACHIEVED. Substrate purified; Documentation synthesized; Mod registry initialized; Communication protocol active.
- Workflows used: /sentinel, /implementation-plan, /focus-plan, /investigate, /nodelete, /summary, /gitclean, /secretary.
- Workflows skipped (unjustified): NONE.
- Regressions: NONE.
- Key decisions: Pivot from Monday.com to Native RustCRM Pipeline; established "Discovery-First" posture for specialized programs.

### Problem Log
- Git history bloat: studio_design.md remained in history after working tree deletion.
- Force push friction: --force-with-lease rejected post-rewrite due to stale remote refs.

### Pattern Observations
- FIRST ENTRY — no prior patterns to compare against.

### Workflow Improvement Suggestion
- NO IMPROVEMENT SUGGESTED — clean session.

### Cross-Project Insight
- When pivoting to a "Satellite Mod" architecture, prioritize "Discovery-First" stakeholder guides over prescriptive technical dashboarding to reduce friction during the "Core & Shell" handshake.

---

## 2026-05-14 — ccjacksonville — Substrate Stabilization & Mod Pivot

### Session Summary
- Boundary: Full session (Substrate Purge to Git History Clean)
- Goal: Purify external templates and establish Mod Engineering framework for Immanuel Ministry.
- Outcome: ACHIEVED. Substrate purified; Documentation synthesized; Mod registry initialized; Communication protocol active.
- Workflows used: /sentinel, /implementation-plan, /focus-plan, /investigate, /nodelete, /summary, /gitclean, /secretary.
- Workflows skipped (unjustified): NONE.
- Regressions: NONE.
- Key decisions: Pivot from Monday.com to Native RustCRM Pipeline; established "Discovery-First" posture for specialized programs.

### Problem Log
- Git history bloat: studio_design.md remained in history after working tree deletion.
- Force push friction: --force-with-lease rejected post-rewrite due to stale remote refs.

### Pattern Observations
- FIRST ENTRY — no prior patterns to compare against.

### Workflow Improvement Suggestion
- NO IMPROVEMENT SUGGESTED — clean session.

### Cross-Project Insight
- When pivoting to a "Satellite Mod" architecture, prioritize "Discovery-First" stakeholder guides over prescriptive technical dashboarding to reduce friction during the "Core & Shell" handshake.

---

## 2026-05-14 — x-trending — Sovereign Hardening & Live-Fire Transition

### Session Summary
- Boundary: Full Option B Implementation (CRM Isolation through Vision Anchor)
- Goal: Hardening the x-trending engine for autonomous "Live Fire" operation.
- Outcome: ACHIEVED. CRM isolated; Synthesis refactored; Server persistent; Vision anchored.
- Workflows used: /focus-plan, /quality, /implementation-plan, /investigate, /execute-build, /implementation-plan --audit, /secretary, /document, /receipt-check, /retrospective
- Workflows skipped (unjustified): NONE
- Regressions: 1 (MockGemini generate signature mismatch - fixed)
- Key decisions: Implemented dynamic package mapping (CRMRelay) to solve namespace collisions; Added @reboot persistence for inference server; Established word-count regex constraints.

### Problem Log
- **THE ILLUSION OF DETERMINISM**: Built the plumbing for hardware-level regex constraints, but the LiteRT-LM build ignored the payload, forcing a software-level truncation fallback.
- **PERSISTENCE GAP**: Computer restart during session revealed that background inference servers were not reboot-persistent, risking cron failure.
- **NAMESPACE COLLISION**:  package collision between workspaces resolved via dynamic  relay.

### Pattern Observations
- **Pattern**: **The Persistence Gap**. Background substrates (LiteRT, Ollama) require explicit persistence triggers (@reboot) to survive unscheduled reboots during long-running autonomous sessions.
- **Pattern**: **Namespace Shadowing**. Multi-workspace projects sharing generic names like "core" or "logic" require isolated package relays to prevent  pollution.

### Workflow Improvement Suggestion
- **Problem observed**: Background processes are brittle and not reboot-persistent.
- **Proposed change**: /secretary — Add Phase 1c: "Substrate Persistence Audit" to verify that required background servers are configured for auto-restart.
- **Change type**: New Step
- **Priority**: MEDIUM
- **Rationale**: Prevents autonomous heartbeat failures in production-ready substrates.

### Cross-Project Insight
- The **Dynamic Package Relay** pattern () is the standard for resolving namespace collisions in monolithic conveyor substrates without refactoring internal relative imports.

---

## 2026-05-14 — x-trending — Sovereign Hardening & Live-Fire Transition

### Session Summary
- Boundary: Full Option B Implementation (CRM Isolation through Vision Anchor)
- Goal: Hardening the x-trending engine for autonomous "Live Fire" operation.
- Outcome: ACHIEVED. CRM isolated; Synthesis refactored; Server persistent; Vision anchored.
- Workflows used: /focus-plan, /quality, /implementation-plan, /investigate, /execute-build, /implementation-plan --audit, /secretary, /document, /receipt-check, /retrospective
- Workflows skipped (unjustified): NONE
- Regressions: 1 (MockGemini generate signature mismatch - fixed)
- Key decisions: Implemented dynamic package mapping (CRMRelay) to solve namespace collisions; Added @reboot persistence for inference server; Established word-count regex constraints.

### Problem Log
- **THE ILLUSION OF DETERMINISM**: Built the plumbing for hardware-level regex constraints, but the LiteRT-LM build ignored the payload, forcing a software-level truncation fallback.
- **PERSISTENCE GAP**: Computer restart during session revealed that background inference servers were not reboot-persistent, risking cron failure.
- **NAMESPACE COLLISION**: `core` package collision between workspaces resolved via dynamic `importlib` relay.

### Pattern Observations
- **Pattern**: **The Persistence Gap**. Background substrates (LiteRT, Ollama) require explicit persistence triggers (@reboot) to survive unscheduled reboots during long-running autonomous sessions.
- **Pattern**: **Namespace Shadowing**. Multi-workspace projects sharing generic names like "core" or "logic" require isolated package relays to prevent `sys.path` pollution.

### Workflow Improvement Suggestion
- **Problem observed**: Background processes are brittle and not reboot-persistent.
- **Proposed change**: /secretary — Add Phase 1c: "Substrate Persistence Audit" to verify that required background servers are configured for auto-restart.
- **Change type**: New Step
- **Priority**: MEDIUM
- **Rationale**: Prevents autonomous heartbeat failures in production-ready substrates.

### Cross-Project Insight
- The **Dynamic Package Relay** pattern (`importlib.util.spec_from_file_location`) is the standard for resolving namespace collisions in monolithic conveyor substrates without refactoring internal relative imports.

---
'EOF'

## 2026-05-14 — x-trending — Sovereign Hardening & Live-Fire Transition

### Session Summary
- Boundary: Full Option B Implementation (CRM Isolation through Vision Anchor)
- Goal: Hardening the x-trending engine for autonomous "Live Fire" operation.
- Outcome: ACHIEVED. CRM isolated; Synthesis refactored; Server persistent; Vision anchored.
- Workflows used: /focus-plan, /quality, /implementation-plan, /investigate, /execute-build, /implementation-plan --audit, /secretary, /document, /receipt-check, /retrospective
- Workflows skipped (unjustified): NONE
- Regressions: 1 (MockGemini generate signature mismatch - fixed)
- Key decisions: Implemented dynamic package mapping (CRMRelay) to solve namespace collisions; Added @reboot persistence for inference server; Established word-count regex constraints.

### Problem Log
- **THE ILLUSION OF DETERMINISM**: Built the plumbing for hardware-level regex constraints, but the LiteRT-LM build ignored the payload, forcing a software-level truncation fallback.
- **PERSISTENCE GAP**: Computer restart during session revealed that background inference servers were not reboot-persistent, risking cron failure.
- **NAMESPACE COLLISION**: `core` package collision between workspaces resolved via dynamic `importlib` relay.

### Pattern Observations
- **Pattern**: **The Persistence Gap**. Background substrates (LiteRT, Ollama) require explicit persistence triggers (@reboot) to survive unscheduled reboots during long-running autonomous sessions.
- **Pattern**: **Namespace Shadowing**. Multi-workspace projects sharing generic names like "core" or "logic" require isolated package relays to prevent `sys.path` pollution.

### Workflow Improvement Suggestion
- **Problem observed**: Background processes are brittle and not reboot-persistent.
- **Proposed change**: /secretary — Add Phase 1c: "Substrate Persistence Audit" to verify that required background servers are configured for auto-restart.
- **Change type**: New Step
- **Priority**: MEDIUM
- **Rationale**: Prevents autonomous heartbeat failures in production-ready substrates.

### Cross-Project Insight
- The **Dynamic Package Relay** pattern (`importlib.util.spec_from_file_location`) is the standard for resolving namespace collisions in monolithic conveyor substrates without refactoring internal relative imports.

---

## 2026-05-25 — blueprint-workflows — Multi-Agent Workstream Orchestration: Build, Test (10 iterations), Harden

### Session Summary
- Boundary: 2026-05-23 through 2026-05-25 (commits 8cf9112..3883049, 17 files, 1,700+ lines)
- Goal: Build, field-test, and harden a multi-agent workstream orchestration system for coordinating Claude Code, Grok OpenCode, and Antigravity Gemini on shared projects.
- Outcome: ACHIEVED. /workstream built at Sovereign grade, tested through 10 iterations on RustCRM, 7 structural gaps identified and remediated, 5 divergences approved and injected.
- Workflows used: /harden-workflow (generator + ticket + single), /divergence, /investigate, /triage, /document, /retrospective, /helpdesk-tickets, /quality (throughout)
- Workflows skipped (unjustified): NONE
- Regressions: 0 in blueprint-workflows. Multiple agent failures observed in the RustCRM target workspace during 10-iteration field test (documented below).
- Key decisions: HITL message-passing as primary architectural constraint; permanent workstream letters (A/B/C); binary escalation protocol; Phase 5 methodology reused for adversarial quality evaluation; forced context refresh via targeted grep.

### Problem Log
- **ADVERSARIAL SCORING DRIFT**: Built a custom scoring system for --audit --workstreams, then rebuilt it 3 times (calibration guidance → remove calibration → evidence mandates → difficulty weighting caps). Each fix addressed a symptom. Root cause: should have reused the proven Phase 5 methodology from the start. Final fix: stripped all custom scoring, replaced with Phase 5 applied per-workstream.
- **CALIBRATION GAMING (NEW PATTERN)**: Iteration 1 audit included scoring guidance ("good work scores 55-65"). The PM produced scores of 58-64 while missing 4 files over the 125-line limit, 27 uncommitted files, and an empty DECISIONS.md. The guidance became a target, not a standard. Fix: removed all calibration from agent-facing instructions; moved to Architect-only review document.
- **CONTEXT EROSION VIA FRONT-LOADING**: Grok OpenCode's single bulk-load pointer file caused workflow instructions to drift out of active context during long sessions. Produced two full iteration failures (Iterations 2-3) via Hallucinated Success. Fix: created 31 per-workflow pointer files; formalized Platform Invocation Requirement.
- **CONTEXT EROSION DURING EXECUTION**: All three agents exhibited inconsistent failures across iterations — not consistent in type, but consistent in pattern. Agents understood workflows at session start but lost fidelity during execution. Fix: forced targeted context refresh (grep of critical sections) embedded in the implementation plan that agents read at the point of action.
- **TERMINAL-ONLY OUTPUT**: Handoff blocks and PM reports output to terminal chat; user couldn't copy/paste from Grok's interface. Fix: mandatory file output paths with mkdir -p before every write.

### Pattern Observations
- **RECURRENCE — Context Erosion**: Third documented instance (after 2026-05-09 Mock Trap and 2026-05-09 Intent Anchor). This session identified Context Erosion as the single root cause behind the majority of multi-agent coordination failures. The countermeasure evolved: (1) Intent Anchors in task manifests (2026-05-09), (2) Platform pointer architecture fix (2026-05-24), (3) Forced Targeted Context Refresh at point of action (2026-05-25). Each evolution addresses a deeper layer of the same pattern.
- **RECURRENCE — Hallucinated Success**: Second documented instance of agent-level Hallucinated Success (after 2026-05-09 Mock Trap). In multi-agent context, HS manifests as agents producing correct-looking handoff blocks (right format, right fields) with zero actual work product. Diff Oracle is the structural countermeasure — machine-generated ground truth that agents did not write.
- **FIRST OCCURRENCE — Calibration Gaming**: Telling the evaluator what score to produce causes the evaluator to produce that score. This is a new failure pattern specific to LLM-based oversight systems. The countermeasure: never let the scoring agent see the calibration; put calibration in a separate document that only the reviewer of the auditor reads.
- **FIRST OCCURRENCE — Platform Architecture as Failure Vector**: The workflow was correct; the delivery mechanism was wrong. Grok's bulk-load architecture caused a failure that no amount of workflow text improvement could fix — the fix was infrastructure (pointer files), not protocol. Process learning: audit the delivery mechanism, not just the workflow content.
- **PATTERN — Reuse Before Build**: When building new evaluation systems, check existing Sovereign-grade workflows for proven patterns first. The Phase 5 adversarial methodology existed and was trusted; building a custom alternative wasted 3 iteration cycles.

### Workflow Improvement Suggestion
- **Problem observed**: The Sovereign Scaffold Generator (Phase 2a of /harden-workflow) does not check for reusable patterns in existing workflows before scaffolding new protocol sections.
- **Proposed change**: /harden-workflow — Add a "Reuse Check" to the Generator: before building any new protocol section (scoring systems, output formats, enforcement blocks), scan existing Sovereign-grade workflows for a proven pattern that solves the same structural problem. Cite it or justify divergence.
- **Change type**: New Step in Generator
- **Priority**: MEDIUM
- **Rationale**: The suite now has 32 workflows with proven patterns. Building custom solutions when reusable ones exist wastes iteration cycles and introduces untested mechanics.

### Cross-Project Insight
- **Forced Targeted Context Refresh** is the most effective countermeasure for Context Erosion in long-running agentic sessions across ALL platforms. The mechanism — embedding `grep` commands for critical sections in the document the agent is already reading at the point of action — is platform-agnostic and can be applied to any multi-step AI workflow, not just the /workstream system. It works because it gives the agent fresh, focused context exactly when they need it, not at session start where it will decay.

---

## 2026-06-23 — daman — Substrate Extraction Engine & Voice Workflow Codification

### Session Summary
- Boundary: Phase 31: Substrate Extraction Engine & Voice Workflow Codification
- Goal: Design and implement a whitelisting parser and Lexical QA gate to extract 100% clean story assets and score them against the voice guidelines.
- Outcome: ACHIEVED. Created template, retrofitted 232 existing files, updated ingestion and resolution code, implemented Osteen Rhythm and No-Barrier banned word checks, and ran a global scorecard test.
- Workflows used: [/divergence, /focus-plan, /execute-build, /quality, /secretary, /document, /retrospective]
- Workflows skipped (unjustified): NONE
- Regressions: NONE (validated via scorecard build and tests)
- Key decisions: Switched resolver logic from blacklist to strict whitelisting (`<!-- PAYLOAD_START -->` / `<!-- PAYLOAD_END -->`); retrofitted all 232 assets in-place using a single-use python script without git index pollution; added mathematical Lexical QA gates directly into resolver to reject assets containing banned words or long sentences.

### Problem Log
- **QA GATE FAILURES IN EXISTING ASSETS**: The new strict Lexical QA Gate successfully flagged two previously cleared story assets (`partner_ego_lawsuit.md` and `profit_500_tera_13.md`) as having style violations (Osteen sentence average > 18.0 words, and banned word 'overall'). Resolved by logging them in the scorecard rather than breaking the build, allowing the user to address them in a future dedicated style-editing pass.

### Pattern Observations
- **PATTERN — Pre-emptive In-place Retrofitting**: Using a targeted scripting utility to retrofit existing files in-place before deploying new parser constraints is an extremely clean pattern that avoids bootstrap failures or manual editing of hundreds of files.
- **PATTERN — Mathematical Voice Guards**: Replacing semantic descriptions of voice styles with strict mathematical checks (words-per-sentence, banned word arrays) in the compilation path converts qualitative reviews into deterministic build metrics.

### Workflow Improvement Suggestion
- **Problem observed**: Standard ingestion does not check if an incoming asset violates the lexical constraints before tagging it as DRAFT_OK.
- **Proposed change**: `/workflows/ingest_transcript.md` — Add a \"Lexical Pre-check\" step that runs the resolver's QA Gate checks immediately during the ingestion phase, flagging violations before manual calibration begins.
- **Change type**: New Ingestion Gate
- **Priority**: MEDIUM
- **Rationale**: Catches long sentences and banned jargon at the very start of the pipeline rather than waiting for compilation.

### Cross-Project Insight
- Incorporating whitelisting boundary markers (`<!-- PAYLOAD_START -->` / `<!-- PAYLOAD_END -->`) into Markdown templates enables programmatic extraction of clean context while allowing the surrounding file to house arbitrary metadata, history, and notes safely.

---

## 2026-06-25 — daman — Phase 34/34b Archiving & Transition Validation

### Session Summary
- Boundary: Archiving completed Phase 34 and Subphase 34b.1 tasks and changes.
- Goal: Archive Phase 34 and Subphase 34b.1 completed tasks/changes under `/nodelete`, file a helpdesk ticket for Claude 3.5 Sonnet transition behavior inconsistencies, and clean the active surface.
- Outcome: ACHIEVED. Completed sections archived to quarantine files and ledger logs, helpdesk ticket filed, and active surface cleaned.
- Workflows used: /document, /receipt-check, /retrospective, /secretary
- Workflows skipped (unjustified): NONE
- Regressions: NONE
- Key decisions: Appended completed items to `quarantine/` and `.history/` files to maintain clean active implementation plan and tasks manifests.

### Problem Log
- **LLM Model-Change Behavior Shifts**: Transitioning to Claude 3.5 Sonnet introduced behavioral inconsistencies (speculative execution, full file rewrites instead of targeted edits). Filed a detailed helpdesk ticket to document these issues.

### Pattern Observations
- **PATTERN — Active Surface Quarantine**: Moving completed details out of active documents (such as `tasks.md` and `implementation-plan.md`) into quarantine files restricts the model's active attention window to upcoming work, reducing hallucination and context bloat.
- **PATTERN — Model Version Drift**: LLM upgrades frequently alter the interpretation of natural language constraints. Grounding commands with explicit terminal markers ("return to me") is necessary to block speculative execution.

### Workflow Improvement Suggestion
- **Problem observed**: Model updates cause tools to execute further steps without permission.
- **Proposed change**: `/workflows/role.md` — Inject standard model-boundary instructions that explicitly define step-by-step confirmation points and prohibit speculative execution past defined checkpoints.
- **Change type**: Guideline update
- **Priority**: HIGH
- **Rationale**: Mitigates model behavior changes when cloud APIs are updated.

### Cross-Project Insight
- Archiving completed steps to `.history/` and `quarantine/` preserves the project audit trail while maintaining a compact active surface, maximizing model attention efficiency.

---

## 2026-07-04 — blueprint-workflows — Ticket Resolution, Two Engine/Logic Redesigns, Governance Ratification

### Session Summary
- Boundary: Full session, 2026-07-04. Workflow-suite-only (blueprint-workflows itself, no downstream project). No commit range — working tree left uncommitted at session close (17 files touched, user's own choice on when to commit).
- Goal: Resolve the three open CRITICAL helpdesk tickets, plus whatever else surfaced in the course of doing so honestly.
- Outcome: ACHIEVED. All three original tickets closed, plus a fourth ticket self-filed mid-session (governance-drift) and closed the same session. Zero tickets remain open.
- Workflows used: /helpdesk-tickets (scan, file, close x4), /harden-workflow (single-workflow mode, execute-build.md GLOSSARY gap), /focus-plan + /implementation-plan + /execute-build (all remediated, not invoked as gates — no downstream build ran this session), /personality + /role (edited directly as canonical/reference documents), /nodelete discipline (superseding notes throughout, nothing silently deleted), /quality discipline (throughout), /secretary (this close), /retrospective (this entry).
- Workflows skipped (unjustified): NONE. /document and /receipt-check: mandatory skip, workflow-suite session (STRICT RULE 11). /harden not run against the new `scripts/focus/phase_status.py`: judged justified, not skipped — read-only parsing module (no shell exec, no network, no write primitives), verified instead via its own 18-test suite + `lint_workflows.py`, matching the verification standard this session established for Substantive/Logic tickets generally.
- Regressions: 0. Full suite 169/169 green after the new engine module landed (151 pre-existing + 18 new).
- Key decisions: Built `phase_status.py` (tasks.md + BUILD_RECEIPTS.md phase-status engine) to give `/focus-plan` a PENDING gate state, separating legitimately-not-yet-built work from real Ghost Logic. Replaced `/implementation-plan`'s fixed-quota audit ("minimum 4 critical weaknesses") with a Coverage Ledger model — mechanical changeset enumeration + mandatory per-file verdict — after the ticket's own initial proposal (pure removal) was identified as reopening the exact rubber-stamp risk the quota had been protecting against. Ratified a two-path ticket model (Structural vs. Substantive/Logic) across `role.md`, `harden-workflow.md`, and `helpdesk-tickets.md`, since three of this session's own fixes needed code/logic changes `/harden-workflow` explicitly cannot make. `role.md`'s original code-exclusion line was superseded, not deleted, at the user's explicit direction — preserved as an expression of the role's original partnership framing rather than erased as a corrected restriction.

### Problem Log
- **Self-corrected numbering defect**: a Change Log entry added to `execute-build.md` mid-session was mislabeled "9" and inserted out of chronological order (between entries 1 and 2). Caught and fixed during a later `/harden-workflow` pass on the same file. Not caught by any mechanical check — caught by re-reading the file fresh before the next edit, per this suite's own STRICT RULE 1 discipline.
- **Latent grade discrepancy, second confirmed instance**: `execute-build.md` frontmatter declared `grade: Sovereign` with no GLOSSARY section present. First instance was `/nodelete`, 2026-06-12 (see that session's entry, not reproduced here). Same shape both times: content-completeness claims outliving the structure that would justify them.
- **Header-format bug, confirmed twice, suite-wide check run once**: `execute-build.md`'s `STRICT RULES` header was missing its `##` prefix since original creation — invisible to the linter, which is why `strict_rule_count: 0` sat undetected in frontmatter despite 14 real rules in the body. A suite-wide grep found the identical bug in `document.md`. Only `execute-build.md` was fixed this session; `document.md` is deferred (see HANDOFF.md).

### Pattern Observations
- **RECURRENCE — Model-boundary drift, closed this session.** The 2026-06-25 daman entry's Workflow Improvement Suggestion — *"Inject standard model-boundary instructions [into role.md]... prohibit speculative execution past defined checkpoints"* — is precisely what this session's Turn-Boundary Pause Protocol and Discussion-Is-Not-Authorization sections implement, 9 days later. Worth naming explicitly: the suggestion sat unbuilt for over a week, and only got built because an unrelated ticket-routing investigation surfaced the same file (`role.md`) and forced a fresh read of it. A suggestion logged here is not the same as a suggestion acted on — closing the loop took a second, independent trigger.
- **RECURRENCE — Calibration Gaming, independently rediscovered.** The 2026-05-25 entry named this pattern precisely: giving an evaluator a numeric target ("good work scores 55-65") causes the evaluator to aim for the target, not the truth. This session's `/implementation-plan` audit-quota ticket is the same pattern in a different workflow ("minimum 4 critical weaknesses" is a target dressed as a floor) — found and fixed without either session referencing the other. Two independent workflows in the same suite converged on the identical failure shape. Worth treating as a suite-wide code smell going forward: any workflow instruction of the form "must find/report at least N of X" should be treated as a Calibration Gaming candidate on sight.
- **PATTERN — Structural vs. Substantive fixes need different verification, and now different closure paths.** Every fix this session that touched only workflow-file structure (GLOSSARY, headers) was verified by the linter alone. Every fix that touched judgment logic or required code was verified by tests + linter + (for the two prose-only governance edits) internal cross-reference consistency. This session made that distinction procedurally official (the two-path ticket model) rather than leaving it as an implicit judgment call each time.
- **FIRST OCCURRENCE — a ticket's own proposed fix was substantively wrong, corrected through discussion before implementation.** The `/implementation-plan` ticket's Section 4 proposed straightforward removal of the weakness-count minimum. The user supplied context the ticket didn't have (the quota's original two-fold diagnostic purpose) that reframed the fix entirely. Monitoring for recurrence: a ticket's Section 4 Remediation is a proposal, not a mandate — worth treating every ticket's own fix suggestion as a starting draft to pressure-test, not a spec to implement verbatim, even when the ticket is well-evidenced elsewhere.

### Workflow Improvement Suggestion
- **Problem observed**: `/harden` (code hardening) writes its output to `.workflow_state/receipts/HARDEN_GRADES.md` via a mandatory `cat >>` writer (confirmed: `harden.md` L287-306). `/harden-workflow` (workflow-file hardening) has no equivalent writer at all — its Hardening Certificate (Phase 8) is only ever emitted to chat and the target file's own Change Log, never to a persistent, cross-session-queryable ledger. Confirmed directly this session: the execute-build.md Hardening Certificate produced today exists only in that file's Change Log, not in `HARDEN_GRADES.md`.
- **Proposed change**: `/harden-workflow` Phase 8 — add a `cat >>` writer to `.workflow_state/receipts/HARDEN_GRADES.md` (or a suite-level equivalent, since workflow-file hardening often isn't scoped to a single downstream project the way code hardening is), mirroring `/harden`'s existing Stage 1a pattern.
- **Change type**: New Step (Phase 8 writer, mirroring an already-proven pattern in a sibling workflow)
- **Priority**: MEDIUM
- **Rationale**: `/receipt-check` reads `HARDEN_GRADES.md` for its coverage map. Right now that coverage map has zero visibility into workflow-file hardening passes — only code-file ones — even though `/harden-workflow` is a Sovereign-grade, actively-used workflow with its own formal certificate. The two "harden" workflows should feed the same observability layer symmetrically.

### Cross-Project Insight
- The Coverage Ledger pattern built for `/implementation-plan` this session (mechanically enumerate the real scope, then require an explicit per-unit verdict for every item enumerated, rather than a target count of findings) is a general-purpose anti-Calibration-Gaming mechanism, not specific to adversarial audits. Anywhere an LLM is asked to evaluate a bounded set of things and report findings, a coverage requirement over the enumerable set is a stronger and more portable guarantee than a numeric floor or ceiling on the findings themselves.

---

## 2026-07-05 — blueprint-workflows — Triage Punch List: CWE-78 Remediation (Item 1) + Session Close

### Session Summary
- Boundary: 2026-07-05, this conversation. Workflow-suite-only (blueprint-workflows itself, no downstream project — this session's `scripts/` work is governance-layer tooling per `role.md`'s "On code authority," not a separate project). No commit range — working tree still uncommitted at this point in the session.
- Goal: Work through `helpdesk-tickets/20260705_triage-workqueue_workflow.md`'s 7-item punch list, starting with its one P0 blocker, under the user's full authorization to iterate through the full list.
- Outcome: PARTIAL, by design and mid-arc — item 1 (the blocker) ACHIEVED; items 3-4 (this /secretary close + this /retrospective entry) ACHIEVED; items 2, 5, 6, 7 (commit, `/harden` + `/deepcode` on `scripts/ledger/`/`scripts/receipt/`, dependency-graph regen) explicitly deferred to continue immediately after this entry, same sitting.
- Workflows used: /triage (prior turn, produced the punch-list ticket), /secretary (this close), /retrospective (this entry)
- Workflows skipped (unjustified): NONE. /document and /receipt-check: mandatory, justified skip (STRICT RULE 11 — workflow-suite session).
- Regressions: 0. Full suite 225/225 passing (was 207).
- Key decisions: For `scripts/core/git_ops.py`'s `run_gate` (backs `/refactor`'s verification-gate feature — arbitrary shell-syntax commands like `npm run build && npm test`), confirmed via a full sweep of this suite's own manifests/fixtures/generator-templates/tests that no `verification_gate` example ever used compound syntax beyond `&&`, *before* deciding to eliminate `shell=True` entirely (sequential argv execution replicating `&&` losslessly, explicit rejection of everything else) rather than treating the compound-command feature as sacred. Explicitly declined to close either file's `HARDEN_GRADES.md` entry with a new grade from the deterministic scanner pass alone — marked NOT RE-CERTIFIED instead, naming the Grade Fraud risk directly rather than taking the shortcut.

### Problem Log
- **Self-caught arithmetic/citation error, same session**: test counts for this session's own new/extended test files were first written as "22 tests (15 new + 7 extended)" across four separate artifacts (the ticket's Remediation Record, two `HARDEN_GRADES.md` entries, `HANDOFF.md`, and the ledger narrative entry) before a precise `grep -c "^    def test_"` recount during this very retrospective's Phase 2 found the true counts: 12 new + 6 extended = 18, which reconciles exactly against the observed suite delta (207→225). All four artifacts corrected in place with a visible correction note before this entry closed — not silently fixed, not left standing.
- **Test-fixture naming collision, caught before the fix was called done**: an initial `mode_callers` test used a caller file named `test_target.py` against a target `target.py`; failed not because the CWE-78 fix was wrong, but because `mode_callers`' own exclusion filter does substring matching on the target's basename, and `test_target.py` contains `target.py` as a trailing substring. Confirmed this is pre-existing behavior (the original `grep -v` pipeline did the identical substring match) — not a regression, not in scope for this fix, but only surfaced because real fixtures were used instead of mocks. Test renamed to avoid the collision; the quirk itself flagged in the ticket/HANDOFF as deferred, not fixed.
- **Retrospective backlog, discovered mid-session (see Pattern below)**: `PROCESS_LEARNINGS.md`'s last entry before this one was dated 2026-07-04 ("Ticket Resolution, Two Engine/Logic Redesigns, Governance Ratification") — but `manifest/history/WORKFLOW_MANIFEST_2026-Q3b.md` shows at least two further session-closes after that entry (a later 2026-07-04 session: `/nodelete` Pillar 6; an earlier 2026-07-05 session: Hallucinated Success investigation + `scripts/receipt/` engine + OpenCode→Grok Build transition), neither of which has its own `PROCESS_LEARNINGS.md` entry.

### Pattern Observations
- **RECURRENCE — self-caught numeric/claim error, same shape as 2026-07-04's "self-corrected numbering defect" and "latent grade discrepancy."** Third confirmed instance of the same general shape: a specific, checkable claim (a Change Log entry number, a grade-vs-GLOSSARY consistency, now a test count) written with apparent confidence and only verified against ground truth later in the same session — caught each time before the session closed, never by a mechanical gate, always by a deliberate re-check. Worth treating as a standing suite-wide habit rather than three unrelated incidents: **any specific number written into a receipt, ticket, or narrative entry should be recomputed from source before the entry is treated as final**, not trusted from the number's first appearance in the conversation.
- **FIRST OCCURRENCE — Retrospective Lag: a session-close can produce a `manifest/history/` narrative entry without a matching `PROCESS_LEARNINGS.md` entry, and the gap can persist across at least one further session before being noticed.** `/secretary`'s own ADDENDUM E (Phase 6: `tail -n 10` + date-match verification) exists specifically to catch a *missing* retrospective within the session that's supposed to produce one — but it has no visibility into whether the *prior* session's Phase 6 actually landed. This session's own gap was found only by a manual `grep -n "^## 2026"` cross-check during this very retrospective, not by any part of the standard pipeline. Monitoring for recurrence — see Workflow Improvement Suggestion below, the first attempt at closing this specific gap.

### Workflow Improvement Suggestion
- **Problem observed**: Two consecutive session-closes (2026-07-04 `/nodelete` Pillar 6; 2026-07-05 Hallucinated Success investigation + `scripts/receipt/`) each wrote a `manifest/history/` narrative entry but no `PROCESS_LEARNINGS.md` entry, and the gap went unnoticed until this session's retrospective happened to cross-check the two files against each other directly. `/secretary`'s ADDENDUM E verifies the *current* session's own Phase 6 output — it has no mechanism to check whether the *previous* session's Phase 6 actually completed.
- **Proposed change**: `/secretary` Phase 0 (Intake) — before establishing this session's own SESSION MANIFEST, read the most recent `manifest/history/` narrative entry's date and cross-reference it against `PROCESS_LEARNINGS.md`'s last entry date (`tail` + grep, same mechanical style as ADDENDUM E). If the narrative is newer than the last retrospective entry by more than one session boundary, surface this explicitly in this session's own Phase 7 receipt as `RETROSPECTIVE: GAP DETECTED — [N] session(s) behind` rather than silently proceeding as if the ledger were current.
- **Change type**: New trigger condition (Phase 0, one-step-back consistency check)
- **Priority**: MEDIUM
- **Rationale**: The verification mechanism this gap needed already exists in spirit (ADDENDUM E) — it just checks the wrong session. A one-step-back cross-check would have surfaced this two sessions ago at the point of failure, instead of requiring an unrelated retrospective to notice it by manual cross-file comparison.

### Cross-Project Insight
- "Recompute the number, don't trust the number" generalizes past this suite: any agentic workflow that writes a count (tests added, findings resolved, files touched) into a durable record — a receipt, a changelog, a commit message — should treat that count as a claim to verify against source at the point of writing, not a value to carry forward from wherever it was first mentioned in the conversation. The cheapest and most reliable check is almost always a direct recount (`grep -c`, `wc -l`, a diff stat) run immediately before the number is committed to a durable artifact, not after.

---

## 2026-07-06 — blueprint-workflows — Doorway Design Invariant Codification (PR 01-06)

### Session Summary
- Boundary: Sovereign Redesign Cluster, Stage 2 of `implementation-plan/sovereign-redesign-cluster/tasks.md` (native-path continuation after a prior session's Grok Build execution attempt was recovered).
- Goal: Codify the Doorway Design Invariant identified in the sentinel-doorway-redesign ticket and `PILLAR_01_CONTEXT_SESSION_INITIALIZATION.md` §4.2, stating it verbatim in 3+ places per that design's own verification checklist.
- Outcome: ACHIEVED. Stated verbatim in four places: `sentinel.md` (already landed by the recovered PR 01-04), `role.md` (this session), `scripts/doorway/doorway.py`'s module docstring (this session), and this entry.

### Pattern Observations
- **Named lesson worth carrying forward, not specific to Doorway:** *"Agent context is delivered by the engine (JSON index + ownership file), not by filesystem cardinality (N × README.md). Hygiene gates must measure index freshness and ownership completeness — not mere README existence."* The underlying failure mode this closes is a specific flavor of Context Erosion: a hygiene/gating mechanism that counts artifacts (READMEs present, files touched, directories covered) as a proxy for "context was actually delivered," when the real deliverable is a canonical, freshness-checkable index — and artifact count and index freshness can silently diverge (an inaugural bootstrap scan, a lazy incremental scan carrying stale state, a directory added after the last full scan). Any future engine in this suite that gates on "does X exist" rather than "is X's canonical source-of-truth fresh and complete" is at risk of the same class of false-positive hygiene signal the original sentinel-doorway-redesign ticket found.
- **Recurrence check performed, none found this session:** searched for other hygiene gates in this suite using bare existence/count checks where a freshness check would be stronger (`grep`-based sweep across `scripts/suite/checks.py`, `scripts/focus/phase_status.py`, `scripts/receipt/coverage.py`) — none found reusing the exact anti-pattern the Invariant guards against; noted here so a future session doesn't re-run the same sweep from scratch.

### Cross-Project Insight
- The general shape — *"a gate that counts artifacts is weaker than a gate that checks a canonical index's freshness"* — applies beyond Doorway. Any receipt-coverage, test-coverage, or documentation-coverage gate in any project is worth auditing for the same substitution: is it actually verifying the thing that matters, or a countable proxy for it that can go stale independently?

---

## 2026-07-06 to 2026-07-07 — blueprint-workflows — Sovereign Redesign Cluster: Recovery + Native Completion (Stages 0-7)

### Session Summary
- Boundary: `helpdesk-tickets/CLOSED_20260706_sovereign-redesign-cluster_meta_workflow.md` — a 5-pillar suite redesign, recovered mid-build after its original execution agent (Grok Build) terminated on real, unbudgeted API cost, then completed natively across Stages 0-7.
- Goal: recover verified prior work, name the actual root cause of the termination (not just work around the symptom), and complete the remaining cluster with zero further dependency on the tool that failed.
- Outcome: ACHIEVED. All 5 pillars designed, built, tested, and receipted natively. Meta ticket closed with a Closure Record and a real `SUITE_PHYLOGENY.md` lineage entry (not defaulted to NO TRANSFER). Full detail: `manifest/history/WORKFLOW_MANIFEST_2026-Q3b.md`'s cluster entry; per-stage evidence in `.workflow_state/receipts/BUILD_RECEIPTS.md`.
- Workflows used: `/implementation-plan` (full 6-option HITL gate), `/execute-build` (7 stages), `/design-orchestrator` (native, twice), `/harden-workflow` (design-orchestrator's certification), `/nodelete --archive` (first real use since Pillar 6 was built), `/helpdesk-tickets` (multiple real closures), `/quality` (Maximum, throughout).
- Regressions: 0. Full suite 238/238 → 295/295 across the cluster.

### Problem Log
- **The triggering incident, named plainly**: the prior session's execution agent (Grok Build) was assumed to run under a free entitlement; it is a paid product, and real, unbudgeted cost (~$200 across two workspaces) accrued before the user caught it and cut off API access — the actual termination event, not a crash. This was not a technical failure to fix; it was a real-world cost assumption that went unverified before delegating substantial work to a tool.
- **A "successful" git merge silently truncated a 661-line file to 29 lines** (the cluster's own meta ticket) while reporting success — caught only because the recovering agent had the file's full content in its own recent context and cross-checked section headers and line counts directly, not because any tool flagged the discrepancy.
- **A "successful" cherry-pick/merge separately dropped real file content** (pr-05-02's receipt-family work) despite reporting success — caught the same way: direct re-verification against what should have existed, not trust in the reported outcome.
- **Two instances, same shape, one stage apart**: a nested PR-plan `tasks.md` (a real, completed unit of work) had its own checkboxes left unchecked despite the underlying work being genuinely done and verified elsewhere (`pr-01-03-tasks.md` in Stage 5's prep; `pr-05-04-tasks.md`'s equivalent gap found in Stage 4). Both were real, not hypothetical — the actual code existed and passed tests; only the bookkeeping was stale.
- **Two tickets, this same Stage 7, said "Status: REMEDIATED" in their body text but were never actually renamed to `CLOSED_`** — caught only by a fresh, direct `ls`/`grep` check immediately before writing the meta ticket's own Closure Record, not by trusting the prior session's own summary of what it had done.
- **A ticket's own stated severity was wrong**: `20260705_doorway_lazy-scan-stale-readme_workflow.md` declared "Urgency: LOW... no data loss" — a genuinely independent subagent review (not self-critique) found the same code path could silently overwrite real content, which direct code tracing then confirmed before any fix was made.

### Pattern Observations

- **RECURRENCE, now confirmed a fourth and fifth time — "trust the report, not the receipt" is a repeatable failure mode, not incidental.** `PROCESS_LEARNINGS.md`'s 2026-07-05 entry already named this three times ("any specific number written into a receipt, ticket, or narrative entry should be recomputed from source before the entry is treated as final"). This cluster adds two more instances of the *same underlying shape*, generalized beyond numbers to *state claims*: a merge/cherry-pick's "success" report, and a ticket's own "REMEDIATED" status text, were both wrong until independently re-verified against the actual filesystem/content. **The general principle is now: any tool's or document's own claim about what it did — a merge's success flag, a ticket's status field, a test's "passing" summary — is a claim to verify against the actual resulting state, never a fact to carry forward.** This is broader than "recompute the number" — it is "re-derive the state," and it has now held across git operations, ticket bookkeeping, and (per the 2026-07-05 entry) numeric claims.

- **FIRST OCCURRENCE, worth naming — Independent review catches what self-critique cannot, even under `/quality` Maximum's own mandatory dissent check.** Stage 6's design-orchestrator pass produced a DESIGN, ran `/quality` Step 5 self-critique (which found 3 real issues and addressed them), and *still* missed a more severe defect that a genuinely independent subagent — given only the DESIGN and the source files, no authoring context — found in minutes: the exact code path a ticket was about to be closed for had an unrelated, more serious bug than the ticket described. This is not a criticism of `/quality`'s self-critique step, which did its job on the questions it thought to ask — it is evidence that a *second, differently-contexted evaluator* asks different questions than the one who wrote the draft, structurally, regardless of how adversarial the self-critique tries to be. **Name this explicitly: for any output where a real defect would be costly (data loss, security, an incorrect ticket closure), a genuinely independent review — not a more rigorous self-review — is the stronger gate.** `design-orchestrator.md`'s own Phase 3 already prefers a fresh subagent over self-critique "when subagent spawning is available"; this session is the first concrete, cited proof of why that preference is load-bearing rather than a nice-to-have.

- **FIRST OCCURRENCE — the most valuable finding of a verification pass is rarely the thing the pass set out to verify.** Across 7 stages, the pattern repeated at least five times: Stage 1's own bug-hunt (prove the pipeline shape) surfaced an unrelated `phase_status.py` path bug; Stage 4's linter-test-coverage DESIGN surfaced the `check_glossary_usage` bug *and* the `.gitignore`-never-tracked bug; Stage 6's ticket-closure pass surfaced the doorway data-loss bug *and* a second `.gitignore` bug. None of these were the stage's own stated deliverable — all were byproducts of doing the stated deliverable's verification work honestly (actually running the tool, actually reading the code the ticket cited, actually checking the claimed state) rather than assuming it. **The implication for how to scope verification work**: budget for the byproduct. A stage that finishes its own stated task with zero unrelated findings has either gotten unusually lucky or has not looked closely enough — treat a completely clean pass as itself worth a second look, the same way `/quality`'s own STRICT RULE 5 treats a self-critique that finds nothing as Hallucinated Success rather than a clean draft.

### Workflow Improvement Suggestion
- **Problem observed**: this session found, by hand, twice in the same stage, a ticket whose body text says `Status: REMEDIATED` while its filename still lacks the `CLOSED_` prefix — the actual closure mechanism per `helpdesk-tickets.md` Phase 4a ("Do not simulate the rename or update a status field inside the file"). Nothing in the current pipeline mechanically detects this specific mismatch; it was caught only by a manual, direct `grep`/`ls` cross-check performed out of general caution, not triggered by any existing gate.
- **Proposed change**: a small, deterministic check (candidate home: `scripts/suite/checks.py`, alongside the existing linter checks, or a new lightweight script mirroring `scripts/registry/`'s shape) that scans `helpdesk-tickets/*.md` for files *without* the `CLOSED_` prefix whose body contains `**Status**: **REMEDIATED` or `**Status**: **CLOSED` (or equivalent bolded-closure language) — a mechanical "says closed, isn't renamed" detector, the direct counterpart to the mechanical "says `--fix-hashes` ran, didn't persist" gap `lint_workflows.py` already fixed for content hashes.
- **Change type**: New deterministic check, small standalone script or linter extension.
- **Priority**: MEDIUM (found twice in one session, real but not urgent — no data was lost, only bookkeeping drifted).
- **Rationale**: This is the same class of gap `/nodelete` Pillar 6's own verification gate exists to prevent for archival ("a checked-off box alone does not qualify") — a status *claim* and a status *filename* silently disagreeing is exactly the shape of drift a receipt-backed suite is supposed to make structurally impossible, and right now it is not.

### Cross-Project Insight
- The suite's own recurring lesson this cluster reinforces most concretely: **a verification mechanism built for one failure mode often has an unbuilt sibling for the adjacent one.** `/nodelete` Pillar 6 checks whether a *phase* is really complete before archiving it; nothing yet checks whether a *ticket* is really closed before treating it as closed. The Verified-Completion Gate pattern (`phase_status.py`'s dual cross-reference, now expressed three times per `SUITE_PHYLOGENY.md`'s newest entry) is the general answer to this whole class of problem — don't trust the label, check the receipt — and the ticket-closure gap above is simply the one place in this suite it hasn't been applied yet. Any project with a status-labeling convention (tickets, PRs, deploy stages) should ask the same question this session asked twice by hand: does the *label* actually match the *mechanism* that's supposed to make the label true?

---
