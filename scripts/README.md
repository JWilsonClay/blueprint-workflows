# global_workflows/scripts — Sovereign Toolkit Scripts

Executable Python scripts callable by any workflow or agent in the global_workflows suite.
All scripts are workspace-agnostic: they accept a `--workspace /absolute/path` argument
and derive all internal paths from it. No script contains hardcoded workspace paths.

---

## doorway/ — Sovereign Workspace Contextualizer

Drift detection, breadcrumb regeneration, MANIFEST synchronization, and protocol
recommendations for any target workspace.

### Calling Convention

```bash
# Standard run — human-readable report:
python /home/jwils/.gemini/antigravity/global_workflows/scripts/doorway/doorway.py \
  --workspace /absolute/path/to/workspace

# Full deep scan (ignores hash cache):
python .../doorway.py --workspace /path --full-scan

# Apply approved breadcrumb proposals:
python .../doorway.py --workspace /path --auto-apply

# JSON output for workflow consumption:
python .../doorway.py --workspace /path --output-json

# Quiet mode (errors only):
python .../doorway.py --workspace /path --quiet
```

### Workflow Invocation Pattern

```bash
# From within a workflow that needs workspace health data:
SCRIPTS_DIR="/home/jwils/.gemini/antigravity/global_workflows/scripts"
TARGET_WORKSPACE="/home/jwils/Public/.blueprints"
python "${SCRIPTS_DIR}/doorway/doorway.py" --workspace "${TARGET_WORKSPACE}" --output-json
```

### Data Directory

Runtime state is stored in `{workspace}/.doorway/` (hidden, workspace-local, gitignored):
- `workspace_snapshot.json` — previous scan state for hash-based delta detection
- `context_updates.log` — pending breadcrumb proposals (agent fills; --auto-apply applies)
- `ctw_last_success.json` — last zero-finding certificate
- `repair_implementation_plan.md` — audit repair plan (present only if violations found)

### Modules

| File | Role |
|------|------|
| `doorway.py` | CLI entry point; orchestrates all tiers |
| `scanner.py` | Hash-based recursive drift detection |
| `breadcrumb.py` | BREADCRUMB/INTERFACE/REQUESTS/WORKLOG tag surgery in READMEs |
| `integrity.py` | Self-healing: creates missing READMEs and governance files from templates |
| `auditor.py` | Structural drift comparison: new / modified / deleted / unowned / missing_readme |
| `recommender.py` | Maps drift conditions → workflow/protocol IDs |
| `manifest.py` | MANIFEST.md auto-sync + Architecture.md Global API Map |
| `reporter.py` | Console and JSON output rendering |
| `audit_repairs.py` | Tier 2 qualitative audit + Tier 3 repair plan / success certificate |
| `templates/` | README.md.template, repair_plan.md.template, Architecture.md.template, etc. |

### Provenance

Extracted and refactored from `.blueprints/governance/thedoorway/` (2026-05-09).
Original design: .blueprints project. Refactor: global_workflows integration.
Key changes: removed all hardcoded PROJECT_ROOT constants; workspace path flows
through every constructor argument; data stored in `.doorway/` not `data/`;
`--output-json` mode added for workflow consumption.

---

## Adding New Scripts

1. Create your script in `scripts/` or a named subdirectory.
2. Accept `--workspace PATH` as the primary input argument.
3. Never hardcode workspace paths. Resolve everything from `Path(args.workspace).resolve()`.
4. Document the calling convention in this README.
5. Run `/harden` before considering it production-ready.


<!-- BREADCRUMB -->
MODULE:scripts TYPE:scripts LANG:python FILES:11(README.md,run_tests.sh,refactor_audit.py...) SUBDIRS:core/,doorway/,focus/,gitignore/,harden/,iterate/,ledger/,quality/,receipt/,registry/,suite/,tests/,workstream/ PURPOSE:sovereign-suite-executable-toolkit DEPS-DETECTED:pytest DRIFT:new-directory SCANNED:2026-07-05
<!-- BREADCRUMB_END -->
