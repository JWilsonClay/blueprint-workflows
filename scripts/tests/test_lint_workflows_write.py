"""
test_lint_workflows_write.py — Tests for lint_workflows.py's --fix-hashes --write mode.

Covers: helpdesk-tickets/CLOSED_20260704_lint-fix-hashes-gap_workflow.md.

Background: --fix-hashes previously only ever printed computed hashes ("paste
by hand into frontmatter"), while the suite's own Change Log convention
described it as if it wrote the value automatically -- a real, repeated
terminology/behavior mismatch. This file proves the new --write mode actually
patches content_hash in place, and that --fix-hashes alone (no --write)
remains print-only, unchanged.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from suite.lint_workflows import _write_content_hash


_SAMPLE = """---
description: "Sample workflow for testing"
version: 1
content_hash: "sha256:PENDING_RECOMPUTE"
---

# /sample — Sample Workflow

Body content that happens to mention content_hash in prose, which must never
be matched by the frontmatter-only replacement.

## STRICT RULES

1. Never do the thing.
"""

_NO_HASH_FIELD = """---
description: "No content_hash field at all"
version: 1
---

# /no-hash — No Hash Field
"""

_NO_FRONTMATTER = "# /no-frontmatter\n\nJust a body, no frontmatter block.\n"


class TestWriteContentHashHelper(unittest.TestCase):
    """Unit tests for _write_content_hash() in isolation."""

    def test_replaces_hash_in_frontmatter_only(self):
        result = _write_content_hash(_SAMPLE, "abc123")
        self.assertIn('content_hash: "sha256:abc123"', result)
        self.assertNotIn("PENDING_RECOMPUTE", result)
        # The body's prose mention of content_hash must be untouched.
        self.assertIn(
            "which must never\nbe matched by the frontmatter-only replacement.",
            result,
        )

    def test_noop_when_no_content_hash_field(self):
        result = _write_content_hash(_NO_HASH_FIELD, "abc123")
        self.assertEqual(result, _NO_HASH_FIELD, "should not silently inject a new field")

    def test_noop_when_no_frontmatter(self):
        result = _write_content_hash(_NO_FRONTMATTER, "abc123")
        self.assertEqual(result, _NO_FRONTMATTER)


class TestFixHashesWriteCLI(unittest.TestCase):
    """Integration test: real subprocess invocation against a temp workspace."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.workspace = self.tmp / "workspace"
        commands_dir = self.workspace / "claude-commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "sample.md").write_text(_SAMPLE, encoding="utf-8")
        self.scripts_dir = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *extra_args):
        return subprocess.run(
            [sys.executable, str(self.scripts_dir / "suite" / "lint_workflows.py"),
             "--workspace", str(self.workspace), "--fix-hashes", *extra_args],
            capture_output=True, text=True, cwd=str(self.scripts_dir),
        )

    def test_fix_hashes_without_write_does_not_modify_file(self):
        before = (self.workspace / "claude-commands" / "sample.md").read_text(encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0)
        after = (self.workspace / "claude-commands" / "sample.md").read_text(encoding="utf-8")
        self.assertEqual(before, after, "--fix-hashes alone must remain print-only")
        self.assertIn("sample.md: sha256:", result.stdout)

    def test_fix_hashes_with_write_patches_file_in_place(self):
        result = self._run("--write")
        self.assertEqual(result.returncode, 0)
        after = (self.workspace / "claude-commands" / "sample.md").read_text(encoding="utf-8")
        self.assertNotIn("PENDING_RECOMPUTE", after)
        self.assertIn("content_hash: \"sha256:", after)
        self.assertIn("Write complete: 1 file(s) updated", result.stdout)
        # Re-running immediately after should now report the hash as already correct
        # (no CRITICAL/WARNING hash-mismatch finding) via the normal lint path.
        lint_result = subprocess.run(
            [sys.executable, str(self.scripts_dir / "suite" / "lint_workflows.py"),
             "--workspace", str(self.workspace), "--quiet"],
            capture_output=True, text=True, cwd=str(self.scripts_dir),
        )
        self.assertNotIn("hash mismatch", lint_result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
