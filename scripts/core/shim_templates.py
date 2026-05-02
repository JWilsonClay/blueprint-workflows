#!/usr/bin/env python3
"""
core/shim_templates.py — Shim File Content Templates
====================================================
Sovereign Refactor Protocol — Core Library

Responsibility: Centralize the templates for forward and reverse shims.
Enforces the 'Option B (Relative)' decision for JS imports.
"""

import os
from pathlib import Path
from core.filesystem import SHIM_FILE_MARKER, REVERSE_SHIM_MARKER
from core.import_patterns import path_to_python_module

def _get_js_rel_import(current_path: str, target_path: str) -> str:
    """
    Calculate the relative import path from current_path to target_path.
    e.g., from 'src/old/m.js' to 'src/new/m.js' returns '../new/m'.
    """
    cur_p = Path(current_path)
    tar_p = Path(target_path)
    
    # Get relative path between directories
    rel_path = os.path.relpath(tar_p.parent, cur_p.parent)
    
    # Construct the final import string
    import_base = Path(rel_path) / tar_p.name
    import_base = import_base.with_suffix("") # Strip extension
    
    # Ensure it starts with ./ or ../
    import_str = str(import_base).replace("\\", "/")
    if not import_str.startswith("."):
        import_str = "./" + import_str
        
    return import_str

# --- Forward Shims (Phase 1) ---

def python_forward_shim(current_path: str) -> str:
    module = path_to_python_module(current_path)
    return (
        f"# {SHIM_FILE_MARKER} — Phase 1 of Sovereign Refactor Protocol\n"
        f"# This file is a temporary compatibility bridge. DO NOT REMOVE until Phase 4.\n"
        f"# Logic currently lives at: {current_path}\n"
        f"# This shim will be replaced by the real file in Phase 2 (git mv).\n"
        f"from {module} import *  # noqa: F401, F403\n"
    )

def js_forward_shim(current_path: str, target_path: str) -> str:
    rel_import = _get_js_rel_import(target_path, current_path)
    return (
        f"// {SHIM_FILE_MARKER} — Phase 1 of Sovereign Refactor Protocol\n"
        f"// DO NOT REMOVE until Phase 4.\n"
        f"// Logic currently lives at: {current_path}\n"
        f"// This shim will be replaced by the real file in Phase 2 (git mv).\n"
        f"export * from '{rel_import}';\n"
    )

# --- Reverse Shims (Phase 2) ---

def python_reverse_shim(new_path: str) -> str:
    module = path_to_python_module(new_path)
    return (
        f"# {REVERSE_SHIM_MARKER} — Phase 2 of Sovereign Refactor Protocol\n"
        f"# DO NOT REMOVE until Phase 4 (all references have been surgically updated).\n"
        f"# This file exists to preserve import compatibility during migration.\n"
        f"# Logic has MOVED to: {new_path}\n"
        f"from {module} import *  # noqa: F401, F403\n"
    )

def js_reverse_shim(current_path: str, new_path: str) -> str:
    rel_import = _get_js_rel_import(current_path, new_path)
    return (
        f"// {REVERSE_SHIM_MARKER} — Phase 2 of Sovereign Refactor Protocol\n"
        f"// DO NOT REMOVE until Phase 4.\n"
        f"// Logic has MOVED to: {new_path}\n"
        f"export * from '{rel_import}';\n"
    )

# --- Dispatch Helpers ---

def make_shim(language: str, current_path: str, target_path: str) -> str:
    if language == "python":
        return python_forward_shim(current_path)
    return js_forward_shim(current_path, target_path)

def make_reverse_shim(language: str, current_path: str, new_path: str) -> str:
    if language == "python":
        return python_reverse_shim(new_path)
    return js_reverse_shim(current_path, new_path)
