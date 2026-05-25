"""
graph.py — Dependency graph generator for the Sovereign Suite
=============================================================
Extracted from lint_workflows.py during SoC decomposition.
"""

from pathlib import Path

from suite.models import COMMANDS_DIR
from suite.checks import parse_frontmatter, extract_workflow_refs


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
