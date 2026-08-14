"""
test_delivery_surfaces.py — Test suite for scripts/secretary/delivery_surfaces.py

Covers: canonical listing, symlink-surface forward resolution (resolve /
broken / missing / wrong-target / regular-file-copy / orphan), pointer-surface
forward resolution (resolve / missing / dead target / no directive /
mismatched target / live-target orphan vs dead-target orphan), registry
loading (missing, unparseable, `~`-expansion), the full verify pass
(CLEAN vs SURFACE_FINDINGS, retired-surface skip, workspace-pointer with no
resolvable instance, PRIMARY-state-root-missing condition), the read-only
invariant, and CLI integration via secretary_audit.py --delivery-registry.

The mismatch/orphan semantics under test are the ones that made the original
incident invisible: 33 = 33 reconciled perfectly while containing two errors,
so every failure must be named, and a live-target orphan must NOT fail a
surface (project-local pointers are legitimate).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from secretary.delivery_surfaces import (
    check_state_roots,
    list_canonical,
    load_registry,
    resolve_pointer_surface,
    resolve_symlink_surface,
    verify_delivery_surfaces,
)

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _pointer_body(target: Path) -> str:
    return (
        "---\ndescription: test pointer\ntags: [t, global, agent]\n---\n\n"
        "Read the full protocol now:\n\n```\n"
        f"view_file {target}\n```\n"
    )


def _snapshot(root: Path) -> dict:
    snap = {}
    for p in sorted(root.rglob("*")):
        try:
            st = p.stat()
            snap[str(p)] = (st.st_size, st.st_mtime_ns)
        except OSError:
            snap[str(p)] = None
    return snap


class _FixtureBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.canonical = self.tmp / "canonical"
        for name in ("alpha.md", "beta.md", "gamma.md"):
            _write(self.canonical / name, f"---\ndescription: \"{name} payload\"\n---\nbody\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestListCanonical(_FixtureBase):
    def test_sorted_basenames(self):
        self.assertEqual(list_canonical(str(self.canonical)),
                         ["alpha.md", "beta.md", "gamma.md"])

    def test_missing_dir_returns_empty(self):
        self.assertEqual(list_canonical(str(self.tmp / "nope")), [])


class TestSymlinkSurface(_FixtureBase):
    def setUp(self):
        super().setUp()
        self.surface = self.tmp / "symlinks"
        self.surface.mkdir()
        self.names = ["alpha.md", "beta.md", "gamma.md"]

    def _link_all(self):
        for name in self.names:
            (self.surface / name).symlink_to(self.canonical / name)

    def test_all_resolve(self):
        self._link_all()
        r = resolve_symlink_surface(str(self.surface), str(self.canonical), self.names)
        self.assertTrue(r.ok)
        self.assertEqual((r.resolved, r.expected), (3, 3))

    def test_broken_symlink_is_dangling_by_name(self):
        self._link_all()
        (self.surface / "beta.md").unlink()
        (self.surface / "beta.md").symlink_to(self.tmp / "gone.md")
        r = resolve_symlink_surface(str(self.surface), str(self.canonical), self.names)
        self.assertFalse(r.ok)
        self.assertEqual([f.name for f in r.dangling], ["beta.md"])

    def test_absent_entry_is_missing_by_name(self):
        self._link_all()
        (self.surface / "gamma.md").unlink()
        r = resolve_symlink_surface(str(self.surface), str(self.canonical), self.names)
        self.assertEqual([f.name for f in r.missing], ["gamma.md"])

    def test_wrong_target_is_mismatched(self):
        self._link_all()
        (self.surface / "alpha.md").unlink()
        (self.surface / "alpha.md").symlink_to(self.canonical / "beta.md")
        r = resolve_symlink_surface(str(self.surface), str(self.canonical), self.names)
        self.assertEqual([f.name for f in r.mismatched], ["alpha.md"])

    def test_regular_file_copy_is_mismatched(self):
        self._link_all()
        (self.surface / "alpha.md").unlink()
        _write(self.surface / "alpha.md", "a drifted copy")
        r = resolve_symlink_surface(str(self.surface), str(self.canonical), self.names)
        self.assertEqual([f.name for f in r.mismatched], ["alpha.md"])
        self.assertIn("regular file", r.mismatched[0].detail)

    def test_healthy_orphan_is_informational_not_failure(self):
        self._link_all()
        (self.surface / "local.md").symlink_to(self.canonical / "alpha.md")
        r = resolve_symlink_surface(str(self.surface), str(self.canonical), self.names)
        self.assertTrue(r.ok)
        self.assertEqual([f.name for f in r.orphaned], ["local.md"])

    def test_missing_surface_dir_is_named_missing(self):
        r = resolve_symlink_surface(str(self.tmp / "absent"), str(self.canonical), self.names)
        self.assertFalse(r.ok)
        self.assertEqual(r.missing[0].name, "<surface directory>")


class TestPointerSurface(_FixtureBase):
    def setUp(self):
        super().setUp()
        self.surface = self.tmp / "pointers"
        self.surface.mkdir()
        self.names = ["alpha.md", "beta.md", "gamma.md"]

    def _point_all(self):
        for name in self.names:
            _write(self.surface / name, _pointer_body(self.canonical / name))

    def test_all_resolve(self):
        self._point_all()
        r = resolve_pointer_surface(str(self.surface), str(self.canonical), self.names)
        self.assertTrue(r.ok)
        self.assertEqual((r.resolved, r.expected), (3, 3))

    def test_missing_pointer_named(self):
        self._point_all()
        (self.surface / "beta.md").unlink()
        r = resolve_pointer_surface(str(self.surface), str(self.canonical), self.names)
        self.assertEqual([f.name for f in r.missing], ["beta.md"])

    def test_dead_target_is_dangling(self):
        self._point_all()
        _write(self.surface / "alpha.md", _pointer_body(self.tmp / "retired.md"))
        r = resolve_pointer_surface(str(self.surface), str(self.canonical), self.names)
        self.assertEqual([f.name for f in r.dangling], ["alpha.md"])

    def test_no_view_file_directive_is_dangling(self):
        self._point_all()
        _write(self.surface / "alpha.md", "---\ndescription: x\n---\nno directive here\n")
        r = resolve_pointer_surface(str(self.surface), str(self.canonical), self.names)
        self.assertEqual([f.name for f in r.dangling], ["alpha.md"])
        self.assertIn("no view_file", r.dangling[0].detail)

    def test_wrong_existing_target_is_mismatched(self):
        self._point_all()
        _write(self.surface / "alpha.md", _pointer_body(self.canonical / "beta.md"))
        r = resolve_pointer_surface(str(self.surface), str(self.canonical), self.names)
        self.assertEqual([f.name for f in r.mismatched], ["alpha.md"])

    def test_orphans_live_vs_dead(self):
        self._point_all()
        _write(self.surface / "project-local.md", _pointer_body(self.canonical / "alpha.md"))
        r = resolve_pointer_surface(str(self.surface), str(self.canonical), self.names)
        self.assertTrue(r.ok)
        self.assertEqual([f.name for f in r.orphaned], ["project-local.md"])

        _write(self.surface / "limitations.md", _pointer_body(self.tmp / "retired-payload.md"))
        r = resolve_pointer_surface(str(self.surface), str(self.canonical), self.names)
        self.assertFalse(r.ok)
        self.assertIn("limitations.md", [f.name for f in r.dangling])


class TestRegistryAndVerify(_FixtureBase):
    def _registry(self, **overrides) -> dict:
        surface = self.tmp / "pointers"
        surface.mkdir(exist_ok=True)
        for name in ("alpha.md", "beta.md", "gamma.md"):
            _write(surface / name, _pointer_body(self.canonical / name))
        reg = {
            "schema_version": 1,
            "canonical": {"path": str(self.canonical), "pattern": "*.md",
                          "data_class": "PRIMARY"},
            "surfaces": [
                {"name": "test-pointers", "type": "pointer", "path": str(surface),
                 "status": "active", "data_class": "DERIVED"},
                {"name": "retired-surface", "type": "pointer",
                 "path": str(self.tmp / "long-gone"), "status": "retired",
                 "data_class": "DERIVED"},
            ],
            "state_roots": [
                {"name": "live-root", "path": str(self.tmp), "status": "active",
                 "data_class": "PRIMARY"},
            ],
        }
        reg.update(overrides)
        return reg

    def test_load_registry_missing_raises(self):
        with self.assertRaises(ValueError):
            load_registry(str(self.tmp / "no-such.json"))

    def test_load_registry_unparseable_raises(self):
        bad = self.tmp / "bad.json"
        _write(bad, "{not json")
        with self.assertRaises(ValueError):
            load_registry(str(bad))

    def test_load_registry_expands_tilde(self):
        reg_file = self.tmp / "reg.json"
        _write(reg_file, json.dumps(self._registry()))
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp)}):
            loaded = load_registry("~/reg.json")
        self.assertEqual(loaded["schema_version"], 1)

    def test_verify_happy_path_is_clean_and_skips_retired(self):
        reg_file = self.tmp / "reg.json"
        _write(reg_file, json.dumps(self._registry()))
        report = verify_delivery_surfaces(str(reg_file))
        self.assertTrue(report["registry_found"])
        self.assertEqual(report["verdict_hint"], "CLEAN")
        by_name = {s["name"]: s for s in report["surfaces"]}
        self.assertTrue(by_name["test-pointers"]["ok"])
        self.assertFalse(by_name["retired-surface"]["checked"])

    def test_verify_missing_registry_is_fail_visible(self):
        report = verify_delivery_surfaces(str(self.tmp / "vanished.json"))
        self.assertFalse(report["registry_found"])
        self.assertEqual(report["verdict_hint"], "SURFACE_FINDINGS")

    def test_verify_dead_surface_yields_findings_verdict(self):
        reg = self._registry()
        shutil.rmtree(self.tmp / "pointers")
        reg_file = self.tmp / "reg.json"
        _write(reg_file, json.dumps(reg))
        report = verify_delivery_surfaces(str(reg_file))
        self.assertEqual(report["verdict_hint"], "SURFACE_FINDINGS")
        self.assertFalse(report["surfaces_ok"])

    def test_workspace_pointer_without_instance_is_unchecked_with_note(self):
        reg = self._registry()
        reg["surfaces"].append({"name": "ws", "type": "workspace-pointer",
                                "path": "{workspace}/.agents/workflows",
                                "status": "active", "data_class": "DERIVED"})
        reg_file = self.tmp / "reg.json"
        _write(reg_file, json.dumps(reg))
        report = verify_delivery_surfaces(str(reg_file))
        ws = [s for s in report["surfaces"] if s["name"] == "ws"][0]
        self.assertFalse(ws["checked"])
        self.assertIn("resolvable_instance", ws["note"])

    def test_primary_state_root_missing_is_named_condition(self):
        roots = [
            {"name": "gone-primary", "path": str(self.tmp / "gone"),
             "status": "active", "data_class": "PRIMARY"},
            {"name": "gone-derived", "path": str(self.tmp / "also-gone"),
             "status": "active", "data_class": "DERIVED"},
        ]
        reports = check_state_roots(roots)
        self.assertEqual(reports[0].finding, "PRIMARY_STATE_ROOT_MISSING")
        self.assertIsNone(reports[1].finding)


class TestReadOnlyInvariant(_FixtureBase):
    """Mirrors the read-only invariant convention (test_secretary_evidence.py)."""

    def test_verify_pass_writes_nothing(self):
        surface = self.tmp / "pointers"
        surface.mkdir()
        _write(surface / "alpha.md", _pointer_body(self.canonical / "alpha.md"))
        reg_file = self.tmp / "reg.json"
        _write(reg_file, json.dumps({
            "canonical": {"path": str(self.canonical), "pattern": "*.md"},
            "surfaces": [{"name": "p", "type": "pointer", "path": str(surface),
                          "status": "active"}],
            "state_roots": [],
        }))
        before = _snapshot(self.tmp)
        verify_delivery_surfaces(str(reg_file))
        self.assertEqual(before, _snapshot(self.tmp))


class TestCliIntegration(_FixtureBase):
    def test_secretary_audit_delivery_registry_flag(self):
        surface = self.tmp / "pointers"
        surface.mkdir()
        for name in ("alpha.md", "beta.md", "gamma.md"):
            _write(surface / name, _pointer_body(self.canonical / name))
        reg_file = self.tmp / "reg.json"
        _write(reg_file, json.dumps({
            "canonical": {"path": str(self.canonical), "pattern": "*.md"},
            "surfaces": [{"name": "p", "type": "pointer", "path": str(surface),
                          "status": "active"}],
            "state_roots": [],
        }))
        proc = subprocess.run(
            [sys.executable, "secretary/secretary_audit.py",
             "--workspace", str(self.tmp),
             "--delivery-registry", str(reg_file),
             "--output-json"],
            cwd=str(SCRIPTS_ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        delivery = payload["delivery_surfaces"]
        self.assertTrue(delivery["registry_found"])
        self.assertEqual(delivery["verdict_hint"], "CLEAN")
        self.assertEqual(delivery["surfaces"][0]["resolved"], 3)


if __name__ == "__main__":
    unittest.main()
