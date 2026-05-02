#!/usr/bin/env python3
"""
core/import_patterns.py — Import String Conversion Logic
=========================================================
Sovereign Refactor Protocol — Core Library

Responsibility: Centralize the logic that converts file paths into 
language-specific import patterns used for scanning and surgery.
"""

from pathlib import Path

def path_to_python_module(rel_path: str) -> str:
    """Convert 'foo/bar/baz.py' to 'foo.bar.baz'."""
    p = Path(rel_path)
    # Strip extension, replace separators with dots
    return str(p.with_suffix("")).replace("/", ".").replace("\\", ".")

def path_to_import_patterns(rel_path: str, language: str) -> list[str]:
    """
    Generate grep patterns that match imports of the given relative path.
    Handles both Python (dotted) and JS (quoted path) syntaxes.
    """
    p = Path(rel_path)
    patterns = []

    if language == "python":
        module_dotted = path_to_python_module(rel_path)
        # Match the full module and partial parent modules
        parts = module_dotted.split(".")
        for i in range(len(parts)):
            partial = ".".join(parts[:i + 1])
            patterns.append(f"from {partial}")
            patterns.append(f"import {partial}")
    else:
        # JS/TS: match quoted paths with and without extensions
        path_no_ext = str(p.with_suffix("")).replace("\\", "/")
        path_with_ext = str(p).replace("\\", "/")
        
        # We look for 'from "path"', 'from "path"', and 'require("path")'
        for path_val in [path_no_ext, path_with_ext]:
            patterns.append(f"from '{path_val}'")
            patterns.append(f'from "{path_val}"')
            patterns.append(f"require('{path_val}')")
            patterns.append(f'require("{path_val}")')

    return list(set(patterns))
