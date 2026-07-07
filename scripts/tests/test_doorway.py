"""
test_doorway.py — Test suite for scripts/doorway/doorway.py's DoorwayContextualizer,
specifically the Option C auto-escalation path and the README existence re-check.

Covers: helpdesk-tickets/CLOSED_20260705_doorway_lazy-scan-stale-readme_workflow.md.

Background: an incremental scan's carry-over logic (scanner.py's should_recurse
branch) copies forward a stale `has_readme` flag for any directory one or more
levels below a content-hash-stable ancestor, without re-statting disk. Two
distinct consequences follow from that one root cause, and this file proves
both fixes:

  1. (Data-loss risk, fixed in integrity.py's create_readme() this same stage)
     auditor.audit() calls create_readme() whenever has_readme is False —
     including a false positive. create_readme() previously had no existence
     check and would silently atomic_write() over a real, hand-authored
     README.md with generic template content. Now it re-verifies against disk
     and no-ops if the file is genuinely present.
  2. (False-reporting risk, Option C, doorway.py run() lines ~214-228)
     Even with fix #1, the stale has_readme flag still makes drift["missing_readme"]
     report a phantom finding. Option C re-scans with full_scan=True when a
     self-heal repair actually occurred, refreshing has_readme for the whole
     tree. This test also proves the escalation condition still fires and
     resolves the phantom report even after fix #1 changes what counts as a
     "repair" (see test_stale_readme_with_no_other_repairs_still_resolves).

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).

[UPDATED 2026-07-07 — Sovereign Scaling Cluster] README self-heal is now
opt-in by default (autoheal_enabled=False in IntegrityManager, completing
the Doorway Design Invariant doorway.py already declared but never finished
enforcing). This file's scenarios are specifically about self-heal/lazy-scan
behavior, so its _run() helper explicitly passes readme_autoheal=True to
keep exercising the real code path each test protects against regression.
TestReadmeAutohealDefaultOff below proves the new suite-wide default
separately, without that override.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from doorway.doorway import DoorwayContextualizer


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestDoorwayStaleReadmeCarryOver(unittest.TestCase):
    """Reproduces the exact carry-over scenario from the governing ticket."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir()
        # A directory with no .py files -- compute_dir_hash() always returns the
        # same (empty-input) hash for it, so an incremental scan never re-visits
        # its children once the first scan has run.
        self.stable_parent = self.workspace / "stable_parent"
        self.stable_parent.mkdir()
        self.child = self.stable_parent / "child"
        self.child.mkdir()
        self.real_readme_content = (
            "# child\n\nThis is a real, hand-authored README with custom content "
            "that must never be silently overwritten by self-healing.\n"
        )
        _write(self.child / "README.md", self.real_readme_content)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, full_scan: bool = False) -> dict:
        ctx = DoorwayContextualizer(
            self.workspace, quiet=True, output_json=True, readme_autoheal=True,
        )
        result = ctx.run(full_scan=full_scan)
        result["metrics"] = dict(ctx.metrics)  # metrics lives on the instance, not in run()'s return dict
        return result

    def _seed_stale_snapshot(self) -> None:
        """
        Run a real full scan first (establishes ground truth: child has_readme
        True), then hand-corrupt the persisted snapshot to say the child's
        README is absent -- reproducing exactly what a lazy incremental scan
        would carry forward if it never re-visited the child directory, without
        needing to fabricate scanner internals.
        """
        self._run(full_scan=True)
        snapshot_path = self.workspace / ".doorway" / "workspace_snapshot.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        key = "stable_parent/child"
        self.assertIn(key, snapshot, "test setup assumption broken: child not in snapshot")
        snapshot[key]["has_readme"] = False
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

    def test_stale_missing_readme_does_not_destroy_real_content(self):
        """The core data-loss regression: a false missing_readme signal must
        never result in a real README's content being overwritten."""
        self._seed_stale_snapshot()
        self._run(full_scan=False)
        self.assertEqual(
            (self.child / "README.md").read_text(encoding="utf-8"),
            self.real_readme_content,
            "create_readme() overwrote real content on a stale has_readme=False signal",
        )

    def test_stale_readme_with_no_other_repairs_still_resolves(self):
        """Even when the ONLY drift signal is the phantom stale entry (so the
        existence re-check means metrics['repairs'] does not increment for it),
        the incremental scan must still end in a state where a subsequent scan
        no longer reports the phantom -- not silently stuck at a false
        missing_readme forever."""
        self._seed_stale_snapshot()
        result = self._run(full_scan=False)
        # Whether via Option C escalating within this same run, or because the
        # snapshot this run persists reflects live disk truth either way, the
        # NEXT incremental scan must be clean.
        second = self._run(full_scan=False)
        self.assertNotIn(
            "stable_parent/child", second.get("drift", {}).get("missing_readme", []),
            "phantom missing_readme persisted across scans with no genuine repair to "
            "trigger Option C's escalation -- the false-positive report never self-corrected",
        )

    def test_escalation_fires_when_a_genuine_repair_also_occurs(self):
        """Positive control: when a real repair happens alongside the stale
        entry, Option C's existing escalation condition (repairs > 0) fires and
        refreshes has_readme for the whole tree in the same run."""
        self._seed_stale_snapshot()
        # A second, genuinely-missing README elsewhere triggers a real repair.
        other = self.workspace / "other_new_dir"
        other.mkdir()
        result = self._run(full_scan=False)
        self.assertGreater(result["metrics"]["repairs"], 0)
        self.assertNotIn(
            "stable_parent/child", result.get("drift", {}).get("missing_readme", []),
            "escalation did not refresh the stale entry within the same run",
        )

    def test_no_escalation_when_nothing_changed(self):
        """Negative control: a clean incremental scan with zero repairs must
        not silently become a full scan every time (perf regression guard)."""
        self._run(full_scan=True)  # establish clean baseline
        result = self._run(full_scan=False)
        self.assertEqual(result["metrics"]["repairs"], 0)


class TestReadmeAutohealDefaultOff(unittest.TestCase):
    """
    [ADDED 2026-07-07 — Sovereign Scaling Cluster]
    Proves the new suite-wide default: a directory with a genuinely missing
    README.md is reported (missing_readme still names it — that reporting is
    unconditional in auditor.py) but no file is materialized and no repair is
    counted, unless the caller explicitly opts in via readme_autoheal=True.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir()
        self.bare_dir = self.workspace / "bare_dir"
        self.bare_dir.mkdir()
        _write(self.bare_dir / "marker.py", "# no README here yet\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_no_readme_created_by_default(self):
        ctx = DoorwayContextualizer(self.workspace, quiet=True, output_json=True)
        result = ctx.run(full_scan=True)
        self.assertFalse(
            (self.bare_dir / "README.md").exists(),
            "README.md was created despite autoheal defaulting to off",
        )
        self.assertEqual(ctx.metrics["repairs"], 0)
        self.assertIn("bare_dir", result.get("drift", {}).get("missing_readme", []))

    def test_readme_created_when_explicitly_opted_in(self):
        ctx = DoorwayContextualizer(
            self.workspace, quiet=True, output_json=True, readme_autoheal=True,
        )
        ctx.run(full_scan=True)
        self.assertTrue(
            (self.bare_dir / "README.md").exists(),
            "opting in via readme_autoheal=True should still materialize a README",
        )
        self.assertGreater(ctx.metrics["repairs"], 0)


if __name__ == "__main__":
    unittest.main()
