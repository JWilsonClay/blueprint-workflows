# Testing the Refactor Script Suite

This document explains how to execute the Post-Modularization Test Package and interpret the results.

## 🚀 Quick Start

To run the entire test suite:
```bash
./run_tests.sh
```

## 📋 Test Suite Structure

- **`tests/test_manifest.py`**: Unit tests for manifest loading and validation.
- **`tests/test_filesystem.py`**: Unit tests for project scanning and skip-logic.
- **`tests/test_shim_templates.py`**: Unit tests for shim generation and relative path math.
- **`tests/test_git_ops.py`**: Unit tests for git movement and verification gates (mocked).
- **`tests/test_contracts.py`**: Ensures the `core` library maintains a stable API surface.
- **`tests/test_integration.py`**: End-to-end simulation of a refactor workflow on a mock repository.
- **`tests/smoke_test.py`**: Lightweight check to verify all scripts can load and show help.

## 🔬 Coverage Reporting

If `coverage` is installed, the `run_tests.sh` script will automatically generate a coverage report.

To install coverage:
```bash
pip install coverage
```

## 🔐 Security Considerations

The `core.git_ops.run_gate` function executes commands via `shell=True`. This is necessary to support complex user-defined verification gates (e.g., `npm test && pytest`). 

**Mitigation**: The `REFACTOR_MANIFEST.yaml` is the ONLY source for these commands, and it MUST be reviewed and approved by a human (Phase 0) before Phase 1 begins.

## ⚡ Performance

The `walk_project` logic is optimized to skip non-source directories (`node_modules`, `.git`, etc.), ensuring fast performance even on large codebases.
