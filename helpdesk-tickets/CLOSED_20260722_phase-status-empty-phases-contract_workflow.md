# Helpdesk Ticket: phase_status.py's "structure not recognized" contract is documented but honored by no consumer (Ghost Logic → false-clear risk)

**To**: Senior Architect of Workflows
**From**: Claude Code (Senior Architect role) — divergence CAPTURE from the 2026-07-22 phase_status regex-broadening session
**Date**: 2026-07-22
**Subject**: `scripts/focus/phase_status.py` documents a mandatory consumer contract — treat `found:true, phases:[]` as "structure not recognized," never as "no phases" — that its four consuming workflows (/focus-plan, /receipt-check, /execute-build, /triage) do not implement, risking a false "nothing to verify / all clear" on a tasks.md whose real structure uses an unrecognized header convention.
**Urgency**: CRITICAL (Architectural) — *scope is cross-cutting (4 workflows, one shared engine); currently LATENT, see §1*
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: NO TRANSFER — the remediation touched engine/consumer scripts (phase_status.py, focus.py, coverage.py), not workflow .md files; no structural pattern moved between two or more workflow files. (The count-verification gate is a candidate reusable pattern — convergent with the /sentinel parity engine's count cross-check — noted in the Remediation Record for possible future propagation, but no transfer was performed this session.)

---

## 1. Executive Summary

`phase_status.py` emits two *distinct* empty-result signals: `found:false` (no tasks.md at all → every absence is legitimately PENDING) and `found:true, phases:[]` (a tasks.md exists but uses a header convention the parser does not recognize). Its own docstring makes honoring that distinction a **consumer obligation** — the `found:true, phases:[]` case "must [be treated] as 'structure not recognized,' not as 'no phases exist.'" No consumer implements the obligation. The result is a latent **Ghost Logic** gap: a plan with real but unrecognized structure can be read as "no phases → nothing to verify," producing a Hallucinated-Success-shaped false clear on a plan that is actually unverified. **It is not currently firing** — this workspace uses recognized `## Phase N` headers, and the 2026-07-22 regex broadening (`CLOSED`-adjacent code half of the campaign-header ticket) widened recognition further — so the classification is CRITICAL by *scope* (cross-cutting, architectural), not by active-fire urgency.

## 2. Root Cause Analysis: "Ghost Logic — a documented contract with no substrate enforcement"

Named failure class: **Ghost Logic** (a promised/documented behavior absent from the actual substrate), with a downstream **Hallucinated Success** risk (a false "verified/complete").

- **The How**: `phase_status.py`'s docstring instructs consumers to branch on `found:true, phases:[]` and treat it as "structure not recognized." The four consumers do not:
  - `scripts/focus/focus.py`'s `_ADVISORY` — the one place the raw signal is editorialized for the /focus-plan agent — guides the `found:false` case ("treat absences as PENDING") and is **silent** on `found:true, phases:[]`. An agent following it has no instruction distinguishing "unrecognized structure" from "no phases," and the nearest guidance (PENDING) points the wrong way.
  - `scripts/receipt/coverage.py` iterates `for phase in phases`; when `phases==[]` the loop is skipped, `checkable_dims==0`, and `gap_percent` becomes `None`. Safer than a false 0% gap — but there is no explicit "tasks.md present, structure unrecognized" note, so `gap_percent:None`-because-unrecognized is indistinguishable from `gap_percent:None`-because-absent, and a reader can still take `phases:[]` as benign.
  - `scripts/build/build_audit.py` and `scripts/triage/triage_audit.py` are faithful pass-throughs — they forward `found`/`phases` into their JSON, but the "structure not recognized" interpretation lives only in workflow prose (execute-build.md / triage.md), where the branch is undocumented.
- **The Why**: The contract was written as a docstring obligation on *consumers*, inside the *producer* module, rather than encoded either (a) as an explicit, un-ignorable field in the engine's own output (e.g. a `structure_recognized: false` status the JSON carries) or (b) in each consumer's own advisory/prose. A contract that lives only in the producer's docstring, addressed to consumers that never execute that docstring at runtime, is enforced by nobody — and drifts out of enforcement silently.

## 3. Forensic Evidence

- **The documented contract (producer side)**: [phase_status.py docstring L54-L56](file:///home/jwils/blueprint-workflows/scripts/focus/phase_status.py#L54-L56)
  *Evidence: "…`found` is still True but `phases` is empty — the workflow must treat that as 'structure not recognized,' not as 'no phases exist.'" — the obligation placed on consumers.*
- **/focus-plan consumer honors only `found:false`**: [focus.py _ADVISORY L51-L59](file:///home/jwils/blueprint-workflows/scripts/focus/focus.py#L51-L59)
  *Evidence: the advisory instructs "No tasks_md ('found': false) … treat absences as PENDING" but says nothing about `found:true, phases:[]`; the agent-facing guidance omits the exact case the contract names.*
- **/receipt-check degrades to gap_percent:None with no unrecognized-structure flag**: [coverage.py L197-L227](file:///home/jwils/blueprint-workflows/scripts/receipt/coverage.py#L197-L227)
  *Evidence: the `for phase in phases` loop is skipped when phases is empty; `gap_percent` becomes None with no note distinguishing "unrecognized structure" from "tasks.md absent."*
- **/execute-build passes the signal through, interprets nowhere**: [build_audit.py L68-L82](file:///home/jwils/blueprint-workflows/scripts/build/build_audit.py#L68-L82)
  *Evidence: `phase_report.as_dict()` is placed into the report dict unmodified; no branch on the empty-but-found case.*
- **/triage passes the signal through, interprets nowhere**: [triage_audit.py L89-L97](file:///home/jwils/blueprint-workflows/scripts/triage/triage_audit.py#L89-L97)
  *Evidence: `build_phase_status_report(...).as_dict()` forwarded into the report; same undocumented-interpretation deferral.*

## 4. Remediation: Encode the "unrecognized structure" signal where consumers can't miss it

Recommended direction (NOT yet executed — pending Architect greenlight):

1. **Engine-side (preferred, single fix point):** have `phase_status.py` carry the distinction explicitly in its output — a top-level `structure_recognized: bool` (or a status when `found and not phases`) so every consumer receives an un-ignorable field instead of re-deriving `found and not phases` and remembering a docstring. Additive, backward-compatible.
2. **focus.py advisory:** extend `_ADVISORY` to name the case — "a tasks.md that exists but yields zero phases is *unrecognized structure*, NOT 'no phases'; do not treat its absences as PENDING — flag for human structure review."
3. **coverage.py:** when `tasks_md_found and not phases`, add an explicit `note` ("tasks.md present but no recognized phase headers — coverage not computed; structure unrecognized") disambiguating `gap_percent:None`.
4. **Consumer prose (execute-build.md / triage.md):** one line each pointing at the new field.

## 5. Recommendation to Senior Architect

Move the "structure not recognized" contract off the producer's docstring and into the engine's *output contract* — a single explicit field (`structure_recognized`/equivalent) computed once in `phase_status.py` and consumed uniformly. A cross-cutting obligation documented only in one module's docstring, addressed to four consumers that never execute that docstring, is structurally guaranteed to drift out of enforcement; making the signal a first-class output field is the general fix that prevents this failure class — *a producer-documented consumer contract with no runtime carrier* — for every future consumer of this engine.

Related, not duplicate: the deferred STRUCTURAL half of `helpdesk-tickets/20260707_phase-status-campaign-header-scope_workflow.md` addresses *detection* (recognizing more header conventions); this ticket addresses *consumption* (honoring the empty signal whatever its cause). They compose — better detection shrinks the trigger surface; this closes the false-clear when the surface is still hit.

---

## 6. Remediation Record [ADDED 2026-07-22, Claude Code, Senior Architect role — direct remediation under /quality Maximum]

Greenlit by the user, who also directed rolling in a **more general fix** than §4's field-only recommendation. §4's `structure_recognized` boolean is all-or-nothing — it catches a tasks.md with ZERO recognized phases, but is blind to a PARTIAL miss (e.g. 8 `## Phase N` + 4 `## Step N` → phases non-empty, structure_recognized true, 4 units silently dropped). The **count-verification gate** closes that broader class: the ingesting agent asserts the unit count it read; the engine refuses (exit 2) if its own recognized count differs, forcing reconciliation to the canonical format. It is the Intelligence-Bridge pattern — a regex can never enumerate every hallucinated header spelling, so the engine verifies its parse against the agent's ground-truth count instead.

```
REMEDIATION RECORD
  Ticket:            20260722_phase-status-empty-phases-contract_workflow.md
  Faulting engine:   scripts/focus/phase_status.py (contract) → 4 consumers
  Root cause fixed:  the "structure not recognized" contract lived only in the producer's
                     docstring, addressed to consumers that never execute it — no runtime carrier.
  Changes made:      phase_status.py — (1) `structure_recognized` first-class output field
                     (found AND non-empty); (2) `verify_phase_count()` + `--expect-phases N`
                     count-verification gate (MATCH / MISMATCH→exit 2 / NO_TASKS_MD→exit 2) with a
                     reconcile-instruction message; docstring contract updated to point at both.
                     focus.py — `_ADVISORY` (runtime-delivered to the /focus-plan agent) extended
                     to name the found-but-empty = unrecognized-structure case AND instruct the
                     count-gate, since a partial miss leaves structure_recognized true.
                     coverage.py — `structure_recognized` + a `structure_note` disambiguating
                     gap_percent:None-because-unrecognized from gap_percent:None-because-absent.
  Tests:             487/487 pass (was 480; +7 — structure_recognized 3-way; verify_phase_count
                     MATCH / MISMATCH-on-partial-miss / NO_TASKS_MD; 2 CLI subprocess exit-code
                     tests proving the gate actually gates; coverage note both directions).
                     Live-probed: the Step-3 partial-miss MISMATCHes and exits 2; MATCH exits 0.
  Linter:            lint_workflows.py N/A — no workflow .md file touched (engine/consumer scripts).
  Deferred:          Wiring the ACTIVE `--expect-phases` gate into the remaining consumers' prose
                     (execute-build.md / triage.md / receipt-check.md ingestion steps). The engine
                     primitive + the passive `structure_recognized` field now serve them; /focus-plan
                     (the blocking pre-gate, the docstring's named consumer) is honored via its
                     runtime advisory. Incremental follow-up, not a reopened root cause.
```

---
**Status**: **REMEDIATED (count-verification gate + `structure_recognized` field added to phase_status.py; honored by focus.py advisory + coverage.py; 487/487 green)**
**Verification**: Remediation Record (§6 above).

---
*Signed,*
**Claude**
*(Senior Architect of Workflows role — divergence CAPTURE, then greenlit remediation, verified against live consumer code + suite)*
