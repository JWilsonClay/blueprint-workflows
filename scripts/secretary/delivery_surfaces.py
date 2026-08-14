"""
delivery_surfaces.py — Delivery-Surface Verification (forward resolution)
===========================================================================
The read-only mechanical layer behind `/secretary` Phase 1 Step 1.1.5, built
for helpdesk-tickets/20260813_secretary_workflow.md (Antigravity Restoration
Cluster, work item 2): the 2026-08-13 Antigravity release moved its state
root and all 33 global pointers went unreachable — while SUITE_HEALTH.md
kept reporting 33/33 healthy, because the suite measured the payload layer
(which cannot break) and never the delivery surfaces (which did).

This module resolves every canonical payload FORWARD onto each registered,
active delivery surface:

  symlink surfaces  — the entry exists, resolves, and lands on the canonical
                      file it names (a regular-file copy is a mismatch: it
                      delivers content today and drifts from canonical
                      tomorrow, which is exactly the risk being measured)
  pointer surfaces  — the pointer file exists, carries a `view_file`
                      directive, and that target exists and IS the canonical
                      file the pointer is named for

and reports every failure BY NAME (missing / dangling / mismatched), never
as a bare count — 33 = 33 reconciles perfectly while containing two errors
(the limitations.md / design-orchestrator.md drifts proved exactly that).

Orphans — surface entries with no canonical counterpart — are reported
informationally and are NOT failures when their own target resolves: a
project workspace may legitimately carry project-local pointers. An orphan
whose target is dead is dangling like any other entry.

State roots carry a data_class: DERIVED (regenerable from canonical) vs
PRIMARY (no other copy exists). A missing PRIMARY root is its own named
condition — this incident's cost asymmetry was invisible to a pointer
count (148 KB of pointers were fully replaceable; the 6.2 GB of agent
history behind them was not).

Reports facts only — it never judges whether a surface SHOULD be active,
whether an orphan is intentional, or what a failure means for the session.
Read-only; writes nothing (per this package's contract).
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from engine_utils import safe_read

VIEW_FILE_RE = re.compile(r"view_file\s+(\S+)")

_FAILURE_VERDICT = "SURFACE_FINDINGS"
_CLEAN_VERDICT = "CLEAN"


@dataclass
class SurfaceEntryFinding:
    name: str
    detail: str

    def as_dict(self) -> dict:
        return {"name": self.name, "detail": self.detail}


@dataclass
class SurfaceReport:
    name: str
    type: str
    path: str
    status: str
    checked: bool
    expected: int = 0
    resolved: int = 0
    missing: List[SurfaceEntryFinding] = field(default_factory=list)
    dangling: List[SurfaceEntryFinding] = field(default_factory=list)
    mismatched: List[SurfaceEntryFinding] = field(default_factory=list)
    orphaned: List[SurfaceEntryFinding] = field(default_factory=list)
    note: str = ""

    @property
    def ok(self) -> bool:
        # Orphans with live targets are informational, never failures.
        return self.checked and not (self.missing or self.dangling or self.mismatched)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "path": self.path,
            "status": self.status,
            "checked": self.checked,
            "expected": self.expected,
            "resolved": self.resolved,
            "missing": [f.as_dict() for f in self.missing],
            "dangling": [f.as_dict() for f in self.dangling],
            "mismatched": [f.as_dict() for f in self.mismatched],
            "orphaned": [f.as_dict() for f in self.orphaned],
            "ok": self.ok,
            "note": self.note,
        }


@dataclass
class StateRootReport:
    name: str
    path: str
    status: str
    data_class: str
    exists: bool
    finding: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "status": self.status,
            "data_class": self.data_class,
            "exists": self.exists,
            "finding": self.finding,
        }


def load_registry(registry_path: str) -> dict:
    """
    Load and parse the delivery-surface registry. Raises ValueError on a
    missing or unparseable registry — surface loss must be fail-visible,
    and a vanished registry is itself a surface loss.
    """
    path = Path(os.path.expanduser(registry_path))
    text = safe_read(path)
    if not text:
        raise ValueError(f"registry missing or unreadable: {path}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"registry unparseable: {path}: {exc}") from exc


def list_canonical(canonical_dir: str, pattern: str = "*.md") -> List[str]:
    """Sorted basenames of the canonical payload set."""
    base = Path(os.path.expanduser(canonical_dir))
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.glob(pattern) if p.is_file())


def _pointer_target(pointer_path: Path) -> Optional[str]:
    text = safe_read(pointer_path)
    match = VIEW_FILE_RE.search(text)
    return match.group(1) if match else None


def resolve_symlink_surface(surface_dir: str, canonical_dir: str,
                            canonical_names: List[str]) -> SurfaceReport:
    """Forward-resolve every canonical name as a symlink under surface_dir."""
    report = SurfaceReport(name="", type="symlink", path=surface_dir,
                           status="active", checked=True,
                           expected=len(canonical_names))
    base = Path(os.path.expanduser(surface_dir))
    canonical_base = Path(os.path.expanduser(canonical_dir))
    if not base.is_dir():
        report.missing = [SurfaceEntryFinding(name="<surface directory>",
                                              detail=f"does not exist: {base}")]
        return report

    canonical_set = set(canonical_names)
    for name in canonical_names:
        entry = base / name
        canonical_file = canonical_base / name
        if entry.is_symlink() and not entry.exists():
            report.dangling.append(SurfaceEntryFinding(
                name=name, detail=f"broken symlink -> {os.readlink(entry)}"))
        elif not entry.exists():
            report.missing.append(SurfaceEntryFinding(
                name=name, detail="no entry on surface"))
        elif not entry.is_symlink():
            report.mismatched.append(SurfaceEntryFinding(
                name=name, detail="regular file, not a symlink — content can drift from canonical"))
        elif entry.resolve() != canonical_file.resolve():
            report.mismatched.append(SurfaceEntryFinding(
                name=name, detail=f"resolves to {entry.resolve()}, not the canonical file"))
        else:
            report.resolved += 1

    for entry in sorted(base.glob("*.md")):
        if entry.name in canonical_set:
            continue
        if entry.is_symlink() and not entry.exists():
            report.dangling.append(SurfaceEntryFinding(
                name=entry.name, detail=f"orphan broken symlink -> {os.readlink(entry)}"))
        else:
            report.orphaned.append(SurfaceEntryFinding(
                name=entry.name, detail="no canonical counterpart (informational)"))
    return report


def resolve_pointer_surface(surface_dir: str, canonical_dir: str,
                            canonical_names: List[str]) -> SurfaceReport:
    """Forward-resolve every canonical name as a pointer file under surface_dir."""
    report = SurfaceReport(name="", type="pointer", path=surface_dir,
                           status="active", checked=True,
                           expected=len(canonical_names))
    base = Path(os.path.expanduser(surface_dir))
    canonical_base = Path(os.path.expanduser(canonical_dir))
    if not base.is_dir():
        report.missing = [SurfaceEntryFinding(name="<surface directory>",
                                              detail=f"does not exist: {base}")]
        return report

    canonical_set = set(canonical_names)
    for name in canonical_names:
        entry = base / name
        canonical_file = canonical_base / name
        if not entry.is_file():
            report.missing.append(SurfaceEntryFinding(
                name=name, detail="no pointer file on surface"))
            continue
        target = _pointer_target(entry)
        if target is None:
            report.dangling.append(SurfaceEntryFinding(
                name=name, detail="no view_file directive in pointer body"))
            continue
        target_path = Path(os.path.expanduser(target))
        if not target_path.is_file():
            report.dangling.append(SurfaceEntryFinding(
                name=name, detail=f"view_file target does not exist: {target}"))
        elif target_path.resolve() != canonical_file.resolve():
            report.mismatched.append(SurfaceEntryFinding(
                name=name, detail=f"view_file targets {target}, not the canonical file"))
        else:
            report.resolved += 1

    for entry in sorted(base.glob("*.md")):
        if entry.name in canonical_set:
            continue
        target = _pointer_target(entry)
        if target is None:
            report.dangling.append(SurfaceEntryFinding(
                name=entry.name, detail="orphan pointer with no view_file directive"))
        elif not Path(os.path.expanduser(target)).is_file():
            report.dangling.append(SurfaceEntryFinding(
                name=entry.name, detail=f"orphan pointer with dead target: {target}"))
        else:
            report.orphaned.append(SurfaceEntryFinding(
                name=entry.name, detail=f"no canonical counterpart, target resolves: {target} (informational)"))
    return report


def check_state_roots(roots: List[dict]) -> List[StateRootReport]:
    """Existence check per registered state root; a missing PRIMARY is named."""
    reports: List[StateRootReport] = []
    for root in roots:
        path = Path(os.path.expanduser(root.get("path", "")))
        exists = path.is_dir()
        data_class = root.get("data_class", "DERIVED")
        finding = None
        if not exists and data_class == "PRIMARY":
            finding = "PRIMARY_STATE_ROOT_MISSING"
        reports.append(StateRootReport(
            name=root.get("name", "<unnamed>"), path=str(path),
            status=root.get("status", "unknown"), data_class=data_class,
            exists=exists, finding=finding))
    return reports


def verify_delivery_surfaces(registry_path: str) -> dict:
    """
    Full verification pass: load registry, forward-resolve every active
    surface, check state roots. Registry problems are reported as findings,
    never swallowed — a health check that fails silent is the defect this
    module exists to close.
    """
    try:
        registry = load_registry(registry_path)
    except ValueError as exc:
        return {
            "registry_found": False,
            "registry_path": str(Path(os.path.expanduser(registry_path))),
            "error": str(exc),
            "surfaces": [],
            "state_roots": [],
            "surfaces_ok": False,
            "verdict_hint": _FAILURE_VERDICT,
        }

    canonical_cfg = registry.get("canonical", {})
    canonical_dir = canonical_cfg.get("path", "")
    pattern = canonical_cfg.get("pattern", "*.md")
    canonical_names = list_canonical(canonical_dir, pattern)

    surface_reports: List[SurfaceReport] = []
    for surface in registry.get("surfaces", []):
        name = surface.get("name", "<unnamed>")
        stype = surface.get("type", "pointer")
        status = surface.get("status", "unknown")
        if status != "active":
            surface_reports.append(SurfaceReport(
                name=name, type=stype, path=surface.get("path", ""),
                status=status, checked=False,
                note=f"not checked — status is '{status}'"))
            continue
        if stype == "symlink":
            resolved_path = surface.get("path", "")
        elif stype == "workspace-pointer":
            resolved_path = surface.get("resolvable_instance", "")
            if not resolved_path:
                surface_reports.append(SurfaceReport(
                    name=name, type=stype, path=surface.get("path", ""),
                    status=status, checked=False,
                    note="active workspace-pointer surface with no resolvable_instance — unverifiable from here, which is itself worth reading as a finding"))
                continue
        else:
            resolved_path = surface.get("path", "")

        if stype == "symlink":
            report = resolve_symlink_surface(resolved_path, canonical_dir, canonical_names)
        else:
            report = resolve_pointer_surface(resolved_path, canonical_dir, canonical_names)
        report.name = name
        report.type = stype
        report.status = status
        if stype == "workspace-pointer":
            report.note = ("verified this repo's own instance only; other workspaces are "
                           "populated/checked per-workspace via scripts/surface/populate_workspace.py")
        surface_reports.append(report)

    root_reports = check_state_roots(registry.get("state_roots", []))

    checked = [s for s in surface_reports if s.checked]
    surfaces_ok = bool(checked) and all(s.ok for s in checked)
    roots_ok = all(r.finding is None for r in root_reports)

    return {
        "registry_found": True,
        "registry_path": str(Path(os.path.expanduser(registry_path))),
        "canonical_dir": str(Path(os.path.expanduser(canonical_dir))),
        "canonical_count": len(canonical_names),
        "surfaces": [s.as_dict() for s in surface_reports],
        "state_roots": [r.as_dict() for r in root_reports],
        "surfaces_ok": surfaces_ok,
        "state_roots_ok": roots_ok,
        "verdict_hint": _CLEAN_VERDICT if (surfaces_ok and roots_ok) else _FAILURE_VERDICT,
    }
