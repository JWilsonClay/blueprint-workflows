"""
diff_checkers.py — Phase-specific filesystem checkers for the Diff Review Node
==============================================================================
Extracted from refactor_diff.py during SoC decomposition.

Each checker compares the actual filesystem state against the declared
intent in REFACTOR_MANIFEST.yaml for a specific refactor phase.
"""

from pathlib import Path

from core.diff_models import Severity, DiffReport
from core.filesystem import (
    walk_project, is_shim_file, get_source_extensions,
    read_file_safe, is_forward_shim, is_reverse_shim, shim_points_to
)


def find_all_shims(root: Path) -> list:
    result = []
    for dirpath, _, filenames in walk_project(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            if is_shim_file(fp):
                result.append(str(fp.relative_to(root)))
    return sorted(result)


def find_unexpected_files(root: Path, language: str, manifest: dict) -> list:
    exts = get_source_extensions(language)
    known_paths = set()
    for e in manifest.get("files", []):
        known_paths.add(e.get("current", ""))
        known_paths.add(e.get("target", ""))

    unexpected = []
    for dirpath, _, filenames in walk_project(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fp.suffix not in exts:
                continue
            rel = str(fp.relative_to(root))
            if rel not in known_paths:
                unexpected.append(rel)
    return sorted(unexpected)


def check_phase_p1(root: Path, manifest: dict, report: DiffReport) -> None:
    files = manifest.get("files", [])

    for entry in files:
        current = entry.get("current", "")
        target = entry.get("target", "")
        action = entry.get("action", "")

        if action in ("MOVE", "SPLIT"):
            target_path = root / target
            if not target_path.exists():
                report.add(
                    Severity.CRITICAL, "MISSING_SHIM", target,
                    f"Expected a forward shim at target path — file does not exist.",
                    f"Run: python3 refactor_bridge.py --project-root <root>"
                )
            elif not is_forward_shim(target_path):
                report.add(
                    Severity.WARNING, "SHIM_HEADER_MISSING", target,
                    f"File exists at target path but does not contain '⚠️ SHIM FILE' header.",
                    f"The real file may have been moved here already. Check Phase 2 status."
                )
            else:
                pointed_to = shim_points_to(target_path)
                if pointed_to and pointed_to != current:
                    report.add(
                        Severity.CRITICAL, "SHIM_WRONG_SOURCE", target,
                        f"Shim points to '{pointed_to}' but manifest says source is '{current}'.",
                        f"The shim was written with an incorrect import path. Regenerate it."
                    )

            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "SOURCE_MISSING", current,
                    f"Original source file missing — was it moved before Phase 2?",
                    f"Phase 1 must not move files. Check if git mv was run prematurely."
                )
            elif is_shim_file(current_path):
                report.add(
                    Severity.WARNING, "SOURCE_IS_SHIM", current,
                    f"Original source path contains a shim header — may be a Phase 2 artifact.",
                    f"If Phase 2 has already run for this file, this is expected."
                )

        elif action == "KEEP":
            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "KEEP_FILE_MISSING", current,
                    f"KEEP entry does not exist on disk.",
                    f"Verify the path in the manifest is correct."
                )
            elif is_shim_file(current_path):
                report.add(
                    Severity.WARNING, "KEEP_FILE_IS_SHIM", current,
                    f"KEEP file contains a shim header — should be a real source file.",
                    f"This file should not have been shimmed."
                )


def check_phase_p2(root: Path, manifest: dict, report: DiffReport) -> None:
    files = manifest.get("files", [])

    for entry in files:
        current = entry.get("current", "")
        target = entry.get("target", "")
        action = entry.get("action", "")

        if action == "MOVE":
            target_path = root / target
            if not target_path.exists():
                report.add(
                    Severity.CRITICAL, "TARGET_MISSING", target,
                    f"Target file does not exist after Phase 2 — was git mv run?",
                    f"Run: python3 refactor_migrate.py --project-root <root> --module <name>"
                )
            elif is_forward_shim(target_path):
                report.add(
                    Severity.CRITICAL, "TARGET_STILL_SHIM", target,
                    f"Target path still contains a Phase 1 forward shim — real file not yet moved here.",
                    f"Run git mv for this module: refactor_migrate.py --module <name>"
                )
            elif is_reverse_shim(target_path):
                report.add(
                    Severity.CRITICAL, "TARGET_IS_REVERSE_SHIM", target,
                    f"Target path contains a reverse shim — migration appears inverted.",
                    f"Investigate whether current and target are swapped in the manifest."
                )

            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "REVERSE_SHIM_MISSING", current,
                    f"Old path does not exist — reverse shim was never written.",
                    f"Write a reverse shim at '{current}' pointing to '{target}'."
                )
            elif not is_reverse_shim(current_path):
                report.add(
                    Severity.WARNING, "REVERSE_SHIM_HEADER_MISSING", current,
                    f"Old path exists but lacks the '⚠️ REVERSE SHIM' header.",
                    f"Confirm this is a proper reverse shim, not the original file."
                )
            else:
                pointed_to = shim_points_to(current_path)
                if pointed_to and pointed_to != target:
                    report.add(
                        Severity.CRITICAL, "REVERSE_SHIM_WRONG_TARGET", current,
                        f"Reverse shim points to '{pointed_to}' but manifest target is '{target}'.",
                        f"Rewrite the reverse shim with the correct new path."
                    )

        elif action == "KEEP":
            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "KEEP_FILE_MISSING", current,
                    f"KEEP file is missing from disk.",
                    f"Verify this file was not accidentally moved or deleted."
                )


def check_phase_p3(root: Path, manifest: dict, report: DiffReport) -> None:
    check_phase_p2(root, manifest, report)

    files = manifest.get("files", [])
    move_entries = [e for e in files if e.get("action") == "MOVE"]
    language = manifest.get("language", "python")

    if language == "python":
        exts = {".py"}
    else:
        exts = {".js", ".ts", ".jsx", ".tsx"}

    for entry in move_entries:
        current = entry.get("current", "")
        target = entry.get("target", "")
        surgery_complete = entry.get("surgery_complete", False)

        target_path = root / target
        if surgery_complete and target_path.exists() and not is_shim_file(target_path):
            content = read_file_safe(target_path)
            for other in move_entries:
                other_current = other.get("current", "")
                if other_current == current:
                    continue
                if language == "python":
                    p = Path(other_current)
                    dotted = str(p.with_suffix("")).replace("/", ".")
                    if f"from {dotted}" in content or f"import {dotted}" in content:
                        report.add(
                            Severity.WARNING, "SURGERY_COMPLETE_BUT_STALE", target,
                            f"Marked surgery_complete=true but still imports from old path: '{other_current}'.",
                            f"Update the import in '{target}' to use '{other.get('target', '')}'."
                        )

    total_move = len(move_entries)
    complete = sum(1 for e in move_entries if e.get("surgery_complete", False))
    remaining = total_move - complete

    if remaining > 0:
        report.add(
            Severity.INFO, "SURGERY_PROGRESS", "REFACTOR_MANIFEST.yaml",
            f"Phase 3 progress: {complete}/{total_move} modules have surgery_complete=true. "
            f"{remaining} remaining.",
            f"Run: python3 refactor_audit.py --project-root <root> --scan"
        )
    else:
        report.add(
            Severity.INFO, "SURGERY_PROGRESS", "REFACTOR_MANIFEST.yaml",
            f"All {total_move} MOVE entries are marked surgery_complete=true in the manifest.",
            f"Run --verify to confirm: python3 refactor_audit.py --project-root <root> --verify"
        )


def check_phase_p4(root: Path, manifest: dict, report: DiffReport, pre_merge: bool) -> None:
    all_shims = find_all_shims(root)
    if all_shims:
        for shim_path in all_shims:
            report.add(
                Severity.CRITICAL, "SHIM_STILL_EXISTS", shim_path,
                f"Shim file still exists — Phase 4 cleanup is incomplete.",
                f"Run: python3 refactor_clean.py --project-root <root>"
            )
    else:
        report.add(
            Severity.INFO, "NO_SHIMS_FOUND", "project",
            "Zero shim files found — shim cleanup is complete.",
        )

    files = manifest.get("files", [])

    for entry in files:
        if entry.get("action") == "KEEP":
            current = entry.get("current", "")
            current_path = root / current
            if not current_path.exists():
                report.add(
                    Severity.CRITICAL, "KEEP_FILE_MISSING", current,
                    f"KEEP file is missing — may have been accidentally deleted.",
                    f"Restore from git: git checkout HEAD -- {current}"
                )

    for entry in files:
        if entry.get("action") == "MOVE":
            target = entry.get("target", "")
            current = entry.get("current", "")
            target_path = root / target
            current_path = root / current
            if not target_path.exists():
                report.add(
                    Severity.CRITICAL, "TARGET_MISSING_AT_P4", target,
                    f"MOVE target is missing at Phase 4 — file was never successfully migrated.",
                    f"Investigate: git log --all -- {target}"
                )
            if current_path.exists():
                report.add(
                    Severity.WARNING, "OLD_PATH_STILL_EXISTS", current,
                    f"Old path still exists — reverse shim may not have been removed.",
                    f"Run: python3 refactor_clean.py --project-root <root> --shim {current}"
                )

    if pre_merge:
        for artifact in ["IMPORT_GRAPH.txt", "REFACTOR_MANIFEST.yaml"]:
            artifact_path = root / artifact
            if artifact_path.exists():
                report.add(
                    Severity.WARNING, "ARTIFACT_NOT_CLEANED", artifact,
                    f"Refactor artifact '{artifact}' still exists — remove before merging.",
                    f"Run: git rm {artifact} && git commit -m 'refactor(p4): remove artifacts'"
                )

        unexpected = find_unexpected_files(root, manifest.get("language", "python"), manifest)
        for uf in unexpected:
            if not is_shim_file(root / uf):
                report.add(
                    Severity.WARNING, "UNEXPECTED_FILE", uf,
                    f"Source file exists on disk but is not referenced in the manifest.",
                    f"Verify this file was not accidentally created. Add to manifest if legitimate."
                )
