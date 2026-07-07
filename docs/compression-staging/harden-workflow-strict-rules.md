# Compressed STRICT RULES — /harden-workflow

Staging artifact for `tasks.md` Phase 2.3. Produced by Claude 2026-07-07 by applying the
Instruction Density Compression test (`implementation-plan.md`, "Instruction Density
Compression — the test") to each of the file's 22 STRICT RULES individually.

**Scope note**: `harden-workflow.md` has TWO `## STRICT RULES (never violate)` headings.
The first (line 369) is embedded example/placeholder text inside the Sovereign Scaffold
Generator template ("`[Rule — always include: ...]`") — it is not a real rule set and MUST
NOT be touched. The real rules are the SECOND occurrence, at line 733 (22 numbered rules).
This staging file concerns only the second occurrence.

**Per-rule disposition:**
Rules 1-14, 15, 16, 17, 19, 20, 21 — left verbatim. All are single dense operative
statements; none carry historical narrative duplicating a `.changelogs/harden-workflow.md`
entry (checked against the changelog directly — its entries are themselves already terse
summaries, not expanded prose the rules repeat). Rule 13's `[PLACEHOLDER]`/grade-fraud
language and Rule 14's Claude-Code-specific symlink instruction are both load-bearing
operative detail, not padding.

Rules 18 and 22 — compressed below: each carried one clause that is pure editorializing/
rationale-restatement rather than new operative content.
- Rule 18: dropped "This is housekeeping, not destruction." — asserts nothing the rest of
  the rule ("never deleted... preserves full ticket content and CLOSED_ prefix") doesn't
  already establish mechanically.
- Rule 22: replaced "this workflow hardens structure, not logic or code (STRICT RULE 3,
  opening line), and cannot fix what it was never built to touch" with a short pointer,
  "(per STRICT RULE 3)" — the clause was restating STRICT RULE 3 verbatim rather than adding
  new behavior-defining content. The operative sequencing and fallback logic (TM-1.5 order,
  provisional STRUCTURAL treatment, mis-routing evidence note) are unchanged and fully
  preserved.

**Non-finding worth recording explicitly**: unlike `secretary.md`, this file's `[INJECTED
...]` rules do not carry duplicated historical narrative — `.changelogs/harden-workflow.md`'s
entries are summaries, not expansions, of what the rules already say. This is why only 2 of
22 rules had a real compression target, not a shallower pass.

**Mechanical instruction**: this file's content from the line below the `---` to the end is
the exact, verbatim replacement for rules 18 and 22 ONLY inside `claude-commands/harden-workflow.md`'s
SECOND `## STRICT RULES (never violate)` section (starting at line 733 in the pre-edit file).
Rules 1-17, 19-21 in that section are untouched — do not re-copy them, only replace the two
lines for rules 18 and 22 with the corresponding lines below. Do NOT touch the first
`## STRICT RULES` occurrence (line 369, inside the Scaffold Generator template).

---

18. **[INJECTED 2026-05-24 — Ticket archival, /nodelete]** In ticket mode, Step TM-5 (archive stale closed tickets) is mandatory at the end of every session. Closed tickets older than 7 days are moved to `helpdesk-tickets/archive/` — never deleted. The archive directory preserves full ticket content and `CLOSED_` prefix for historical reference.
22. **[INJECTED 2026-07-04 — Root Cause Type redirect, /nodelete, resolves helpdesk-tickets/CLOSED_20260704_ticket-remediation-authority_workflow.md]** In ticket mode, Step TM-1.5 (Root Cause Type check) runs before TM-2. A SUBSTANTIVE-LOGIC ticket must be redirected immediately, not processed through Phase 1-8 (per STRICT RULE 3). A ticket with no Root Cause Type (filed before this field existed) is treated as STRUCTURAL provisionally; if Phase 1's Assessment Card then shows the file already meets every Sovereign criterion, that is itself evidence the ticket was actually SUBSTANTIVE-LOGIC and was mis-routed — note this in the certificate rather than silently halting with nothing to report.
