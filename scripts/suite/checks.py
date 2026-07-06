"""
checks.py — Validation checks for the Sovereign Suite Linter
=============================================================
Extracted from lint_workflows.py during SoC decomposition.

Each check function takes a workflow's content/frontmatter and a LintReport,
appending findings as it evaluates.
"""

import hashlib
import re
from pathlib import Path

from suite.models import (
    LintReport, V1_REQUIRED_FIELDS, VALID_TYPES, VALID_GRADES,
    VALID_RETENTION, SYMLINK_DIR, OPENCODE_DIR, ANTIGRAVITY_DIR, COMMANDS_DIR,
    GROK_BUILD_DIR,
)

try:
    import yaml
except ImportError:
    yaml = None


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


def _extract_strict_rules_section(body):
    matches = list(re.finditer(r'##\s+STRICT RULES[^\n]*\n(.*?)(?=\n---\s*$|\n##\s[^#]|\n────)', body, re.DOTALL | re.MULTILINE))
    if matches:
        return matches[-1].group(1)
    match = re.search(r'##\s+STRICT RULES[^\n]*\n(.*)', body, re.DOTALL)
    return match.group(1) if match else ""


def count_strict_rules(body):
    section = _extract_strict_rules_section(body)
    return len(re.findall(r'^\d+\.\s+', section, re.MULTILINE))


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

    rules_section = _extract_strict_rules_section(body)
    rule_numbers = [int(m) for m in re.findall(r'^(\d+)\.\s+', rules_section, re.MULTILINE)]
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

    # [RETARGETED 2026-07-05, resolves helpdesk-tickets/20260705_opencode-to-grok-build-transition_workflow.md]
    # Only check individual pointer files when the runtime's directory exists at
    # all. A wholly-absent directory means the runtime itself isn't installed —
    # that is a single fact (see check_runtime_availability, called once per
    # scan), not 32 near-identical per-file gaps. This distinguishes "the
    # runtime was never set up / was removed" from "one specific new file is
    # missing its pointer" — a real, different finding from the same signal.
    if Path(OPENCODE_DIR).is_dir():
        opencode_link = Path(OPENCODE_DIR) / workflow_name
        if not opencode_link.exists():
            report.add("WARNING", workflow_name, "pointer", f"OpenCode pointer missing: {opencode_link}")

    if Path(ANTIGRAVITY_DIR).is_dir():
        antigravity_link = Path(ANTIGRAVITY_DIR) / workflow_name
        if not antigravity_link.exists():
            report.add("WARNING", workflow_name, "pointer", f"Antigravity pointer missing: {antigravity_link}")

    # Dir existence handling (generalized) + Grok runtime note: is_dir gate
    # + single INFO. [pr-05-01a per PILLAR_05]
    if Path(GROK_BUILD_DIR).is_dir():
        grok_link = Path(GROK_BUILD_DIR) / workflow_name
        if not grok_link.exists():
            report.add("WARNING", workflow_name, "pointer", f"Grok Build pointer missing: {grok_link}")


def check_runtime_availability(report):
    """
    [ADDED 2026-07-05, resolves helpdesk-tickets/20260705_opencode-to-grok-build-transition_workflow.md]
    Run once per scan (not per file). Reports whether each pointer-runtime
    directory exists at all, as a single INFO-level note — not a WARNING,
    since a runtime being absent may be a deliberate choice (a tool retired
    and replaced), not a defect. check_symlinks skips its per-file checks for
    whichever runtime is reported unavailable here, so the two never double-warn.
    """
    for label, directory in (("OpenCode", OPENCODE_DIR), ("Antigravity", ANTIGRAVITY_DIR), ("Grok Build", GROK_BUILD_DIR)):
        if not Path(directory).is_dir():
            report.add("INFO", "(suite)", "runtime",
                       f"{label} runtime directory not found at {directory} — "
                       f"skipping per-file pointer checks for this runtime. "
                       f"If retired/replaced intentionally, no action needed; "
                       f"if unexpected, verify the runtime is installed.")


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
