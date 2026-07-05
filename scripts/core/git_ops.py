#!/usr/bin/env python3
"""
core/git_ops.py — Subprocess and Git Orchestration
==================================================
Sovereign Refactor Protocol — Core Library

Responsibility: Centralize execution of git commands and verification gates.
"""

import subprocess
import shlex
import time
from pathlib import Path
from core.console import out

import re

import os

DEFAULT_TIMEOUT = 60      # 1 minute for standard git commands
GATE_TIMEOUT = 600        # 10 minutes for user-defined test suites (verification gates)

# SECURITY: Mask potentially sensitive strings in logs
SENSITIVE_PATTERNS = re.compile(r"(token|key|pass|auth|secret|cred)=[\w\-._~%]+", re.IGNORECASE)

# SECURITY: Minimal environment whitelist to prevent credential leakage
# We include some common Windows variables for cross-platform robustness
SAFE_ENV_WHITELIST = frozenset({
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM", "PYTHONPATH", 
    "PWD", "SHELL", "EDITOR", "TMPDIR", "TEMP", "TMP",
    "SYSTEMROOT", "WINDIR", "USERPROFILE"
})

def _sanitize_log(msg: str) -> str:
    """Mask sensitive patterns in log messages (e.g. tokens, keys)."""
    return SENSITIVE_PATTERNS.sub(r"\1=********", msg)

def _get_safe_env() -> dict[str, str]:
    """Return a restricted environment containing only whitelisted variables."""
    return {k: v for k, v in os.environ.items() if k.upper() in SAFE_ENV_WHITELIST}

# SECURITY: Block obvious destructive patterns in shell gates
DANGEROUS_PATTERNS = re.compile(
    r"(rm\s+-rf\s+/)|(>\s+/dev/sd)|(mkfs)|(dd\s+if=)|(rm\s+-rf\s+\.\.)",
    re.IGNORECASE
)

def _is_dangerous_command(cmd_str: str) -> bool:
    """Return True if the command contains known catastrophic patterns."""
    return bool(DANGEROUS_PATTERNS.search(cmd_str))

# SECURITY: run_gate no longer invokes a shell at all (CWE-78 / harden_audit.py STRICT
# RULE 8 flags shell invocation unconditionally, regardless of mitigation). && composition
# is supported by splitting into sequential argv commands; anything else that depends on
# shell interpretation (pipes, redirects, subshells, backgrounding, variable expansion)
# is rejected explicitly rather than silently mis-executed as a literal argument.
UNSUPPORTED_SHELL_SYNTAX = re.compile(r"[|<>;`&()$\n]")

def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """
    Execute a command list securely and capture its output.
    Includes timeout protection, robust error handling, and environment isolation.
    """
    # SECURITY: Guard against empty or invalid command lists
    if not isinstance(cmd, list) or not cmd or not all(isinstance(c, str) for c in cmd):
        return subprocess.CompletedProcess([], 1, stdout="", stderr="Invalid or empty command format")

    sanitized_cmd = _sanitize_log(" ".join(cmd))

    try:
        # SECURITY: Canonicalize path and verify existence
        safe_cwd = cwd.resolve()
        if not safe_cwd.exists():
            out("❌", f"Execution directory does not exist: {safe_cwd}")
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Invalid directory")

        return subprocess.run(
            cmd, 
            cwd=str(safe_cwd), 
            capture_output=True, 
            text=True, 
            timeout=DEFAULT_TIMEOUT,
            check=False,
            env=_get_safe_env() # SECURITY: Environment isolation
        )
    except subprocess.TimeoutExpired:
        out("❌", f"Command timed out after {DEFAULT_TIMEOUT}s: {sanitized_cmd}")
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Timeout")
    except (FileNotFoundError, PermissionError) as e:
        out("❌", f"Execution failed: {e}")
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=str(e))

def run_gate(gate_cmd: str, root: Path) -> bool:
    """
    Run the verification gate command with safety filters and environment isolation.
    Supports sequential composition via && (stops at the first failure, matching shell
    && semantics). Does not invoke a shell: pipes, redirects, subshells, backgrounding,
    and variable expansion are not supported and are rejected explicitly rather than
    silently mis-executed. Shell globbing (*, ?, ~) is likewise not expanded — no
    verification_gate example in this suite's manifests, fixtures, or tests uses it.
    """
    if not gate_cmd or not gate_cmd.strip():
        out("⚠️ ", "Empty verification gate — skipping.")
        return True

    sanitized_gate = _sanitize_log(gate_cmd)

    # SECURITY: Destructive command filtering (checked on the full string, before
    # segmenting, so it still catches attempts spanning multiple && segments)
    if _is_dangerous_command(gate_cmd):
        out("🛑", "SECURITY ALERT: Destructive command pattern detected in gate!")
        out("🛑", f"  Blocked command: {sanitized_gate}")
        return False

    segments = [seg.strip() for seg in gate_cmd.split("&&")]
    if any(not seg for seg in segments):
        out("❌", "Verification gate has an empty && segment — check for a stray or trailing &&.")
        return False

    argv_segments = []
    for seg in segments:
        if UNSUPPORTED_SHELL_SYNTAX.search(seg):
            out("❌", f"Verification gate uses unsupported shell syntax (no shell is invoked — "
                       f"CWE-78): {_sanitize_log(seg)}")
            return False
        try:
            argv_segments.append(shlex.split(seg))
        except ValueError as e:
            out("❌", f"Could not parse verification gate segment: {e}")
            return False

    out("🔬", f"Running verification gate: {sanitized_gate}")

    safe_root = root.resolve()
    if not safe_root.exists():
        out("❌", f"Gate directory does not exist: {safe_root}")
        return False

    deadline = time.monotonic() + GATE_TIMEOUT
    for argv in argv_segments:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            out("❌", f"Verification gate TIMED OUT after {GATE_TIMEOUT}s.")
            return False
        try:
            result = subprocess.run(
                argv,
                shell=False,
                cwd=str(safe_root),
                timeout=remaining,
                env=_get_safe_env()  # SECURITY: Environment isolation
            )
        except subprocess.TimeoutExpired:
            out("❌", f"Verification gate TIMED OUT after {GATE_TIMEOUT}s.")
            return False
        except FileNotFoundError as e:
            out("❌", f"Verification gate command not found: {e}")
            return False
        except Exception as e:
            # SECURITY: Ensure the exception message itself doesn't leak sensitive context
            out("❌", f"Gate execution error: {type(e).__name__}")
            return False

        if result.returncode != 0:
            out("❌", f"Verification gate FAILED (exit code {result.returncode}).")
            return False

    out("✅", "Verification gate PASSED.")
    return True

def check_git_status(root: Path) -> bool:
    """
    Check if the git working tree is clean. 
    Outputs warnings if uncommitted changes are found.
    """
    r = run_cmd(["git", "status", "--porcelain"], root)
    if r.returncode != 0:
        # Git missing or not a repo; we return True (safe default) as scripts 
        # like Scout handle the 'not a repo' logic specifically.
        return True
    
    if r.stdout.strip():
        out("⚠️ ", "Uncommitted changes detected. Refactor operations recommend a clean tree.")
        return False
    
    out("✅", "Git working tree is clean.")
    return True
