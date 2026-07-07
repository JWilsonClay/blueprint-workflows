# Helpdesk Ticket: /redteam's own secret-leakage scan (Phase 3a) instructs a command that would violate its own STRICT RULE 6

**To**: Senior Architect of Workflows
**From**: Claude Code (Sovereign Scaling Cluster, implementation-plan.md Phase 5.1)
**Date**: 2026-07-07
**Subject**: `/redteam` Phase 3a's secret leakage scan instructed a plain `grep -n "SECRET\|...` — which prints the entire matched line, including any live secret value, directly to the agent's own visible output — directly contradicting the same file's STRICT RULE 6 ("Never expose actual secret values in the REDTEAM RECEIPT or in any log entry"). Separately, Phase 1a/1b re-derive coverage/mock facts by eye that a schema-agnostic scanner can enumerate mechanically.
**Urgency**: MEDIUM (a real, live self-contradiction in a security-audit workflow — the exact tool meant to catch secret leakage was itself instructed to leak the secret it found, into the agent's own context/output)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: NO TRANSFER
**Phylogeny Disposition Note** [RESOLVED 2026-07-07, retroactive fix per helpdesk-tickets/CLOSED_20260707_helpdesk-tickets-engine-gap_workflow.md]: `scripts/redteam/` is new, self-contained code with no shared structural pattern moved between workflow files. No lineage entry warranted.

---

## 1. Executive Summary

Phase 3a's literal instruction, `grep -rn "SECRET\|SALT\|API_KEY\|..." [project_root]/logs/`, does exactly what `grep -n` is designed to do: print each matching line in full, including whatever value follows the matched keyword. If that value is a real, live secret, this command surfaces it directly into the agent's context and, potentially, into any transcript or receipt built from that output — precisely the failure STRICT RULE 6 exists to prevent, instructed by the same file that states the rule.

## 2. Root Cause

Phase 3a was written as a quick illustrative `grep` example without considering that `grep`'s default behavior is to print the matched line's full content, not just confirm a match occurred. The mismatch between "scan for secrets" (intent: detect presence) and `grep -n`'s actual behavior (prints the value) went unnoticed because this phase, like the rest of `/redteam`, has never been executed against a real Ghost Logic/secret-leakage scenario during this suite's own hardening passes — it was hardened structurally (GLOSSARY, STRICT RULES, etc.) but never re-examined for this specific self-contradiction.

## 3. Forensic Evidence

- **The engine now wired in**: [redteam.md](file:///home/jwils/blueprint-workflows/claude-commands/redteam.md#L124-L129)
  *Evidence: Phase 1a's ENGINE-BACKED block, added this session, invoking `scripts/redteam/redteam_audit.py`.*
- **The mechanical layer itself**: [scripts/redteam/__init__.py](file:///home/jwils/blueprint-workflows/scripts/redteam/__init__.py#L1-L46)
  *Evidence: the package's own contract docstring describing the schema-agnostic design and the structural redaction guarantee for secret values.*
- `claude-commands/redteam.md` (pre-fix) Phase 3a: `grep -rn "SECRET\|SALT\|API_KEY\|TOKEN\|PASSWORD\|ADMIN_PATH\|BACKDOOR" [project_root]/logs/` — prints full matching lines.
- Same file, STRICT RULE 6: "Never expose actual secret values in the REDTEAM RECEIPT or in any log entry." No mechanism connected the two — the rule was aspirational text, not enforced by the tooling the same phase instructed.
- Separately: Phase 1a ("Flag every module with coverage < 80%") and Phase 1b ("Read every `@patch`... call") both re-derive facts by eye that `coverage.py`'s own JSON output and a simple Python regex scan can supply mechanically — neither needs project-schema knowledge, unlike Phase 5's Ghost Logic reconstruction (which genuinely cannot be generalized, see the governing design doc).

## 4. Impact

Medium. This is a workflow that audits OTHER codebases for exactly this failure class — a self-contradiction here undermines the credibility of every audit `/redteam` performs and could, in a live run against a real system with real secrets, actually cause the leak it's meant to catch.

## 5. Recommendation

Replace the plain grep with a scanner that reports match location and which keyword matched, but never the matched line's content. Build `scripts/redteam/` (schema-agnostic, since `/redteam` audits arbitrary external codebases, unlike this campaign's other 4 already-built engines). See `implementation-plan.md` Phase 5.1 and `docs/compression-staging/redteam-honest-design.md` for the full design, including why Phase 5's Ghost Logic check does NOT get a generic engine (project-schema-specific, out of honest scope).

---
**Status**: **REMEDIATED (2026-07-07)**
**Verification**: `scripts/redteam/` built — `secret_scanner.py` structurally excludes the matched value from its result object's shape entirely (not merely displaying "[REDACTED]" — the field doesn't exist). 19/19 new tests passing, including a redaction test at the Python-object level AND a second one at the CLI/JSON-stdout boundary specifically (confirms a live test secret value is genuinely absent from the actual text an agent would read). Full suite 397/397 passing. `redteam.md` Phase 3a rewritten with an explicit warning against the old plain-grep approach and a redaction-safe fallback if the engine is unavailable. Phase 1a/1b also wired to the same engine for coverage-gap parsing and mock enumeration. Frontmatter: version 2→3, `last_hardened` 2026-07-07. Lint: CLEAN (0 CRITICAL/WARNING) after `--fix-hashes --write`.

---
*Signed,*
**Claude Code**
*(Sovereign Scaling Cluster, Phase 5 — first of the remaining 5 targets)*
