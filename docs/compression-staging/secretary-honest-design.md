# Honest-Design Discipline — /secretary (Phase 4.3)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. Re-runs the
three-question test (`implementation-plan.md`, "HONEST-DESIGN DISCIPLINE")
against `/secretary` as it stands today (v5, 571 lines, last hardened
2026-07-05), not the 2026-06-02 queue entry (which listed `/secretary` as
PENDING #7 with no seed design of its own beyond the generic queue framing).

## 1. What is mechanically verifiable here?

`/secretary` already delegates several of its steps to existing engines —
this is not starting from zero:

| Step | Already engine-backed? | Engine |
|---|---|---|
| 1.0 Suite linter | Yes | `scripts/suite/lint_workflows.py` |
| 1.0.5 Suite Learning Registry | Yes | `scripts/registry/registry.py` |
| 1.2 Ledger growth / narrative rollover | Yes | `scripts/ledger/ledger.py` |
| Phase 3 (/receipt-check trigger) | Yes (transitively) | `scripts/receipt/receipt_audit.py` |

None of those need re-wiring. The genuine gap is different in kind from
`/execute-build`'s: `/execute-build`'s gap was "the agent reads a file and
tallies things by eye instead of asking a script." `/secretary`'s gap is
**"the agent claims five artifacts were produced/updated this session, and
nothing structurally confirms any of them actually were."** This is the
workflow's own named risk — HOW TO BEGIN already contains a hand-written
warning: *"CRITICAL: Do not present SUITE_HEALTH.md, the manifest narrative
shard, HANDOFF.md, or ANOMALY_LOG.md as the completion of /secretary."* That
sentence is a prose defense against exactly the failure pattern this suite
calls **Hallucinated Success** — and prose defenses against Hallucinated
Success are precisely what the Verification-Spine campaign exists to convert
into structural ones.

Four genuinely new mechanical facts, none currently backed by any script:

1. **Artifact freshness** — was `SUITE_HEALTH.md`, `HANDOFF.md`,
   `ANOMALY_LOG.md`, and the active `manifest/history/` shard actually
   modified *today* (or, more precisely, after this session's start), or is
   the Phase 7 receipt about to claim work that never touched disk? A
   file's mtime is a fact a script can check; a human/agent claiming "I
   updated it" is not.
2. **Retrospective presence + freshness (ADDENDUM E, already partially
   mechanical)** — `tail -n 10` + eyeball date-match is already the
   documented mechanism, just not scripted. A script can extract the last
   `## YYYY-MM-DD` entry and compare it to today's date exactly, removing
   the "eyeball the tail output" step.
3. **Retrospective Lag (Step 0b.5, already partially mechanical)** — the
   two greps (narrative shards' latest `SESSION APPEND` date vs.
   `PROCESS_LEARNINGS.md`'s latest date) are already specified as shell
   commands; the *comparison itself* (is date A later than date B?) is
   currently left for the agent to eyeball across two separate command
   outputs. A script can return `gap_detected: true/false` directly.
4. **Receipt-family presence (TRIAGE_RECEIPTS.md / DESIGN_RECEIPTS.md,
   already partially mechanical)** — existence + `tail -n 5` is already
   shell, just not a structured result the model reads as a fact rather
   than parsed prose.

## 2. What is irreducible judgment?

Everything about *what the session actually was*: Phase 0a's Session
Manifest (scope, session type, deliverables, deferred items — this requires
synthesizing the conversation, not reading a file), which anomalies
occurred and their rationale (Phase 0a/5), the actual prose content of
`HANDOFF.md`'s "Current Project State" / "Suggested First Workflow" /
"Deferred Items" (foresight and synthesis, not fact-lookup), whether a
Registry `REVIEW` verdict names a *real* recurring pattern worth a ticket
(1.0.5 — explicitly already reserved as judgment, correctly), and whether a
`SUITE_PHYLOGENY.md` WARN "now warrants" a split (1.2 — same, correctly
advisory). None of this should be touched.

## 3. Mock-Trap test, applied to each of the four new candidates

- **Artifact freshness**: an mtime check cannot judge whether the *content*
  written to `SUITE_HEALTH.md` is good, complete, or honest — only whether
  the file changed. That is exactly the right scope: a script reporting
  "this file's mtime is before session start" is a fact the model cannot
  talk its way around; a script cannot and must not try to grade the
  content itself.
- **Retrospective presence**: extracting "last entry's date" and comparing
  to `date +%Y-%m-%d` is arithmetic, not judgment — this literally is
  ADDENDUM E's own existing instruction, just moved from "eyeball the tail
  output" to "read a boolean." No new capability invented; formalizing an
  existing mechanical step.
- **Retrospective Lag**: same — a date comparison between two already-
  specified greps. The *disposition* (is a gap acceptable, does it need
  escalating) stays advisory exactly as STRICT RULE 20 already states;
  only the arithmetic moves to the engine.
- **Receipt-family presence**: existence + last-N-lines is a filesystem
  fact. No judgment currently or newly invented.

**None of the four requires inventing a function that secretly judges
quality, session-scope correctness, or narrative honesty.** All four report
a fact the model was always supposed to check mechanically per the file's
own existing ADDENDUM/Step text — this is formalization, not new scope.

## 4. Engine design for Phase 4.4 (naming follows this file's own numbering:
`/secretary` is queue-adjacent #7, but per the corrected campaign order this
is executed as the second Phase 4 build, following `/execute-build`)

New package `scripts/secretary/` (sibling of `scripts/build/`, `scripts/receipt/`):

1. **`freshness.py`**: `check_freshness(paths: List[Path], since: datetime) -> List[FreshnessResult]` —
   for each path, report `exists`, `mtime_iso`, `touched_since` (mtime >=
   `since`). `since` is supplied by the caller (session start time is not
   knowable to a script — the model must supply it, or the script defaults
   to "today" via `date.today()`, mirroring `scripts/ledger/`'s existing
   "never LLM-inferred, always the real OS clock" principle for date
   handling).
2. **`retrospective_check.py`**: two functions —
   `last_dated_entry(path, pattern) -> Optional[date]` (generalizes both the
   ADDENDUM E `## YYYY-MM-DD` extraction and the Step 0b.5 `SESSION APPEND`
   extraction with a caller-supplied regex, avoiding two near-duplicate
   parsers) and `compute_retrospective_lag(narrative_dir, process_learnings_path) -> LagReport`
   (glob all `manifest/history/*.md` shards, extract the latest date across
   all of them, compare against `PROCESS_LEARNINGS.md`'s latest — direct
   `gap_detected` boolean, no eyeballing).
3. **`receipt_presence.py`**: `check_receipt_family(receipts_dir, filenames) -> List[ReceiptPresence]` —
   generalizes the existing TRIAGE_RECEIPTS/DESIGN_RECEIPTS ad hoc `ls`/`tail`
   pairs into one reusable check, parameterized by filename (so a future
   receipt-family member — e.g. a hypothetical `SENTINEL_RECEIPTS.md` — needs
   no new prose block, just another filename in the call).
4. **`secretary_audit.py`** CLI: combines all three into one JSON report;
   `--workspace`, `--project` (for the per-project `.workflow_state/` files),
   `--since` (ISO datetime, optional, defaults to today), `--output-json`.

**Explicitly not built**: anything touching Phase 0a's Session Manifest
synthesis, HANDOFF.md's narrative sections, Phase 5's anomaly rationale
text, the Registry/Ledger/Linter engines (already built, already wired,
untouched here), or any verdict on whether a REVIEW/WARN "matters."

## 5. Disposition

**No seed design existed to confirm or correct** — `/secretary` was queue
entry #7 with no per-workflow seed sketch beyond the generic seven-workflow
enumeration in the archived 2026-06-02 scan. This section stands as the
first seed design for `/secretary`'s engine, produced fresh from Honest-
Design Discipline applied to the file's *current* (2026-07-05-hardened)
content, including its own already-partially-mechanical ADDENDUM E and Step
0b.5 text as the direct source for what to formalize. Ready for Phase 4.4's
build.
