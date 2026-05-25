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
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

COMMANDS_DIR = "claude-commands"
SYMLINK_DIR = os.path.expanduser("~/.claude/commands")
OPENCODE_DIR = os.path.expanduser("~/.opencode/commands")

V1_REQUIRED_FIELDS = [
    "description", "type", "grade", "version", "content_hash",
    "last_hardened", "strict_rule_count", "phase_count",
    "context_retention", "flags", "dependencies", "triggers",
    "produces", "consumes", "platform_requirements",
]

VALID_TYPES = ["execution", "behavioral-modifier", "meta", "audit", "documentation"]
VALID_GRADES = ["Sovereign", "Hardened", "Structured", "Legacy"]
VALID_RETENTION = ["high", "medium", "low"]


class Finding:
    def __init__(self, severity, workflow, check, message):
        self.severity = severity
        self.workflow = workflow
        self.check = check
        self.message = message

    def __str__(self):
        return f"  [{self.severity}] {self.workflow}: {self.check} — {self.message}"


class LintReport:
    def __init__(self):
        self.findings = []
        self.workflows_scanned = 0
        self.workflows_clean = 0

    def add(self, severity, workflow, check, message):
        self.findings.append(Finding(severity, workflow, check, message))

    @property
    def criticals(self):
        return [f for f in self.findings if f.severity == "CRITICAL"]

    @property
    def warnings(self):
        return [f for f in self.findings if f.severity == "WARNING"]

    @property
    def infos(self):
        return [f for f in self.findings if f.severity == "INFO"]


def parse_frontmatter(content):
    if not content.startswith("---"):
        return None, content
    end = content.find("---", 3)
    if end == -1:
        return None, content
    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()
    if yaml:
        try:
            return yaml.safe_load(fm_text) or {}, body
        except yaml.YAMLError:
            return {"_parse_error": True}, body
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm, body


def compute_content_hash(content):
    body_without_changelog = re.split(r"###?\s*Change\s*Log", content, maxsplit=1)[0]
    _, body = parse_frontmatter(body_without_changelog)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def extract_workflow_refs(body):
    return set(re.findall(r'/([a-z][a-z0-9-]+)', body))


def count_strict_rules(body):
    return len(re.findall(r'^\d+\.\s+\*\*', body, re.MULTILINE))


def count_phases(body):
    return len(re.findall(r'^##\s+PHASE\s+\d', body, re.MULTILINE))


def extract_glossary_terms(body):
    terms = []
    in_glossary = False
    for line in body.splitlines():
        if "GLOSSARY" in line and ("##" in line or "**" in line):
            in_glossary = True
            continue
        if in_glossary and line.startswith("---"):
            break
        if in_glossary and line.startswith("| **"):
            match = re.match(r'\|\s*\*\*(.+?)\*\*', line)
            if match:
                terms.append(match.group(1))
    return terms


def check_frontmatter(fm, workflow_name, report):
    if fm is None:
        report.add("CRITICAL", workflow_name, "frontmatter", "No YAML frontmatter found")
        return
    if fm.get("_parse_error"):
        report.add("CRITICAL", workflow_name, "frontmatter", "YAML parse error in frontmatter")
        return
    if not fm.get("description"):
        report.add("CRITICAL", workflow_name, "frontmatter", "description field missing or empty")

    for field in V1_REQUIRED_FIELDS:
        if field not in fm:
            report.add("INFO", workflow_name, "frontmatter_v1", f"v1 field '{field}' not yet present")

    if "type" in fm and fm["type"] not in VALID_TYPES:
        report.add("WARNING", workflow_name, "frontmatter", f"type '{fm['type']}' not in valid set: {VALID_TYPES}")
    if "grade" in fm and fm["grade"] not in VALID_GRADES:
        report.add("WARNING", workflow_name, "frontmatter", f"grade '{fm['grade']}' not in valid set: {VALID_GRADES}")
    if "context_retention" in fm and fm["context_retention"] not in VALID_RETENTION:
        report.add("WARNING", workflow_name, "frontmatter", f"context_retention '{fm['context_retention']}' not valid")


def check_structure(body, workflow_name, fm, report):
    has_glossary = bool(re.search(r'GLOSSARY', body))
    has_how_to_begin = bool(re.search(r'HOW TO BEGIN', body))
    has_strict_rules = bool(re.search(r'STRICT RULES', body))
    has_integration = bool(re.search(r'INTEGRATION', body))
    has_changelog = bool(re.search(r'Change Log', body))

    wf_type = fm.get("type", "execution") if fm else "execution"

    if not has_glossary:
        report.add("WARNING", workflow_name, "structure", "GLOSSARY section missing")
    if not has_how_to_begin:
        report.add("WARNING", workflow_name, "structure", "HOW TO BEGIN section missing")
    if not has_strict_rules and wf_type != "documentation":
        report.add("WARNING", workflow_name, "structure", "STRICT RULES section missing")
    if not has_integration:
        report.add("WARNING", workflow_name, "structure", "INTEGRATION section missing")
    if not has_changelog:
        report.add("WARNING", workflow_name, "structure", "Change Log section missing")

    actual_rules = count_strict_rules(body)
    actual_phases = count_phases(body)

    if fm and "strict_rule_count" in fm:
        expected = int(fm["strict_rule_count"])
        if actual_rules != expected:
            report.add("WARNING", workflow_name, "strict_rules",
                        f"Expected {expected} rules, found {actual_rules}")

    if fm and "phase_count" in fm:
        expected = int(fm["phase_count"])
        if actual_phases != expected:
            report.add("WARNING", workflow_name, "phases",
                        f"Expected {expected} phases, found {actual_phases}")

    rule_numbers = [int(m) for m in re.findall(r'^(\d+)\.\s+\*\*', body, re.MULTILINE)]
    for i in range(1, len(rule_numbers)):
        if rule_numbers[i] != rule_numbers[i - 1] + 1:
            report.add("WARNING", workflow_name, "strict_rules",
                        f"Rule numbering gap: {rule_numbers[i-1]} → {rule_numbers[i]}")


def check_cross_references(body, workflow_name, all_workflows, report):
    refs = extract_workflow_refs(body)
    known = {w.replace(".md", "") for w in all_workflows}
    noise = {"nodelete", "e", "x", "s", "a", "b", "c", "n", "name", "workflow",
             "path", "file", "this", "next", "prior", "new", "old"}

    for ref in refs:
        if ref in noise or len(ref) < 3:
            continue
        if ref not in known and ref.replace("-", "") not in {k.replace("-", "") for k in known}:
            if ref in known or any(ref in w for w in known):
                continue
            report.add("INFO", workflow_name, "xref",
                        f"Reference '/{ref}' — verify this resolves to a workflow")


def check_symlinks(workflow_name, workspace_root, report):
    claude_link = Path(SYMLINK_DIR) / workflow_name
    if not claude_link.exists():
        report.add("WARNING", workflow_name, "symlink", f"Claude Code symlink missing: {claude_link}")
    elif claude_link.is_symlink():
        target = claude_link.resolve()
        expected = (Path(workspace_root) / COMMANDS_DIR / workflow_name).resolve()
        if target != expected:
            report.add("CRITICAL", workflow_name, "symlink",
                        f"Symlink points to {target}, expected {expected}")

    opencode_link = Path(OPENCODE_DIR) / workflow_name
    if not opencode_link.exists():
        report.add("INFO", workflow_name, "symlink", f"OpenCode pointer missing: {opencode_link}")


def check_content_hash(content, fm, workflow_name, report):
    if not fm or "content_hash" not in fm:
        return
    declared = fm["content_hash"]
    actual = "sha256:" + compute_content_hash(content)
    if declared != actual:
        report.add("WARNING", workflow_name, "hash",
                    f"Content hash mismatch: declared={declared}, actual={actual}")


def check_glossary_usage(body, workflow_name, report):
    terms = extract_glossary_terms(body)
    glossary_end = body.find("---", body.find("GLOSSARY") + 1) if "GLOSSARY" in body else 0
    post_glossary = body[glossary_end:] if glossary_end > 0 else body

    for term in terms:
        if term.lower() not in post_glossary.lower():
            report.add("INFO", workflow_name, "glossary",
                        f"Term '{term}' defined in GLOSSARY but not used in body")


def generate_dependency_graph(workspace_root, all_files):
    graph = {}
    commands_dir = Path(workspace_root) / COMMANDS_DIR

    for wf_file in all_files:
        wf_path = commands_dir / wf_file
        content = wf_path.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(content)
        name = "/" + wf_file.replace(".md", "")

        entry = {
            "type": fm.get("type", "unknown") if fm else "unknown",
            "grade": fm.get("grade", "unknown") if fm else "unknown",
            "dependencies": fm.get("dependencies", []) if fm else [],
            "triggers": fm.get("triggers", []) if fm else [],
            "produces": fm.get("produces", []) if fm else [],
            "consumes": fm.get("consumes", []) if fm else [],
            "flags": fm.get("flags", []) if fm else [],
            "detected_refs": sorted(
                r for r in extract_workflow_refs(body)
                if len(r) >= 3 and r + ".md" in all_files
            ),
        }
        graph[name] = entry

    return graph


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


def print_report(report):
    print()
    print("=" * 70)
    print(f"  SOVEREIGN SUITE LINT REPORT")
    print(f"  Workflows scanned: {report.workflows_scanned}")
    print(f"  Clean:             {report.workflows_clean}")
    print(f"  Findings:          {len(report.findings)}")
    print(f"    CRITICAL: {len(report.criticals)}")
    print(f"    WARNING:  {len(report.warnings)}")
    print(f"    INFO:     {len(report.infos)}")
    print("=" * 70)

    if report.criticals:
        print("\n  CRITICAL:")
        for f in report.criticals:
            print(f)

    if report.warnings:
        print("\n  WARNING:")
        for f in report.warnings:
            print(f)

    if report.infos:
        print("\n  INFO:")
        for f in report.infos:
            print(f)

    print()
    if not report.criticals and not report.warnings:
        print("  VERDICT: CLEAN — no critical or warning findings.")
    elif not report.criticals:
        print("  VERDICT: WARNINGS ONLY — review recommended.")
    else:
        print(f"  VERDICT: {len(report.criticals)} CRITICAL finding(s) require attention.")
    print("=" * 70)
    print()


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
                        help="Recompute and print content hashes for all workflows")
    parser.add_argument("--quiet", action="store_true", help="Suppress INFO findings")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    commands_dir = workspace / COMMANDS_DIR

    if not commands_dir.exists():
        print(f"ERROR: {commands_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    all_files = sorted(f.name for f in commands_dir.glob("*.md"))

    if args.fix_hashes:
        print("Content hashes (paste into frontmatter as content_hash):")
        for wf_file in all_files:
            content = (commands_dir / wf_file).read_text(encoding="utf-8", errors="replace")
            h = compute_content_hash(content)
            print(f"  {wf_file}: sha256:{h}")
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

    if args.file:
        target = args.file if args.file.endswith(".md") else args.file + ".md"
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
