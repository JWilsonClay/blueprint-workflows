#!/usr/bin/env python3
"""
core/git_ops.py — Subprocess and Git Orchestration
==================================================
Sovereign Refactor Protocol — Core Library

Responsibility: Centralize execution of git commands and verification gates.
"""

import subprocess
from pathlib import Path
from core.console import out

def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Execute a command list and capture its output."""
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)

def run_gate(gate_cmd: str, root: Path) -> bool:
    """
    Run the verification gate command (shell string).
    Outputs the status to the terminal. Returns True if exit code 0.
    """
    out("🔬", f"Running verification gate: {gate_cmd}")
    # We use shell=True because verification_gate is a free-form user string
    result = subprocess.run(gate_cmd, shell=True, cwd=str(root))
    if result.returncode == 0:
        out("✅", "Verification gate PASSED.")
        return True
    else:
        out("❌", f"Verification gate FAILED (exit code {result.returncode}).")
        return False

def check_git_status(root: Path) -> bool:
    """
    Check if the git working tree is clean. 
    Outputs warnings if uncommitted changes are found.
    """
    r = run_cmd(["git", "status", "--porcelain"], root)
    if r.returncode != 0:
        return True  # Not a git repo or git missing; handled by scripts
    
    if r.stdout.strip():
        out("⚠️ ", "Uncommitted changes detected. Refactor operations recommend a clean tree.")
        return False
    
    out("✅", "Git working tree is clean.")
    return True
