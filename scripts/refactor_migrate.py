#!/usr/bin/env python3
"""
refactor_migrate.py — Phase 2: Physical Migration
==================================================
Sovereign Refactor Protocol — Script Suite

Responsibilities:
  1. Read REFACTOR_MANIFEST.yaml from the project root.
  2. For a specified module (--module <name>) or all modules (--all):
     a. Execute `git mv old_path new_path` (never cp+rm).
     b. Write a REVERSE SHIM at the old path pointing to the new location.
     c. Run the verification gate.
     d. Print PASS/FAIL with specific error output if failing.
  3. With --all: process all MOVE entries sequentially, stopping on first failure.

Hallucination prevented: The LLM cannot use cp+rm instead of git mv, or
write a reverse shim that points to the wrong new path.

Usage:
  python3 refactor_migrate.py --project-root /path/to/project --module <filename_stem>
  python3 refactor_migrate.py --project-root /path/to/project --all [--dry-run]

Requirements: Python 3.8+, PyYAML (pip install pyyaml), git in PATH.
"""

import argparse
import sys
from pathlib import Path

from core.console import out, fail, section_header, section_rule
from core.manifest import load_manifest, get_language, get_verification_gate
from core.git_ops import run_cmd, run_gate
from core.shim_templates import make_reverse_shim

try:
    import yaml
except ImportError:
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Core migration logic
# ---------------------------------------------------------------------------

def git_mv(root: Path, current: str, target: str, dry_run: bool) -> bool:
    """
    Execute git mv. Returns True on success.
    This is the ONLY acceptable move mechanism — preserves full git history.
    """
    old_abs = root / current
    new_abs = root / target

    if not old_abs.exists():
        out("❌", f"Source file does not exist: {old_abs}")
        out("❌", "Cannot git mv a file that doesn't exist.")
        return False

    if new_abs.exists():
        # Check if it's a shim (created by bridge.py in Phase 1)
        content = new_abs.read_text(encoding="utf-8", errors="replace")
        if "⚠️ SHIM FILE" in content:
            out("⚠️ ", f"Target is a Phase 1 shim — removing it before git mv: {new_abs.relative_to(root)}")
            if not dry_run:
                r = run_cmd(["git", "rm", "-f", str(new_abs.relative_to(root))], root)
                if r.returncode != 0:
                    out("❌", f"Could not git rm shim: {r.stderr.strip()}")
                    return False
        else:
            out("❌", f"Target already exists and is NOT a shim: {new_abs}")
            out("❌", "Refusing to overwrite. Resolve manually.")
            return False

    # Ensure target parent directory exists
    if not dry_run:
        new_abs.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["git", "mv", current, target]
    out("📦", f"{'[DRY RUN] ' if dry_run else ''}git mv {current} → {target}")

    if dry_run:
        return True

    r = run_cmd(cmd, root)
    if r.returncode != 0:
        out("❌", f"git mv failed:\n{r.stderr.strip()}")
        return False

    out("✅", f"git mv complete: {current} → {target}")
    return True


def write_reverse_shim(root: Path, current: str, target: str, language: str, dry_run: bool) -> bool:
    """Write the reverse shim at the old (current) path."""
    old_path = root / current
    content = make_reverse_shim(language, current, target)

    what = f"{'[DRY RUN] ' if dry_run else ''}reverse shim → {current}"
    out("📄", f"Writing {what}")
    out("📄", f"  Points to: {target}")

    if dry_run:
        return True

    old_path.parent.mkdir(parents=True, exist_ok=True)
    with open(old_path, "w", encoding="utf-8") as f:
        f.write(content)

    out("✅", f"Reverse shim written: {current}")
    return True


def migrate_entry(root: Path, entry: dict, language: str, gate_cmd: str,
                  dry_run: bool) -> bool:
    """
    Migrate one MOVE entry:
      1. git mv current → target
      2. Write reverse shim at current
      3. Run verification gate
    Returns True if all three steps succeed.
    """
    current = entry["current"]
    target = entry["target"]
    action = entry.get("action", "MOVE")

    section_rule(f"[{action}] {current} → {target}")

    # Step 1: git mv
    if not git_mv(root, current, target, dry_run):
        out("❌", f"git mv failed for: {current}")
        return False

    # Step 2: reverse shim
    if not write_reverse_shim(root, current, target, language, dry_run):
        out("❌", f"Failed to write reverse shim for: {current}")
        return False

    # Step 3: verification gate
    if gate_cmd and not gate_cmd.startswith("#") and not dry_run:
        if not run_gate(gate_cmd, root):
            out("❌", f"Verification gate failed after migrating: {current}")
            out("🛑", "Stopping. Do not proceed until the gate passes.")
            return False

    out("🎉", f"Migration complete: {current} → {target}")
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="refactor_migrate.py",
        description=(
            "Phase 2: Execute git mv for each MOVE entry in the manifest,\n"
            "then write a reverse shim at the old path and run the gate."
        ),
    )
    p.add_argument("--project-root", required=True,
                   help="Path to the root of the project being refactored.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--module", metavar="NAME",
                      help="Migrate one module (stem of current filename, e.g. 'utils').")
    mode.add_argument("--all", action="store_true",
                      help="Migrate all MOVE entries sequentially. Stops on first failure.")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview all actions without writing or moving any files.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    if not root.exists():
        fail(f"Project root does not exist: {root}")

    out("🏗️ ", "Sovereign Refactor Protocol — Phase 2: Physical Migration")
    out("📁", f"Project root: {root}")

    if args.dry_run:
        out("🔍", "DRY RUN mode — no files will be moved or written.")

    manifest = load_manifest(root)
    language = get_language(manifest)
    gate_cmd = get_verification_gate(manifest)
    files = manifest.get("files", [])

    if not gate_cmd:
        out("⚠️ ", "verification_gate is not set — gate will be SKIPPED.")

    # Get MOVE-eligible entries
    move_entries = [e for e in files if e.get("action") == "MOVE"]

    if not move_entries:
        out("⚠️ ", "No MOVE entries found in the manifest. Nothing to do.")
        sys.exit(0)

    # Select entries to process
    if args.all:
        selected = move_entries
        out("📋", f"Processing ALL {len(selected)} MOVE entries sequentially.")
    else:
        # Match by module name (filename stem or partial path match)
        needle = args.module.lower()
        selected = [
            e for e in move_entries
            if needle in Path(e["current"]).stem.lower()
            or needle in e["current"].lower()
        ]
        if not selected:
            out("❌", f"No MOVE entry found matching module name: '{args.module}'")
            out("❌", "Available MOVE entries:")
            for e in move_entries:
                print(f"    {e['current']} → {e['target']}")
            sys.exit(1)
        if len(selected) > 1:
            out("⚠️ ", f"Multiple matches for '{args.module}':")
            for e in selected:
                print(f"    {e['current']}")
            out("⚠️ ", "Proceeding with all matches. Use a more specific name to narrow.")

    # Execute migrations
    succeeded = 0
    failed = 0
    for entry in selected:
        ok = migrate_entry(root, entry, language, gate_cmd or "", dry_run=args.dry_run)
        if ok:
            succeeded += 1
        else:
            failed += 1
            if not args.dry_run:
                out("🛑", "Stopping on first failure (--all mode).")
                break

    # Final report
    section_header("REFACTOR MIGRATE — Phase 2 Report")
    print(f"  ✅ Migrated successfully : {succeeded}")
    print(f"  ❌ Failed               : {failed}")
    if args.dry_run:
        print("  🔍 Mode                 : DRY RUN (no changes made)")
    print()
    if failed == 0:
        print("  ─── NEXT STEPS ────────────────────────────────────────")
        print("  1. Verify with: git log --oneline -5")
        print("  2. Commit: git add . && git commit -m 'refactor(p2): git mv <module>'")
        print("  3. Repeat for next module, or proceed to Phase 3:")
        print("     python3 refactor_audit.py --project-root <root> --scan")
    print("═" * 65)
    print()

    out("🏁", f"Phase 2 migration complete. Exit code: {'0' if failed == 0 else '1'}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
