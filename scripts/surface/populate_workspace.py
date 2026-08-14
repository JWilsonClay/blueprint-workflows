#!/usr/bin/env python3
"""
populate_workspace.py — Antigravity workspace pointer population
===================================================================
Generates the `<workspace>/.agents/workflows/` pointer set from the
canonical `claude-commands/` payloads — the per-workspace delivery this
suite requires since the 2026-08-13 Antigravity release retired the global
pointer root (probe-confirmed; see the Antigravity Restoration Cluster,
helpdesk-tickets/20260813_secretary_workflow.md).

Usage:
    python3 populate_workspace.py --workspace /abs/path [options]

Modes:
    --mode check   (default) Read-only: forward-resolve the workspace's
                   pointer set against canonical via the secretary engine's
                   resolver. Writes nothing.
    --mode sync    Create a pointer for every canonical payload that lacks
                   one. Existing pointer files are LEFT ALONE (history is
                   not churned) unless --force-regenerate is given.

Options:
    --canonical PATH       Canonical payload directory
                           (default: ~/blueprint-workflows/claude-commands).
    --force-regenerate     In sync mode, rewrite existing pointers whose
                           content differs from the generated template.
    --prune                In sync mode, delete orphan pointers whose own
                           view_file target is DEAD (dead pointers only —
                           live-target project-local pointers are legitimate
                           and are never touched).
    --output-json          Emit the run report as JSON to stdout.
    --quiet                Suppress human-readable output.

Write boundary: every write lands inside <workspace>/.agents/workflows/,
enforced by engine_utils.assert_within; every file write is atomic
(engine_utils.atomic_write). The canonical directory is never written.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from engine_utils import assert_within, atomic_write, safe_mkdir, safe_read
from secretary.delivery_surfaces import list_canonical, resolve_pointer_surface

DEFAULT_CANONICAL = "~/blueprint-workflows/claude-commands"

_DESCRIPTION_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)

POINTER_TEMPLATE = """---
description: "{description}"
tags: [{tag}, global, agent]
---

This workflow uses the Pointer/Payload architecture.

Read the full protocol now:

```
view_file {target}
```

Execute the protocol exactly as written. Do not narrate the file read — begin immediately. If the file is not found, halt and report: `PAYLOAD MISSING: {target}`
"""


def extract_description(canonical_file: Path) -> str:
    """First `description:` value from the canonical frontmatter, unquoted."""
    text = safe_read(canonical_file)
    match = _DESCRIPTION_RE.search(text)
    if not match:
        return canonical_file.stem
    desc = match.group(1).strip()
    if len(desc) >= 2 and desc[0] == desc[-1] and desc[0] in ('"', "'"):
        desc = desc[1:-1]
    return desc.replace('"', r"'")


def render_pointer(canonical_dir: Path, name: str) -> str:
    canonical_file = canonical_dir / name
    return POINTER_TEMPLATE.format(
        description=extract_description(canonical_file),
        tag=Path(name).stem,
        target=str(canonical_file),
    )


def sync_workspace(workspace: str, canonical: str,
                   force_regenerate: bool = False, prune: bool = False) -> dict:
    """
    Fill the workspace's pointer-set gaps from canonical. Returns the run
    report. Raises ValueError on an invalid workspace or a target directory
    that escapes it (symlinked .agents, etc.).
    """
    ws = Path(os.path.expanduser(workspace)).resolve()
    if not ws.is_dir():
        raise ValueError(f"workspace is not a directory: {ws}")
    canonical_dir = Path(os.path.expanduser(canonical)).resolve()
    if not canonical_dir.is_dir():
        raise ValueError(f"canonical directory is not a directory: {canonical_dir}")

    target_dir = ws / ".agents" / "workflows"
    safe_mkdir(target_dir)
    target_dir = assert_within(target_dir, ws)

    canonical_names = list_canonical(str(canonical_dir))
    created, regenerated, present = [], [], []
    for name in canonical_names:
        target = target_dir / name
        rendered = render_pointer(canonical_dir, name)
        if not target.exists():
            atomic_write(assert_within(target, ws), rendered)
            created.append(name)
        elif force_regenerate and safe_read(target) != rendered:
            atomic_write(assert_within(target, ws), rendered)
            regenerated.append(name)
        else:
            present.append(name)

    pruned = []
    check = resolve_pointer_surface(str(target_dir), str(canonical_dir), canonical_names)
    if prune:
        canonical_set = set(canonical_names)
        for finding in list(check.dangling):
            if finding.name in canonical_set:
                continue  # dead canonical-named pointers are repair targets, not prune targets
            victim = target_dir / finding.name
            if victim.is_file():
                assert_within(victim, ws).unlink()
                pruned.append(finding.name)
        if pruned:
            check = resolve_pointer_surface(str(target_dir), str(canonical_dir), canonical_names)

    return {
        "mode": "sync",
        "workspace": str(ws),
        "target_dir": str(target_dir),
        "canonical_dir": str(canonical_dir),
        "canonical_count": len(canonical_names),
        "created": created,
        "regenerated": regenerated,
        "present_count": len(present),
        "pruned": pruned,
        "check": check.as_dict(),
    }


def check_workspace(workspace: str, canonical: str) -> dict:
    """Read-only forward-resolution of the workspace's pointer set."""
    ws = Path(os.path.expanduser(workspace)).resolve()
    if not ws.is_dir():
        raise ValueError(f"workspace is not a directory: {ws}")
    canonical_dir = Path(os.path.expanduser(canonical)).resolve()
    target_dir = ws / ".agents" / "workflows"
    canonical_names = list_canonical(str(canonical_dir))
    check = resolve_pointer_surface(str(target_dir), str(canonical_dir), canonical_names)
    return {
        "mode": "check",
        "workspace": str(ws),
        "target_dir": str(target_dir),
        "canonical_dir": str(canonical_dir),
        "canonical_count": len(canonical_names),
        "check": check.as_dict(),
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="populate_workspace.py",
        description="Populate or check a workspace's .agents/workflows/ Antigravity "
                    "pointer set from the canonical claude-commands/ payloads.",
    )
    p.add_argument("--workspace", required=True, type=str,
                   help="Absolute path to the target workspace root.")
    p.add_argument("--canonical", type=str, default=DEFAULT_CANONICAL,
                   help=f"Canonical payload directory (default: {DEFAULT_CANONICAL}).")
    p.add_argument("--mode", choices=("check", "sync"), default="check",
                   help="check = read-only resolution report (default); sync = fill gaps.")
    p.add_argument("--force-regenerate", action="store_true",
                   help="sync mode: rewrite existing pointers that differ from the template.")
    p.add_argument("--prune", action="store_true",
                   help="sync mode: delete orphan pointers whose view_file target is dead.")
    p.add_argument("--output-json", action="store_true", help="Emit JSON to stdout.")
    p.add_argument("--quiet", action="store_true", help="Suppress human-readable output.")
    return p.parse_args()


def _render_human(report: dict) -> None:
    print("=" * 60)
    print(f"  WORKSPACE POINTER SURFACE — mode={report['mode']}")
    print(f"  workspace: {report['workspace']}")
    print(f"  canonical: {report['canonical_dir']} ({report['canonical_count']} files)")
    if report["mode"] == "sync":
        print(f"  created: {len(report['created'])}  regenerated: {len(report['regenerated'])}  "
              f"already present: {report['present_count']}  pruned: {len(report['pruned'])}")
        for name in report["created"]:
            print(f"    + {name}")
        for name in report["regenerated"]:
            print(f"    ~ {name}")
        for name in report["pruned"]:
            print(f"    - {name} (dead orphan)")
    check = report["check"]
    flag = "OK" if check["ok"] else "FAIL"
    print(f"  resolution: [{flag}] {check['resolved']}/{check['expected']}")
    for category in ("missing", "dangling", "mismatched"):
        for f in check[category]:
            print(f"    {category.upper()}: {f['name']} — {f['detail']}")
    for f in check["orphaned"]:
        print(f"    orphan (info): {f['name']} — {f['detail']}")
    print("=" * 60)


def main() -> int:
    args = _parse_args()
    try:
        if args.mode == "sync":
            report = sync_workspace(args.workspace, args.canonical,
                                    force_regenerate=args.force_regenerate,
                                    prune=args.prune)
        else:
            report = check_workspace(args.workspace, args.canonical)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.output_json:
        print(json.dumps(report, indent=2))
    elif not args.quiet:
        _render_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
