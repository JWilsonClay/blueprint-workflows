#!/usr/bin/env python3
"""
core/console.py — Console Output and Terminal Formatting
========================================================
Sovereign Refactor Protocol — Core Library

Responsibility: Centralize all terminal output formatting, emoji prefixing,
and fatal error handling to ensure a consistent CLI experience across the suite.
"""

import sys

def out(emoji: str, msg: str) -> None:
    """Print a message prefixed with an emoji to stdout."""
    print(f"{emoji}  {msg}", flush=True)

def fail(msg: str) -> None:
    """Print a fatal error message and exit with code 1."""
    out("❌", f"FATAL: {msg}")
    sys.exit(1)

def section_header(title: str, width: int = 65) -> None:
    """Print a prominent section header using double-line borders."""
    print()
    print("═" * width)
    print(f"  {title}")
    print("═" * width)

def section_rule(label: str = "", width: int = 60) -> None:
    """Print a horizontal rule with an optional label."""
    if label:
        print(f"  ─── {label} " + "─" * (width - len(label) - 7))
    else:
        print(f"  " + "─" * width)
