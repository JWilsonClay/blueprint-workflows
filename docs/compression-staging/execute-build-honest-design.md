# Honest-Design Discipline — /execute-build (Phase 4.1)

Produced by Claude, 2026-07-07. Re-runs the three-question test
(`implementation-plan.md`, "HONEST-DESIGN DISCIPLINE") against `/execute-build`
as it stands today (v5, 2026-07-04/06 hardening passes, 519 lines), not the
2026-06-02 seed design written before this file's last three hardening passes.

## 1. What changed since the seed design (2026-06-02)

The original queue entry (`.history/archive/implementation-plan-verification-spine-queue-format.md.ledger.md`
line 90) sketched: *"task-state machine validator: parse tasks.md phase/task
markers, verify Build Receipt presence per completed phase, detect orphaned
`[/]` tasks, check phase_count frontmatter coherence against the .md plan"*
as the mechanical layer, with *"the actual build decisions, phase ordering
judgment, and HALT-or-proceed calls"* as irreducible judgment.

Two things happened since that was written that change the design:

1. **The first three mechanical items are already built** — `scripts/focus/phase_status.py`
   (built 2026-06-30 for `/focus-plan`, extended 2026-07-04 for `/nodelete`
   Pillar 6 Archival Mode and the Completion Marking sub-pass). It parses
   `tasks.md` into phases, tallies checkboxes into a `status` (`complete` /
   `in_progress` / `not_started` / `no_checkboxes`), and cross-references
   `BUILD_RECEIPTS.md` into a `receipt_status` (`found_complete` /
   `found_incomplete` / `not_found` / `receipts_file_absent`) per phase. This
   is not a new engine to build — it is an existing engine `/execute-build`
   does not yet call. Building a second, parallel parser would itself be a
   form of duplication this suite's own `/nodelete`/`/divergence` disciplines
   exist to prevent.
2. **`/execute-build` gained two judgment-heavy gates since the seed design**:
   STRICT RULE 15 (Discussion Is Not Authorization — confirm `tasks.md`
   reflects genuine approval, not a conversational sketch) and STRICT RULE 16
   (Turn-Boundary Pause Protocol). Both are irreducible judgment calls about
   *intent and social context*, not facts about the substrate — no engine
   should touch either.

## 2. The three-question test, applied fresh

**Q1 — What is mechanically verifiable?**

| # | Mechanical fact | Currently done by | Gap |
|---|---|---|---|
| a | Phase Map: phase list, per-phase checkbox tally, status | `phase_status.py` (exists) | No CLI entrypoint — only imported as a library by `focus.py`/`coverage.py`. `/execute-build` Step 0b still says "Read `<TASKS_FILE>` in full [and] Extract..." by eye. |
| b | Build Receipt presence/status per phase | `phase_status.py` (exists) | Same gap — not wired into Step 0d/5a/6. |
| c | Orphaned `[/]` detection | `phase_status.py`'s `in_progress` status is the raw signal | No dedicated "stale in-progress" flag (e.g. age since last touch) — advisory enrichment, not a blocker to reuse as-is. |
| d | Completeness Scan (5d): `TODO`/`FIXME`/`HACK`/`PLACEHOLDER`/bare `pass`/`raise NotImplementedError` | Not built | Real gap — pure grep, zero judgment in the *search*; judgment stays in whether a match is "justified." |
| e | Syntax/Import Verification (5e) | Not built as an engine — inline bash snippets in the `.md` itself | Real gap, but low-value to formalize: the commands are already mechanical and already in the `.md`; wrapping them in a script mainly adds a JSON envelope, not new rigor. |
| f | Scope Compliance (5f) file-list fact: which files were actually touched this phase (`git diff --stat` / `git status`) vs. the phase's declared scope | Not built | Real gap — a script can report the *fact* of what changed; whether an out-of-scope touch was "warranted" stays judgment. |
| g | Frontmatter `phase_count` coherence (the seed design's 4th item) | N/A | Re-examined below — **this item does not survive the honest-design test as originally scoped (see 2c).** |

**Q2 — What is irreducible judgment?**

Everything in Phases 1-5's actual reasoning content: the Drift Check
(Phase 1 — does prior work contradict intent), the Phase Build Goal and
Acceptance Criteria (Phase 2 — are criteria complete/observable), Build Risk
identification (Phase 3), the code-writing itself (Phase 4), Acceptance
Criteria mapping to actual code (5a), Risk Resolution (5b), the Regression
Guard's semantic contradiction check (5c — a script cannot know whether new
code "silently narrows intent"), whether a Completeness Scan match is
justified (5d), whether an out-of-scope touch was warranted (5f), STRICT
RULE 15's approval-genuineness call, and STRICT RULE 16's pause-signal
interpretation. None of this is a Mock-Trap candidate — none of it should be
touched.

**Q3 — Mock-Trap test, applied to each mechanical candidate above:**

- (a)/(b): `phase_status.py` already passes this — it reports `status` and
  `receipt_status` as plain enums derived from string-matching, never a
  judgment about whether the phase is *good*. Safe to wire in as-is.
- (d): a grep for `TODO`/`FIXME`/etc. cannot judge whether a match is
  "justified" — and must not try. The engine reports match locations only;
  the model decides justification. This is exactly the 5d text's own
  framing ("Any of these found without explicit justification..." — the
  justification call was always the model's job, the scan was always meant
  to be mechanical).
- (f): reporting "these files changed, this was the declared scope, here is
  the diff" is a pure set-difference — no judgment. Judging "was it
  warranted" stays explicitly with the model, one-directional advisory
  (a file appearing outside declared scope is a flag to review, never an
  auto-fail).
- (g), the frontmatter `phase_count` check: **re-scoped, not built as
  originally imagined.** The seed design's phrasing is ambiguous about
  which file's frontmatter it meant. Read literally against *this* workflow
  file's own frontmatter (`phase_count: 7`), it would be a self-referential
  lint check with no per-build-session value — already covered by
  `lint_workflows.py`'s existing frontmatter checks, so building a second
  instance would be duplication. Read as "does the number of phases in the
  *target* `tasks.md` match some declared expectation" — no such expectation
  field exists in this suite's `tasks.md` convention (phases are just
  headers, uncounted anywhere else), so there is nothing to check it
  against. **Disposition: drop this item from the engine design.** It does
  not name a real mechanical fact this workspace's documents actually
  produce; keeping it would mean inventing a field for the engine to check,
  which is scope invention, not honest design.

## 3. Corrected engine design for Phase 4.2

Not a new parser — a thin CLI wrapper that exposes `phase_status.py`'s
existing `build_phase_status_report()` as JSON (matching the `focus.py` /
`coverage.py` CLI convention: `argparse` + `main()` + `__main__` guard), plus
two genuinely new, narrow, read-only checks:

1. **`scripts/focus/phase_status.py`**: add a `--cli` entrypoint (or a small
   sibling `scripts/build/build_status.py` that imports and calls it) so
   `/execute-build` Step 0b/0d/6 can invoke it directly instead of eyeballing
   `tasks.md`. Output: the existing `TasksMdReport.as_dict()` shape, unchanged.
2. **A completeness-scan script** (new, small): given a list of
   created/modified file paths, grep each for the 5d marker set and return
   `{file, line, marker, snippet}` matches. Zero judgment — a match list, not
   a verdict.
3. **A scope-diff script** (new, small): given a workspace root and a
   declared file-scope list, run `git status --porcelain` and return the set
   difference (`touched_not_declared`, `declared_not_touched`). Zero
   judgment — a set operation, not a verdict.

Both (2) and (3) can plausibly live in one new module,
`scripts/build/build_evidence.py`, mirroring the existing `scripts/receipt/`
and `scripts/registry/` package shape (one module, one clear mechanical
question, imported by other engines rather than duplicated).

**Explicitly not built**: anything for Phase 1 (Drift Check), Phase 2
(Acceptance Criteria completeness judgment), Phase 3 (Risk identification),
Phase 4 (the build itself), 5c (Regression Guard's semantic check), STRICT
RULE 15/16. Step 5g/5h remain delegations to `/continuous-verify` and
`/divergence` respectively — those are Phase 5.3's and (out-of-campaign)
`/divergence`'s own engine concerns, not `/execute-build`'s to duplicate.

## 4. Disposition

**Seed design CORRECTED, not confirmed as originally written.** Three of its
four mechanical items are already built (reuse, don't rebuild); its fourth
item (frontmatter `phase_count` coherence) does not survive re-application of
the Mock-Trap test today and is dropped; two new narrow mechanical checks
(completeness scan, scope diff) are added that the original 2026-06-02 sketch
did not name, surfaced by reading the current 5d/5f text directly rather than
the archived one-line summary. Ready for Phase 4.2's actual build.
