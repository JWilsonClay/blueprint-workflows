# Honest-Design Discipline — /redteam (Phase 5.1)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. First of the
remaining 5 Verification-Spine targets. Re-runs the three-question test
against `/redteam` (v2, 468 lines, last hardened 2026-05-08).

## 0. A structural difference from every engine built so far

`/execute-build`, `/secretary`, `/triage`, and `/harden-workflow` all operate
on **this repo's own fixed conventions** — `tasks.md`, `BUILD_RECEIPTS.md`,
`triage.md`'s Trigger Matrix, `claude-commands/*.md`. Their engines could
assume a known schema because the target is always blueprint-workflows
itself.

`/redteam` is different: it audits an **arbitrary external codebase** —
Phase 0's own intake asks for "project root," and nothing about the target's
language, test framework, mock library, log format, or database schema is
known until Phase 0 discovers it. This matters directly for what a
read-only engine can honestly promise here: a generic script cannot assume
a DB event schema or a specific log format the way `phase_status.py` can
assume `tasks.md`'s `## Phase N` convention. Any engine built for
`/redteam` must be schema-agnostic — pure text/pattern analysis over files
the caller points it at, nothing more.

This directly bears on the archived queue's own seed note (tasks.md 5.1):
*"thin evidence rail (Ghost Logic collector); never script the adversarial
verdict."* The "Ghost Logic collector" framing (Phase 5's DB-event-vs-log
reconstruction) is the one piece that does NOT survive this constraint —
see Section 3.

## 1. What is mechanically verifiable here?

Four candidates survive the schema-agnostic test — each is pure pattern
matching over source/log text, assuming nothing about the target project's
internal schema:

| Phase | Currently | Mechanizable? |
|---|---|---|
| 1a Coverage gap analysis | Runs `pytest --cov`, manually reads output for <80%/<100% modules | YES — `coverage.py`'s own `coverage json` output is a stable, well-known schema (not project-specific); parsing it for per-file percentages and flagging below-threshold is arithmetic |
| 1b Mock audit | "Read every `@patch`/`Mock()`/`MagicMock()`/`monkeypatch` call" by eye | YES, partially — *enumerating* mock call-sites (file, line, target) is pure regex over Python source; the *assessment* (VALID/TAUTOLOGY/UNREALISTIC) requires reading semantic context and stays judgment |
| 1d Race condition probe | A single inline `grep` already given verbatim in the file | Already maximally mechanical as plain shell — wrapping one grep command adds ceremony, not rigor (same disposition already given to `/triage`'s 0a/0d) |
| 3a Secret leakage scan | Inline `grep` for `SECRET\|API_KEY\|...` in logs | YES — same pattern-scan shape as 1b's mock enumeration; genuinely reusable, and STRICT RULE 6 already requires the *value* never be exposed in output, which a generic redaction rule can enforce structurally rather than trusting the agent to remember every time |

## 2. What is irreducible judgment?

Everything requiring the audited system to actually RUN: Phase 2's fault
injection (network timeouts, DB disconnection, resource exhaustion — these
require executing the target system, not reading its files), Phase 3b's
social engineering simulation (requires invoking the target AI live), Phase
4's Adversarial LLM Pressure (requires a live Breaker-vs-Dispatcher loop).
None of these are read-only evidence collection — they are active testing
against a running system, a fundamentally different engineering problem
than every engine this campaign has built so far. Also irreducible: every
mock's VALID/TAUTOLOGY/UNREALISTIC classification (1b), mutation testing's
actual code mutation + re-run (1c — mutating code, even temporarily, is a
write operation, architecturally incompatible with this engine family's
read-only invariant), and the entire Phase 6 Remediation Report (turning a
failure into a specific, implementable fix is the whole point of red-
teaming and cannot be mechanized).

## 3. Mock-Trap test, applied — including the one candidate that fails it

- **Mock enumeration**: reporting "line N has `@patch('foo.bar')`" is a
  fact about source text; it cannot and does not judge whether the mock is
  a tautology. Safe — matches the same discipline as `/execute-build`'s
  completeness scanner (match list only, justification stays with the
  model).
- **Coverage gap parsing**: `coverage.py`'s JSON output already contains
  the percentage; flagging `<80%` or `<100%` (for surface-map modules) is
  arithmetic over a number the tool computed, not this engine's opinion.
- **Secret-pattern scan with structural redaction**: the scan reports "a
  string matching `API_KEY` appears at this line" — never the matched
  value itself in the finding (the redaction is enforced by the scanner,
  not left to the agent to remember, closing a real gap: STRICT RULE 6
  already prohibits exposing secret values, but nothing before this engine
  structurally prevented an agent from doing it anyway by pasting a grep
  match verbatim into the receipt).
- **The Phase 5 "Ghost Logic collector" (the seed design's own framing)
  does NOT survive this test as a generic engine.** Determining whether a
  DB event has "a corresponding log entry" requires knowing that specific
  project's event schema and log format — there is no schema-agnostic
  regex for "this log entry documents that decision." Building a generic
  version would mean inventing a fake, opinionated schema and forcing
  every audited project to conform to it, which is scope invention, not
  honest design — the same disposition already applied to dropping
  `/execute-build`'s `phase_count` coherence check. **This phase stays
  fully manual, exactly as written**, unless a future ticket scopes a
  project-specific Ghost Logic adapter for one particular target codebase
  (out of this campaign's scope, which is suite-wide and project-agnostic).

## 4. Engine design for Phase 5.1's build

New package `scripts/redteam/` (sibling of `scripts/harden_workflow/`):

1. **`mock_scanner.py`**: `scan_for_mocks(paths: List[str]) -> List[MockUsage]` —
   regex over `.py` files for `@patch`, `Mock(`, `MagicMock(`,
   `monkeypatch.`, reporting `{file, line, construct, snippet}`. Match list
   only — VALID/TAUTOLOGY/UNREALISTIC stays the model's call.
2. **`secret_scanner.py`**: `scan_for_secrets(paths, patterns=DEFAULT_PATTERNS) -> List[SecretHit]` —
   the same keyword set already given verbatim in Phase 3a
   (`SECRET|SALT|API_KEY|TOKEN|PASSWORD|ADMIN_PATH|BACKDOOR`), reporting
   `{file, line, pattern_matched}` — **the snippet is always redacted**
   (the matched keyword's line, with the value after `=`/`:` masked), a
   structural enforcement of STRICT RULE 6 that removes the risk of an
   agent pasting a live secret into a receipt by mistake.
3. **`coverage_gap.py`**: `parse_coverage_json(path) -> List[CoverageGap]` —
   reads `coverage.py`'s own `coverage json` output (a stable, tool-owned
   schema, not project-specific), reports each file's percentage and
   whether it's below an 80% default threshold (or a caller-supplied
   surface-map file list at a 100% threshold, matching Phase 1a's own
   two-tier requirement).
4. **`reporter.py` + `redteam_audit.py` CLI**: `--project-root`, `--coverage-json`
   (optional), `--output-json`. Combines all three into one evidence
   report.

**Explicitly not built**: anything for Phases 0 (intake/scoping — pure
judgment about what's in scope), 1c (mutation testing — a write operation),
1d (already-minimal single grep), 2 (fault injection — requires live
execution), 3b (social engineering — requires live LLM invocation), 3c/5c
(PII-in-log business judgment — flagging a phone-number-shaped string is
a reasonable future addition but is intentionally deferred here to keep
this build tight and because "constitutes a business commitment" already
requires judgment the scan cannot replace), 4 (Adversarial LLM Pressure —
live execution), 5 (Ghost Logic reconstruction — project-schema-specific,
see Section 3), 6 (Remediation Report — the entire point of the workflow).

## 5. Disposition

Seed design (tasks.md 5.1) **partially corrected**: its "Ghost Logic
collector" framing for a generic engine does not survive re-application of
the Mock-Trap test once the project-agnostic nature of `/redteam`'s target
is taken seriously — no schema-agnostic version of that check exists.
Three narrower, genuinely generalizable mechanical pieces (mock
enumeration, secret-pattern scan with structural redaction, coverage-gap
parsing) replace it, closing real gaps (STRICT RULE 6's redaction
requirement had no structural backing) without inventing scope the target
codebases don't actually provide. Ready for the build.
