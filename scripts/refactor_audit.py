#!/usr/bin/env python3
"""
refactor_audit.py — Phase 3: Reference Surgery Auditor
=======================================================
Sovereign Refactor Protocol — Script Suite

Dual-mode script for Phase 3 reference surgery support.

--scan mode:
  Reads the manifest and greps the entire codebase for any import statement
  that still references an OLD path (a path that has moved to a new location).
  Produces a "Surgery Queue" report listing every file that needs updating
  and exactly which import lines require changing. The LLM uses this report
  as its session instructions — it rewrites only what the script finds.

--verify mode:
  Re-runs the same scan after the LLM's surgery and confirms that zero
  stale old-path imports remain before the phase is committed.

Hallucination prevented: The LLM cannot believe it updated all references
when it missed 3 files deep in a subdirectory.

Usage:
  python3 refactor_audit.py --project-root /path/to/project --scan
  python3 refactor_audit.py --project-root /path/to/project --verify

Requirements: Python 3.8+, PyYAML (pip install pyyaml).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

MANIFEST_FILENAME = "REFACTOR_MANIFEST.yaml"
SHIM_HEADER_MARKERS = ["⚠️ SHIM FILE", "⚠️ REVERSE SHIM"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def out(emoji: str, msg: str) -> None:
    print(f"{emoji}  {msg}", flush=True)


def fail(msg: str) -> None:
    out("❌", f"FATAL: {msg}")
    sys.exit(1)


def load_manifest(root: Path) -> dict:
    mp = root / MANIFEST_FILENAME
    if not mp.exists():
        fail(f"{MANIFEST_FILENAME} not found. Run refactor_scout.py (Phase 0) first.")
    with open(mp, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "files" not in data:
        fail(f"{MANIFEST_FILENAME} is empty or missing the 'files' key.")
    return data


def is_shim_file(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return any(m in content for m in SHIM_HEADER_MARKERS)
    except (OSError, PermissionError):
        return False


def path_to_import_patterns(rel_path: str, language: str) -> list:
    """
    Convert a file's relative path to the grep patterns that would detect
    imports of that path in source code.

    For Python: 'foo/bar/baz.py' → patterns for 'from foo.bar.baz' and 'import foo.bar.baz'
    For JS/TS: 'foo/bar/baz.ts' → patterns for "from 'foo/bar/baz'" and "require('foo/bar/baz')"
    """
    p = Path(rel_path)
    patterns = []

    if language == "python":
        # Dotted module notation
        module_dotted = str(p.with_suffix("")).replace("/", ".").replace("\\", ".")
        # Also match partial paths (e.g., 'from foo.bar import baz')
        parts = module_dotted.split(".")
        for i in range(len(parts)):
            partial = ".".join(parts[:i + 1])
            patterns.append(f"from {partial}")
            patterns.append(f"import {partial}")
    else:
        # JS path (with and without extension)
        path_no_ext = str(p.with_suffix("")).replace("\\", "/")
        path_with_ext = str(p).replace("\\", "/")
        patterns.append(f"from '{path_no_ext}'")
        patterns.append(f'from "{path_no_ext}"')
        patterns.append(f"from '{path_with_ext}'")
        patterns.append(f'from "{path_with_ext}"')
        patterns.append(f"require('{path_no_ext}')")
        patterns.append(f'require("{path_no_ext}")')

    return list(set(patterns))


# ---------------------------------------------------------------------------
# Core scan logic
# ---------------------------------------------------------------------------

def find_stale_imports(root: Path, manifest: dict) -> dict:
    """
    Scan the codebase for any import that references a path that has MOVED.

    Returns a dict: { source_file: [(line_num, line_content, old_path, new_path), ...] }
    Only non-shim files are included in the results (shims are expected to have these imports).
    """
    language = manifest.get("language", "python")
    files = manifest.get("files", [])

    # Build a map: old_path → new_path (only MOVE entries)
    moved = {
        e["current"]: e["target"]
        for e in files
        if e.get("action") == "MOVE" and e.get("current") != e.get("target")
    }

    if not moved:
        out("⚠️ ", "No MOVE entries found in the manifest. Nothing to scan for.")
        return {}

    # Walk the project and scan each source file
    if language == "python":
        include_ext = {".py"}
    else:
        include_ext = {".js", ".ts", ".jsx", ".tsx", ".mjs"}

    # Map: source_file_rel → list of stale import findings
    findings: dict = defaultdict(list)

    for dirpath, dirnames, filenames in _walk_project(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fp.suffix not in include_ext:
                continue
            if is_shim_file(fp):
                continue

            rel_fp = fp.relative_to(root)
            try:
                lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
            except (OSError, PermissionError):
                continue

            for lineno, line in enumerate(lines, start=1):
                for old_path, new_path in moved.items():
                    patterns = path_to_import_patterns(old_path, language)
                    for pattern in patterns:
                        if pattern in line:
                            findings[str(rel_fp)].append({
                                "line_num": lineno,
                                "line_content": line.rstrip(),
                                "old_path": old_path,
                                "new_path": new_path,
                                "pattern_matched": pattern,
                            })
                            break  # avoid duplicate entries per line per old_path

    return dict(findings)


SKIP_DIRS = {
    "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".tox",
    ".venv", "venv", "env", "node_modules", "dist", "build",
}


def _walk_project(root: Path):
    """Walk project tree, skipping irrelevant directories."""
    import os
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not d.endswith(".egg-info")]
        yield dirpath, dirnames, filenames


# ---------------------------------------------------------------------------
# --scan mode
# ---------------------------------------------------------------------------

def run_scan(root: Path, manifest: dict) -> int:
    """
    Scan mode: produce the Surgery Queue report.
    Returns the number of stale imports found (0 = all clear).
    """
    out("🔍", "SCAN MODE — Searching for stale old-path imports…")

    findings = find_stale_imports(root, manifest)

    if not findings:
        print()
        print("═" * 65)
        print("  ✅  SCAN COMPLETE — Zero stale imports found!")
        print("═" * 65)
        print("  All source files already import from the new (target) paths.")
        print("  Phase 3 reference surgery is complete.")
        print("  Proceed to: python3 refactor_clean.py --project-root <root>")
        print("═" * 65)
        print()
        return 0

    total_stale = sum(len(v) for v in findings.values())

    print()
    print("═" * 65)
    print(f"  🔬  SURGERY QUEUE — {total_stale} stale import(s) in {len(findings)} file(s)")
    print("═" * 65)
    print()
    print("  The following files contain imports from OLD paths (moved in Phase 2).")
    print("  Each file must be surgically updated before Phase 4 can begin.")
    print()

    for file_rel, stale_list in sorted(findings.items()):
        print(f"  📄 {file_rel}  ({len(stale_list)} stale import(s))")
        print(f"  {'─' * 60}")
        for item in stale_list:
            print(f"    Line {item['line_num']:4d} │ {item['line_content']}")
            print(f"           ├─ OLD: {item['old_path']}")
            print(f"           └─ NEW: {item['new_path']}")
            print()

    print("═" * 65)
    print("  ─── LLM SURGERY INSTRUCTIONS ──────────────────────────")
    print("  For each file listed above:")
    print("  1. Open the file.")
    print("  2. Update each listed import line to use the NEW path.")
    print("  3. Run the verification gate to confirm no breakage.")
    print("  4. Commit: git add <file> && git commit -m 'refactor(p3): update imports in <file>'")
    print("  5. Run --verify to confirm zero stale imports remain.")
    print("═" * 65)
    print()

    return total_stale


# ---------------------------------------------------------------------------
# --verify mode
# ---------------------------------------------------------------------------

def run_verify(root: Path, manifest: dict, gate_cmd: str) -> int:
    """
    Verify mode: confirm zero stale imports remain.
    Returns 0 if clean, 1 if stale imports still exist.
    """
    out("🔬", "VERIFY MODE — Confirming zero stale old-path imports remain…")

    findings = find_stale_imports(root, manifest)

    if not findings:
        print()
        print("═" * 65)
        print("  ✅  VERIFY PASSED — Zero stale imports remain!")
        print("═" * 65)
        print("  All source files import directly from new (target) paths.")

        if gate_cmd and not gate_cmd.startswith("#"):
            print()
            print("  Running final verification gate…")
            result = subprocess.run(gate_cmd, shell=True, cwd=str(root))
            if result.returncode == 0:
                print("  ✅  Verification gate PASSED.")
                print()
                print("  Phase 3 is complete. Proceed to:")
                print("  python3 refactor_clean.py --project-root <root>")
            else:
                print("  ❌  Verification gate FAILED despite zero stale imports.")
                print("  Diagnose the failure before proceeding to Phase 4.")
                print("═" * 65)
                return 1
        else:
            print()
            print("  ⚠️   verification_gate not set — skipping gate run.")
            print("  Proceed to: python3 refactor_clean.py --project-root <root>")

        print("═" * 65)
        print()
        return 0

    # Still stale imports found
    total = sum(len(v) for v in findings.values())
    print()
    print("═" * 65)
    print(f"  ❌  VERIFY FAILED — {total} stale import(s) still found in {len(findings)} file(s)")
    print("═" * 65)
    print()
    for file_rel, stale_list in sorted(findings.items()):
        print(f"  📄 {file_rel}")
        for item in stale_list:
            print(f"    Line {item['line_num']:4d} │ {item['line_content']}")
            print(f"           └─ Should import from: {item['new_path']}")
        print()
    print("  Return to Phase 3 surgery and update the files listed above.")
    print("═" * 65)
    print()
    return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="refactor_audit.py",
        description=(
            "Phase 3 Auditor: scan for stale old-path imports (--scan) or\n"
            "verify zero stale imports remain after surgery (--verify)."
        ),
    )
    p.add_argument("--project-root", required=True,
                   help="Path to the root of the project being refactored.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--scan", action="store_true",
                      help="Scan and produce the Surgery Queue report.")
    mode.add_argument("--verify", action="store_true",
                      help="Verify zero stale imports remain (run after surgery).")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    if not root.exists():
        fail(f"Project root does not exist: {root}")

    mode = "SCAN" if args.scan else "VERIFY"
    out("🏗️ ", f"Sovereign Refactor Protocol — Phase 3: Reference Auditor ({mode})")
    out("📁", f"Project root: {root}")

    manifest = load_manifest(root)
    gate_cmd = manifest.get("verification_gate", "")

    if args.scan:
        result = run_scan(root, manifest)
        # 0 = no stale imports (all clear), non-zero = queue depth
        # Exit 0 either way (finding stale imports is not a script failure)
        sys.exit(0)
    else:
        result = run_verify(root, manifest, gate_cmd)
        sys.exit(result)


if __name__ == "__main__":
    main()
