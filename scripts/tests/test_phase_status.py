"""
test_phase_status.py — Test suite for the tasks.md + BUILD_RECEIPTS.md
phase status engine (scripts/focus/phase_status.py).

Covers: phase-boundary detection ("Phase N"/"Stage N" titles, not raw header
level), per-phase checkbox tallies and derived status, BUILD_RECEIPTS.md entry
parsing against the exact /execute-build writer format, phase/receipt
cross-referencing, and the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from focus.phase_status import (
    BUILD_RECEIPTS_RELPATH,
    build_phase_status_report,
    parse_build_receipts,
    parse_tasks_md,
    verify_phase_count,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _all_paths(root: Path) -> set:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


class TestParseTasksMd(unittest.TestCase):
    def test_splits_on_phase_titles(self):
        text = (
            "## Phase 1: Setup\n- [x] task a\n- [x] task b\n\n"
            "## Phase 2: Build\n- [ ] task c\n"
        )
        phases = parse_tasks_md(text)
        self.assertEqual([p.title for p in phases], ["Phase 1: Setup", "Phase 2: Build"])
        self.assertEqual(phases[0].status, "complete")
        self.assertEqual(phases[1].status, "not_started")

    def test_stage_title_recognized(self):
        text = "## Stage 1: Foo\n- [x] a\n"
        phases = parse_tasks_md(text)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].status, "complete")

    def test_non_phase_headers_do_not_fragment(self):
        # A "### Acceptance Criteria" sub-header inside a phase must not
        # start a new phase — its checkboxes belong to the enclosing phase.
        text = (
            "## Phase 1: Setup\n"
            "### Acceptance Criteria\n"
            "- [x] a\n- [ ] b\n"
        )
        phases = parse_tasks_md(text)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].checkboxes.done, 1)
        self.assertEqual(phases[0].checkboxes.open, 1)
        self.assertEqual(phases[0].status, "in_progress")

    def test_overview_header_ignored_as_phase_boundary(self):
        text = "## Overview\nsome prose, no tasks\n\n## Phase 1: Real\n- [ ] a\n"
        phases = parse_tasks_md(text)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].title, "Phase 1: Real")

    def test_mixed_checkboxes_are_in_progress(self):
        text = "## Phase 1: Mix\n- [x] a\n- [/] b\n- [ ] c\n"
        phases = parse_tasks_md(text)
        self.assertEqual(phases[0].status, "in_progress")

    def test_no_checkboxes_status(self):
        text = "## Phase 1: Narrative only\nJust prose, no checkboxes.\n"
        phases = parse_tasks_md(text)
        self.assertEqual(phases[0].status, "no_checkboxes")

    def test_headers_inside_fences_ignored(self):
        text = "## Phase 1: Real\n```\n## Phase 9: not a real phase\n```\n- [x] a\n"
        phases = parse_tasks_md(text)
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0].title, "Phase 1: Real")

    def test_no_phase_titled_headers_yields_empty_not_error(self):
        # An unrecognized naming convention must not raise — found=True,
        # phases=[] is handled at the report level (see TestBuildReport).
        text = "## Milestone A\n- [x] a\n"
        self.assertEqual(parse_tasks_md(text), [])


class TestParseBuildReceipts(unittest.TestCase):
    def test_single_entry(self):
        text = (
            "## 2026-07-04 — /execute-build — Phase 1: Setup\n"
            "- Phase/Stage: Phase 1: Setup\n"
            "- Grade/Status: PHASE COMPLETE\n"
            "- Files: a.py | b.py\n"
            "- Commit: abc1234\n"
            "---\n"
        )
        entries = parse_build_receipts(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].phase, "Phase 1: Setup")
        self.assertEqual(entries[0].grade_status, "PHASE COMPLETE")

    def test_multiple_entries_separated_by_dashes(self):
        text = (
            "## D1 — /execute-build — Phase 1: A\n"
            "- Phase/Stage: Phase 1: A\n- Grade/Status: PHASE COMPLETE\n---\n"
            "## D2 — /execute-build — Phase 2: B\n"
            "- Phase/Stage: Phase 2: B\n- Grade/Status: PHASE COMPLETE\n---\n"
        )
        entries = parse_build_receipts(text)
        self.assertEqual({e.phase for e in entries}, {"Phase 1: A", "Phase 2: B"})

    def test_malformed_block_skipped(self):
        text = "## D1 — /execute-build — Broken\n- Phase/Stage: Broken\n---\n"  # no Grade/Status
        self.assertEqual(parse_build_receipts(text), [])

    def test_grade_status_compared_case_insensitively(self):
        # Only parse_build_receipts + the matching helper need to agree on
        # case-insensitivity; exercised end-to-end via build_phase_status_report
        # in TestBuildReport.test_matching_receipt_found_complete.
        text = "## D1 — /execute-build — Phase 1\n- Phase/Stage: Phase 1\n- Grade/Status: phase complete\n---\n"
        entries = parse_build_receipts(text)
        self.assertEqual(entries[0].grade_status.lower(), "phase complete")


class TestBuildPhaseStatusReport(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_no_tasks_md_at_all(self):
        report = build_phase_status_report(self.tmp)
        self.assertFalse(report.found)
        self.assertEqual(report.phases, [])

    def test_tasks_md_path_override(self):
        # [ADDED 2026-07-06 — Sovereign Redesign Cluster Stage 1 prototype]
        # tasks.md deliberately placed outside workspace root (a real case:
        # implementation-plan/sovereign-redesign-cluster/tasks.md avoids
        # colliding with a separate campaign's root implementation-plan.md).
        # Receipts stay workspace-root-relative regardless -- they are a
        # workspace-wide ledger, not per-plan.
        nested_dir = self.tmp / "nested" / "plan"
        nested_dir.mkdir(parents=True)
        nested_tasks = nested_dir / "tasks.md"
        _write(nested_tasks, "## Phase 1: Setup\n- [x] a\n")
        _write(
            self.tmp / BUILD_RECEIPTS_RELPATH,
            "## 2026-07-06 — /execute-build — Phase 1: Setup\n"
            "- Phase/Stage: Phase 1: Setup\n- Grade/Status: PHASE COMPLETE\n---\n",
        )
        # Default lookup (workspace/tasks.md) must not find the nested file.
        default_report = build_phase_status_report(self.tmp)
        self.assertFalse(default_report.found)
        # Explicit override finds it, and still cross-references the
        # workspace-root receipts ledger correctly.
        report = build_phase_status_report(self.tmp, tasks_md_path=nested_tasks)
        self.assertTrue(report.found)
        self.assertEqual(report.path, str(nested_tasks))
        self.assertTrue(report.receipts_file_found)
        self.assertEqual(report.phases[0].receipt_status, "found_complete")

    def test_tasks_md_present_no_receipts_file(self):
        _write(self.tmp / "tasks.md", "## Phase 1: Setup\n- [x] a\n")
        report = build_phase_status_report(self.tmp)
        self.assertTrue(report.found)
        self.assertFalse(report.receipts_file_found)
        self.assertEqual(report.phases[0].receipt_status, "receipts_file_absent")
        self.assertEqual(report.phases[0].status, "complete")

    def test_matching_receipt_found_complete(self):
        _write(self.tmp / "tasks.md", "## Phase 1: Setup\n- [x] a\n")
        _write(
            self.tmp / BUILD_RECEIPTS_RELPATH,
            "## 2026-07-04 — /execute-build — Phase 1: Setup\n"
            "- Phase/Stage: Phase 1: Setup\n- Grade/Status: PHASE COMPLETE\n---\n",
        )
        report = build_phase_status_report(self.tmp)
        self.assertTrue(report.receipts_file_found)
        self.assertEqual(report.phases[0].receipt_status, "found_complete")

    def test_receipt_for_different_phase_is_not_found(self):
        _write(self.tmp / "tasks.md", "## Phase 1: Setup\n- [x] a\n\n## Phase 2: Build\n- [ ] b\n")
        _write(
            self.tmp / BUILD_RECEIPTS_RELPATH,
            "## D — /execute-build — Phase 1: Setup\n"
            "- Phase/Stage: Phase 1: Setup\n- Grade/Status: PHASE COMPLETE\n---\n",
        )
        report = build_phase_status_report(self.tmp)
        by_title = {p.title: p for p in report.phases}
        self.assertEqual(by_title["Phase 1: Setup"].receipt_status, "found_complete")
        self.assertEqual(by_title["Phase 2: Build"].receipt_status, "not_found")

    def test_checked_but_incomplete_receipt_flagged(self):
        # Checkboxes say done, but the matching receipt's own status isn't a
        # COMPLETE value — surfaced as found_incomplete, a discrepancy for
        # the agent to note rather than silently trusting either signal alone.
        _write(self.tmp / "tasks.md", "## Phase 1: Setup\n- [x] a\n")
        _write(
            self.tmp / BUILD_RECEIPTS_RELPATH,
            "## D — /execute-build — Phase 1: Setup\n"
            "- Phase/Stage: Phase 1: Setup\n- Grade/Status: BUILD FAILED\n---\n",
        )
        report = build_phase_status_report(self.tmp)
        self.assertEqual(report.phases[0].receipt_status, "found_incomplete")

    def test_read_only(self):
        _write(self.tmp / "tasks.md", "## Phase 1: Setup\n- [x] a\n")
        before = _all_paths(self.tmp)
        build_phase_status_report(self.tmp)
        after = _all_paths(self.tmp)
        self.assertEqual(before, after)

    def test_strip_header_annotations_logic(self):
        from focus.phase_status import _strip_header_annotations
        self.assertEqual(_strip_header_annotations("Phase 1: Setup — **READY FOR HANDOFF**"), "Phase 1: Setup")
        self.assertEqual(_strip_header_annotations("Phase 2 - **COMPLETE 2026-07-07** (notes)"), "Phase 2")
        self.assertEqual(_strip_header_annotations("Phase 3 **COMPLETE**"), "Phase 3")
        self.assertEqual(_strip_header_annotations("Phase 4 (handoff: Gemini)"), "Phase 4 (handoff: Gemini)")

    def test_receipt_status_exact_match_with_bold_annotations_stripped(self):
        # Even if headers contain bold annotations, stripping is done first.
        _write(self.tmp / "tasks.md", "## Phase 1 — Quick Wins — **READY FOR HANDOFF**\n- [x] a\n")
        _write(
            self.tmp / BUILD_RECEIPTS_RELPATH,
            "## 2026-07-04 — /execute-build — Phase 1 — Quick Wins\n"
            "- Phase/Stage: Phase 1 — Quick Wins\n- Grade/Status: PHASE COMPLETE\n---\n",
        )
        report = build_phase_status_report(self.tmp)
        self.assertEqual(report.phases[0].receipt_status, "found_complete")

    def test_receipt_status_approx_match_with_parentheticals_stripped(self):
        # If headers contain trailing parentheticals, Pass 2 strips them to match.
        _write(self.tmp / "tasks.md", "## Phase 8: Remediation Pass (handoff: Gemini)\n- [x] a\n")
        _write(
            self.tmp / BUILD_RECEIPTS_RELPATH,
            "## 2026-07-07 — /execute-build — Phase 8: Remediation Pass\n"
            "- Phase/Stage: Phase 8: Remediation Pass\n- Grade/Status: PHASE COMPLETE\n---\n",
        )
        report = build_phase_status_report(self.tmp)
        self.assertEqual(report.phases[0].receipt_status, "found_complete_approx")

    def test_alphanumeric_phase_with_annotation_matches_receipt(self):
        # The real remediation-plan shape (hebrews_6_reader): an alphanumeric
        # sub-phase carrying a completion annotation. The broadened detection
        # regex, annotation stripping, and receipt matching must compose end to
        # end to found_complete — a toy "Phase 3B" alone would not exercise the
        # detection ↔ _strip_header_annotations ↔ _receipt_status_for interaction.
        _write(
            self.tmp / "tasks.md",
            "## Phase 3C-Rem — Structure — **COMPLETE 2026-07-09**\n- [x] a\n",
        )
        _write(
            self.tmp / BUILD_RECEIPTS_RELPATH,
            "## 2026-07-09 — /execute-build — Phase 3C-Rem — Structure\n"
            "- Phase/Stage: Phase 3C-Rem — Structure\n- Grade/Status: PHASE COMPLETE\n---\n",
        )
        report = build_phase_status_report(self.tmp)
        self.assertEqual(len(report.phases), 1)
        self.assertEqual(report.phases[0].title, "Phase 3C-Rem — Structure — **COMPLETE 2026-07-09**")
        self.assertEqual(report.phases[0].receipt_status, "found_complete")

    def test_structure_recognized_field(self):
        # helpdesk-tickets/20260722_phase-status-empty-phases-contract: the
        # "structure not recognized" signal is now a first-class output field.
        # found=False (no tasks.md) → False, distinguished from found-but-empty
        # by `found` itself.
        r0 = build_phase_status_report(self.tmp)
        self.assertFalse(r0.found)
        self.assertFalse(r0.as_dict()["structure_recognized"])
        # found=True with recognized phases → True.
        _write(self.tmp / "tasks.md", "## Phase 1: A\n- [x] a\n")
        self.assertTrue(build_phase_status_report(self.tmp).as_dict()["structure_recognized"])
        # found=True but only unrecognized headers → False (the ticket's core case).
        _write(self.tmp / "tasks.md", "## Scope\n- [ ] x\n\n## Milestone A\n- [ ] y\n")
        r2 = build_phase_status_report(self.tmp)
        self.assertTrue(r2.found)
        self.assertFalse(r2.as_dict()["structure_recognized"])


class TestAlphanumericSubPhases(unittest.TestCase):
    """Coverage for the 2026-07-22 _PHASE_TITLE_RE broadening.

    Letter/dash-suffixed remediation phases ("3B", "3C-Rem", "2a") must be
    recognized, while the by-design rejection of descriptive campaign headers
    (the ticket's deferred STRUCTURAL half) must be preserved.
    Resolves the code half of
    helpdesk-tickets/20260707_phase-status-campaign-header-scope_workflow.md.
    """

    def test_letter_suffixed_phases_recognized(self):
        text = (
            "## Phase 3B: Length Restoration\n- [x] a\n\n"
            "## Phase 3C-Rem: Structure\n- [ ] b\n\n"
            "## Phase 2a: Prep\n- [x] c\n"
        )
        phases = parse_tasks_md(text)
        self.assertEqual(
            [p.title for p in phases],
            ["Phase 3B: Length Restoration", "Phase 3C-Rem: Structure", "Phase 2a: Prep"],
        )
        self.assertEqual(phases[0].status, "complete")
        self.assertEqual(phases[1].status, "not_started")
        self.assertEqual(phases[2].status, "complete")

    def test_numeric_and_letter_suffixed_are_distinct_phases(self):
        # "Phase 3" and "Phase 3B" must NOT collapse into one phase — distinct
        # normalized keys keep their receipts matched independently, so
        # broadening detection introduces no false-positive receipt match.
        text = "## Phase 3: Core\n- [x] a\n\n## Phase 3B: Follow-up\n- [ ] b\n"
        phases = parse_tasks_md(text)
        self.assertEqual([p.title for p in phases], ["Phase 3: Core", "Phase 3B: Follow-up"])
        self.assertEqual(phases[0].status, "complete")
        self.assertEqual(phases[1].status, "not_started")

    def test_descriptive_campaign_headers_still_rejected(self):
        # The load-bearing safety property: the broadening extends the phase
        # SUFFIX, never the phase|stage + digit anchor. Descriptive preamble
        # headers (Scope/Risks/Triage sections — the ticket's STRUCTURAL,
        # deferred half) must remain non-phases.
        text = (
            "## Scope\n- [ ] x\n\n"
            "## Triage Report Recommendations\n- [ ] y\n\n"
            "## Risks & Dependencies\n- [ ] z\n\n"
            "## Phase 1: Real\n- [x] a\n"
        )
        phases = parse_tasks_md(text)
        self.assertEqual([p.title for p in phases], ["Phase 1: Real"])


class TestVerifyPhaseCount(unittest.TestCase):
    """The count-verification gate — the general fix for undercount by ANY
    unrecognized header convention (Step N / Part N / descriptive), including
    the PARTIAL miss that the all-or-nothing structure_recognized boolean is
    blind to. helpdesk-tickets/20260722_phase-status-empty-phases-contract.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_match(self):
        _write(self.tmp / "tasks.md", "## Phase 1: A\n- [x] a\n\n## Phase 2: B\n- [ ] b\n")
        result = verify_phase_count(build_phase_status_report(self.tmp), 2)
        self.assertEqual(result["verdict"], "MATCH")
        self.assertEqual(result["recognized"], 2)

    def test_mismatch_on_partial_miss(self):
        # The exact case structure_recognized CANNOT catch: 2 recognized Phase
        # headers + 1 unrecognized "Step 3". The agent honestly counts 3 units.
        _write(
            self.tmp / "tasks.md",
            "## Phase 1: A\n- [x] a\n\n## Phase 2: B\n- [ ] b\n\n## Step 3: C\n- [ ] c\n",
        )
        report = build_phase_status_report(self.tmp)
        # The boolean is blind to the miss — this is precisely why the gate exists.
        self.assertTrue(report.structure_recognized)
        result = verify_phase_count(report, 3)
        self.assertEqual(result["verdict"], "MISMATCH")
        self.assertEqual(result["recognized"], 2)
        self.assertIn("Revise tasks.md", result["message"])

    def test_no_tasks_md(self):
        result = verify_phase_count(build_phase_status_report(self.tmp), 5)
        self.assertEqual(result["verdict"], "NO_TASKS_MD")

    def test_cli_mismatch_exits_2(self):
        # End-to-end: the gate must actually GATE (non-zero exit), via the
        # module's standalone CLI (self-bootstrapping sys.path, no PYTHONPATH).
        import subprocess
        _write(
            self.tmp / "tasks.md",
            "## Phase 1: A\n- [x] a\n\n## Step 2: B\n- [ ] b\n",
        )
        script = Path(__file__).resolve().parents[1] / "focus" / "phase_status.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--workspace", str(self.tmp),
             "--expect-phases", "2", "--quiet"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2)

    def test_cli_match_exits_0(self):
        import subprocess
        _write(self.tmp / "tasks.md", "## Phase 1: A\n- [x] a\n\n## Phase 2: B\n- [ ] b\n")
        script = Path(__file__).resolve().parents[1] / "focus" / "phase_status.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--workspace", str(self.tmp),
             "--expect-phases", "2", "--quiet"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
