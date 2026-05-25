---
description: "Post Modularization Test Package Workflow — QA verification suite for decomposed modules"
type: audit
grade: Hardened
version: 2
content_hash: "sha256:e6d915f1cc624e1c"
last_hardened: "2026-05-07"
strict_rule_count: 0
phase_count: 0
context_retention: medium
flags: []
dependencies:
  - "/soc"
triggers: []
produces: []
consumes: []
platform_requirements:
  file_write: false
  shell_exec: true
  git_access: true
---

You are an expert QA automation engineer. Execute this complete, best-practice workflow to build a production-ready "Post Modularization Test Package" for newly refactored or extracted modules:

1. **Module Inventory & Dependency Mapping**  
   Catalog every new/refactored module, document public APIs/contracts, internal dependencies, and generate a visual dependency graph.

2. **Unit Test Creation**  
   Write isolated unit tests for each module (target >85% code coverage) covering happy paths, edge cases, error handling, and boundary conditions using your project's preferred framework.

3. **Contract & Interface Testing**  
   Create contract tests to validate that each module's inputs/outputs and API surfaces remain compatible with consumers and other modules.

4. **Integration Testing**  
   Build integration tests that verify correct interaction between the new modules and existing system components (database, services, external calls).

5. **Smoke Test Development**  
   Create lightweight smoke tests that quickly confirm core functionality and critical user journeys still work after modularization.

6. **Dry-Run & Staging Simulation**  
   Implement full dry-run tests and staging-environment simulations that mimic production behavior without side effects, including configuration validation and rollback checks.

7. **Regression & Impact Testing**  
   Update the existing regression suite and add targeted tests for any legacy code paths affected by the modularization.

8. **Test Data & Environment Management**  
   Package all required test data fixtures, environment setup scripts, and containerized test environments.

9. **Automation & CI/CD Packaging**  
   Bundle the entire test suite into a reusable, versioned test package (with runners, parallel execution configs, reporting dashboards, and CI/CD pipeline integration scripts).

10. **Performance, Security & Compliance Checks**  
    Add lightweight performance benchmarks, security scans, and compliance validation steps specific to the modular changes.

11. **Documentation & Reporting**  
    Generate complete documentation: execution guide, test coverage report, known limitations, and automated result summary templates.

12. **Peer Review & Sign-Off**  
    Perform internal review, run the full package end-to-end, and obtain stakeholder approval before marking the test package as "ready for release".

Output the final test package as a self-contained artifact ready for immediate use in CI/CD pipelines.

### Change Log
1. **[ORIGINAL]**: Created as a standalone post-modularization test package workflow.
2. **2026-05-21**: `[PORTED — Claude Code migration]` Standalone file confirmed as single merged command at `~/blueprint-workflows/claude-commands/testpackage.md`. No content changes.
