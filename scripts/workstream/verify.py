#!/usr/bin/env python3
"""
verify.py — Sovereign Verification Substrate CLI
=================================================
Project-agnostic verification tool for multi-agent workstream orchestration.
Performs pre-flight checks, diff oracle analysis, dependency tracing, and
caller map generation against any target workspace.

Usage:
    python verify.py --workspace /absolute/path --mode <mode> [options]

Required:
    --workspace PATH    Absolute path to the target workspace root.
    --mode MODE         One of: preflight, diff-oracle, dependency, callers

Mode-specific options:
    --mode preflight        No additional options. Checks git state, build, file sizes.
    --mode diff-oracle      --since DATE (default: 7 days ago). Git diff ground truth.
    --mode dependency       --files FILE[,FILE,...] Trace imports for specified files.
    --mode callers          --file FILE  Scan for all callers of a single target file.

Optional:
    --limit N           File size limit in lines (default: 125).
    --output-json       Emit results as JSON to stdout.
    --quiet             Suppress all output except errors and structured output.

Workflow calling convention:
    python ~/blueprint-workflows/scripts/workstream/verify.py \\
        --workspace /path/to/project --mode preflight

Data directory:
    Runtime state stored in {workspace}/.workflow_state/verify/ (auto-created).

Origin: Divergence synthesis from /workstream 10-iteration investigation (2026-05-25).
Consolidates: Pre-Flight Manifest, Diff Oracle, Dependency Boundary Scan, and
soc_caller_scan.py (D4 from helpdesk ticket 20260515_soc_caller_scan_script.md).
"""

import argparse
import os
import subprocess
import sys
import re
from pathlib import Path


def run_cmd(cmd, cwd=None):
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# MODE: preflight
# ---------------------------------------------------------------------------
def mode_preflight(workspace, limit):
    print(f"PRE-FLIGHT MANIFEST — {workspace}")
    print("━" * 50)

    git_out, _, rc = run_cmd("git status --short", cwd=workspace)
    dirty_count = len(git_out.splitlines()) if git_out else 0
    git_status = "CLEAN" if dirty_count == 0 else f"DIRTY — {dirty_count} files"
    print(f"Git working tree:    {git_status}")
    if git_out:
        for line in git_out.splitlines()[:10]:
            print(f"  {line}")

    build_status = "UNKNOWN"
    pkg_json = os.path.join(workspace, "package.json")
    cargo_toml = os.path.join(workspace, "Cargo.toml")
    if os.path.exists(pkg_json):
        _, _, rc = run_cmd("npm run lint 2>&1 | tail -5", cwd=workspace)
        build_status = "PASS" if rc == 0 else f"FAIL (exit {rc})"
    elif os.path.exists(cargo_toml):
        _, _, rc = run_cmd("cargo check 2>&1 | tail -5", cwd=workspace)
        build_status = "PASS" if rc == 0 else f"FAIL (exit {rc})"
    print(f"Build status:        {build_status}")

    violations = []
    extensions = ("*.ts", "*.tsx", "*.py", "*.rs", "*.js", "*.jsx")
    for ext in extensions:
        find_out, _, _ = run_cmd(
            f"find . -name '{ext}' ! -path '*/node_modules/*' ! -path '*/__pycache__/*' "
            f"! -path '*/target/*' ! -path '*/.git/*' -exec wc -l {{}} + 2>/dev/null "
            f"| sort -rn | head -20",
            cwd=workspace,
        )
        for line in find_out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].isdigit():
                loc = int(parts[0])
                fpath = parts[1]
                if loc > limit and fpath != "total":
                    violations.append((loc, fpath))

    violations.sort(reverse=True)
    if violations:
        print(f"Files over {limit}-line limit: {len(violations)}")
        for loc, fpath in violations[:15]:
            print(f"  {loc:>5} {fpath}")
    else:
        print(f"Files over {limit}-line limit: 0")

    print("━" * 50)
    blocked = dirty_count > 0 and build_status.startswith("FAIL")
    decision = "BLOCKED" if blocked else "PROCEED"
    print(f"DECISION: {decision}")
    return 0 if decision == "PROCEED" else 1


# ---------------------------------------------------------------------------
# MODE: diff-oracle
# ---------------------------------------------------------------------------
def mode_diff_oracle(workspace, since):
    print(f"DIFF ORACLE — {workspace}")
    print("━" * 50)

    git_out, _, _ = run_cmd("git status --short", cwd=workspace)
    uncommitted = len(git_out.splitlines()) if git_out else 0
    print(f"Uncommitted files:    {uncommitted}")

    diff_out, _, _ = run_cmd(
        f'git log --oneline --since="{since}"', cwd=workspace
    )
    commits = diff_out.splitlines() if diff_out else []
    print(f"Commits since {since}: {len(commits)}")

    if commits:
        first_hash = commits[-1].split()[0]
        stat_out, _, _ = run_cmd(
            f"git diff --stat {first_hash}^..HEAD 2>/dev/null || git diff --stat {first_hash}..HEAD",
            cwd=workspace,
        )
        print(f"\nFiles changed (git):")
        for line in stat_out.splitlines():
            print(f"  {line}")

    print("━" * 50)
    return 0


# ---------------------------------------------------------------------------
# MODE: dependency
# ---------------------------------------------------------------------------
def mode_dependency(workspace, files):
    print(f"DEPENDENCY BOUNDARY SCAN — {workspace}")
    print("━" * 50)

    for target in files:
        basename = os.path.basename(target).replace(".ts", "").replace(".tsx", "").replace(".py", "").replace(".rs", "")
        print(f"\n  Target: {target}")
        print(f"  Basename: {basename}")

        grep_out, _, _ = run_cmd(
            f'grep -rn "import.*{basename}\\|from.*{basename}\\|require.*{basename}" '
            f'--include="*.ts" --include="*.tsx" --include="*.py" --include="*.rs" '
            f'--include="*.js" . 2>/dev/null | grep -v node_modules | grep -v __pycache__ '
            f'| grep -v ".git/" | grep -v target/',
            cwd=workspace,
        )
        if grep_out:
            importers = grep_out.splitlines()
            print(f"  Imported by: {len(importers)} files")
            for imp in importers[:20]:
                print(f"    {imp}")
        else:
            print("  Imported by: 0 files")

    print("\n" + "━" * 50)
    return 0


# ---------------------------------------------------------------------------
# MODE: callers
# ---------------------------------------------------------------------------
def mode_callers(workspace, target_file):
    """
    Generates a structured CALLER MAP for a target file.
    Scans for: direct imports, barrel/index re-exports, framework registries,
    dynamic imports, and test fixtures.
    Output matches SOC_MANIFEST.md CALLER MAP format.
    """
    print(f"CALLER MAP — {target_file}")
    print(f"Workspace: {workspace}")
    print("━" * 50)

    basename = os.path.basename(target_file)
    stem = Path(basename).stem
    ext = Path(basename).suffix

    categories = {
        "direct_imports": [],
        "barrel_exports": [],
        "framework_registries": [],
        "dynamic_imports": [],
        "test_fixtures": [],
    }

    grep_out, _, _ = run_cmd(
        f'grep -rn "{stem}" --include="*.ts" --include="*.tsx" --include="*.py" '
        f'--include="*.rs" --include="*.js" --include="*.jsx" . 2>/dev/null '
        f'| grep -v node_modules | grep -v __pycache__ | grep -v ".git/" '
        f'| grep -v "target/" | grep -v "{basename}"',
        cwd=workspace,
    )

    if not grep_out:
        print("No callers found.")
        print("━" * 50)
        return 0

    for line in grep_out.splitlines():
        lower = line.lower()
        filepath = line.split(":")[0] if ":" in line else ""

        is_test = any(t in filepath.lower() for t in ["test", "spec", "mock", "fixture", "__tests__"])
        is_index = any(idx in filepath for idx in ["index.ts", "index.js", "__init__.py", "mod.rs"])
        is_registry = any(
            r in lower
            for r in ["router", "app.use", "urlpatterns", "app.route", "register", ".mount"]
        )
        is_dynamic = any(d in lower for d in ["importlib", "import_module", "require(", "import("])
        is_import = any(i in lower for i in ["import ", "from ", "use ", "mod "])

        if is_test:
            categories["test_fixtures"].append(line.strip())
        elif is_index:
            categories["barrel_exports"].append(line.strip())
        elif is_registry:
            categories["framework_registries"].append(line.strip())
        elif is_dynamic:
            categories["dynamic_imports"].append(line.strip())
        elif is_import:
            categories["direct_imports"].append(line.strip())
        else:
            categories["direct_imports"].append(line.strip())

    print("\n## CALLER MAP")
    for category, entries in categories.items():
        print(f"- {category}:")
        if entries:
            for entry in entries:
                print(f"    {entry}")
        else:
            print("    (none)")

    total = sum(len(v) for v in categories.values())
    print(f"\nTotal callers: {total}")
    print("━" * 50)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Sovereign Verification Substrate — project-agnostic verification tool"
    )
    parser.add_argument("--workspace", required=True, help="Absolute path to workspace root")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["preflight", "diff-oracle", "dependency", "callers"],
        help="Verification mode",
    )
    parser.add_argument("--files", help="Comma-separated file list (dependency mode)")
    parser.add_argument("--file", help="Single target file (callers mode)")
    parser.add_argument("--since", default="7 days ago", help="Date range (diff-oracle mode)")
    parser.add_argument("--limit", type=int, default=125, help="File size limit in lines")
    parser.add_argument("--output-json", action="store_true", help="JSON output")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output")

    args = parser.parse_args()

    if not os.path.isdir(args.workspace):
        print(f"ERROR: workspace {args.workspace} does not exist", file=sys.stderr)
        sys.exit(1)

    ensure_dir(os.path.join(args.workspace, ".workflow_state", "verify"))

    if args.mode == "preflight":
        sys.exit(mode_preflight(args.workspace, args.limit))
    elif args.mode == "diff-oracle":
        sys.exit(mode_diff_oracle(args.workspace, args.since))
    elif args.mode == "dependency":
        if not args.files:
            print("ERROR: --files required for dependency mode", file=sys.stderr)
            sys.exit(1)
        file_list = [f.strip() for f in args.files.split(",")]
        sys.exit(mode_dependency(args.workspace, file_list))
    elif args.mode == "callers":
        if not args.file:
            print("ERROR: --file required for callers mode", file=sys.stderr)
            sys.exit(1)
        sys.exit(mode_callers(args.workspace, args.file))


if __name__ == "__main__":
    main()
