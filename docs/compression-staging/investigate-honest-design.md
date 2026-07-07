# Honest-Design Discipline — /investigate (Phase 5.4)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. Fourth of
the remaining 5 Verification-Spine targets.

## 1. What is mechanically verifiable here?

Like `/redteam`, `/investigate` operates against an arbitrary target
system — its investigation target's codebase, logs, and schema are
unknown in advance. But two of its own conventions are **suite-defined,
not target-defined**, and therefore genuinely schema-agnostic to verify:

1. **Citation format.** STRICT RULE 2 and the GLOSSARY's own "Citation"
   term mandate `[label](file:///absolute/path/to/file#LN-LM)` for every
   piece of evidence in the Investigation Report. This is `/investigate`'s
   own imposed convention, not the target project's — so checking whether
   a citation actually resolves (does the file exist? is `LN-LM` within
   the file's real line count?) is a pure, schema-agnostic fact, exactly
   matching tasks.md's own "citation fidelity report" framing. Today,
   nothing checks this — a hallucinated line range or a stale citation
   (correct at write time, since drifted) would be invisible unless a
   human manually opens every link.
2. **Search Log claims.** Phase 1c's SEARCH LOG requires `grep "[pattern]"
   [path] → [N matches / 0 matches]` for every search run, explicitly
   noting "a zero-result search is evidence too." Nothing currently
   confirms the claimed match count is real — an agent could log `grep
   "foo" bar.py → 0 matches` without having actually run it (or having
   misremembered the result), and nothing would catch the discrepancy.
   Re-running the exact stated `pattern`/`path` and comparing counts is
   pure mechanical verification of a claim already made in the report's
   own text — not new investigative work, just confirming the log is
   honest.

Both checks operate on the Investigation Report's OWN text (a citation
string, a search-log line) plus the real filesystem — never on the target
codebase's unknown internal schema. This is the same schema-agnostic
discipline `/redteam`'s engines already established.

## 2. What is irreducible judgment?

Whether the issue is ambiguous enough to halt (Phase 0a), which files are
"the crime scene" (Phase 0b), the entire Differential/root-cause elimination
process (Phase 2), the plain-language narrative itself, the Confidence
rating, the MRC's design (Phase 4a), and all remediation-option judgment
(Phase 4b-4d). None of this is remotely mechanizable, and — as with
`/redteam`'s Phase 5 Ghost Logic reconstruction — attempting to mechanize
root-cause determination itself would be the exact Mock Trap this
discipline exists to prevent: a script cannot know *why* something is
broken, only whether a cited piece of evidence for that claim is real.

## 3. Mock-Trap test

Checking whether `file:///path#LN-LM` resolves to a real file and a real
line range cannot and does not judge whether the CONTENT at those lines
actually supports the finding — only whether the citation points somewhere
real and addressable. A `VALID` result is a precondition for a trustworthy
citation, never proof the finding itself is correct. Same for the Search
Log check: confirming a claimed grep match count is accurate says nothing
about whether the search was the *right* search to run, or whether the
matches found are actually relevant — that interpretation stays entirely
with the model. Both checks are structural-honesty checks, not
investigative-quality checks.

## 4. Engine design for Phase 5.4's build

New package `scripts/investigate/` (schema-agnostic, same architectural
class as `scripts/redteam/`):

1. **`citation_fidelity.py`**: `extract_citations(report_text) ->
   List[Citation]` (regex for `\[([^\]]+)\]\(file://(/[^)#]+)(?:#L(\d+)(?:-L?(\d+))?)?\)`)
   and `verify_citation(citation) -> CitationResult` (`VALID` / `FILE_MISSING`
   / `LINE_OUT_OF_RANGE` — counts the target file's actual lines and checks
   `LN`/`LM` against it).
2. **`search_log_verifier.py`**: `extract_search_log_entries(report_text) ->
   List[SearchLogEntry]` (regex for the `grep "pattern" path → N matches`
   convention) and `verify_search_entry(entry) -> SearchVerifyResult` —
   re-runs the exact pattern against the exact path (via Python's own `re`
   module over file contents, not a shell `grep` subprocess, to avoid
   shell-injection risk from an attacker-influenced report string) and
   compares the actual count to the claimed count.
3. **`reporter.py` + `investigate_audit.py` CLI**: `--report-file`
   (the Investigation Report's text, for citation extraction),
   `--workspace` (root for resolving relative claims), `--output-json`.

**Explicitly not built**: anything for Phase 0 (scope judgment), Phase 2
(root-cause/Differential — pure judgment), Phase 4 (MRC design, remediation
options — judgment), or the Doorway integration phases (1d/2d/4e — already
correctly delegate to `doorway.py`'s existing JSON output, no new
mechanization needed, consistent with `/sentinel`'s finding that reuse
without duplication is already the right shape there).

## 5. Disposition

Seed design **confirmed and specified**: tasks.md's "citation fidelity
report" framing named exactly the right mechanical target. A second,
closely related check (Search Log verification) was found by reading
Phase 1c's own text directly — the same convention risk (an unverified
claim about evidence) applies to search results as much as to citations,
and both are genuinely schema-agnostic since they check `/investigate`'s
own imposed reporting conventions, not the target project's structure.
Ready for the build.
