"""
test_investigate_evidence.py — Test suite for scripts/investigate/

Covers: citation extraction (with/without line range), citation
verification (VALID, FILE_MISSING, LINE_OUT_OF_RANGE), search-log
extraction, search-log verification against a real file and a real
directory (VERIFIED and MISMATCH — the mismatch case is a regression test
proving the checker catches a genuinely fabricated match count, not just a
clean-input pass), a shell-injection-safety test proving a malicious
pattern/path cannot execute anything (this module never shells out), and
the read-only invariant.

Run via scripts/run_tests.sh (unittest discover, PYTHONPATH=scripts/).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from investigate.citation_fidelity import extract_citations, verify_citation
from investigate.search_log_verifier import extract_search_log_entries, verify_search_entry


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestExtractCitations(unittest.TestCase):
    def test_extracts_label_path_and_range(self):
        text = "See [evidence](file:///abs/path/to/file.py#L10-L20) for details."
        citations = extract_citations(text)
        self.assertEqual(len(citations), 1)
        c = citations[0]
        self.assertEqual(c.label, "evidence")
        self.assertEqual(c.path, "/abs/path/to/file.py")
        self.assertEqual(c.line_start, 10)
        self.assertEqual(c.line_end, 20)

    def test_extracts_single_line_citation(self):
        text = "[x](file:///abs/path.py#L5)"
        citations = extract_citations(text)
        self.assertEqual(citations[0].line_start, 5)
        self.assertIsNone(citations[0].line_end)

    def test_extracts_citation_with_no_line_range(self):
        text = "[x](file:///abs/path.py)"
        citations = extract_citations(text)
        self.assertIsNone(citations[0].line_start)

    def test_multiple_citations(self):
        text = "[a](file:///x.py#L1-L2) and [b](file:///y.py#L3-L4)"
        citations = extract_citations(text)
        self.assertEqual(len(citations), 2)

    def test_no_citations_returns_empty(self):
        self.assertEqual(extract_citations("no citations here"), [])


class TestVerifyCitation(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_valid_citation_within_range(self):
        f = self.tmp / "file.py"
        _write(f, "\n".join(f"line{i}" for i in range(1, 21)))
        text = f"[x](file://{f}#L5-L10)"
        citation = extract_citations(text)[0]
        result = verify_citation(citation)
        self.assertEqual(result.status, "VALID")

    def test_file_missing(self):
        text = f"[x](file://{self.tmp}/nonexistent.py#L1-L2)"
        citation = extract_citations(text)[0]
        result = verify_citation(citation)
        self.assertEqual(result.status, "FILE_MISSING")

    def test_line_out_of_range_hallucinated_citation(self):
        # Regression: a real, previously-invisible failure mode -- a
        # citation claiming lines that don't exist in the file.
        f = self.tmp / "file.py"
        _write(f, "line1\nline2\nline3\n")
        text = f"[x](file://{f}#L100-L200)"
        citation = extract_citations(text)[0]
        result = verify_citation(citation)
        self.assertEqual(result.status, "LINE_OUT_OF_RANGE")

    def test_no_line_range_but_file_exists(self):
        f = self.tmp / "file.py"
        _write(f, "content\n")
        text = f"[x](file://{f})"
        citation = extract_citations(text)[0]
        result = verify_citation(citation)
        self.assertEqual(result.status, "VALID_NO_LINE_RANGE")


class TestExtractSearchLogEntries(unittest.TestCase):
    def test_extracts_pattern_path_count(self):
        text = 'SEARCH LOG:\n  grep "TODO" src/module.py → 3 matches\n'
        entries = extract_search_log_entries(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].pattern, "TODO")
        self.assertEqual(entries[0].path, "src/module.py")
        self.assertEqual(entries[0].claimed_count, 3)

    def test_zero_match_entry_extracted(self):
        text = 'grep "nonexistent" src/module.py → 0 matches'
        entries = extract_search_log_entries(text)
        self.assertEqual(entries[0].claimed_count, 0)

    def test_ascii_arrow_variant_also_matches(self):
        text = 'grep "TODO" src/module.py -> 2 matches'
        entries = extract_search_log_entries(text)
        self.assertEqual(len(entries), 1)


class TestVerifySearchEntry(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_verified_when_count_matches_single_file(self):
        f = self.tmp / "module.py"
        _write(f, "TODO: fix this\nregular line\nTODO: fix that\n")
        text = f'grep "TODO" {f} → 2 matches'
        entry = extract_search_log_entries(text)[0]
        result = verify_search_entry(entry)
        self.assertEqual(result.status, "VERIFIED")
        self.assertEqual(result.actual_count, 2)

    def test_mismatch_when_claimed_count_is_fabricated(self):
        # Regression: proves the checker actually catches a hallucinated
        # search-log claim, not just a clean-input pass.
        f = self.tmp / "module.py"
        _write(f, "TODO: fix this\nregular line\n")
        text = f'grep "TODO" {f} → 99 matches'
        entry = extract_search_log_entries(text)[0]
        result = verify_search_entry(entry)
        self.assertEqual(result.status, "MISMATCH")
        self.assertEqual(result.actual_count, 1)

    def test_verified_across_directory(self):
        _write(self.tmp / "a.py", "TODO: a\n")
        _write(self.tmp / "sub" / "b.py", "TODO: b\nTODO: c\n")
        text = f'grep "TODO" {self.tmp} → 3 matches'
        entry = extract_search_log_entries(text)[0]
        result = verify_search_entry(entry)
        self.assertEqual(result.status, "VERIFIED")

    def test_path_not_found(self):
        text = f'grep "TODO" {self.tmp}/nope → 0 matches'
        entry = extract_search_log_entries(text)[0]
        result = verify_search_entry(entry)
        self.assertEqual(result.status, "PATH_NOT_FOUND")

    def test_invalid_regex_pattern_reported_not_raised(self):
        f = self.tmp / "module.py"
        _write(f, "content\n")
        text = f'grep "[unclosed" {f} → 0 matches'
        entry = extract_search_log_entries(text)[0]
        result = verify_search_entry(entry)
        self.assertEqual(result.status, "INVALID_PATTERN")

    def test_shell_metacharacters_in_pattern_do_not_execute(self):
        """
        Shell-injection safety: a malicious pattern/path combination must
        never be passed to a shell. Since this module never shells out
        (pure Python `re` + file I/O), a pattern like this can only ever be
        treated as a (harmless, if odd) regex -- never executed.
        """
        f = self.tmp / "module.py"
        _write(f, "content\n")
        malicious_pattern = "$(touch /tmp/pwned_marker_should_never_exist)"
        marker = Path("/tmp/pwned_marker_should_never_exist")
        if marker.exists():
            marker.unlink()
        text = f'grep "{malicious_pattern}" {f} → 0 matches'
        entry = extract_search_log_entries(text)[0]
        verify_search_entry(entry)  # must not raise, must not execute anything
        self.assertFalse(marker.exists())


class TestReadOnlyInvariant(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _write(self.tmp / "module.py", "TODO: x\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self) -> set:
        return {p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")}

    def test_writes_nothing(self):
        before = self._snapshot()
        f = self.tmp / "module.py"
        text = f'[x](file://{f}#L1-L1)\ngrep "TODO" {f} → 1 matches'
        for c in extract_citations(text):
            verify_citation(c)
        for e in extract_search_log_entries(text):
            verify_search_entry(e)
        self.assertEqual(before, self._snapshot())


if __name__ == "__main__":
    unittest.main()
