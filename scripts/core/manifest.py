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

def load_manifest(root: Path) -> dict:
    """
    Load and return the manifest YAML as a dictionary.
    Aborts the script if the file is missing or malformed.
    """
    mp = root / MANIFEST_FILENAME
    if not mp.exists():
        fail(f"{MANIFEST_FILENAME} not found at {root}. Run refactor_scout.py (Phase 0) first.")
    
    try:
        with open(mp, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        fail(f"Failed to parse {MANIFEST_FILENAME}: {e}")

    if not data or "files" not in data:
        fail(f"{MANIFEST_FILENAME} is empty or missing the 'files' key.")
    
    return data

def get_language(manifest: dict) -> str:
    """Extract language from manifest, defaulting to 'python'."""
    lang = manifest.get("language", "python")
    return "python" if lang == "TBD" else lang

def get_verification_gate(manifest: dict) -> str:
    """
    Extract verification_gate command. 
    Returns an empty string if unset or if it starts with '#'.
    """
    gate = manifest.get("verification_gate", "")
    if not gate or gate.strip().startswith("#"):
        return ""
    return gate.strip()
