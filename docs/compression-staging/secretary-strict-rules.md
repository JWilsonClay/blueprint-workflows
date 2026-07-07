# Compressed STRICT RULES — /secretary

Staging artifact for `tasks.md` Phase 2.1. Produced by Claude 2026-07-07 by applying the
Instruction Density Compression test (`implementation-plan.md`, "Instruction Density
Compression — the test") to each of the file's 20 STRICT RULES individually.

**Per-rule disposition** (so the mechanical replacement step is auditable, not a black box):
Rules 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 — left verbatim (already a single dense imperative;
no historical narrative to compress out). Rule 14 — left verbatim and MUST stay verbatim: it is
a `**[SUPERSEDED ...]**` marker preserved per `/nodelete`'s "a STRICT RULE is never removed
without a superseding replacement" doctrine — compressing a superseded rule's provenance text
would contradict the preservation principle the compression test itself is scoped underneath.
Rules 2, 13, 15, 16, 17, 18, 19, 20 — compressed below: each had a dense operative core plus
multi-sentence historical justification that duplicates an entry already preserved verbatim in
`.changelogs/secretary.md` (Phase 1 externalized it there) — the compression drops the duplicated
prose, keeps a pointer, and keeps any clause that is actually behavior-defining (e.g. rule 18's
"STRICT RULE 11 does NOT apply here" is kept in full — that is an operative override, not narrative).

**Mechanical instruction**: this file's content from the line below the `---` to the end is the
exact, verbatim replacement for the numbered-rules portion of `claude-commands/secretary.md`'s
`## STRICT RULES (never violate)` section (i.e. replace lines with rule numbers 1-20; leave the
`## STRICT RULES (never violate)` heading itself and the blank line after it untouched, and leave
everything after rule 20 — the `---` and HOW TO BEGIN section — untouched).

---

1. /secretary is always the LAST workflow invoked in a session. Do not run it mid-session while build or test activity is ongoing.
2. `SUITE_HEALTH.md` is updated on every /secretary run, without exception — always written to `~/blueprint-workflows/manifest/SUITE_HEALTH.md`. **[RETARGETED 2026-07-04 from WORKFLOW_MANIFEST.md — full rationale in Change Log]**
3. HANDOFF.md is overwritten each session. This is the only correct behavior — it is the current-session briefing, not a history. Prior content is NOT archived unless it contains anomalies not in ANOMALY_LOG.md.
4. ANOMALY_LOG.md is append-only. Never rewrite or remove entries. An anomaly that was logged cannot be unlogged.
5. Never modify any workflow protocol file or project source code. /secretary is documentation-only.
6. Never fabricate anomalies. If no STRICT RULE overrides, MISMATCH acceptances, or unjustified skips occurred: log "NO ANOMALIES" explicitly.
7. Phase 6 (/retrospective) is mandatory. /secretary without a retrospective entry is incomplete. The Secretary Receipt must show /retrospective status — COMPLETE or FAILED. FAILED is acceptable; SKIPPED without logging is not.
8. If the project does not have a `.workflow_state/` directory: create it. Never halt because the target directory is missing.
9. The `SUITE_HEALTH.md` Suite Health Score must be recalculated on every run from actual live file reads — never from a cached or remembered prior value. **[RETARGETED 2026-07-04, was WORKFLOW_MANIFEST.md]**
10. If any Phase fails (/document not found, receipt-check payload missing, retrospective failure, etc.): log the failure in the Secretary Receipt and continue. Do not halt the entire close sequence for a sub-workflow failure.
11. **Phase 3 (/receipt-check) and Phase 2 (/document) are MANDATORY SKIP for workflow-suite-only sessions.** If the session worked exclusively on `~/blueprint-workflows/` (no project workspace code was built, tested, hardened, or documented), both phases must be explicitly skipped and logged in the Secretary Receipt. Do not run /document or /receipt-check against the blueprint-workflows directory itself.
12. Phase 2 (/document) is mandatory for project sessions. A session close without documentation is incomplete by definition. The only valid skip condition is a confirmed workflow-suite-only session (STRICT RULE 11).
13. All six phases (0–6) must execute in order, confirmed before the Phase 7 receipt. Producing only the three Phase 1 artifacts (WORKFLOW_MANIFEST, HANDOFF, ANOMALY_LOG) without Phases 2/3/6 = Phase 1 only, not a completed /secretary run.
14. **[SUPERSEDED 2026-07-04 — the migration this rule guarded against completed 2026-05-08; preserved per /nodelete, not deleted]** ~~If `WORKFLOW_MANIFEST.md` is found at the old path `~/blueprint-workflows/WORKFLOW_MANIFEST.md`: migrate it to `~/blueprint-workflows/manifest/WORKFLOW_MANIFEST.md` immediately. The correct location is the manifest/ subdirectory.~~ `WORKFLOW_MANIFEST.md` itself is now a short redirect stub (see Phase 1) — `SUITE_HEALTH.md` and `manifest/history/*` are the live successors and were created directly at their correct locations; no equivalent legacy-path migration risk exists for them.
15. **[INJECTION 2026-05-08, RETARGETED 2026-07-04]** Never overwrite `SUITE_HEALTH.md` via a full-file Write call if it already exists — always use targeted Edit calls. (Prevents the blind-overwrite risk on unexpectedly large files; targeted edits are the sovereign-grade method for index maintenance.)
16. **[INJECTION 2026-05-15, /nodelete]** If `/receipt-check` returns `RECEIPT INFRASTRUCTURE NOT INITIALIZED` for ≥ 2 consecutive sessions on the same project: auto-file a helpdesk ticket in Phase 3, before Phase 4. (Closes the gap STRICT RULE 10's continue-past-failures behavior would otherwise leave open indefinitely.)
17. **[INJECTION 2026-05-15, /nodelete]** All ANOMALY_LOG.md writes MUST use `cat >>` via Bash, except the first (file-creation) write, which may use the Write tool. (Mirrors `/retrospective` STRICT RULE 9's atomic-append mandate — same failure mode once destroyed PROCESS_LEARNINGS.md entries live.)
18. **[INJECTION 2026-07-04]** Phase 1 always runs the Suite Learning Registry pass (Step 1.0.5) on every `/secretary` invocation, regardless of session type — STRICT RULE 11's workflow-suite skip does NOT apply here (registry data is not project-specific). A REVIEW verdict must be ingested and judged per Step 1.0.5, never skipped.
19. **[INJECTION 2026-07-04]** Phase 1 always runs the ledger growth check (Step 1.2) on every run, without exception — same STRICT RULE 11 exemption as Rule 18. Append the session's narrative entry to whichever shard the monitor reports active; never hardcode a shard filename. A `SUITE_PHYLOGENY.md` WARN is advisory, like a Registry REVIEW verdict — always note the disposition in the Secretary Receipt, never silently absorb it.
20. **[INJECTION 2026-07-05]** Phase 0 always runs the Retrospective Lag check (Step 0b.5) on every run, without exception — same STRICT RULE 11-independent status as Rules 18-19. A `GAP DETECTED` result is advisory (does not block this session's own Phase 6) but must be noted in the Secretary Receipt every time it fires, never silently absorbed.
