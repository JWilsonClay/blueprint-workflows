# Helpdesk Ticket: Suite Learning Registry and Phylogeny Archive Silently Stopped Updating

**To**: Senior Architect of Workflows
**From**: Claude (session agent, direct user discussion — documentation-strategy audit)
**Date**: 2026-07-04
**Subject**: `manifest/CONTRADICTION_REGISTRY.md` and `manifest/SUITE_PHYLOGENY.md` both stopped updating on 2026-06-12 because their only trigger (`/harden-workflow --ticket`'s Step TM-6 and Phase 9) is structurally bypassed by the two-path ticket model ratified earlier today.
**Urgency**: HIGH
**Root Cause Type**: STRUCTURAL
**Phylogeny Disposition**: CONFIRMED — lineage entry added: `manifest/SUITE_PHYLOGENY.md`, "Lineage Entry — 2026-07-04 — the 'X.5 insertion' convention propagates (harden-workflow.md → helpdesk-tickets.md, secretary.md)"

---

## 1. Executive Summary

`manifest/CONTRADICTION_REGISTRY.md` (deterministic, via `scripts/registry/registry.py`) and `manifest/SUITE_PHYLOGENY.md` (LLM-authored lineage narrative) are both suite-wide learning artifacts, both built 2026-06-12, both read by `/harden-workflow` and `/secretary` to gauge whether the suite's own improvement loop is working. Neither has a single entry after 2026-06-12. Five tickets have closed since (`20260625_role`, `20260625_limitations`, `20260625_implementation-plan`, `20260630_focus-plan`, `20260704_ticket-remediation-authority`) and none of the five moved either document, because all five closed via direct remediation — never through `/harden-workflow --ticket`, the only workflow that contains the steps that update them. This was surfaced today during a user-directed documentation-strategy audit, not discovered by any workflow's own self-check.

## 2. Root Cause Analysis: "Ghost Logic"

The Suite Learning Registry (Step TM-6) and the Phylogeny Archive (Phase 9) are both real, correctly-designed, and were both promised to fire "at the end of every ticket-mode session." Their expected effect on the substrate — a fresh registry snapshot, a new lineage entry — is absent for every session since 2026-06-12, with no error, no halt, and no log entry anywhere noting the gap. This is Ghost Logic: behavior that was designed and documented but is absent from the actual substrate, discoverable only by directly checking dates against ticket closures rather than by any built-in signal.

- **The How**: Both mechanisms live entirely inside `/harden-workflow`, reachable only via `--ticket` mode's TM-1 → TM-6 sequence (registry) or a full Phase 1-8+ hardening pass (phylogeny, Phase 9). All five tickets closed since 2026-06-12 did so via `/helpdesk-tickets` Phase 4's "or by the creating agent if the fix was applied in the same session" clause instead — confirmed directly in each ticket's own closure record (e.g. `CLOSED_20260704_ticket-remediation-authority_workflow.md:29`: "never routed through `/harden-workflow`"; `CLOSED_20260625_limitations_workflow.md:34`: "not a `/harden-workflow` pass"). Since TM-6 and Phase 9 only execute inside that workflow, and the workflow was never invoked, neither document had a chance to move.
- **The Why**: `/harden-workflow`'s own structure-only mandate (opening line, STRICT RULE 3) correctly excludes what these five tickets actually needed — logic fixes, sometimes new code — so invoking it would only have halted uselessly on "already Sovereign, nothing to do." Agents correctly bypassed it each time. Today's session formally ratified this as the two-path model and added Step TM-1.5 (`harden-workflow.md:122-140`), which now redirects a Substantive/Logic ticket immediately, "or halt entirely in single-ticket mode" (`harden-workflow.md:127`) — meaning the bypass is no longer informal, it is now a *designed* property of one of the two officially sanctioned closure paths. Nobody carried a registry/phylogeny hook along to the new path when it was formalized, because the fork was scoped to solve routing ("which tool fixes the logic"), not learning-loop freshness.

## 3. Forensic Evidence

- **Registry snapshot frozen at 2026-06-12**: [manifest/CONTRADICTION_REGISTRY.md](file:///home/jwils/blueprint-workflows/manifest/CONTRADICTION_REGISTRY.md#L7-L13)
  *Evidence: "Snapshot — regenerated 2026-06-12... Total events: 29... verdict: REVIEW (threshold 10)" — already past its own review threshold on the day it was built, and unchanged since.*
- **Phylogeny archive frozen at 2026-06-12**: [manifest/SUITE_PHYLOGENY.md](file:///home/jwils/blueprint-workflows/manifest/SUITE_PHYLOGENY.md#L17-L82)
  *Evidence: all four lineage entries are dated 2026-06-12, the file's creation day. Zero entries despite subsequent rule-adding sessions (personality.md Sections 7-8, role.md's code-authority addition, the two-path ticket model itself).*
- **TM-6's sole trigger point**: [harden-workflow.md#L197-L212](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L197-L212)
  *Evidence: "At the END of every ticket-mode session (after TM-5), run the deterministic Suite Learning Registry" — only reachable from inside `--ticket` mode.*
- **Phase 9's structural position**: [harden-workflow.md#L686](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L686)
  *Evidence: Phylogeny sits after Phase 8 in the full hardening sequence; ticket mode's TM-4 explicitly closes "after Phase 8," with no reference to Phase 9 in the per-ticket loop at all.*
- **TM-1.5's redirect, added today**: [harden-workflow.md#L122-L140](file:///home/jwils/blueprint-workflows/claude-commands/harden-workflow.md#L122-L140)
  *Evidence: a SUBSTANTIVE-LOGIC ticket now redirects before TM-2, "or halt entirely in single-ticket mode" — formalizing, not fixing, the bypass of TM-6/Phase 9.*
- **All five recent closures confirm the direct-remediation path**: [CLOSED_20260704_ticket-remediation-authority_workflow.md#L29](file:///home/jwils/blueprint-workflows/helpdesk-tickets/CLOSED_20260704_ticket-remediation-authority_workflow.md#L29), [CLOSED_20260625_limitations_workflow.md#L34](file:///home/jwils/blueprint-workflows/helpdesk-tickets/CLOSED_20260625_limitations_workflow.md#L34)
  *Evidence: both explicitly state closure occurred outside `/harden-workflow`.*
- **The Registry data is mechanically recoverable; the Phylogeny data is not**: [scripts/registry/aggregator.py#L70-L85](file:///home/jwils/blueprint-workflows/scripts/registry/aggregator.py#L70-L85)
  *Evidence: `collect_ticket_events` mines `date`, `workflow`, and `patterns` from any ticket's filename and full text with no dedicated field required — the registry can be caught up at any time. No equivalent mechanism exists or could exist for Phylogeny's editorial judgment about cross-workflow pattern transfer; a judgment not captured at the time of the fix cannot be reconstructed with the same fidelity later.*

## 4. Remediation: Registry via `/secretary`, Phylogeny via a Mandatory Ticket Gate

Applied directly this session, asymmetrically by design (the two documents are not equally at-risk):

1. **`secretary.md`**: added Step 1.2 (Suite Learning Registry pass) to Phase 1 — runs `registry.py` unconditionally on every `/secretary` invocation, regardless of session type, independent of whether `/harden-workflow --ticket` ran. Softer trigger is acceptable here because the underlying data is retroactively recoverable at any time.
2. **`helpdesk-tickets.md`**: added a mandatory **Phylogeny Disposition** field — PENDING at filing (Phase 1 template), gated at closure (new Step 4a.5) so a ticket cannot reach REMEDIATED status via *either* closure path while it remains PENDING. This is the hard gate, because Phylogeny has no retroactive-recovery fallback — it needed to live in the one artifact guaranteed to be read regardless of which workflow (if any) does the actual fix.
3. Ran `registry.py` now to clear the mechanical backlog through today.
4. Retroactively reconstructed `SUITE_PHYLOGENY.md` lineage entries for the two 2026-06-25/2026-07-04 closures with genuine cross-workflow pattern transfer, flagged as reconstructed-from-context per the suite's own Remediation on Contact convention (`nodelete.md` Pillar 5).

## 5. Recommendation to Senior Architect

Any future workflow fork that creates a second legitimate path to the same outcome (as the two-path ticket model just did for ticket closure) should be checked against every mechanism that assumed the old single path was the only route in — not just the routing logic itself. The failure here was not that TM-6 or Phase 9 were poorly built; it's that a downstream assumption ("closure always passes through `/harden-workflow`") silently stopped holding, and nothing detected the divergence for three weeks. The general pattern worth naming: when forking a pipeline, audit what else was silently relying on the pipeline being singular.

---
**Status**: **REMEDIATED (secretary.md gains an unconditional Registry pass; helpdesk-tickets.md gains a mandatory Phylogeny Disposition gate covering both closure paths; registry backlog cleared 29→36 events; three retroactive Phylogeny lineage entries written, including this ticket's own)**
**Verification**: See Remediation Record below.

---
*Signed,*
**Claude**
*(Session Agent — Senior Architect of Workflows role)*

---

## REMEDIATION RECORD

```
REMEDIATION RECORD
  Ticket:            20260704_registry-phylogeny-gap_workflow.md
  Faulting workflow: /helpdesk-tickets, /secretary (missing hooks); /harden-workflow (orphaned
                     steps, unchanged — TM-6 and Phase 9 remain correct on their own path)
  Root cause fixed:  Registry/Phylogeny freshness depended entirely on /harden-workflow --ticket
                     being invoked, which the two-path ticket model (ratified today) now
                     structurally bypasses for Substantive/Logic closures — the path that has
                     closed every ticket since 2026-06-25.
  Changes made:      secretary.md — new Phase 1 Step 1.0.5 (unconditional Registry pass),
                     GLOSSARY entry, preamble table row, produces: entry, STRICT RULE 18,
                     Change Log entry 7, frontmatter v2→v3.
                     helpdesk-tickets.md — new mandatory Phylogeny Disposition field
                     (GLOSSARY, Phase 1 template, Phase 2 validation, Phase 3 report, new
                     Step 4a.5 closure gate covering both paths), STRICT RULE 12, INTEGRATION
                     line, Change Log entry 4, frontmatter v3→v4.
                     manifest/CONTRADICTION_REGISTRY.md — regenerated via registry.py:
                     29→36 total events (9 new this run), verdict REVIEW.
                     manifest/SUITE_PHYLOGENY.md — three lineage entries added: two
                     retroactive (Turn-Boundary Pause Protocol propagation from the
                     2026-06-25 role_workflow ticket; the two-path ticket model propagation
                     from this same day's ticket-remediation-authority ticket), one live
                     (this ticket's own "X.5 insertion convention" propagating from
                     harden-workflow.md into both files touched here) — plus a short
                     candidate-transfer list for two patterns reviewed and found NOT
                     phylogeny-worthy yet (Coverage Ledger, PENDING gate state). All three
                     entries clearly flagged per their provenance (retroactive vs. live).
  Tests:             scripts/run_tests.sh — 169/169 passed, 0 failures. No Python code
                     touched this session; full suite run purely to confirm no regression.
  Linter:            lint_workflows.py --workspace ~/blueprint-workflows: 0 CRITICAL,
                     19 WARNING (all pre-existing — nodeleteshort.md/refactor.md/soc.md/
                     testpackage.md structure gaps, role.md structure gaps, sentinel.md
                     stale hash — none introduced this session; both files touched here
                     are hash-clean). Content hashes for helpdesk-tickets.md and
                     secretary.md set from the linter's own computed values (see incidental
                     finding below).
  Deferred:          NONE for this ticket's scope. Two incidental findings surfaced but not
                     acted on, by design (see notes):
                     (1) The Registry's REVIEW verdict (36 unreviewed events, threshold 10)
                     technically calls for a judgment on whether Hallucinated Success
                     (7 of 36, the largest category, spanning multiple workflows) warrants
                     its own new ticket. Deliberately not acted on here — that judgment is
                     a separate decision from this ticket's scope (fixing the silent-failure
                     mechanism), not a substitute for one. Surfaced to the user, not decided
                     unilaterally.
                     (2) `lint_workflows.py --fix-hashes` computed correct hashes for every
                     file (including sentinel.md's pre-existing stale one) but did not
                     appear to persist any of them to disk — confirmed by re-running the
                     linter immediately after, which still showed the same mismatches until
                     the two files in this ticket's scope were corrected by hand from the
                     tool's own printed values. Not investigated further; out of scope here.
                     sentinel.md's pre-existing mismatch was left untouched, matching
                     HANDOFF.md's own prior note that it's a deferred batch-hardening item.
```
