# Helpdesk Ticket: /continuous-verify re-implements anchor checking that scripts/focus/anchor_scanner.py already does, and has no Mock Trap vocabulary

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 5.3)
**Date**: 2026-07-07
**Subject**: `continuous-verify.md` Phase 1/2 instruct manual anchor-checking ("use the Read tool or grep") that duplicates `scripts/focus/anchor_scanner.py`'s already-built, already-proven `verify_file()`/`verify_symbol()` — and has no way to surface `verify_symbol()`'s `FOUND_TEST_ONLY` (Mock Trap) signal at all, despite `/focus-plan` already relying on that exact signal.
**Urgency**: MEDIUM (a real capability gap in a gate that runs at every `/execute-build` phase boundary — a criterion whose anchor exists only in test code could be marked SATISFIED with nothing flagging the risk)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

`scripts/focus/anchor_scanner.py`'s `AnchorScanner` class already verifies file and symbol anchors against a target workspace, already split into production-vs-test-only matches for Mock Trap detection, already proven in production for `/focus-plan`. `/continuous-verify` — which asks precisely this question at Phase 1 (does this criterion's anchor exist?) and Phase 2 (does this contract's anchor exist?) — never calls it, instead instructing manual Read-tool/grep verification with no path to the Mock Trap signal at all.

## 2. Root Cause

`anchor_scanner.py` has no standalone CLI — it has only ever been invoked as a class inside `focus.py`'s full plan-parsing pipeline, which does substantially more than `/continuous-verify` needs (it re-parses the whole implementation plan; `/continuous-verify` already knows its scope from its own Phase 0c). Without a thin, standalone entrypoint, `/continuous-verify` had no way to reuse the scanner without either re-implementing it or pulling in the whole `/focus-plan` pipeline.

## 3. Forensic Evidence

- `claude-commands/continuous-verify.md` (pre-fix) Phase 1: "Read the anchor: use the Read tool on `{path}`, or `grep` as appropriate" — no script call.
- `scripts/focus/anchor_scanner.py`'s `verify_symbol()`: already returns `FOUND_PRODUCTION`/`FOUND_TEST_ONLY`/`ABSENT`, with `FOUND_TEST_ONLY` an explicit Mock Trap signal.
- `continuous-verify.md`'s Phase 1 assessment vocabulary: `SATISFIED`/`NOT SATISFIED`/`UNVERIFIABLE` — no field or instruction anywhere referencing Mock Trap risk, despite this suite naming that exact failure pattern globally (`~/.claude/CLAUDE.md`'s Failure Pattern Vocabulary).

## 4. Impact

Medium. This gate runs automatically at every phase boundary inside `/execute-build` — a Mock-Trap-shaped false SATISFIED verdict here would let a phase advance on the strength of a test-only implementation, exactly the failure `/focus-plan`'s own anchor scanner was built to catch elsewhere in the suite.

## 5. Recommendation

Build a thin CLI wrapper (`scripts/continuous_verify/anchor_cli.py`) exposing `AnchorScanner.verify_file()`/`verify_symbol()` directly for caller-supplied queries, with an explicit `mock_trap_candidate` flag on `FOUND_TEST_ONLY` results. Wire into Phase 1/2. See `implementation-plan.md` Phase 5.3 and `docs/compression-staging/continuous-verify-honest-design.md` for the full design.

---
**Status**: **REMEDIATED (2026-07-07)**
**Verification**: `scripts/continuous_verify/` built — 10/10 new tests passing, including a read-only invariant test, a plan-file-exclusion test (with a companion test proving the exclusion mechanism does something, not a vacuous pass), and a CLI-level end-to-end test. Full suite 421/421 passing. Live-run against this actual workspace confirmed correct behavior on real symbols. `continuous-verify.md` wired at Phase 1 and Phase 2 — both keep explicit manual-fallback instructions and explicit Mock Trap handling guidance (flag, investigate, don't auto-fail). Frontmatter: version 2→3, `last_hardened` 2026-07-07. Lint: CLEAN (0 CRITICAL/WARNING) after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 5)*
