# Honest-Design Discipline — /harden-workflow (Phase 4.5)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. Re-runs the
three-question test against `/harden-workflow` as it stands today (v4,
856 lines, last hardened 2026-07-04), the last of the four Phase 4
re-verification targets.

## 1. What is mechanically verifiable here?

This file already runs `scripts/suite/lint_workflows.py` — but only ONCE,
late, as a blocking gate at **Phase 7d** (right before certification). Every
earlier phase that asks the SAME structural questions the linter already
answers does so by manual re-reading instead:

| Step | Currently | Duplicates |
|---|---|---|
| Phase 1 Assessment Card | Hand-checklist: "[ ] GLOSSARY section present", "[ ] STRICT RULES...", etc. | `scripts/suite/checks.py`'s `check_structure()` — the exact same five presence checks (GLOSSARY, HOW TO BEGIN, STRICT RULES, INTEGRATION, Change Log), plus `count_strict_rules()`/`count_phases()` for the rule/phase counts |
| Phase 4d Inter-Workflow Reference Integrity | "Identify every reference... confirm the referenced workflow exists" — manual hunting | `check_cross_references()`/`extract_workflow_refs()` — already does exactly this, already run at Phase 7d |
| Phase 5b `/triage` Compatibility Audit | "Cross-reference the description against the trigger matrix... is this workflow represented?" — manual read of `triage.md` | `scripts/triage/matrix_completeness.py`'s `extract_matrix_workflows()` (built this same session, Phase 4.4b) — already extracts every workflow name from `triage.md`'s Trigger Matrix; checking membership is a one-line lookup |
| Phase 7a/7c Command File Completeness Check | A second hand-checklist, immediately before Phase 7d re-derives the same facts via the linter anyway | Same `check_structure()` output Phase 1 should already have produced |

None of this needs a new parser — `scripts/suite/checks.py` already exports
the exact functions needed as importable, tested library code (not just a
CLI): `parse_frontmatter()`, `extract_glossary_terms()`,
`count_strict_rules()`, `count_phases()`, `check_symlinks()`,
`extract_workflow_refs()`. The gap is that `/harden-workflow` never imports
them directly — it re-derives the same facts by eye four separate times
(Phase 1, 4d, 5b, 7a/7c) before finally confirming them mechanically once,
at 7d, near the very end.

One genuinely new mechanical piece, not currently backed anywhere: the
**Degradation Check** (Phase 1) asks the agent to find `Standard Version: N`
in a workflow's Change Log/Certificate and compare it to the Current
Standard Version. That extraction-plus-comparison is pure text-and-arithmetic,
not currently wrapped in any function.

A second new piece, narrower: the **Grade Table** itself (THE SOVEREIGN
STANDARD section) states its four grades as an explicit, binary decision
table over presence/absence of named criteria — "Grades are assigned based
on the presence... of specific structural elements — not subjective quality
of the workflow's content" (the file's own words). Given a set of presence
booleans, computing which of the four grades they satisfy is arithmetic over
a fixed table, not a quality judgment.

## 2. What is irreducible judgment?

Whether a STRICT RULES section is genuinely *complete* (not just present —
STRICT RULE 4b's own text: "a STRICT RULES section that doesn't address the
halt condition is incomplete" is a content-quality call, not a presence
check); Phase 4c's Decision Branch Completeness (identifying every
decision point and whether HALT/PROCEED/third-outcome are all handled);
Phase 2a's Sovereign Scaffold Generator content-filling; the actual STRICT
RULE 3 boundary itself (never touch protocol logic, only structure — a
judgment call about what counts as "structure" vs. "content" in a given
edit); the Hardening Intelligence Payload's "Observed Patterns" and
"Suggested STRICT RULE additions" (Phase 8b); the Phylogeny/crossover
analysis (Phase 9); and the entire Ecosystem Immunity Layer's "antibody"
generation (Phase 10) — none of this is remotely mechanizable, and none of
it should be touched.

## 3. Mock-Trap test, applied to each candidate

- **Reusing `checks.py`'s presence functions**: these report structural
  facts (a section header matched a regex, a rule was numbered N) — they
  cannot and do not judge whether the STRICT RULES are *good* rules, only
  whether the section exists and how many numbered entries it has. Safe.
- **Reusing `extract_matrix_workflows()` for the /triage gap check**: a
  membership test (`is this name in that list?`) — cannot judge whether
  the Trigger Matrix's *treatment* of the workflow is adequate, only whether
  it's named at all. Safe, and explicitly narrower than what Phase 5b's
  prose already claims to check (which is itself just presence, per its own
  wording: "is this workflow represented").
- **Grade computation from the literal Grade Table**: this is the one
  candidate worth stating the boundary on explicitly. The table's stated
  criteria are structural presence/absence — computing the grade from them
  is arithmetic over a fixed rule set, not a design-quality judgment. But
  the file's own STRICT RULE 2 phrasing ("presence and quality of specific
  structural elements") leaves a narrow escape hatch: a STRICT RULES section
  could be *present* but *incomplete* (4b's own words), and the grade table
  as literally written does not capture that nuance — it only asks "is the
  section present," not "is it complete." **Disposition: the engine computes
  a `grade_hint` from presence/absence only, labeled explicitly as advisory
  and one-directional** (mirrors the smell-linter precedent from `/quality`
  v4) — it can suggest "this cannot be Sovereign, Change Log is absent" with
  full confidence (a true negative is unambiguous), but a "$all criteria
  present$" result is a hint toward Sovereign, not a certified grade — the
  model still performs the completeness judgment 4b/4c ask for before
  certifying. This mirrors the same discipline already proven for
  `/quality`'s smell linter: "no smells found says NOTHING about quality."
- **Degradation Check**: extracting a version number and comparing two
  integers cannot judge whether a workflow "still meets" a newer standard's
  spirit — only whether its stamped version number is behind the current
  one. The judgment of "which new criteria apply and whether they matter" is
  explicitly retained (Phase 1's own text: "List which new criteria... Ask
  the user: re-certify now, or log as deferred?" stays exactly as-is).

## 4. Engine design for Phase 4.5's build

New package `scripts/harden_workflow/` (sibling of `scripts/triage/`,
`scripts/secretary/`; named with an underscore to avoid collision with the
existing `scripts/harden/` package, which backs the different workflow
`/harden`, code security):

1. **No new parsing module for structural facts** — import
   `suite.checks.parse_frontmatter`, `extract_glossary_terms`,
   `count_strict_rules`, `count_phases`, `check_symlinks`,
   `extract_workflow_refs` directly. One small, additive refactor to
   `scripts/suite/checks.py`: extract the three inline regex booleans
   currently only computed inside `check_structure()` (`has_how_to_begin`,
   `has_integration`, `has_changelog`) into three standalone, importable
   one-line functions, with `check_structure()` calling them internally —
   behavior-preserving, covered by `test_suite_checks.py`'s existing tests.
2. **`degradation_check.py`**: `extract_standard_version(text) -> Optional[int]`
   (regex for `Standard Version:\s*(\d+)`, takes the last match — a
   Hardening Certificate is typically the final such mention) and
   `check_degradation(certified_version, current_version) -> DegradationResult`
   (`degraded: bool`, both version numbers). `CURRENT_STANDARD_VERSION = 3`
   lives here as the same constant this file's own GLOSSARY names.
3. **`grade_hint.py`**: `compute_grade_hint(facts: dict) -> GradeHintResult` —
   pure function over the presence booleans (frontmatter, glossary,
   how_to_begin, strict_rules_present, structured_output_present,
   changelog_present, symlink_present) implementing the Grade Table's
   literal decision logic, returning `grade_hint` + `missing_criteria`
   (the Hardening Delta list) + a mandatory advisory string repeating the
   one-directional caveat.
4. **`harden_workflow_audit.py`** CLI: given `--workflow-name`, reads the
   target command file, runs all of the above plus the `/triage` gap check
   (importing `triage.matrix_completeness.extract_matrix_workflows`
   directly), emits one consolidated JSON evidence report covering what
   Phase 1's Assessment Card, the Degradation Check, Phase 5b's compatibility
   audit, and Phase 7c's completeness check all separately ask for today.

**Explicitly not built**: `structured_output_present` is the one presence
check with no existing regex anywhere in `checks.py` (a receipt/report/
certificate template's shape varies too much for a single reliable pattern)
— the engine reports `structured_output_present: null` (unknown) rather
than guessing, and the model performs this one check by reading, exactly as
today. Guessing wrong here would be worse than not automating it at all.

## 5. Disposition

Seed design corrected: the real gap is not "no engine exists" (one already
does, thoroughly — `lint_workflows.py`/`checks.py`) but "this file re-derives
by eye, four separate times across four phases, facts an existing engine
already computes once, late, as a final gate." The fix is wiring, not new
parsing, for the bulk of the gap; two small new modules (Degradation Check,
Grade Hint) close the remainder, both scoped tightly to avoid the Mock-Trap
the Grade Table's own "presence vs. quality" distinction warns against.
Ready for the build.
