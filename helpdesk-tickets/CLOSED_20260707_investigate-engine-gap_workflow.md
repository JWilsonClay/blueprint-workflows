# Helpdesk Ticket: /investigate's citation and search-log claims have no structural verification

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 5.4)
**Date**: 2026-07-07
**Subject**: `investigate.md` mandates a `[label](file:///path#LN-LM)` citation format (STRICT RULE 2) and a `grep "pattern" path → N matches` Search Log convention (Phase 1c), but nothing confirms either is actually accurate — a hallucinated line range or a fabricated match count would be invisible unless a human manually re-verifies every citation and search.
**Urgency**: MEDIUM (this workflow's entire output is evidence-cited findings; unverified citations undermine the core guarantee the workflow exists to provide)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

`/investigate`'s Investigation Report is only as trustworthy as its citations and search-log claims. Neither is currently checked: a citation's line range could be stale (correct when written, drifted since) or simply wrong, and a search-log entry's match count could be misremembered or fabricated, with nothing in the workflow surfacing the discrepancy before the report reaches the user.

## 2. Root Cause

Both conventions were designed as instructional discipline (STRICT RULE 2: "Prose assertions without citations are not acceptable") without a structural verification layer — the same enforcement-by-instruction gap this campaign has closed in four prior workflows this session.

## 3. Forensic Evidence

- `claude-commands/investigate.md` GLOSSARY "Citation" term: mandates the `file:///path#LN-LM` format with no verification mechanism referenced anywhere in the file.
- Phase 1c: "Log every search and its result... A zero-result search is evidence too" — no mechanism confirms the logged count is accurate.

## 4. Impact

Medium. `/investigate` produces the Investigation Report that gates all subsequent remediation discussion (Phase 5, STRICT RULE 5) — an unverified citation or search claim propagates directly into a decision the user makes about how to proceed.

## 5. Recommendation

Build `scripts/investigate/` (schema-agnostic, following the `/redteam`/`/continuous-verify` precedent — these check `/investigate`'s OWN reporting conventions, not the target system's schema): a citation resolver (file existence + line-range validity) and a search-log verifier (re-run the exact claimed search, compare counts) — the latter implemented via Python's `re` module over file contents rather than a shell subprocess, since the pattern/path strings originate from report text that could be untrusted in an autonomous pipeline. See `implementation-plan.md` Phase 5.4 and `docs/compression-staging/investigate-honest-design.md` for the full design.

---
**Status**: **REMEDIATED (2026-07-07)**
**Verification**: `scripts/investigate/` built — 19/19 new tests passing, including a read-only invariant test, two regression tests proving the checkers catch a genuinely hallucinated citation and a genuinely fabricated search-log count (not just clean-input passes), and an explicit shell-injection-safety test confirming a malicious pattern cannot execute anything. Full suite 440/440 passing. Live-run against this actual workspace confirmed both checks work end-to-end. `investigate.md` wired at Phase 1c (search-log verification) and a new Phase 3 Citation Fidelity Gate — both keep explicit manual-fallback instructions and are explicit the engine confirms resolution only, never whether cited content supports a finding. Frontmatter: version 2→3, `last_hardened` 2026-07-07 (this file's `dependencies` field was previously empty — now correctly populated). Lint: CLEAN (0 CRITICAL/WARNING) after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 5)*
