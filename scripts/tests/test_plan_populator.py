"""
test_plan_populator.py — Test suite for the canonical plan/tasks populator
(scripts/plan/ensure_plan_templates.py).

Covers: absent-file population + customization, the Safety Invariant (a file
with real content is NEVER overwritten, force or no force), the empty-file +
--force path, dry-run (reports without writing), idempotency, and error
handling for a missing templates directory.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from plan.ensure_plan_templates import PlanPopulator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestPlanPopulator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir()
        self.templates_dir = self.tmp / "templates" / "plan"
        self.templates_dir.mkdir(parents=True)
        _write(
            self.templates_dir / "tasks.md.template",
            "# tasks.md — [Workspace/Project Name] (Active — only uncompleted items)\n",
        )
        _write(
            self.templates_dir / "implementation-plan.md.template",
            "# implementation-plan.md — [Workspace/Project Name]\n\n## [INTENT] User Objective\n",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _populator(self, **kwargs):
        return PlanPopulator(workspace=self.workspace, templates_dir=self.templates_dir, **kwargs)

    def test_absent_files_are_populated_and_customized(self):
        report = self._populator().run()
        actions = {a["file"]: a["action"] for a in report["actions"]}
        self.assertEqual(actions, {"tasks.md": "populated", "implementation-plan.md": "populated"})
        tasks_content = (self.workspace / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("workspace", tasks_content)
        self.assertNotIn("[Workspace/Project Name]", tasks_content)
        self.assertEqual(report["summary"], {"populated": 2, "would_populate": 0, "skipped": 0, "errors": 0})

    def test_existing_file_with_content_is_never_overwritten(self):
        original = "# tasks.md — my real, hand-written plan\n\n- [x] real work already done\n"
        _write(self.workspace / "tasks.md", original)
        report = self._populator().run()
        action = next(a for a in report["actions"] if a["file"] == "tasks.md")
        self.assertEqual(action["action"], "skipped_exists")
        self.assertEqual((self.workspace / "tasks.md").read_text(encoding="utf-8"), original)

    def test_existing_file_with_content_is_never_overwritten_even_with_force(self):
        original = "# tasks.md — my real, hand-written plan\n\n- [x] real work already done\n"
        _write(self.workspace / "tasks.md", original)
        report = self._populator(force=True).run()
        action = next(a for a in report["actions"] if a["file"] == "tasks.md")
        self.assertEqual(action["action"], "skipped_exists")
        self.assertEqual((self.workspace / "tasks.md").read_text(encoding="utf-8"), original)

    def test_empty_file_skipped_without_force(self):
        _write(self.workspace / "tasks.md", "   \n\n  ")
        report = self._populator().run()
        action = next(a for a in report["actions"] if a["file"] == "tasks.md")
        self.assertEqual(action["action"], "skipped_empty")
        self.assertEqual((self.workspace / "tasks.md").read_text(encoding="utf-8"), "   \n\n  ")

    def test_empty_file_populated_with_force(self):
        _write(self.workspace / "tasks.md", "   \n")
        report = self._populator(force=True).run()
        action = next(a for a in report["actions"] if a["file"] == "tasks.md")
        self.assertEqual(action["action"], "populated")
        self.assertIn("workspace", (self.workspace / "tasks.md").read_text(encoding="utf-8"))

    def test_dry_run_reports_without_writing(self):
        report = self._populator(dry_run=True).run()
        actions = {a["file"]: a["action"] for a in report["actions"]}
        self.assertEqual(actions, {"tasks.md": "would_populate", "implementation-plan.md": "would_populate"})
        self.assertFalse((self.workspace / "tasks.md").exists())
        self.assertFalse((self.workspace / "implementation-plan.md").exists())

    def test_idempotent_second_run_skips(self):
        self._populator().run()
        second = self._populator().run()
        actions = {a["file"]: a["action"] for a in second["actions"]}
        self.assertEqual(actions, {"tasks.md": "skipped_exists", "implementation-plan.md": "skipped_exists"})

    def test_missing_template_reports_error_not_crash(self):
        (self.templates_dir / "tasks.md.template").unlink()
        report = self._populator().run()
        action = next(a for a in report["actions"] if a["file"] == "tasks.md")
        self.assertEqual(action["action"], "error")
        self.assertEqual(report["summary"]["errors"], 1)


if __name__ == "__main__":
    unittest.main()
