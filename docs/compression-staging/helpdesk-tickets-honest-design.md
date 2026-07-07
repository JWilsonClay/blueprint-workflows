# Honest-Design Discipline — /helpdesk-tickets (Phase 5.5)

Produced by Claude, 2026-07-07, under `/quality` Maximum rigor. Fifth and
last of the remaining 5 Verification-Spine targets.

## 1. What is mechanically verifiable here?

Unlike `/redteam`/`/investigate`, `/helpdesk-tickets` operates entirely on
**this repo's own fixed convention** — the `helpdesk-tickets/` directory
and its own mandated ticket schema (Phase 1's "Required structure"). This
is closer to the Phase 4 targets' architecture than to `/redteam`'s
arbitrary-external-target problem.

tasks.md's own hint ("OPEN/CLOSED counts, schema validation, staleness
detection") maps directly onto three real, currently-manual mechanisms:

1. **Phase 2's TICKET VALIDATION checklist is almost entirely mechanical**
   and is currently a hand-checked list: filename convention, all 5
   sections present, Root Cause Type declared as one of two valid values,
   Phylogeny Disposition present, ≥2 forensic citations with `file:///`
   links, Status line matches `OPEN`/`REMEDIATED (...)`. None of this
   requires judging the ticket's *content quality* — only whether the
   required scaffold elements are present and well-formed.
2. **STRICT RULE 7's duplicate-ticket check is currently manual and
   unenforced**: "Check `helpdesk-tickets/` for existing open tickets
   against the same faulting workflow before creating a new one." This is
   a simple scan-and-compare — list open tickets (non-`CLOSED_` prefix),
   extract each one's declared "Faulting workflow" field, compare against
   the new ticket's target.
3. **Staleness has no mechanism at all today**, despite the campaign's own
   naming of it as an expected dimension. An OPEN ticket sitting unresolved
   for weeks is itself a signal worth surfacing — the ticket filename's own
   `YYYYMMDD` prefix (STRICT RULE 10: "the date of the failure event") is
   exactly the data needed to compute days-open mechanically.
4. **STRICT RULE 12's Phylogeny gate has no mechanical enforcement either**:
   "Before Phase 4 may set Status to REMEDIATED... this field must be
   resolved to CONFIRMED." Nothing currently checks that a ticket claiming
   `REMEDIATED` doesn't still carry `Phylogeny Disposition: PENDING` — a
   real, checkable contradiction between two fields in the same file.

A fifth item is **pure reuse, not new work**: Section 3's citation format
(`[label](file:///absolute/path#LN-LM)`) is byte-for-byte identical to
`/investigate`'s own citation convention, already verified this same
session by `scripts/investigate/citation_fidelity.py`. Building a second
citation checker here would be exactly the duplication this campaign's own
discipline (established across `/execute-build`, `/triage`,
`/harden-workflow`) exists to prevent — this engine imports that module
directly.

## 2. What is irreducible judgment?

Everything about the failure itself: which failure class applies (Phase
0a), whether the root cause is genuinely STRUCTURAL vs. SUBSTANTIVE-LOGIC,
the actual root-cause narrative (Section 2), the recommendation (Section
5), Urgency-level judgment (STRICT RULE 9 gives a rule of thumb, but
"affects multiple workflows" still requires reading the failure), and the
entire Phylogeny Disposition judgment itself (was a pattern genuinely
transferred between workflows? — the engine can check the FIELD isn't
left PENDING when the ticket claims REMEDIATED, but it cannot determine
whether `NO TRANSFER` was the *correct* call). None of this is
mechanizable and none of it should be touched.

## 3. Mock-Trap test

Checking section presence, citation format resolution (reusing an already-
Mock-Trap-cleared module), filename-vs-content field consistency (does the
filename's workflow name match the "Faulting workflow" field? does a
`REMEDIATED` status coexist with a `PENDING` Phylogeny field?), and
days-since-filed arithmetic are all structural/textual facts — none require
judging whether the ticket's failure analysis is *correct*, only whether
its required scaffold is genuinely present and internally consistent. The
duplicate-ticket check reports "another open ticket already names this
workflow" as a fact for the agent to evaluate (it might be a legitimately
distinct, unrelated failure in the same workflow) — never an automatic
rejection.

## 4. Engine design for Phase 5.5's build

New package `scripts/helpdesk_tickets/` (underscore; sibling of
`scripts/investigate/`, imports it directly rather than duplicating):

1. **`ticket_parser.py`**: `parse_ticket(text) -> TicketFields` — extracts
   the header block fields (To/From/Date/Subject/Urgency/Root Cause
   Type/Phylogeny Disposition), which of the 5 required `## N.` sections
   are present, and the Status line's value. Pure regex over this
   workflow's own fixed template — not schema-agnostic like `/redteam`'s
   target, because this workflow's ticket format IS the schema, not an
   external unknown.
2. **`schema_validator.py`**: `validate_ticket(fields, filename) ->
   ValidationResult` — checks filename-convention match, all 5 sections
   present, Root Cause Type ∈ `{STRUCTURAL, SUBSTANTIVE-LOGIC}`, Phylogeny
   Disposition present, Status matches `OPEN`/`REMEDIATED (...)`, AND the
   Phylogeny-vs-Status contradiction check (STRICT RULE 12: `REMEDIATED`
   status with `PENDING` Phylogeny Disposition is a real, catchable
   defect). Citation count/resolution is delegated to
   `investigate.citation_fidelity` directly — imported, not reimplemented.
3. **`duplicate_detector.py`**: `find_open_tickets_for_workflow(tickets_dir,
   workflow_name) -> List[str]` — lists non-`CLOSED_`-prefixed tickets
   whose parsed "Faulting workflow" field matches, for STRICT RULE 7.
4. **`staleness.py`**: `compute_staleness(tickets_dir, today=None) ->
   List[StalenessResult]` — for every open ticket, extracts the
   `YYYYMMDD` from its filename and reports days-open; flags a
   caller-supplied threshold (default advisory, no hardcoded "bad" value —
   staleness is context-dependent and this campaign's own Mock-Trap
   discipline says a script shouldn't invent an urgency judgment the
   workflow's own STRICT RULE 9 already reserves for the agent).
5. **`reporter.py` + `helpdesk_tickets_audit.py` CLI**.

**Explicitly not built**: anything judging failure class, root cause
narrative, urgency correctness, or Phylogeny Disposition correctness (only
its PRESENCE and its consistency with Status are checked) — all
irreducible judgment per Section 2.

## 5. Disposition

Seed design **confirmed and specified**: tasks.md's "OPEN/CLOSED counts,
schema validation, staleness detection" hint named three real, currently-
unenforced mechanisms exactly. A fourth (Phylogeny/Status consistency) was
found by reading STRICT RULE 12 directly rather than stopping at the
seed's three named items. Citation verification is pure reuse of
`scripts/investigate/citation_fidelity.py` — zero new parsing for that
piece, closing the loop on this campaign's own no-duplication discipline
with its very last Phase 5 target. Ready for the build.
