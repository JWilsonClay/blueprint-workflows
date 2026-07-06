#!/usr/bin/env python3
"""
lint_workflows.py — Sovereign Suite Protocol Linter
====================================================
Treats workflow .md files as source code and validates internal consistency,
cross-references, structural requirements, frontmatter integrity, and
symlink health across the entire suite.

Usage:
    python lint_workflows.py --workspace ~/blueprint-workflows
    python lint_workflows.py --workspace ~/blueprint-workflows --file workstream.md
    python lint_workflows.py --workspace ~/blueprint-workflows --generate-graph
    python lint_workflows.py --workspace ~/blueprint-workflows --fix-hashes

Origin: Workspace-level Divergence #1 (The Living Specification), 2026-05-25.

SoC decomposition (2026-05-25):
  Data models + constants -> suite/models.py
  All check functions     -> suite/checks.py
  Dependency graph        -> suite/graph.py
  Report formatting       -> suite/report.py
  CLI + orchestration     -> this file
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from suite.models import COMMANDS_DIR, SYMLINK_DIR, OPENCODE_DIR, ANTIGRAVITY_DIR, LintReport, LINT_EXCLUDE_FILES
from suite.checks import (
    parse_frontmatter, compute_content_hash,
    check_frontmatter, check_structure, check_cross_references,
    check_symlinks, check_content_hash, check_glossary_usage,
    check_runtime_availability,
)
from suite.graph import generate_dependency_graph
from suite.report import print_report


def lint_single(workspace_root, wf_file, all_files, report):
    commands_dir = Path(workspace_root) / COMMANDS_DIR
    wf_path = commands_dir / wf_file

    if not wf_path.exists():
        report.add("CRITICAL", wf_file, "existence", "File does not exist")
        return

    content = wf_path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(content)
    size = wf_path.stat().st_size

    if size > 50000:
        report.add("INFO", wf_file, "size", f"File is {size:,} bytes (exceeds 50KB clarity threshold)")

    check_frontmatter(fm, wf_file, report)
    check_structure(body, wf_file, fm, report)
    check_cross_references(body, wf_file, all_files, report)
    check_symlinks(wf_file, workspace_root, report)
    check_content_hash(content, fm, wf_file, report)
    check_glossary_usage(body, wf_file, report)

    wf_findings = [f for f in report.findings if f.workflow == wf_file]
    if not any(f.severity in ("CRITICAL", "WARNING") for f in wf_findings):
        report.workflows_clean += 1


def main():
    parser = argparse.ArgumentParser(
        prog="lint_workflows.py",
        description="Sovereign Suite Protocol Linter — validates workflow .md files"
    )
    parser.add_argument("--workspace", required=True, help="Path to blueprint-workflows root")
    parser.add_argument("--file", help="Lint a single workflow file (e.g., workstream.md)")
    parser.add_argument("--generate-graph", action="store_true",
                        help="Generate dependency_graph.json in manifest/")
    parser.add_argument("--fix-hashes", action="store_true",
                        help="Recompute and print content hashes for all workflows (paste by hand into frontmatter per convention)")
    parser.add_argument("--fix-pointers", action="store_true",
                        help="Auto-create missing pointer files for all 3 platforms")
    parser.add_argument("--quiet", action="store_true", help="Suppress INFO findings")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    commands_dir = workspace / COMMANDS_DIR

    if not commands_dir.exists():
        print(f"ERROR: {commands_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    all_files = sorted(f.name for f in commands_dir.glob("*.md"))
    # P1 stabilization (pr-01-00): filter README.md (e.g. claude-commands/README.md has no frontmatter by design)
    all_files = [f for f in all_files if f not in LINT_EXCLUDE_FILES]

    if args.fix_hashes:
        print("Content hashes (computed via --fix-hashes and pasted by hand into frontmatter):")
        for wf_file in all_files:
            content = (commands_dir / wf_file).read_text(encoding="utf-8", errors="replace")
            h = compute_content_hash(content)
            print(f"  {wf_file}: sha256:{h}")
        sys.exit(0)

    if args.fix_pointers:
        canonical = Path(workspace) / COMMANDS_DIR
        created = 0
        for wf_file in all_files:
            name = wf_file
            canon_path = canonical / name
            content = canon_path.read_text(encoding="utf-8", errors="replace")
            fm, _ = parse_frontmatter(content)
            desc = fm.get("description", name.replace(".md", "")) if fm else name.replace(".md", "")

            # Claude Code symlink
            claude_path = Path(SYMLINK_DIR) / name
            if not claude_path.exists():
                os.makedirs(SYMLINK_DIR, exist_ok=True)
                os.symlink(str(canon_path), str(claude_path))
                print(f"  Created symlink: {claude_path}")
                created += 1

            # OpenCode pointer
            opencode_path = Path(OPENCODE_DIR) / name
            if not opencode_path.exists():
                os.makedirs(OPENCODE_DIR, exist_ok=True)
                with open(opencode_path, "w") as f:
                    f.write(f"# /{name.replace('.md', '')}\n\n@home/jwils/blueprint-workflows/claude-commands/{name}\n")
                print(f"  Created OpenCode pointer: {opencode_path}")
                created += 1

            # Antigravity pointer
            antigravity_path = Path(ANTIGRAVITY_DIR) / name
            if not antigravity_path.exists():
                os.makedirs(ANTIGRAVITY_DIR, exist_ok=True)
                with open(antigravity_path, "w") as f:
                    f.write(f'---\ndescription: "{desc}"\n---\n\n# PAYLOAD LOCATION\nview_file /home/jwils/blueprint-workflows/claude-commands/{name}\n\n# IF PAYLOAD MISSING\nIf the file above cannot be read, HALT and report:\n"PAYLOAD MISSING: {name} not found at the canonical path."\n')
                print(f"  Created Antigravity pointer: {antigravity_path}")
                created += 1

        print(f"\nPointer fix complete: {created} pointers created across {len(all_files)} workflows")
        sys.exit(0)

    if args.generate_graph:
        graph = generate_dependency_graph(workspace, all_files)
        out_path = workspace / "manifest" / "dependency_graph.json"
        os.makedirs(out_path.parent, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(graph, f, indent=2)
        print(f"Dependency graph written to {out_path} ({len(graph)} workflows)")
        sys.exit(0)

    report = LintReport()
    check_runtime_availability(report)  # once per scan, not per file — see docstring

    if args.file:
        target = args.file if args.file.endswith(".md") else args.file + ".md"
        if target in LINT_EXCLUDE_FILES:
            print(f"[LINT] Skipping excluded file per LINT_EXCLUDE_FILES: {target}")
            sys.exit(0)
        report.workflows_scanned = 1
        lint_single(workspace, target, all_files, report)
    else:
        report.workflows_scanned = len(all_files)
        for wf_file in all_files:
            lint_single(workspace, wf_file, all_files, report)

    if args.quiet:
        report.findings = [f for f in report.findings if f.severity != "INFO"]

    print_report(report)
    sys.exit(1 if report.criticals else 0)


if __name__ == "__main__":
    main()
