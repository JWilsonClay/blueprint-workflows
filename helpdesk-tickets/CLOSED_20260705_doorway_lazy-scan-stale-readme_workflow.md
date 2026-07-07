# Helpdesk Ticket: Doorway Lazy-Scan Carries Stale `has_readme` — Phantom `missing_readme` Drift After Self-Heal

**To**: Senior Architect of Workflows
**From**: Grok (Grok Build session — discovered during second `/sentinel` run after inaugural scan + `/document` hygiene on blueprint-workflows)
**Date**: 2026-07-05
**Subject**: Incremental Doorway scans report `missing_readme` drift and route to `/document` even when every README exists on disk — caused by `scanner.py` carrying forward stale child metadata from the prior snapshot when parent `.py` hashes are unchanged.
**Urgency**: LOW (workaround confirmed: `--full-scan` yields zero-finding; no data loss; wrong routing only) **[CORRECTION — 2026-07-07, /nodelete: this framing was wrong. Remediation (Section 6) found the same stale signal also reaches `create_readme()` with no existence check, meaning real data loss was genuinely possible, not just wrong routing. Original text preserved per /nodelete; do not trust this line alone.]**
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: `NO TRANSFER` — [RESOLVED 2026-07-07, see Section 6 Remediation Record]

---

## 1. Executive Summary

During the inaugural Grok Build session on blueprint-workflows, `/sentinel` self-healed 32 READMEs and populated breadcrumbs. A follow-up incremental Doorway scan immediately afterward still reported 23 `missing_readme` directories and recommended `/document` — despite every listed path having a `README.md` on disk (verified via `test -f`). A `--full-scan` on the same workspace produced `zero_finding: true` with 33/33 READMEs ingested. The defect is in the lazy-scan cache: child directory entries copied from the previous snapshot retain `has_readme: false` from before self-heal, because directory hashes are computed from `.py` files only and README creation does not invalidate the cache branch.

## 2. Root Cause Analysis: "Stale Snapshot Carry-Over"

- **The How**: `WorkspaceScanner.scan()` skips recursion into unchanged branches (`should_recurse` returns false when `content_hash` matches the prior snapshot). When skipping, it copies all child paths from `previous_map` verbatim — including stale `has_readme` flags — without re-statting `README.md` on disk. `compute_dir_hash()` hashes only `*.py` files, so markdown-only changes (README self-heal, breadcrumb writes) never trigger a fresh walk of affected subtrees.
- **The Why**: The Doorway engine optimizes scan performance via content-hash short-circuiting but does not reconcile carry-over metadata against the live filesystem. Any workflow consuming incremental scan output (`/sentinel`, `/triage`, `/investigate --patrol`) can therefore emit false hygiene findings and route agents to `/document` for work already complete. This is a substantive logic gap in `scripts/doorway/`, not a structural gap in a workflow `.md` file — `/harden-workflow` cannot remediate it.

## 3. Forensic Evidence

- **Carry-over copies stale metadata without disk check**: [scripts/doorway/scanner.py#L107-L118](file:///home/jwils/blueprint-workflows/scripts/doorway/scanner.py#L107-L118)
  *Evidence: When `should_recurse` is false, `workspace_map[p_old] = info_old` preserves prior `has_readme` values; no `README.md` existence check.*
- **Hash ignores README changes**: [scripts/doorway/scanner.py#L35-L52](file:///home/jwils/blueprint-workflows/scripts/doorway/scanner.py#L35-L52)
  *Evidence: `compute_dir_hash()` concatenates only sorted `*.py` files; README creation in a no-Python directory leaves hash unchanged indefinitely.*
- **Stale snapshot persisted after self-heal**: [.doorway/workspace_snapshot.json#L41-L48](file:///home/jwils/blueprint-workflows/.doorway/workspace_snapshot.json#L41-L48)
  *Evidence: `helpdesk-tickets/archive` shows `has_readme: false` with `files_count: 24` while `README.md` exists on disk — snapshot written before breadcrumb pass, never refreshed on incremental scan.*
- **Incremental vs full-scan divergence (this session)**: Incremental scan output: `missing_readme: 23`, `recommendations: [SEQ-SUBSTRATE-MAINTAIN → /document]`. `--full-scan` output: `missing_readme: []`, `zero_finding: true`, `ingested: 33`. Confirmed in Grok Build session 2026-07-05.
- **README verified on disk**: `test -f helpdesk-tickets/archive/README.md` → EXISTS (same session, same paths listed in drift report).

## 4. Remediation: Auto-Escalate Full-Scan After Repairs (Option C — User Selected)

**Primary fix (engine-owned — keeps workflows thin):**

1. **`doorway.py` auto-escalation (Option C)**: In `DoorwayContextualizer.run()`, after Step 3 (structural audit), if `self.metrics["repairs"] > 0` (or `created > 0`) AND `full_scan` is False AND `drift["missing_readme"]` is non-empty, silently re-run Steps 2–3 with `full_scan=True`, then continue Steps 4–9 on the refreshed map/drift. Log `[DOORWAY] Auto-escalated to full-scan after self-heal repairs` when triggered. Emit final JSON/report from the escalated pass only.
2. **Regression test**: Add `scripts/tests/test_doorway.py` (or extend existing) scenario: seed snapshot with `has_readme: false`, create `README.md` on disk, run incremental scan without escalation flag — assert zero phantom `missing_readme` after fix (or assert auto-escalation fired and corrected drift).
3. **Interim workflow guard (until engine fix ships)**: Inject `/sentinel` Step 1e — if `metrics.repairs > 0` OR non-empty `missing_readme` after Step 1a, re-run `doorway.py --full-scan --output-json` before Phase 2 classification. Remove Step 1e once Option C is verified in tests.

**Agent advisory (written this session — LIVE until ticket closes):**

4. **SUITE_HEALTH.md active advisory**: Bullet added under `## Suite Health` in `manifest/SUITE_HEALTH.md` — mandatory session-start read per `role.md` Section VI. Tells agents: phantom `missing_readme` → `--full-scan` first; do not route to `/document` on signal alone.

**Mandatory closure step — advisory supersession:**

5. **On ticket closure (REMEDIATED)**: Remove the `[ACTIVE ADVISORY 2026-07-05 — ticket …]` bullet from `manifest/SUITE_HEALTH.md` OR replace it with a single `[RESOLVED YYYY-MM-DD — CLOSED_20260705_doorway_lazy-scan-stale-readme_workflow.md]` line stating Option C is live and verified. This step is **required** before Status may read REMEDIATED — the advisory exists only while the defect is open. Verifier: grep SUITE_HEALTH for `ACTIVE ADVISORY` → 0 matches after closure.

6. **Remediation Record** (Substantive/Logic closure artifact): Document test command run, sample before/after JSON (`missing_readme` count), and confirmation that incremental post-repair scan no longer routes to `/document`.

## 5. Recommendation to Senior Architect

Engine-owned reconciliation (Option C) is preferable to scattering `--full-scan` instructions across `/sentinel`, `/triage`, and `/investigate`: the executing agent should not need to know cache semantics to get a truthful drift report. The pattern generalizes — **any self-heal that mutates files excluded from the hash function must trigger a reconciliation pass** before recommendations are emitted. Consider documenting this as a Doorway design invariant in `scripts/doorway/doorway.py` module docstring and in `/sentinel` INTEGRATION (one sentence, not a multi-step agent workaround) once Option C ships.

Secondary: `breadcrumb.py`'s `apply_approved()` proposal-delimiter mismatch (`--- PROPOSAL` vs blank-line-separated entries) caused only one breadcrumb to apply during inaugural `/sentinel` — separate LOW ticket if not bundled here.

---

## 6. Remediation Record — [ADDED 2026-07-07, Sovereign Redesign Cluster Stage 6 Task 6.2, closed by Claude Code]

```
REMEDIATION RECORD
  Ticket:            20260705_doorway_lazy-scan-stale-readme_workflow.md
  Faulting workflow: N/A (SUBSTANTIVE-LOGIC — scripts/doorway/ engine code, not a workflow .md file)
  Root cause fixed:  Two, not one. (a) Option C's auto-escalation (this ticket's own prescribed
                     fix) was ALREADY implemented (doorway.py, landed during Stage 1/2's P1
                     stabilization work, pr-01-00) but never verified with a dedicated test and
                     the ticket itself was never closed to reflect this. (b) A genuinely NEW,
                     more severe defect, found via independent design review (not this ticket's
                     own original investigation): integrity.py's create_readme() had no
                     existence check before overwriting a target file — the exact stale
                     has_readme carry-over this ticket describes could silently destroy a real,
                     hand-authored README's content, not just mis-report drift. This ticket's own
                     original Urgency ("LOW... no data loss") was incorrect; superseded by this
                     finding, documented here rather than silently corrected.
  Changes made:      scripts/doorway/integrity.py: create_readme() re-verifies target.exists()
                     before writing; no-op (no overwrite, no repair counted) if a README is
                     genuinely present. scripts/doorway/doorway.py: Option C's escalation
                     condition changed from `repairs > 0` to any non-empty `missing_readme`,
                     since fix (a) means a stale-but-present README no longer counts as a
                     "repair" -- found via a real failing test before the fix was written, not
                     assumed necessary. scripts/tests/test_doorway.py (new): 4 direct tests
                     against real temp-workspace fixtures -- content preservation, phantom
                     self-correction with no other repair, escalation still fires on a genuine
                     repair, no escalation when nothing changed (perf regression guard).
                     manifest/SUITE_HEALTH.md: ACTIVE ADVISORY superseded with a RESOLVED line.
  Tests:             4/4 new tests passing (scripts/tests/test_doorway.py); full suite 295/295
                     (was 291 before this ticket's remediation).
  Linter:            0 CRITICAL (python3 scripts/suite/lint_workflows.py --workspace . --quiet).
  Deferred:          The ticket's own Section 5 "Secondary" item (breadcrumb.py proposal-
                     delimiter mismatch) -- explicitly named there as a separate LOW ticket if
                     not bundled, not bundled here. The sibling ticket
                     20260705_sentinel-doorway-redesign_workflow.md's remaining Phase 0 items
                     (LINT_EXCLUDE_FILES, doorway skip-list, breadcrumb.py) are that ticket's own
                     separate, still-open scope -- confirmed via helpdesk-tickets.md's new Step
                     4d (Stage 6 Task 6.1, this same stage): a sibling ticket closes independently
                     on its own merit; this closure does not require that one to close too.
```

**Phylogeny Disposition**: `NO TRANSFER` — this remediation is contained within `scripts/doorway/`'s own two files (`integrity.py`, `doorway.py`); the fix pattern (a self-heal write function must re-verify its own precondition against live disk state immediately before a destructive write, not trust a possibly-stale caller-supplied signal) did not move between independent workflow `.md` protocol files, which is what this suite's Phylogeny mechanism tracks.

---
**Status**: **REMEDIATED (Option C verified; a more severe, previously-unknown data-loss defect in the same self-heal path found via independent review and fixed alongside it; see Remediation Record above)**
**Verification**: Remediation Record above. 4/4 new tests passing, 295/295 full suite, 0 CRITICAL lint. SUITE_HEALTH advisory superseded (`grep -c "ACTIVE ADVISORY" manifest/SUITE_HEALTH.md` → 0).

---
*Originally filed by Grok (Grok Build session, 2026-07-05). Closed by Claude Code, Sovereign Redesign Cluster Stage 6, 2026-07-07 — native path, no Grok involved in the remediation.*