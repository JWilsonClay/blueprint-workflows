---
description: "Small native DESIGN for PR 06-02 (doorway auto-escalation regression test + ticket close) — Sovereign Redesign Cluster Stage 6 end-to-end pipeline vehicle: sentinel briefing -> native design -> native build -> hygiene marking -> nodelete --archive, on a genuinely new, real target"
---

# DESIGN: Doorway Option C Auto-Escalation — Regression Test + Ticket Closure

**Author:** Claude Code, via `/design-orchestrator`'s native path (Phase 0-5, no Grok involved) — Sovereign Redesign Cluster Stage 6, Task 6.2 end-to-end pipeline vehicle
**Date:** 2026-07-07
**Status:** Draft, independently critiqued (see Independent Critique below)
**Governing:** `helpdesk-tickets/20260705_doorway_lazy-scan-stale-readme_workflow.md` (the open ticket this closes)

---

## [INTENT]

> `helpdesk-tickets/20260705_doorway_lazy-scan-stale-readme_workflow.md` — open since 2026-07-05, SUBSTANTIVE-LOGIC, describes a real Doorway lazy-scan defect (an incremental scan carries forward stale `has_readme: false` for a subtree whose parent's `.py`-only content hash didn't change, even after a README was created on disk inside it) and prescribes "Option C" (auto-escalate to a full scan when self-heal repairs occurred and phantom `missing_readme` persists) as the fix.
>
> **Investigation finding, not assumed from the ticket's own Status field:** Option C is already implemented — `scripts/doorway/doorway.py` lines 214-228, explicitly commented `# Option C auto-escalate (P1 stabilization, pr-01-00, PILLAR_01 §4.4)`. It shipped as part of Stage 1/2's earlier P1 stabilization work, but the ticket itself was never closed to reflect this, and Stage 2's own Change Log (`test_doorway_auditor.py`'s creation) explicitly named the gap: "Option C's auto-escalation trigger (doorway.py) still has no dedicated test... worth a helpdesk ticket if it ever misfires" — it already has one; it just hasn't been acted on. The real remaining work is narrower than the ticket's original Remediation section implies: prove the existing logic with a direct regression test, supersede the live SUITE_HEALTH advisory, and close the ticket with an honest Remediation Record — not implement Option C from scratch.
>
> Marked /nodelete: not applicable (net-new small DESIGN).

---

## Investigation (evidence-based — real focus-plan Evidence Report + direct code reads, not assumption)

- **Primary payload (focus-plan Evidence Report, run live this session):** N/A for this narrow a change — the investigation was done via direct, cited code reads (below) rather than a plan-anchor scan, since there is no pre-existing plan document describing this specific fix; the ticket itself is the intent anchor.
- **Sentinel briefing (doorway --context-only, run live this session, Stage 6 Task 6.2):** `zero_finding: True` on the second run (the first run of this same session reported `False`, correctly reflecting genuine, real drift from Stage 5's new `scripts/plan/` and `templates/` directories not yet registered in the snapshot — the scan itself registers them; not a bug, the expected first-scan-after-new-directories behavior).
- **Direct code read — `scripts/doorway/scanner.py` (full file, 135 lines):** confirms the root cause exactly as the ticket describes. `compute_dir_hash()` (L49-66) hashes only `*.py` files. `scan()`'s carry-over branch (L122-132) copies forward `previous_map` entries verbatim for any subtree whose parent hash didn't change, without re-statting `README.md` on disk for those carried-over children specifically. A directory with zero `.py` files (confirmed live: every directory in this repo's own sentinel briefing this session shares the identical empty-input SHA-256, `e3b0c442...`) never re-triggers recursion into its children via hash comparison, so a README created 2+ levels below such a directory is invisible to an incremental scan indefinitely.
- **Direct code read — `scripts/doorway/doorway.py` `run()` (L164-310):** confirms Option C's auto-escalation (L214-228) is real, live code: `if (not full_scan and self.metrics.get("repairs", 0) > 0 and drift.get("missing_readme")): ... re-scan with full_scan=True ... escalated = True`. Confirmed no dedicated test exists (`grep -rl "escalat" scripts/tests/` → no matches). Confirmed the ticket's Item 3 (an interim `/sentinel` Step 1e workaround) was never added (`grep "Step 1e" claude-commands/sentinel.md` → no matches) — consistent with Option C having shipped directly rather than needing an interim guard first.
- **Negative Space Scan:** is there a reason this was never tested? Checked Stage 2's own Change Log (`claude-commands/execute-build.md`... no — `scripts/tests/test_doorway_auditor.py`'s creation context, Sovereign Redesign Cluster Stage 2 Task 2.3): the gap was named and deliberately deferred as disproportionate for that stage ("verifying it properly requires simulating incremental-scan carry-over state precisely, judged out of proportion for this stage"). This DESIGN is exactly that deferred follow-up, now proportionate as Stage 6's real end-to-end target.
- `manifest/SUITE_HEALTH.md:23` — confirmed live: the `[ACTIVE ADVISORY 2026-07-05 — ticket 20260705_doorway_lazy-scan-stale-readme...]` bullet is still present, still says "Permanent fix tracked in the open ticket," and explicitly states "On ticket closure: this bullet MUST be removed or superseded."

## Scope & Boundaries

**In scope:**
- A direct, real regression test for `doorway.py`'s Option C auto-escalation logic (`scripts/tests/test_doorway.py`, new file — no existing top-level `doorway.py` test file exists; `test_doorway_auditor.py` covers `auditor.py` specifically, a different module).
- Superseding the `manifest/SUITE_HEALTH.md` ACTIVE ADVISORY per the ticket's own Section 4 Step 5 closure requirement.
- Closing `helpdesk-tickets/20260705_doorway_lazy-scan-stale-readme_workflow.md` with a Remediation Record, per `helpdesk-tickets.md` Phase 4 (SUBSTANTIVE-LOGIC path).

**Out of scope (named, not silently dropped):**
- The ticket's Section 5 "Secondary" item (`breadcrumb.py`'s proposal-delimiter mismatch) — explicitly flagged in the ticket itself as "separate LOW ticket if not bundled here." Not bundled here; remains a candidate for its own future ticket if not already filed.
- The sibling ticket `20260705_sentinel-doorway-redesign_workflow.md`'s other Phase 0 items (breadcrumb.py delimiter fix, `LINT_EXCLUDE_FILES` for README.md, doorway skip-list for `claude-commands/`) — that ticket has real, separate remaining work beyond Option C (confirmed via direct read, Stage 6 Task 6.1) and is not closed by this DESIGN. Only the lazy-scan ticket closes here.
- Any change to `scanner.py`'s or `doorway.py`'s actual logic — Option C is already correct and live; this DESIGN proves it, it does not modify it.

## Build Ingestion Manifest

- **Intent Anchor:** this DESIGN's own `[INTENT]` section above, and the governing ticket's own Section 4.
- **Gaps & Divergences:** the ticket's Remediation Section 4 items 1 and 3 are already satisfied (Option C live; no interim guard was needed) — this DESIGN's actual PR Plan is narrower than the ticket's original prescription, and that narrowing is the DESIGN's own primary finding, stated plainly rather than padded to match the ticket's original scope.
- **Verification:** live code reads (cited above) + this DESIGN's own PR Plan's test, to be run for real via `/execute-build`.
- **Native Gates Mapping:** this DESIGN's own `tasks.md` (generated by `/implementation-plan` via `/execute-build`'s Native Execution Trigger) requires the Completion Marking sub-pass (Stage 5) to independently confirm before `/nodelete --archive` may act on it — this DESIGN is itself Stage 6's live proof that the full chain coheres end to end.
- **Substrate Hygiene:** `zero_finding: True` (confirmed live this session, second sentinel run); no `/divergence --convergence` run (scope too narrow — one new test file, two doc edits, no dead-substrate risk).

## Acceptance Criteria (measurable)

1. A direct, real test exists proving Option C's auto-escalation fires under the exact carry-over scenario the ticket describes (stale `has_readme: false` snapshot entry, real README on disk, incremental scan without `--full-scan` self-corrects) — not a smoke test, an assertion against the documented failure shape.
2. The same test proves the *negative* case too: when no repairs occurred, escalation does NOT fire (avoiding a performance regression where every scan silently becomes a full scan).
3. `manifest/SUITE_HEALTH.md`'s ACTIVE ADVISORY bullet is replaced with a `[RESOLVED 2026-07-07 — CLOSED_20260705_doorway_lazy-scan-stale-readme_workflow.md]` line, verified via `grep "ACTIVE ADVISORY" manifest/SUITE_HEALTH.md` → 0 matches.
4. The ticket is renamed to `CLOSED_...` with Phylogeny Disposition resolved and a Remediation Record attached, per `helpdesk-tickets.md` Phase 4 (SUBSTANTIVE-LOGIC path, Step 4d not applicable — this is a sibling ticket closing independently, not the meta ticket itself).
5. Full suite still passes; 0 CRITICAL lint.

## PR Plan

**PR 06-02 (single, small): Doorway Option C regression test + ticket closure**
- Files: `scripts/tests/test_doorway.py` (new — direct test of the auto-escalation branch in `doorway.py`'s `run()`); `manifest/SUITE_HEALTH.md` (advisory supersession); `helpdesk-tickets/20260705_doorway_lazy-scan-stale-readme_workflow.md` → renamed `CLOSED_...` with Remediation Record.
- Dependencies: none (pure test addition + two doc closures, no other PR needed first).
- Description: implements this DESIGN's Acceptance Criteria 1-5 directly.

---

## Independent Critique (native path, no Grok — `/quality` Step 5 adversarial self-critique, per §15 Mock Trap guard)

**Critique 1:** Is testing `doorway.py`'s `run()` directly (rather than `scanner.py`'s `scan()` in isolation) the right test boundary? — Addressed: the bug is specifically about the *interaction* between `scanner.py`'s carry-over and `doorway.py`'s escalation decision (`self.metrics["repairs"]`, which `scanner.py` doesn't even compute — it's set elsewhere in `doorway.py`'s own self-heal step). A `scanner.py`-only test could prove the carry-over behavior exists but not that Option C actually catches it — the acceptance criteria specifically require proving the *fix*, which lives in `doorway.py`. Testing at the `run()` boundary, against real temp-directory fixtures (matching this suite's own established test convention — real files, not mocks), is the correct level.

**Critique 2:** Does closing this ticket without also fixing the sibling `sentinel-doorway-redesign` ticket's remaining items (breadcrumb.py, LINT_EXCLUDE_FILES, skip-list) leave things in a confusing half-done state? — Considered and rejected: `helpdesk-tickets.md`'s newly-added Step 4d (Stage 6 Task 6.1, this same stage) explicitly establishes that sibling tickets close independently, on their own merit — the lazy-scan ticket's own remediation is genuinely, fully complete once this PR lands; bundling in unrelated items from a different ticket to avoid "looking incomplete" would be scope creep, not rigor.

**Critique 3:** Is "the code already existed" itself suspicious — did Stage 1/2 actually build and verify Option C, or could this be an unverified code path that merely looks plausible? — Addressed directly by this DESIGN's own Acceptance Criteria 1-2: the regression test is the actual verification that was missing. If it fails, that is itself the finding (a Mock Trap risk avoided by testing rather than trusting the docstring's own confident description).

**Zero remaining open issues.** Ready for handoff via `/execute-build`'s Native Execution Trigger.

**[SUPERSEDED — see Independent Review Findings below. The self-critique above was genuine but incomplete: it defended the test's boundary and scope well, but never independently re-read `auditor.py`/`integrity.py` — the exact files implementing the self-heal mechanism this DESIGN is about — which is precisely where the real remaining issue lived. Preserved above per /nodelete rather than edited away; this is the honest record of what self-critique alone did and did not catch.]**

---

## Independent Review Findings + Resolution (genuinely independent subagent, not self-critique — [ADDED 2026-07-07, Sovereign Redesign Cluster Stage 6 Task 6.2])

Per `design-orchestrator.md`'s preferred method (a fresh subagent with no authoring context, per PILLAR_02 §15 and this cluster's own Stage 3 Task 3.2 precedent), this DESIGN was reviewed by a separate agent instance given only the DESIGN, the governing ticket, and the actual source files — not this document's own self-critique. It found what the self-critique missed:

**Confirmed accurate:** Option C's existence and location (`doorway.py` L214-228 at time of review), the scanner.py root-cause description, the "no interim Step 1e guard" finding — all independently re-verified against the code, not just re-stated from the DESIGN's own claims.

**Real defect found, independently re-verified by direct code read before any fix was made (not trusted on the subagent's word alone):** `integrity.py`'s `create_readme()` (L192-249 at time of review) had **no existence check** before `atomic_write()`-ing a generic template over the target path. Traced the call chain myself: `auditor.py`'s `audit()` (L112-117) calls `create_readme(path)` whenever `has_readme` is False — including the exact stale-carry-over false positive this ticket is about. Confirmed via direct reads of both files, independently of the subagent's report, before acting: **the original ticket's own "no data loss" framing (Urgency: LOW) was wrong.** A real README sitting inside a subtree whose parent has a stable, `.py`-file-only content hash was one incremental scan away from being silently overwritten with boilerplate.

**Fixed, then empirically verified — not assumed correct from reasoning alone:**
1. `integrity.py`'s `create_readme()` now re-verifies `target.exists()` before writing; no-ops (returns `False`, no repair counted) if a README is genuinely present.
2. Writing the real regression test (`scripts/tests/test_doorway.py`) surfaced a *second-order* interaction fix #1 alone didn't cover: since a stale-but-present README no longer counts as a "repair" once fixed, Option C's original `self.metrics.get("repairs", 0) > 0` escalation gate stopped firing for exactly the phantom-only scenario — confirmed via a failing test (`test_stale_readme_with_no_other_repairs_still_resolves`) before changing anything, not assumed. Fixed by escalating on any non-empty `missing_readme`, dropping the `repairs > 0` requirement (safe: excluded directories never populate `missing_readme` in the first place, so this cannot loop forever on an expected, permanent exclusion).
3. All 4 tests in `test_doorway.py` pass (content-preservation, phantom self-correction with no other repair, escalation still fires on a genuine repair, no escalation when nothing changed — the last one guards against a performance regression from over-escalating). Full suite: 295/295, 0 CRITICAL lint.

**Revised Acceptance Criteria (supersedes the original AC1-2, which the independent review correctly flagged as rubber-stampable — an escalation-only test could pass while data loss stayed invisible):**
1. ~~A direct, real test exists proving Option C's auto-escalation fires...~~ **Revised:** the test suite proves BOTH that real README content is never destroyed by a false missing_readme signal (the primary, higher-severity fix) AND that a phantom missing_readme entry still self-corrects within one or two scans even when no other genuine repair occurs (the escalation-condition fix) — not escalation behavior alone.
2. (unchanged) The same test proves the *negative* case: no escalation when nothing changed.
3-5. (unchanged, all met — see PR Plan below, now executed).

This is the concrete, real proof-point for why `design-orchestrator.md`'s independent-review requirement (Phase 3, PILLAR_02 §15) is load-bearing and not ceremonial: this specific defect was invisible to the producing agent's own self-critique and would have shipped a ticket closure that itself contained an unfixed, more severe version of the exact problem being closed.
