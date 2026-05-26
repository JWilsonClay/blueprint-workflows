"""
models.py — Data models and constants for the Sovereign Suite Linter
====================================================================
Extracted from lint_workflows.py during SoC decomposition.
"""

import os

COMMANDS_DIR = "claude-commands"
SYMLINK_DIR = os.path.expanduser("~/.claude/commands")
OPENCODE_DIR = os.path.expanduser("~/.opencode/commands")
ANTIGRAVITY_DIR = os.path.expanduser("~/.gemini/antigravity/global_workflows")

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
