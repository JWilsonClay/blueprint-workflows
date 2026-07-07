# Helpdesk Ticket: Grok OpenCode Retired, Official Grok Build Adopted Pending — Suite-Side Implications Deferred, Not Fixed

**To**: Senior Architect of Workflows
**From**: Claude (session agent — surfaced when the linter's OpenCode pointer check went from clean to 32 warnings mid-session, traced to a real environment change, not a defect)
**Date**: 2026-07-05
**Subject**: The user has uninstalled Grok OpenCode (retired, replaced) and installed x.ai's official Grok Build, but will not actively use Grok Build for approximately one week while learning its interface. The suite's documentation and tooling still assume Grok OpenCode as the third runtime alongside Claude Code and Antigravity. This ticket tracks that gap; it does not close it.
**Urgency**: LOW (nothing is broken or blocking — Claude Code and Antigravity are both fully functional; the affected surface, multi-agent workstream orchestration via Grok, is not in active use right now regardless)
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

This is not a failure report. The user researched and adopted x.ai's official Grok Build as a replacement for the community `opencode` tool the suite's triple-runtime architecture was built against, uninstalling `opencode` in the process. This was discovered mid-session as a side effect of unrelated work: the suite linter's per-file OpenCode pointer check, previously clean, suddenly reported all 32 workflow files missing their pointer, tracing to `/home/jwils/.opencode/` no longer existing at all (confirmed via direct `stat`/`ls`; Antigravity's equivalent directory was checked as a control and is unaffected — this is OpenCode-specific, not a broader environment problem). The user is not yet using Grok Build in practice and asked for approximately a week before treating it as production-ready in their own workflow.

## 2. Root Cause Analysis: "Suite Assumes a Retired External Dependency"

- **The How**: `scripts/suite/checks.py`'s `check_symlinks` hardcodes `OPENCODE_DIR = ~/.opencode/commands` and warns per-file when a pointer is missing there. Multiple suite documents (`/workstream`'s "Claude/Gemini/Grok" framing, historical `WORKFLOW_MANIFEST.md`/manifest narrative entries describing a "Dual-Runtime" then "triple-runtime-via-workstream" architecture) describe Grok OpenCode as a standing, symlinked-equivalent runtime alongside Claude Code and Antigravity. None of this was wrong when written — `helpdesk-tickets/CLOSED_20260524_workstream_opencode_pointer_workflow.md` even confirmed 31 real per-workflow pointer files existed there as recently as earlier in today's own session (see that ticket's now-superseded verification note).
- **The Why**: An external tool the suite depended on was replaced by its own vendor's official release, and the user's adoption of the replacement is itself still in progress (explicitly not yet in active use). There is no code or documentation defect here — the suite's assumptions were accurate until a legitimate external change invalidated them, and the user flagged the gap themselves rather than the suite silently drifting unnoticed.

## 3. Forensic Evidence

- **The vanished directory, confirmed not a path/environment mistake**: direct `stat /home/jwils/.opencode/commands` → "No such file or directory"; `whoami` → `jwils`; `$HOME` → `/home/jwils` (matches expectation, rules out a resolution bug).
- **Confirmed OpenCode-specific, not systemic**: `ls /home/jwils/.gemini/antigravity/global_workflows/` → populated, unaffected, same session.
- **The now-stale ticket**: [helpdesk-tickets/CLOSED_20260524_workstream_opencode_pointer_workflow.md](file:///home/jwils/blueprint-workflows/helpdesk-tickets/archive/CLOSED_20260524_workstream_opencode_pointer_workflow.md) — its verification note (added earlier this same session) confirmed 31 pointer files and a retired bulk-loader; both are accurate historical fact, now superseded by the uninstall. Addendum added there pointing at this ticket.
- **The noisy linter symptom**: `lint_workflows.py` went from 19 pre-existing WARNING to 52 in one run, 31 of them the identical new "OpenCode pointer missing" message — a real signal, but reported with poor proportionality (one root cause, 31 near-duplicate lines).
- **User's own words, this session**: "the official Grok Build is better than opencode... I uninstalled opencode, as a deprecated and replaced system... for the time being, I will not be using Grok Build, for about a week, until I can understand the interface a bit better."

## 4. Remediation: One General Fix Now, Everything Else Explicitly Deferred

**Done as part of this ticket** (a genuinely general robustness fix, independent of which specific runtime comes or goes):
1. `scripts/suite/checks.py`'s `check_symlinks` now checks whether `OPENCODE_DIR`/`ANTIGRAVITY_DIR` exist *at all* before checking individual files within them. A wholly-absent runtime directory now produces one clear aggregate note ("OpenCode runtime not detected — skipping N per-file pointer checks") instead of one warning per workflow file. This directly prevents today's exact confusion from recurring for any future runtime addition or removal, regardless of which one.

**Explicitly deferred, not built now** — premature until the user has hands-on familiarity with Grok Build's actual conventions:
1. Any Grok-Build-specific pointer/command generation (mirroring what existed for OpenCode). Grok Build's interface is unknown to both the user and this session right now; building against an unlearned interface would be speculative, ungrounded work — the same failure shape this session has spent considerable effort steering away from elsewhere.
2. `/workstream`'s "Claude/Gemini/Grok" framing and its Workstream C (Grok) role description — still describes the old OpenCode integration. Update once Grok Build is actually in use and its real invocation model is known.
3. Any `role.md` / manifest narrative language describing the runtime count or dual/triple-runtime architecture that specifically names OpenCode as a standing member.
4. Re-adding an OpenCode-equivalent pointer set — moot unless the user reverses course; not assumed either way.

**Do not treat this ticket's LOW urgency as "ignorable."** It is low because nothing is currently broken — Claude Code and Antigravity fully cover this session's actual work, and Grok-anything is dormant right now regardless of tooling state. But it should not be silently forgotten either; re-open review once the user reports actual Grok Build usage.

## 5. Recommendation to Senior Architect

Two lessons worth keeping, beyond this specific transition:
1. **The general linter fix (directory-existence gating before per-file checks) is worth its own small principle**: when a check's failure mode can legitimately be "the whole category is absent" as well as "one instance is missing," gate on the category first. A wall of identical warnings is worse than one clear one — it obscures rather than informs, which is its own small case of the same "signal vs. noise" problem this suite cares about elsewhere (e.g., the Suite Learning Registry's REVIEW-not-a-decision framing).
2. **Do not build tooling against an interface neither the user nor the agent has learned yet**, even when explicitly invited to "proceed in full" — that authorization was for the plan as discussed, and this ticket's deferred items were never part of it. The right move on discovering an adjacent, temptingly-related task mid-flow is to scope it into its own tracked ticket, not fold it into momentum.

---
**Status**: **OPEN — deliberately left open, tracking a pending external adoption, not a bug awaiting a fix**
**Verification**: N/A until the user reports active Grok Build usage; re-open review at that point, not before.

---
*Signed,*
**Claude**
*(Session Agent — Senior Architect of Workflows role)*
