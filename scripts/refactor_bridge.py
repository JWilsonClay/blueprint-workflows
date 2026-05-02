#!/usr/bin/env python3
"""
refactor_bridge.py — Phase 1: Shim Layer Creation
==================================================
Sovereign Refactor Protocol — Script Suite

Responsibilities:
  1. Read REFACTOR_MANIFEST.yaml from the project root.
  2. For each MOVE or SPLIT entry: create the target directory if missing,
     write the appropriate shim file (Python or JS/TS) with the mandatory
     ⚠️ SHIM FILE header comment.
  3. Run the verification gate after each shim is created.
  4. Print a per-shim success/failure report.

Hallucination prevented: The LLM cannot write a shim with an incorrect import
path or silently skip a file because it ran out of context.

Usage:
  python3 refactor_bridge.py --project-root /path/to/project [--dry-run]

Requirements: Python 3.8+, PyYAML (pip install pyyaml).
"""

import argparse
import sys
import os
from pathlib import Path

from core.console import out, fail, section_header
from core.manifest import load_manifest, get_language, get_verification_gate
from core.git_ops import run_gate
from core.shim_templates import make_shim

try:
    import yaml
except ImportError:
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def _is_path_in_root(root: Path, path: Path) -> bool:
    """
    SECURITY: Return True if 'path' is a descendant of 'root'.
    Prevents workspace escape via malicious paths.
    """
    try:
        # resolve() handles '..' and symlinks, commonpath ensures boundary
        root_res = root.resolve()
        path_res = path.resolve()
        return os.path.commonpath([root_res]) == os.path.commonpath([root_res, path_res])
    except (ValueError, OSError):
        return False

def write_shim(root: Path, target_path: Path, current_path: str, language: str, dry_run: bool) -> bool:
    """
    Write a shim file at target_path, pointing back to current_path.
    Returns True if successful.
    """
    # SECURITY: Absolute boundary check before any disk write
    if not _is_path_in_root(root, target_path):
        out("❌", f"SECURITY ALERT: Target path is outside project root: {target_path}")
        return False

    content = make_shim(language, current_path, str(target_path))

    if dry_run:
        out("🔍", f"[DRY RUN] Would write shim → {target_path}")
        out("🔍", f"          Content preview: {content.splitlines()[0]}")
        return True

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            out("⚠️ ", f"Shim target already exists — skipping: {target_path}")
            return False

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        out("📄", f"Shim written → {target_path}")
        return True
    except (OSError, PermissionError) as e:
        out("❌", f"Failed to write shim: {e}")
        return False


def ensure_python_init_files(root: Path, target_path: Path) -> None:
    """Ensure all parent directories of a Python target exist and have __init__.py."""
    # SECURITY: Ensure we don't start walking above the root
    if not _is_path_in_root(root, target_path):
        return

    candidate = target_path.parent
    while candidate != root and candidate != candidate.parent:
        if not _is_path_in_root(root, candidate):
            break
            
        candidate.mkdir(parents=True, exist_ok=True)
        init = candidate / "__init__.py"
        if not init.exists():
            init.touch()
            out("📄", f"Created __init__.py → {init.relative_to(root)}")
        candidate = candidate.parent


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    if not root.exists():
        fail(f"Project root does not exist: {root}")

    out("🏗️ ", "Sovereign Refactor Protocol — Phase 1: Shim Layer Creation")
    out("📁", f"Project root: {root}")

    if args.dry_run:
        out("🔍", "DRY RUN mode — no files will be written.")

    manifest = load_manifest(root)
    language = get_language(manifest)
    gate_cmd = get_verification_gate(manifest)
    files = manifest.get("files", [])

    out("📋", f"Manifest loaded: {len(files)} entries, language={language}")

    if not gate_cmd:
        out("⚠️ ", "verification_gate is not set in the manifest.")
        out("⚠️ ", "Shims will be created but the gate will be SKIPPED.")

    # Filter to MOVE and SPLIT entries only
    candidates = [e for e in files if e.get("action") in ("MOVE", "SPLIT")]
    if not candidates:
        out("⚠️ ", "No MOVE or SPLIT entries found in the manifest.")
        out("⚠️ ", "Nothing to do. Has the manifest been filled in by the LLM?")
        sys.exit(0)

    out("📋", f"Found {len(candidates)} MOVE/SPLIT entries to process.")

    # Validate all entries have a valid target before doing any writes
    out("🔍", "Pre-validating all target paths…")
    errors = []
    for entry in candidates:
        current = entry.get("current", "")
        target = entry.get("target", "")
        action = entry.get("action", "")
        if not target or target == current:
            errors.append(f"  {action} entry '{current}' has no distinct target path set.")
        if target.startswith("#") or target == "TBD":
            errors.append(f"  {action} entry '{current}' target is still placeholder: '{target}'")
    if errors:
        out("❌", "Manifest validation failed — fix these entries before running:")
        for e in errors:
            print(e)
        sys.exit(1)
    out("✅", "All entries validated.")

    # Process each entry
    results = {"success": 0, "skipped": 0, "failed": 0}
    for entry in candidates:
        current = entry["current"]
        target = entry["target"]
        action = entry["action"]

        out("🔧", f"[{action}] Creating shim: {current} → {target}")

        target_path = root / target
        current_source_path = root / current

        # SECURITY: Verify source exists before shimming
        if not current_source_path.exists():
            out("⚠️ ", f"Source file does not exist — cannot create shim: {current}")
            results["skipped"] += 1
            continue

        # Ensure parent __init__.py chain for Python
        if language == "python" and not args.dry_run:
            ensure_python_init_files(root, target_path)

        if write_shim(root, target_path, current, language, dry_run=args.dry_run):
            results["success"] += 1
        else:
            results["failed"] += 1
            continue

        if not args.dry_run and gate_cmd:
            if not run_gate(gate_cmd, root):
                out("❌", f"Gate failed after creating shim for: {current}")
                out("🛑", "Stopping. Do not proceed until the gate passes.")
                out("🛑", f"  Failed shim: {target_path}")
                sys.exit(1)

        results["success"] += 1

    # Final report
    section_header("REFACTOR BRIDGE — Phase 1 Complete")
    print(f"  ✅ Shims created  : {results['success']}")
    print(f"  ⏭️  Skipped        : {results['skipped']}")
    print(f"  ❌ Failed         : {results['failed']}")
    print()
    print("  ─── NEXT STEPS ────────────────────────────────────────")
    print("  1. Confirm all shim files exist at their target paths.")
    print("  2. Verify the project still passes its verification gate.")
    print("  3. Commit: git add . && git commit -m 'refactor(p1): inject shim layer'")
    print("  4. Run: python3 refactor_migrate.py --project-root <root> --module <name>")
    print("═" * 65)
    print()

    if args.dry_run:
        out("🔍", "DRY RUN complete — no files were written.")

    out("🏁", "Phase 1 bridge complete. Exit code: 0")
    sys.exit(0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="refactor_bridge.py",
        description="Phase 1: Create shim files at all MOVE/SPLIT target paths.",
    )
    p.add_argument("--project-root", required=True,
                   help="Path to the root of the project being refactored.")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview what would be written without writing any files.")
    return p.parse_args()


if __name__ == "__main__":
    main()
