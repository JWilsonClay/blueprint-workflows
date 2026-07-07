# Honest-Design Discipline — /triage (Phase 4.4)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. Re-runs the
three-question test against `/triage` as it stands today (v3, 502 lines,
last hardened 2026-05-25), continuing the campaign after `/execute-build`
and `/secretary`.

## 1. What is mechanically verifiable here?

`/triage` already reuses three existing engines directly in its Trigger
Matrix (a real, working precedent for this exact discipline):
`scripts/harden/harden_audit.py` (`/harden` row), `scripts/iterate/iterate_audit.py`
(`/iterate-test` row), `scripts/quality/quality_audit.py` (`/quality` row).
`lint_workflows.py --quiet` is called directly for the `/harden-workflow` row.
None of these need re-wiring.

Two of Phase 0's steps duplicate engine logic that already exists elsewhere
in the suite, just not called from here:

| Step | Currently | Existing engine that already does this |
|---|---|---|
| 0b (Tasks & Plan State) | "Read tasks.md... Count tasks by state... note orphaned in-progress" — hand-counted | `scripts/focus/phase_status.py` — already parses `tasks.md` into per-phase checkbox tallies and `status` (`in_progress` directly names the orphaned case) |
| 0c (Receipt State) | "Check `.workflow_state/receipts/`... Are Build Receipts present?... Harden Grades?..." — hand-checked per receipt type | `scripts/receipt/coverage.py`'s `compute_coverage()` — already computes exactly this (`receipt_files_present` for build/validation/harden/docs/design/triage) for `/receipt-check` |

Building new parsers for either would be duplication, not new engine work —
the same finding shape as `/execute-build`'s Phase 4.1.

One genuinely new mechanical gap, directly tied to this file's own most
heavily-repeated STRICT RULE: **Trigger Matrix completeness**. STRICT RULES
3 and 9 both independently name the same guarantee — "never omit a workflow
from the report; omission is Hallucinated Success" — and Phase 1's own
"Completeness requirement" injection restates it a third time. Despite three
separate prose statements of this guarantee, nothing mechanically confirms
it: the model must remember, unaided, to mention all ~24 Trigger Matrix
blocks in the final report. This is exactly the failure shape the
Verification-Spine campaign exists to convert from instruction to structure.

## 2. What is irreducible judgment?

Every actual trigger evaluation: whether a file's mtime pattern, a journal
gap, a commit message, or `<WORKSTREAM_STATE>` genuinely constitutes a
P0-P3 finding: is this suite's entire Trigger Matrix (24 blocks of
judgment-laden conditions like "codebase has not been refactored since
inception" or "journal entries describing unexpected behavior"). Also
irreducible: which priority to assign, whether an intent modifier applies,
and the evidence-citation quality the report requires (STRICT RULE 1).
None of this should be touched — a script cannot decide "is > 500 LOC modified
in the last 7 days actually worth a P2 today," only report the LOC and mtime
facts the model already reads directly via `find`/`wc -l` (0d) — those two
`find` pipelines are already pure shell with zero interpretation baked in;
formalizing them into a Python wrapper would add ceremony, not rigor, so
they are correctly left as inline bash (see disposition below).

## 3. Mock-Trap test, applied to the completeness candidate

Extracting the list of workflow names named in `claude-commands/triage.md`'s
own `### Trigger Matrix` section (each block header is a `**`/name`**`
markdown pattern — a fixed, parseable convention, not free text) and
comparing it against which workflow names appear in a given Triage Report
text is a pure set-difference. It cannot and does not judge whether a
workflow's *triggers were evaluated with genuine rigor* — only whether its
name appears somewhere in the final report (recommendation or "NO ACTION
NEEDED"). A model could still satisfy this mechanical check by pasting a
workflow name into "NO ACTION NEEDED" without truly evaluating its
triggers — that residual risk is real and explicitly *not* eliminated by
this check, and the honest disposition is to say so rather than oversell
the guarantee. What the check *does* eliminate is the narrower, purely
mechanical failure this file's STRICT RULES actually describe: a workflow
silently missing from the report text entirely.

## 4. Engine design for Phase 4.5

New package `scripts/triage/` (sibling of `scripts/secretary/`):

1. **`matrix_completeness.py`**: `extract_matrix_workflows(triage_md_path) -> List[str]`
   (regex `\*\*`(/[\w-]+(?:\s--\S+)*)`\*\*` over `### Trigger Matrix`'s own
   block headers, e.g. `` **`/harden`** `` and `` **`/implementation-plan --workstreams`** ``)
   and `check_report_completeness(matrix_workflows, report_text) -> CompletenessResult`
   (which workflow names from the matrix are absent from `report_text`).
2. No new module needed for 0b/0c — `/triage` calls `phase_status.py`'s
   `build_phase_status_report()` and `receipt/coverage.py`'s
   `compute_coverage()` directly (already CLI-callable via `receipt_audit.py`;
   `phase_status.py` needs the same direct-import pattern `build_audit.py`
   and `secretary_audit.py` already established, not a new CLI).
3. **`triage_audit.py`** CLI: `--workspace`, `--report-file` (path to the
   report text to check for completeness, or `--report-text` inline),
   `--output-json`. Combines the matrix-completeness check with direct
   invocations of the two existing engines' JSON output for one consolidated
   evidence report.

**Explicitly not built**: any wrapper around the 0a git commands, 0d
find/wc pipelines, or 0e journal-staleness check — all three are already
pure, zero-interpretation shell with no duplication anywhere else in the
suite; wrapping them would not increase rigor, only add ceremony for its
own sake, which this suite's own Depth Trap / Instruction Density
Compression discipline explicitly warns against. The 0g Failure Pattern
Surface Scan is judgment-adjacent (flagging *potential* pattern evidence)
and stays prose-guided, matching the precedent already set for the Trigger
Matrix's own P0-P3 assignments.

## 5. Disposition

Seed design confirmed in part, corrected in part: two of Phase 0's steps
should call existing engines directly instead of hand-counting (no new code
needed there — pure wiring, mirroring `/execute-build`'s reuse of
`phase_status.py`); one genuinely new, narrowly-scoped mechanical check
(Trigger Matrix completeness) directly defends this file's own
most-repeated STRICT RULE. Ready for Phase 4.5's build.
