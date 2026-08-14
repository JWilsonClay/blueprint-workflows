"""
test_populate_workspace.py — Test suite for scripts/surface/populate_workspace.py

Covers: sync creating a fully-resolving pointer set (including description
extraction from canonical frontmatter and internal-quote sanitization),
idempotency, the leave-existing-alone default vs --force-regenerate, orphan
semantics (live-target orphans survive prune; dead-target orphans are pruned
only when asked; dead CANONICAL-named pointers are never pruned — they are
repair targets, not clutter), the write boundary (a `.agents` symlinked
outside the workspace is refused via assert_within), check-mode read-only
invariant, and CLI integration.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from surface.populate_workspace import (
    check_workspace,
    extract_description,
    render_pointer,
    sync_workspace,
)

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
        _write(self.canonical / "alpha.md",
               '---\ndescription: "Alpha protocol — does \"quoted\" things"\n---\nbody\n')
        _write(self.canonical / "beta.md",
               "---\ndescription: Beta protocol\n---\nbody\n")
        self.workspace = self.tmp / "ws"
        self.workspace.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _target(self) -> Path:
        return self.workspace / ".agents" / "workflows"


class TestSync(_FixtureBase):
    def test_sync_creates_fully_resolving_set(self):
        report = sync_workspace(str(self.workspace), str(self.canonical))
        self.assertEqual(sorted(report["created"]), ["alpha.md", "beta.md"])
        self.assertTrue(report["check"]["ok"])
        self.assertEqual(report["check"]["resolved"], 2)
        body = (self._target() / "beta.md").read_text(encoding="utf-8")
        self.assertIn(f"view_file {self.canonical / 'beta.md'}", body)
        self.assertIn("PAYLOAD MISSING", body)

    def test_description_extracted_and_sanitized(self):
        desc = extract_description(self.canonical / "alpha.md")
        self.assertIn("Alpha protocol", desc)
        self.assertNotIn('"', desc)
        rendered = render_pointer(self.canonical, "alpha.md")
        self.assertIn('description: "Alpha protocol', rendered)

    def test_sync_is_idempotent(self):
        sync_workspace(str(self.workspace), str(self.canonical))
        second = sync_workspace(str(self.workspace), str(self.canonical))
        self.assertEqual(second["created"], [])
        self.assertEqual(second["present_count"], 2)

    def test_existing_pointer_left_alone_unless_forced(self):
        sync_workspace(str(self.workspace), str(self.canonical))
        custom = self._target() / "alpha.md"
        _write(custom, f"---\ndescription: hand-tuned\n---\n\n```\nview_file {self.canonical / 'alpha.md'}\n```\n")
        report = sync_workspace(str(self.workspace), str(self.canonical))
        self.assertEqual(report["regenerated"], [])
        self.assertIn("hand-tuned", custom.read_text(encoding="utf-8"))

        forced = sync_workspace(str(self.workspace), str(self.canonical),
                                force_regenerate=True)
        self.assertEqual(forced["regenerated"], ["alpha.md"])
        self.assertNotIn("hand-tuned", custom.read_text(encoding="utf-8"))

    def test_prune_removes_only_dead_orphans(self):
        sync_workspace(str(self.workspace), str(self.canonical))
        live_orphan = self._target() / "project-local.md"
        _write(live_orphan,
               f"---\ndescription: local\n---\n\n```\nview_file {self.canonical / 'alpha.md'}\n```\n")
        dead_orphan = self._target() / "retired-thing.md"
        _write(dead_orphan,
               f"---\ndescription: dead\n---\n\n```\nview_file {self.tmp / 'gone.md'}\n```\n")

        unpruned = sync_workspace(str(self.workspace), str(self.canonical))
        self.assertEqual(unpruned["pruned"], [])
        self.assertTrue(dead_orphan.exists())

        pruned = sync_workspace(str(self.workspace), str(self.canonical), prune=True)
        self.assertEqual(pruned["pruned"], ["retired-thing.md"])
        self.assertFalse(dead_orphan.exists())
        self.assertTrue(live_orphan.exists())

    def test_dead_canonical_named_pointer_is_never_pruned(self):
        sync_workspace(str(self.workspace), str(self.canonical))
        broken = self._target() / "alpha.md"
        _write(broken, f"---\ndescription: broken\n---\n\n```\nview_file {self.tmp / 'gone.md'}\n```\n")
        report = sync_workspace(str(self.workspace), str(self.canonical), prune=True)
        self.assertEqual(report["pruned"], [])
        self.assertTrue(broken.exists())
        self.assertIn("alpha.md", [f["name"] for f in report["check"]["dangling"]])

    def test_workspace_must_exist(self):
        with self.assertRaises(ValueError):
            sync_workspace(str(self.tmp / "no-such-ws"), str(self.canonical))

    def test_agents_symlinked_outside_workspace_is_refused(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.workspace / ".agents").symlink_to(outside)
        with self.assertRaises(ValueError):
            sync_workspace(str(self.workspace), str(self.canonical))
        self.assertEqual(list(outside.rglob("*.md")), [])


class TestCheckMode(_FixtureBase):
    def test_check_reports_without_writing(self):
        sync_workspace(str(self.workspace), str(self.canonical))
        before = _snapshot(self.tmp)
        report = check_workspace(str(self.workspace), str(self.canonical))
        self.assertTrue(report["check"]["ok"])
        self.assertEqual(before, _snapshot(self.tmp))

    def test_check_on_unpopulated_workspace_names_the_gap(self):
        report = check_workspace(str(self.workspace), str(self.canonical))
        self.assertFalse(report["check"]["ok"])
        self.assertEqual(report["check"]["missing"][0]["name"], "<surface directory>")


class TestCliIntegration(_FixtureBase):
    def test_cli_sync_then_check(self):
        proc = subprocess.run(
            [sys.executable, "surface/populate_workspace.py",
             "--workspace", str(self.workspace),
             "--canonical", str(self.canonical),
             "--mode", "sync", "--output-json"],
            cwd=str(SCRIPTS_ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(sorted(payload["created"]), ["alpha.md", "beta.md"])
        self.assertTrue(payload["check"]["ok"])

    def test_cli_invalid_workspace_exits_nonzero(self):
        proc = subprocess.run(
            [sys.executable, "surface/populate_workspace.py",
             "--workspace", str(self.tmp / "absent"),
             "--canonical", str(self.canonical)],
            cwd=str(SCRIPTS_ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
