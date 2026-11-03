# Helpdesk Ticket: `/continuous-verify`'s Anchor Engine Cannot See `scripts/build/`, Manufacturing False `ABSENT` Verdicts And False Mock-Trap Candidates That Halt Correct Builds

**To**: Senior Architect of Workflows
**From**: Claude Code session (`research/proforma` workspace, Phase 67 / Fix 258)
**Date**: 2026-07-30
**Subject**: `anchor_cli.py` returns `ABSENT` (or `FOUND_TEST_ONLY` with `production_matches: 0`) for symbols that are genuinely defined in production code, because `IGNORE_DIRS` prunes any directory named `build`. `/continuous-verify` Phase 1's Null-evidence rule reads `ABSENT` as NOT SATISFIED, so a correct build is failed on a criterion it actually met
**Urgency**: HIGH
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING — **escalates the scope of `20260729_focus-plan_workflow.md`, whose diagnosis this ticket independently CONFIRMS**

---

## 1. Executive Summary

`/continuous-verify`'s Anchor Verification Engine (`scripts/continuous_verify/anchor_cli.py`, wrapping `scripts/focus/anchor_scanner.py`) never indexes `research/proforma/scripts/build/` — the project's hand-authored, version-controlled production source tree. Consequently **no symbol defined there is ever located at its definition site.** A symbol resolves only if it happens to be *mentioned* somewhere the scanner does index (a markdown plan, a scratch script). A symbol with no such incidental mention returns `ABSENT`.

This matters because of what the consuming workflow does with `ABSENT`: `/continuous-verify` Phase 1's **Null-evidence rule reads `ABSENT` as NOT SATISFIED**. An acceptance criterion anchored on a newly-authored production symbol is therefore reported as failing a criterion it genuinely met — **a false MISMATCH, which halts a correct build**, in any workspace on this suite that keeps source in a directory named `build`.

A second consequence is worse in kind: a production symbol that exists only in `scripts/build/` and in its test file resolves as **`FOUND_TEST_ONLY`, `production_matches: 0`** — the Mock Trap candidate shape. The engine accuses genuinely-production code of existing only in tests.

**This ticket confirms the diagnosis already filed in `20260729_focus-plan_workflow.md`** (`IGNORE_DIRS` containing `"build"`). It is filed separately because that ticket is scoped to `/focus-plan`'s file anchors, and the consequence reaches further: into `/continuous-verify`'s symbol anchors, its Null-evidence rule, and its Mock Trap detection.

## 2. Root Cause Analysis: "Generic Ignore Convention Prunes A Real Source Tree"

- **The How**: `~/blueprint-workflows/scripts/focus/_utils.py:34-38` defines
  ```python
  IGNORE_DIRS = frozenset({
      ".git", ".venv", "venv", "__pycache__", ".ipynb_checkpoints",
      "node_modules", "build", "dist", ".pytest_cache", ".mypy_cache",
      ".doorway", ".focus", "site-packages",
  })
  ```
  `"build"` sits alongside `node_modules`/`dist` — a set tuned for JS/web projects where `build/` is disposable compiled output. `research/proforma/scripts/build/` is the opposite: hand-authored Python that generates the client deliverable and implements the project's own verification gates. The prune is by bare name, with no inspection of contents.
- **The Why**: the scanner reports "I looked and found nothing" as evidence of absence, but it never looked. The consuming rule then converts that non-evidence into a verdict.

## 3. Forensic Evidence — measured 2026-07-30, ground truth by `grep`

**Invocation validated before any negative was trusted.** An earlier probe using `--symbol` (not a real flag) returned empty output; that was a statement about the flag, not the engine. The runs below use the documented `--symbol-queries`. *(This precaution exists because an audit of this project once reported a present, git-tracked file as missing on the strength of an unvalidated search pattern.)*

| Symbol | Genuine definition (`grep`) | Engine verdict | Locations returned |
|---|---|---|---|
| `resolve_unresolved` | `scripts/build/status_text_lint.py:437` | **`ABSENT`**, prod=0, test=0 | `[]` |
| `tasks_phase_spans` | `scripts/build/status_text_lint.py:335` | `FOUND_PRODUCTION`, prod=1 | `scratch/ph67_fix255_mutation_check.py:L59` — **a mention, not the definition** |
| `acknowledgement` | `scripts/build/status_text_lint.py:419` | `FOUND_PRODUCTION`, prod=3 | `implementation-plan.md:L635`, `tasks.md:L829`, `scratch/…:L16` — **all mentions** |
| `block_parity` | `scripts/build/status_text_lint.py:387` | **`FOUND_TEST_ONLY`**, prod=0 | `scripts/tests/test_status_text_lint.py:L47` |
| `mask_mentions` | `scripts/build/status_text_lint.py:258` | `FOUND_PRODUCTION`, prod=4 | 4 markdown/scratch mentions — **definition site absent from the list** |

**The decisive row is `resolve_unresolved`**: a genuinely-production function with no incidental mention anywhere else. It returns `ABSENT`. Every symbol that *does* resolve does so through a mention in an indexed file; the `scripts/build/` definition never appears in any location list.

**`block_parity` is the Mock Trap false accusation**, live: `production_matches: 0`, `FOUND_TEST_ONLY`, for a function defined in production at line 387 of a script that is a mandatory verification gate.

### Correction to a prior record, on this evidence

`research/proforma/implementation-plan.md`'s **P7** hypothesised that `IGNORE_DIRS`'s `"build"` entry *"cannot explain this session's result"* — because `convert_workbook` returned `FOUND_PRODUCTION` from inside `scripts/build/` — and therefore that `20260729_focus-plan_workflow.md` **"has diagnosed the wrong defect."** P7 was careful to label this a hypothesis, not a finding. **It is now refuted.** A `FOUND_PRODUCTION` result does not imply the directory was indexed: it implies the symbol was *named somewhere else*. `20260729_focus-plan_workflow.md`'s diagnosis is correct and should not be retracted. That earlier session's uncertainty was reasonable given one data point; this is five, with the definition-site column making the mechanism unambiguous.

## 4. Remediation

Not applied — this workflow does not fix failures. The three shapes proposed in `20260729_focus-plan_workflow.md` (per-workspace override; content-aware `build`/`dist` detection; narrowing the default set) all apply unchanged, since it is the same root cause. Additions specific to the `/continuous-verify` consumption path:

1. **Do not let `ABSENT` mean NOT SATISFIED when the scanner's own coverage is in doubt.** A scanner that pruned a directory the anchor path points into should report *unverifiable*, not *absent*. Null-evidence is only evidence when the search was actually performed over the relevant substrate.
2. **Location lists should distinguish a definition from a mention.** Every misleading row above would have been self-evident if the output separated `def`/`class` sites from incidental textual occurrences — and the `FOUND_PRODUCTION` verdicts here rest entirely on mentions.
3. **Gate `FOUND_TEST_ONLY` on the same coverage question.** Accusing code of being test-only is a serious verdict; producing it from an index that excluded the production directory is a false positive with reputational cost inside an audit trail.

## 5. Cross-References

- **Same root cause, already filed**: `20260729_focus-plan_workflow.md` — this ticket confirms its diagnosis and extends the blast radius to `/continuous-verify`.
- Project-local record: `research/proforma/implementation-plan.md`, outstanding-work row **`U10`**, and the **P7** hypothesis corrected above.
- Practical consequence already anticipated in that project: Phases 61-63 deliver constants and defined names rather than functions, so their 5g gates were expected to raise spurious Mock Trap candidates. This ticket is why those must not be read as findings.
- Sibling tickets filed the same day by the same Fix: `20260730_remediation-ledger-unparseable-findings_workflow.md`, `20260730_defect-classes-recommendation-overmatch_workflow.md`, `20260730_phase-status-found-incomplete-conflation_workflow.md`.
- **Nothing under `~/blueprint-workflows/` was edited to file this ticket.**
