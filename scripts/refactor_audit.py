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
import sys
from pathlib import Path
from collections import defaultdict

from core.console import out, fail, section_header, section_rule
from core.manifest import load_manifest, get_language, get_verification_gate
from core.filesystem import walk_project, is_shim_file, get_source_extensions
from core.git_ops import run_gate
from core.import_patterns import path_to_import_patterns

try:
    import yaml
except ImportError:
    print("❌  FATAL: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


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
    include_ext = get_source_extensions(language)

    # Map: source_file_rel → list of stale import findings
    findings: dict = defaultdict(list)

    for dirpath, dirnames, filenames in walk_project(root):
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
        section_header("SCAN COMPLETE — Zero stale imports found!")
        print("  All source files already import from the new (target) paths.")
        print("  Phase 3 reference surgery is complete.")
        print("  Proceed to: python3 refactor_clean.py --project-root <root>")
        print("═" * 65)
        print()
        return 0

    total_stale = sum(len(v) for v in findings.values())

    section_header(f"SURGERY QUEUE — {total_stale} stale import(s) in {len(findings)} file(s)")
    print()
    print("  The following files contain imports from OLD paths (moved in Phase 2).")
    print("  Each file must be surgically updated before Phase 4 can begin.")
    print()

    for file_rel, stale_list in sorted(findings.items()):
        print(f"  📄 {file_rel}  ({len(stale_list)} stale import(s))")
        section_rule()
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
        section_header("VERIFY PASSED — Zero stale imports remain!")
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
    section_header(f"VERIFY FAILED — {total} stale import(s) still found in {len(findings)} file(s)")
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
    gate_cmd = get_verification_gate(manifest)

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
