# Helpdesk Ticket: Routing Gap — /continuous-verify Is Invisible to /triage

**To**: Senior Architect of Workflows
**From**: Sovereign Depreciate + Investigate Joint Audit Agent
**Date**: 2026-05-12
**Subject**: /continuous-verify self-declares as non-user-invokable, creating a routing black hole — users who need forward-contract verification cannot reach it through /triage, and /triage cannot route them there even indirectly.
**Urgency**: MEDIUM

---

## 1. Executive Summary

`/continuous-verify` is the suite's forward-contract verification gate — it answers the question "does what I just built still comply with the full implementation plan, including future phases?" This is a capability users may actively need between sessions or when debugging MISMATCH states. However, the workflow self-declares as non-user-invokable ("This workflow is NOT user-invoked. It is invoked automatically by `/execute-build` Step 5g") and its INTEGRATION section explicitly instructs `/triage` not to route to it directly. The result is an invisible capability: the suite provides forward-contract verification but provides no user-facing entry point for it. Users who express the need that `/continuous-verify` solves will receive no routing guidance from `/triage`.

## 2. Root Cause Analysis: "Invisible Capability"

**Failure class**: Routing Gap / Context Erosion

- **The How**: `/continuous-verify` was designed as an internal gate invoked by `/execute-build` Step 5g. The INTEGRATION section actively suppresses triage routing to it. No advisory trigger, no "if user asks about forward-contract compliance, route them here" hook exists.
- **The Why**: The workflow was built for machine-to-machine invocation. The user-facing equivalent of its function — "check if my build is still compliant with the full plan" — is a valid and distinct use case that was not designed for. The current architecture assumes the only path to forward-contract verification is through a full `/execute-build` run, which is heavyweight and may not be what the user needs.

## 3. Forensic Evidence

- **[continuous-verify/core.md — explicit non-user-invocable declaration]**: [continuous-verify/core.md:L7](file:///home/jwils/.gemini/antigravity/global_workflows/continuous-verify/core.md#L7)
  *Evidence: "This workflow is NOT user-invoked. It is invoked automatically by /execute-build Step 5g at each phase boundary." This is the direct cause of the routing black hole.*

- **[continuous-verify/core.md — triage suppression]**: [continuous-verify/core.md:L288-L295](file:///home/jwils/.gemini/antigravity/global_workflows/continuous-verify/core.md#L288-L295)
  *Evidence: The INTEGRATION section states "/triage does not recommend it directly. /triage may recommend /execute-build, which invokes this gate..." — the triage router is explicitly told not to route to the workflow that solves forward-contract verification questions.*

- **[triage/core.md — no /continuous-verify triggers]**: [triage/core.md](file:///home/jwils/.gemini/antigravity/global_workflows/triage/core.md)
  *Evidence: A full read of the triage payload confirms zero trigger entries for any variation of "does my build still match the plan," "forward contract," "phase compliance," or "continuous verify." These are valid user expressions with no routing path.*

- **[focus-plan/core.md — MISMATCH detection exists but does not route to continuous-verify]**: [focus-plan/core.md](file:///home/jwils/.gemini/antigravity/global_workflows/focus-plan/core.md)
  *Evidence: /focus-plan detects MISMATCH states and routes to /provenance, but does not route to /continuous-verify for forward-contract checking after a repair. The two workflows address different moments in the same compliance concern but have no connection.*

## 4. Remediation: Add User-Facing Advisory Triggers Without Breaking Machine-Invocation Design

The remediation preserves the machine-invocation design while adding user discoverability:

1. **Inject into `/triage/core.md`** an advisory trigger set:
   - "Does my build still comply with the full implementation plan?" → Advisory: `/continuous-verify` (explain it runs automatically within `/execute-build`; if outside a build, suggest `/focus-plan` followed by a targeted `/execute-build` phase re-run with Step 5g enabled)
   - "Check if what I built matches the plan including future phases" → `/continuous-verify` advisory
   - "Forward contract verification" → `/continuous-verify` advisory
2. **Update `/continuous-verify/core.md` INTEGRATION section**: Add a "User-Facing Advisory" sub-section that describes when a user might want to understand or manually trigger it, and what the equivalent manual operation is when outside an `/execute-build` run.
3. **Connect `/focus-plan` → `/continuous-verify`**: When `/focus-plan` detects PARITY, add a suggestion to run `/continuous-verify` as a forward-looking gate before the next build phase.

## 5. Recommendation to Senior Architect

Any workflow that is internally invoked by another workflow but solves a user-expressible problem should have an "Advisory" triage trigger that explains the capability and its manual equivalent. The pattern of "machine-only invocation = no user entry point" is a discoverability anti-pattern that will recur as the suite grows. Add to `/harden-workflow` Phase 0: "Identify whether the target workflow has user-facing value beyond its machine-invocation role. If yes, add an Advisory triage trigger even if direct invocation is not the intended path."

---
**Status**: **OPEN**
**Verification**: Resolved when `/triage/core.md` contains at minimum 2 trigger entries that route users to `/continuous-verify` (advisory mode), and `/continuous-verify/core.md` INTEGRATION section contains a "User-Facing Advisory" sub-section explaining manual access patterns.

---
*Signed,*
**Sovereign Depreciate + Investigate Joint Audit Agent**
*(Forensic Audit — global_workflows substrate, 2026-05-12)*

---
**Status**: **REMEDIATED**
**Closed**: 2026-05-15
**Changes**:
- `triage/core.md`: 2 advisory trigger rows added to the /continuous-verify block. Routing is now discoverable.
- `continuous-verify/core.md`: User-Facing Advisory sub-section added to INTEGRATION. Documents non-user-invocable status, /execute-build automatic path, /focus-plan as manual equivalent.
- Change Log entries added to both files.
