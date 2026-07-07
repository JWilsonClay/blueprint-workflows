# Honest-Design Discipline — /continuous-verify (Phase 5.3)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. Third of the
remaining 5 Verification-Spine targets.

## 1. What is mechanically verifiable here?

`/continuous-verify` operates against an arbitrary target project's
`implementation_plan.md`, the same way `/execute-build` does — but unlike
`/redteam`'s arbitrary-external-codebase problem, this project's *plan
structure* is suite-imposed (any project using `/implementation-plan` or
`/execute-build` gets the same `implementation-plan.md`/`tasks.md`
conventions), and — critically — `scripts/focus/anchor_scanner.py` already
verifies exactly the kind of question this gate asks, against arbitrary
target workspaces, and is already proven in production for `/focus-plan`.

Phase 1 (Acceptance Criteria Verification) and Phase 2 (Forward Contract
Verification) both currently instruct: "identify the physical anchor... use
the Read tool or grep... assess whether it satisfies the criterion" — a
manual re-implementation of what `AnchorScanner.verify_file()` /
`verify_symbol()` already do mechanically:

- `verify_file(query)` → `EXISTS` / `MISSING` / `INVALID`, with locations.
- `verify_symbol(query)` → `FOUND_PRODUCTION` / `FOUND_TEST_ONLY` / `ABSENT`
  — and `FOUND_TEST_ONLY` is a **Mock Trap** signal `/focus-plan` already
  relies on, that `continuous-verify.md` currently has no way to surface at
  all. A criterion whose anchor symbol exists only in test/mock code is
  exactly the failure shape this suite names explicitly, and the current
  workflow's Phase 1 assessment (`SATISFIED`/`NOT SATISFIED`/`UNVERIFIABLE`)
  has no vocabulary for it — a symbol that's `FOUND_TEST_ONLY` could be
  marked `SATISFIED` today with no mechanism flagging the risk.

`anchor_scanner.py` has no standalone CLI today — it's only ever invoked as
a class inside `focus.py`'s full `FocusVerifier` pipeline (plan-parsing +
anchor verification together). `/continuous-verify` needs the anchor-check
half only (it receives its scope — which criteria, which contracts — from
its own Phase 0c, not from re-parsing the whole plan the way `/focus-plan`
does) — so the honest design is a **thin CLI wrapper exposing the class
directly for arbitrary queries**, not a new anchor-verification engine and
not a duplicate of `focus.py`'s full pipeline.

## 2. What is irreducible judgment?

Extracting WHICH criteria and forward contracts apply to Phase N from the
plan's prose (Phase 0c's Scope Manifest) — this requires reading and
interpreting natural-language plan text ("expects", "depends on", "receives
from phase N"), which varies per project and per plan author. Also
irreducible: the actual SATISFIED/NOT SATISFIED semantic judgment once an
anchor's existence is confirmed (does the function's *logic*, not just its
*existence*, fulfill the criterion?), the MISMATCH/UNVERIFIABLE/PARITY
aggregation logic (Phase 3 — already correctly gated by explicit boolean
rules, not touched here), and Options A/B/C's resolution judgment when a
MISMATCH is found.

## 3. Mock-Trap test

`verify_file`/`verify_symbol` report existence and production-vs-test-only
location facts — they cannot and do not judge whether the code at that
anchor actually *implements* the criterion correctly, only whether
something with that name/path exists and where. A `FOUND_PRODUCTION`
result is a precondition for `SATISFIED`, never proof of it — the semantic
check (does this code do what the plan says?) stays with the model, exactly
as `/focus-plan`'s own established precedent already treats this same
scanner's output. Surfacing `FOUND_TEST_ONLY` as a flag is safe because it
is one-directional and advisory (a Mock Trap candidate to investigate, not
an automatic NOT SATISFIED verdict — a test-only symbol could still be
correct if the criterion is genuinely about test coverage).

## 4. Engine design for Phase 5.3's build

New package `scripts/continuous_verify/` (thin — most of the real work is
already `scripts/focus/anchor_scanner.py`, imported directly, not
duplicated):

1. **`anchor_cli.py`**: a standalone CLI wrapper exposing
   `AnchorScanner.verify_file()`/`verify_symbol()` for a list of
   caller-supplied queries (each tagged `file` or `symbol` by the caller,
   since the anchor *kind* is a judgment call about what the plan text
   names — the scanner doesn't need to guess). Given
   `--workspace`, `--file-queries`, `--symbol-queries`, `--exclude` (to
   exclude the plan file itself from its own substrate index, matching
   `AnchorScanner`'s own `exclude` parameter and `focus.py`'s existing
   practice), returns each query's verification result plus an explicit
   `mock_trap_candidate: true` flag on any `FOUND_TEST_ONLY` symbol result.
2. **`reporter.py`**.

**Explicitly not built**: any plan-text parser (Phase 0c's criteria/
contract extraction stays entirely manual — it is genuinely
interpretation-heavy and varies per plan), any SATISFIED/NOT SATISFIED
verdict logic (Phase 1/2's own assessment step, judgment), any MISMATCH
aggregation (Phase 3, already correctly boolean-gated in the existing text
and not touched).

## 5. Disposition

Seed design **confirmed**, not corrected — tasks.md's own hint ("plan-
alignment cross-checker, reusing `scripts/focus/anchor_scanner.py`") was
accurate. The one refinement found during the pass: `anchor_scanner.py`
has no standalone CLI, so a thin wrapper is needed (not a new
verification engine), and doing so surfaces a real, previously-invisible
capability gap — `verify_symbol()`'s `FOUND_TEST_ONLY`/Mock Trap signal,
which `/focus-plan` already relies on, had no path into
`/continuous-verify`'s vocabulary at all. Ready for the build.
