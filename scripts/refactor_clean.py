#!/usr/bin/env python3
"""
refactor_clean.py — Phase 4: Safe Shim Removal
===============================================
Sovereign Refactor Protocol — Script Suite

Responsibilities:
  1. Find every file containing the ⚠️ SHIM FILE or ⚠️ REVERSE SHIM header.
  2. For each shim: verify that NOTHING in the codebase still imports from
     that path (using grep on actual source files).
  3. If safe: print what it is about to do, execute `git rm`, run the gate.
  4. If NOT safe: report the specific file(s) still importing the shim path.
     Do NOT remove it. Flag it for the LLM to fix first.
  5. After all removals: do a final pass confirming zero shim headers remain.

Hallucination prevented: The LLM cannot delete a shim still being imported
by one overlooked file, causing a silent runtime crash.

Usage:
  python3 refactor_clean.py --project-root /path/to/project [--dry-run]
  python3 refactor_clean.py --project-root /path/to/project --shim <relative/path.py>

Requirements: Python 3.8+, PyYAML (pip install pyyaml), git in PATH.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

MANIFEST_FILENAME = "REFACTOR_MANIFEST.yaml"
SHIM_HEADER_MARKERS = ["⚠️ SHIM FILE", "⚠️ REVERSE SHIM"]

SKIP_DIRS = {
    "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".tox",
    ".venv", "venv", "env", "node_modules", "dist", "build",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def out(emoji: str, msg: str) -> None:
    print(f"{emoji}  {msg}", flush=True)


def fail(msg: str) -> None:
    out("❌", f"FATAL: {msg}")
    sys.exit(1)


def run_cmd(cmd: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def run_gate(gate_cmd: str, root: Path) -> bool:
    out("🔬", f"Running verification gate: {gate_cmd}")
    result = subprocess.run(gate_cmd, shell=True, cwd=str(root))
    if result.returncode == 0:
        out("✅", "Verification gate PASSED.")
        return True
    out("❌", f"Verification gate FAILED (exit code {result.returncode}).")
    return False


def load_manifest(root: Path) -> dict:
    mp = root / MANIFEST_FILENAME
    if not mp.exists():
        # Manifest may have been cleaned already — that's okay in Phase 4
        out("⚠️ ", f"{MANIFEST_FILENAME} not found — proceeding by scanning for shim headers only.")
        return {}
    with open(mp, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def is_shim_file(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return any(m in content for m in SHIM_HEADER_MARKERS)
    except (OSError, PermissionError):
        return False


def _walk_project(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not d.endswith(".egg-info")]
        yield dirpath, dirnames, filenames


# ---------------------------------------------------------------------------
# Step 1: Find all shim files
# ---------------------------------------------------------------------------

def find_all_shims(root: Path) -> list:
    """Return sorted list of Path objects for every shim file in the project."""
    shims = []
    for dirpath, dirnames, filenames in _walk_project(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            if is_shim_file(fp):
                shims.append(fp)
    return sorted(shims)


# ---------------------------------------------------------------------------
# Step 2: Check if a shim is still being imported
# ---------------------------------------------------------------------------

def path_to_import_patterns(rel_path: str, language: str) -> list:
    """Convert a shim's relative path to import patterns that would detect usage."""
    p = Path(rel_path)
    patterns = []

    if language == "python":
        module = str(p.with_suffix("")).replace("/", ".").replace("\\", ".")
        parts = module.split(".")
        for i in range(len(parts)):
            partial = ".".join(parts[:i + 1])
            patterns.append(f"from {partial}")
            patterns.append(f"import {partial}")
    else:
        path_no_ext = str(p.with_suffix("")).replace("\\", "/")
        path_with_ext = str(p).replace("\\", "/")
        for fmt in [f"'{path_no_ext}'", f'"{path_no_ext}"',
                    f"'{path_with_ext}'", f'"{path_with_ext}"']:
            patterns.append(f"from {fmt}")
            patterns.append(f"require({fmt})")

    return list(set(patterns))


def find_importers(root: Path, shim_path: Path, language: str) -> list:
    """
    Scan the project for any non-shim file that imports from the shim's path.
    Returns a list of (rel_path, line_num, line_content) tuples.
    """
    rel_shim = shim_path.relative_to(root)
    patterns = path_to_import_patterns(str(rel_shim), language)

    if language == "python":
        include_ext = {".py"}
    else:
        include_ext = {".js", ".ts", ".jsx", ".tsx", ".mjs"}

    importers = []

    for dirpath, dirnames, filenames in _walk_project(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fp.suffix not in include_ext:
                continue
            if fp == shim_path:
                continue
            if is_shim_file(fp):
                continue  # Other shims importing this shim is OK

            try:
                lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
            except (OSError, PermissionError):
                continue

            for lineno, line in enumerate(lines, start=1):
                for pat in patterns:
                    if pat in line:
                        importers.append((
                            str(fp.relative_to(root)),
                            lineno,
                            line.rstrip(),
                        ))
                        break

    return importers


# ---------------------------------------------------------------------------
# Step 3: Remove a shim safely
# ---------------------------------------------------------------------------

def remove_shim(root: Path, shim_path: Path, language: str, gate_cmd: str,
                dry_run: bool) -> bool:
    """
    Verify safety and remove one shim via git rm.
    Returns True if successfully removed (or would be in dry-run).
    Returns False if the shim is still being imported.
    """
    rel = shim_path.relative_to(root)
    out("🔍", f"Checking safety of: {rel}")

    importers = find_importers(root, shim_path, language)

    if importers:
        out("🚫", f"Cannot remove — {len(importers)} file(s) still import from: {rel}")
        for imp_file, lineno, line_content in importers:
            print(f"       📄 {imp_file}:{lineno} │ {line_content}")
        out("🚫", "Fix Phase 3 surgery for the file(s) above, then re-run refactor_clean.py.")
        return False

    # Safe to remove
    out("🗑️ ", f"{'[DRY RUN] ' if dry_run else ''}Safe to remove: {rel}")

    if dry_run:
        return True

    # Execute git rm
    r = run_cmd(["git", "rm", "-f", str(rel)], root)
    if r.returncode != 0:
        out("❌", f"git rm failed: {r.stderr.strip()}")
        return False

    out("✅", f"Shim removed: {rel}")

    # Run verification gate after each removal
    if gate_cmd and not gate_cmd.startswith("#"):
        if not run_gate(gate_cmd, root):
            out("❌", f"Gate failed after removing shim: {rel}")
            out("🛑", "Stopping. Do not remove additional shims until gate passes.")
            return False

    return True


# ---------------------------------------------------------------------------
# Step 4: Final confirmation pass
# ---------------------------------------------------------------------------

def final_confirmation_pass(root: Path) -> bool:
    """Confirm zero shim headers remain anywhere in the project."""
    out("🔍", "Final confirmation pass — scanning for any remaining shim headers…")
    remaining = find_all_shims(root)
    if remaining:
        out("❌", f"{len(remaining)} shim(s) still found:")
        for s in remaining:
            print(f"    🔴 {s.relative_to(root)}")
        return False
    out("✅", "Zero shim headers found. Project is clean.")
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="refactor_clean.py",
        description=(
            "Phase 4: Safely remove all shim files.\n"
            "Verifies nothing still imports each shim before running git rm."
        ),
    )
    p.add_argument("--project-root", required=True,
                   help="Path to the root of the project being refactored.")
    p.add_argument("--shim", metavar="REL_PATH",
                   help="Remove a single specific shim (relative path). "
                        "If omitted, all shims are processed.")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview all actions without removing any files.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    if not root.exists():
        fail(f"Project root does not exist: {root}")

    out("🏗️ ", "Sovereign Refactor Protocol — Phase 4: Safe Shim Removal")
    out("📁", f"Project root: {root}")

    if args.dry_run:
        out("🔍", "DRY RUN mode — no files will be removed.")

    manifest = load_manifest(root)
    language = manifest.get("language", "python")
    gate_cmd = manifest.get("verification_gate", "")

    if not gate_cmd or gate_cmd.startswith("#"):
        out("⚠️ ", "verification_gate not set — gate will be SKIPPED after each removal.")
        gate_cmd = ""

    # Find shims to process
    if args.shim:
        shim_path = root / args.shim
        if not shim_path.exists():
            fail(f"Specified shim path does not exist: {shim_path}")
        if not is_shim_file(shim_path):
            fail(f"Specified file does not contain a shim header: {shim_path}")
        shims_to_process = [shim_path]
        out("📋", f"Processing single shim: {args.shim}")
    else:
        out("🔍", "Scanning project for all shim files…")
        shims_to_process = find_all_shims(root)
        out("📋", f"Found {len(shims_to_process)} shim file(s) to process.")

    if not shims_to_process:
        print()
        print("═" * 65)
        print("  ✅  No shim files found — project is already clean!")
        print("═" * 65)
        print("  Phase 4 is complete. You may merge to main.")
        print("═" * 65)
        print()
        sys.exit(0)

    # Process each shim
    removed = 0
    blocked = 0
    failed_list = []

    print()
    print(f"  Processing {len(shims_to_process)} shim(s)…")
    print()

    for shim_path in shims_to_process:
        ok = remove_shim(root, shim_path, language, gate_cmd, dry_run=args.dry_run)
        if ok:
            removed += 1
        else:
            blocked += 1
            failed_list.append(str(shim_path.relative_to(root)))
        print()

    # Final confirmation pass (only if not dry-run and something was removed)
    if not args.dry_run and removed > 0:
        final_ok = final_confirmation_pass(root)
    else:
        final_ok = True

    # Report
    print()
    print("═" * 65)
    print("  🏗️   REFACTOR CLEAN — Phase 4 Report")
    print("═" * 65)
    print(f"  ✅ Shims removed  : {removed}")
    print(f"  🚫 Shims blocked  : {blocked}  (still have dependents)")
    if args.dry_run:
        print("  🔍 Mode          : DRY RUN (no changes made)")
    print()

    if blocked > 0:
        print("  ─── BLOCKED SHIMS ─────────────────────────────────────")
        print("  These shims are still imported by other source files.")
        print("  Complete Phase 3 surgery for the importing files first:")
        for b in failed_list:
            print(f"    🚫 {b}")
        print()
        print("  After fixing, re-run:")
        print("    python3 refactor_clean.py --project-root <root>")
    else:
        print("  ─── ALL SHIMS REMOVED ─────────────────────────────────")
        print("  1. Commit: git add . && git commit -m 'refactor(p4): remove all shims'")
        print("  2. Optionally clean up IMPORT_GRAPH.txt and REFACTOR_MANIFEST.yaml:")
        print("     git rm IMPORT_GRAPH.txt REFACTOR_MANIFEST.yaml")
        print("     git commit -m 'refactor(p4): remove refactor artifacts'")
        print("  3. Merge to main:")
        print("     git checkout main && git merge --no-ff refactor/<project>")
        print("     git tag refactor/<project>-complete")
        print("     git push origin main --tags")

    print("═" * 65)
    print()

    exit_code = 0 if (blocked == 0 and final_ok) else 1
    out("🏁", f"Phase 4 clean complete. Exit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
