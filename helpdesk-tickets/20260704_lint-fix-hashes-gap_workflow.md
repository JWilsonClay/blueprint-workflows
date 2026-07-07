# Helpdesk Ticket: `lint_workflows.py --fix-hashes` Is Print-Only by Design, But the Suite's Own Change Log Convention Describes It as if It Writes

**To**: Senior Architect of Workflows
**From**: Claude (session agent — found while recomputing hashes for `helpdesk-tickets.md` and `secretary.md`)
**Date**: 2026-07-04
**Subject**: `scripts/suite/lint_workflows.py --fix-hashes` computes and prints correct content hashes but never writes them to any file — this is its documented, intentional behavior, not a defect — yet the suite's own Change Log entries (including two written earlier in this same session) describe using it as though the hash was "recomputed via `--fix-hashes`" with no mention of the required manual paste step.
**Urgency**: LOW
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

This is **not a bug in `lint_workflows.py`.** The tool does exactly what its own `--help` text says. The finding is narrower and easy to miss: this repo's own convention for describing hash maintenance ("content_hash recomputed via `lint_workflows.py --fix-hashes`") reads as if the tool performs the write, when it only ever prints a value for a human or agent to paste in by hand. Confirmed directly this session: after running `--fix-hashes` suite-wide, re-running the linter immediately after showed the same declared/actual hash mismatches unchanged for every file — including two files whose frontmatter still read the placeholder `sha256:PENDING_RECOMPUTE` until corrected by hand from the tool's printed output.

## 2. Root Cause Analysis: Terminology/Behavior Mismatch (not a named failure-pattern class — closest adjacent: a mild, repeated form of imprecise self-reporting, distinct from Hallucinated Success since the eventual hash values are genuinely correct once pasted)

- **The How**: `--fix-hashes` (`lint_workflows.py:79-80`) is defined with help text "Recompute and **print** content hashes for all workflows." Its handler (`lint_workflows.py:95-101`) reads every command file, computes `sha256`, and calls `print(f"  {wf_file}: sha256:{h}")` — line 96's own preceding print statement is explicit: `"Content hashes (paste into frontmatter as content_hash):"`. There is no file-write call anywhere in this code path.
- **The Why**: The tool was apparently always meant to be a compute-and-report helper, with the paste-in step left to the operator. That's a legitimate design. The gap is that the suite's own Change Log entries don't say "computed via `--fix-hashes`, pasted in by hand" — they say "recomputed via `lint_workflows.py --fix-hashes`," full stop, which reads as fully automatic. Confirmed 3 instances suite-wide (`grep -rn "fix-hashes" claude-commands/*.md`): `execute-build.md:474`, and — worth naming plainly — **two written earlier in this very session**, `helpdesk-tickets.md:372` and `secretary.md:512`. The pattern is subtle enough that it was repeated inside the same session that is now filing a ticket about it.

## 3. Forensic Evidence

- **The tool's own declared behavior**: [scripts/suite/lint_workflows.py#L79-L80](file:///home/jwils/blueprint-workflows/scripts/suite/lint_workflows.py#L79-L80)
  *Evidence: `--fix-hashes` help text reads "Recompute and print content hashes for all workflows" — "print," not "write" or "apply."*
- **The handler never writes**: [scripts/suite/lint_workflows.py#L95-L101](file:///home/jwils/blueprint-workflows/scripts/suite/lint_workflows.py#L95-L101)
  *Evidence: `print("Content hashes (paste into frontmatter as content_hash):")` followed by one `print()` per file. No `write_text` or equivalent call in this branch.*
- **Reproduced live, this session**: after `python3 scripts/suite/lint_workflows.py --workspace ~/blueprint-workflows --fix-hashes`, an immediate re-run of the linter (no `--fix-hashes`) still reported `helpdesk-tickets.md` and `secretary.md` as hash-mismatched (`declared=sha256:PENDING_RECOMPUTE`) until both were corrected by hand.
- **The imprecise phrasing, including same-session instances**: [claude-commands/execute-build.md#L474](file:///home/jwils/blueprint-workflows/claude-commands/execute-build.md#L474), [claude-commands/helpdesk-tickets.md#L372](file:///home/jwils/blueprint-workflows/claude-commands/helpdesk-tickets.md#L372), [claude-commands/secretary.md#L512](file:///home/jwils/blueprint-workflows/claude-commands/secretary.md#L512)
  *Evidence: all three say "content_hash recomputed via `lint_workflows.py --fix-hashes`" with no mention of a manual paste step.*

## 4. Remediation: Two Legitimate Directions, Not Yet Chosen

1. **Give the tool a real write mode** — e.g. `--fix-hashes --write`, which parses each file's frontmatter and replaces the `content_hash` line in place (excluding that line from its own hash computation, the same self-referential-safe approach already confirmed working when done by hand this session). Matches how the suite has apparently been assuming it works.
2. **Leave the tool as-is and correct the convention** — going forward, Change Log entries say "content hash computed via `lint_workflows.py --fix-hashes` and pasted in by hand," not "recomputed via" alone. Cheaper, no code risk, but relies on every future session remembering the distinction — the same class of soft-instruction fragility this suite has been actively moving away from this session (registry/phylogeny).

No preference recorded here; this is a judgment call for whoever picks this ticket up.

## 5. Recommendation to Senior Architect

Whichever direction is chosen, the fix is narrow and low-risk (one script or one phrasing convention). Not urgent — flagged LOW rather than MEDIUM/HIGH because the actual hash values in the suite are correct today; this is about preventing a future session from trusting an unwritten "recomputed" claim at face value.

---
**Status**: **OPEN — deliberately deferred, not now, per explicit user direction**
**Verification**: N/A — no remediation attempted yet.

---
*Signed,*
**Claude**
*(Session Agent — Senior Architect of Workflows role)*
