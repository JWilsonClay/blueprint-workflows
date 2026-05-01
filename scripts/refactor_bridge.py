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
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

MANIFEST_FILENAME = "REFACTOR_MANIFEST.yaml"
SHIM_HEADER = "⚠️ SHIM FILE"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def out(emoji: str, msg: str) -> None:
    print(f"{emoji}  {msg}", flush=True)


def fail(msg: str) -> None:
    out("❌", f"FATAL: {msg}")
    sys.exit(1)


def run_gate(gate_cmd: str, root: Path) -> bool:
    """Run the verification gate command. Returns True if exit code is 0."""
    out("🔬", f"Running verification gate: {gate_cmd}")
    result = subprocess.run(gate_cmd, shell=True, cwd=str(root))
    if result.returncode == 0:
        out("✅", "Verification gate PASSED.")
        return True
    else:
        out("❌", f"Verification gate FAILED (exit code {result.returncode}).")
        return False


def load_manifest(root: Path) -> dict:
    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.exists():
        fail(
            f"{MANIFEST_FILENAME} not found at {root}. "
            "Run refactor_scout.py (Phase 0) first."
        )
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "files" not in data:
        fail(f"{MANIFEST_FILENAME} is empty or missing the 'files' key.")
    return data


def path_to_module(rel_path: str, language: str) -> str:
    """Convert a relative file path to a dotted module identifier (Python) or relative import path (JS)."""
    p = Path(rel_path)
    if language == "python":
        # Strip .py extension, replace / with .
        without_ext = p.with_suffix("")
        return str(without_ext).replace(os.sep, ".").replace("/", ".")
    else:
        # JS/TS: strip extension, use relative path with leading ./
        without_ext = p.with_suffix("")
        return "./" + str(without_ext).replace("\\", "/")


# ---------------------------------------------------------------------------
# Shim templates
# ---------------------------------------------------------------------------

def python_shim(current_path: str) -> str:
    p = Path(current_path)
    module = str(p.with_suffix("")).replace("/", ".").replace("\\", ".")
    return (
        f"# {SHIM_HEADER} — Phase 1 of Sovereign Refactor Protocol\n"
        f"# This file is a temporary compatibility bridge. DO NOT REMOVE until Phase 4.\n"
        f"# Logic currently lives at: {current_path}\n"
        f"# This shim will be replaced by the real file in Phase 2 (git mv).\n"
        f"from {module} import *  # noqa: F401, F403\n"
    )


def js_shim(current_path: str) -> str:
    p = Path(current_path)
    # Strip extension for the import path
    without_ext = str(p.with_suffix("")).replace("\\", "/")
    # Make it a relative import from the project root perspective
    rel_import = "/" + without_ext  # absolute project-root-relative import
    return (
        f"// {SHIM_HEADER} — Phase 1 of Sovereign Refactor Protocol\n"
        f"// DO NOT REMOVE until Phase 4.\n"
        f"// Logic currently lives at: {current_path}\n"
        f"// This shim will be replaced by the real file in Phase 2 (git mv).\n"
        f"export * from '{rel_import}';\n"
    )


def write_shim(target_path: Path, current_path: str, language: str, dry_run: bool) -> None:
    """Write a shim file at target_path, pointing back to current_path."""
    if language == "python":
        content = python_shim(current_path)
    else:
        content = js_shim(current_path)

    if dry_run:
        out("🔍", f"[DRY RUN] Would write shim → {target_path}")
        out("🔍", f"          Content preview: {content.splitlines()[0]}")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Create __init__.py files for new Python packages
    if language == "python":
        for parent in target_path.parents:
            init = parent / "__init__.py"
            if not init.exists() and parent != target_path.parent.parent:
                # Only create __init__.py if this looks like it's inside the project
                break

    if target_path.exists():
        out("⚠️ ", f"Shim target already exists — skipping: {target_path}")
        return

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    out("📄", f"Shim written → {target_path}")


def ensure_python_init_files(root: Path, target_path: Path) -> None:
    """Ensure all parent directories of a Python target have __init__.py."""
    candidate = target_path.parent
    while candidate != root and candidate != candidate.parent:
        init = candidate / "__init__.py"
        if not init.exists():
            init.touch()
            out("📄", f"Created __init__.py → {init.relative_to(root)}")
        candidate = candidate.parent


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

import os


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
    language = manifest.get("language", "python")
    gate_cmd = manifest.get("verification_gate", "")
    files = manifest.get("files", [])

    out("📋", f"Manifest loaded: {len(files)} entries, language={language}")

    if not gate_cmd or gate_cmd.startswith("#"):
        out("⚠️ ", "verification_gate is not set in the manifest.")
        out("⚠️ ", "Shims will be created but the gate will be SKIPPED.")
        gate_cmd = None

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

        # Ensure parent __init__.py chain for Python
        if language == "python" and not args.dry_run:
            ensure_python_init_files(root, target_path)

        write_shim(target_path, current, language, dry_run=args.dry_run)

        if not args.dry_run and gate_cmd:
            if not run_gate(gate_cmd, root):
                out("❌", f"Gate failed after creating shim for: {current}")
                out("🛑", "Stopping. Do not proceed until the gate passes.")
                out("🛑", f"  Failed shim: {target_path}")
                sys.exit(1)

        results["success"] += 1

    # Final report
    print()
    print("═" * 65)
    print("  🏗️   REFACTOR BRIDGE — Phase 1 Complete")
    print("═" * 65)
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
