#!/usr/bin/env python3
"""
core/manifest.py — REFACTOR_MANIFEST.yaml I/O and Validation
============================================================
Sovereign Refactor Protocol — Core Library

Responsibility: Centralize manifest loading, path resolution, and 
basic schema validation. Ensures all scripts read the same 'contract'.
"""

from pathlib import Path
from core.console import fail

try:
    import yaml
except ImportError:
    # This should have been caught by the script's pre-flight, 
    # but we handle it here just in case.
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    import sys
    sys.exit(1)

MANIFEST_FILENAME = "REFACTOR_MANIFEST.yaml"
MAX_MANIFEST_SIZE = 5 * 1024 * 1024  # 5 MB limit to prevent DoS

import os

def _is_safe_path(path_str: str) -> bool:
    """
    Return True if the path is relative and does not attempt upward traversal.
    Blocks absolute paths and '..' components.
    """
    # Reject absolute paths
    if os.path.isabs(path_str):
        return False
    
    # Reject paths containing '..' components
    parts = Path(path_str).parts
    if ".." in parts:
        return False
        
    return True

ALLOWED_LANGUAGES = frozenset({"python", "javascript", "typescript"})

def _validate_manifest_schema(data: dict) -> None:
    """
    Perform strict schema validation on the manifest dictionary.
    Aborts if mandatory keys are missing, paths are unsafe, or collisions occur.
    """
    if not isinstance(data, dict):
        fail("Manifest root must be a dictionary.")
    
    # SECURITY: Validate language early
    lang = data.get("language", "python")
    if lang != "TBD" and lang not in ALLOWED_LANGUAGES:
        fail(f"Unsupported language in manifest: {lang}")

    files = data.get("files")
    if not isinstance(files, list):
        fail("Manifest must contain a 'files' list.")
    
    seen_targets = set()
    for i, entry in enumerate(files):
        if not isinstance(entry, dict):
            fail(f"Manifest file entry {i} must be a dictionary.")
        
        # SECURITY: Ensure mandatory fields exist to prevent KeyErrors
        if "current" not in entry or "target" not in entry:
            fail(f"Manifest file entry {i} is missing 'current' or 'target' keys.")
        
        curr, tar = entry["current"], entry["target"]
        if not isinstance(curr, str) or not isinstance(tar, str):
            fail(f"Manifest file entry {i} paths must be strings.")

        # SECURITY: Guard against empty paths
        if not curr.strip() or not tar.strip():
            fail(f"Manifest entry {i} has empty paths.")
            
        # SECURITY: Path Boundary Enforcement
        if not _is_safe_path(curr):
            fail(f"Manifest entry {i} has unsafe 'current' path: {curr}")
        if not _is_safe_path(tar):
            fail(f"Manifest entry {i} has unsafe 'target' path: {tar}")

        # SECURITY: Collision Detection (Prevent Overwrite Data Loss)
        if tar in seen_targets:
            fail(f"Manifest collision: Multiple files target '{tar}'. Data loss prevented.")
        seen_targets.add(tar)

def load_manifest(root: Path) -> dict:
    """
    Load and return the manifest YAML as a dictionary.
    Includes resource limits, collision detection, and strict schema validation.
    """
    mp = root / MANIFEST_FILENAME
    if not mp.exists():
        fail(f"{MANIFEST_FILENAME} not found at {root}. Run refactor_scout.py (Phase 0) first.")
    
    # SECURITY: Prevent memory exhaustion DoS
    try:
        file_size = mp.stat().st_size
        if file_size > MAX_MANIFEST_SIZE:
            fail(f"{MANIFEST_FILENAME} exceeds size limit ({file_size} > {MAX_MANIFEST_SIZE} bytes).")
    except OSError as e:
        fail(f"Failed to check manifest size: {e}")

    try:
        with open(mp, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        fail(f"Failed to parse {MANIFEST_FILENAME}: {e}")

    # SECURITY: Enforce the 'contract' before returning data
    _validate_manifest_schema(data)
    
    return data

import re

# SECURITY: Block obvious destructive patterns in shell gates
DANGEROUS_GATE_PATTERNS = re.compile(
    r"(rm\s+-rf\s+/)|(>\s+/dev/sd)|(mkfs)|(dd\s+if=)|(rm\s+-rf\s+\.\.)", 
    re.IGNORECASE
)

def get_language(manifest: dict) -> str:
    """Extract language from manifest, defaulting to 'python'."""
    lang = manifest.get("language", "python")
    return "python" if lang == "TBD" else lang

def get_verification_gate(manifest: dict) -> str:
    """
    Extract verification_gate command with safety scrubbing. 
    Returns an empty string if unset or if it starts with '#'.
    Aborts if a destructive pattern is detected.
    """
    gate = manifest.get("verification_gate", "")
    if not gate or gate.strip().startswith("#"):
        return ""
    
    gate_str = gate.strip()
    
    # SECURITY: Scrutinize command for destructive patterns before execution
    if DANGEROUS_GATE_PATTERNS.search(gate_str):
        fail(f"SECURITY ALERT: Destructive command detected in verification_gate: {gate_str}")
        
    return gate_str
