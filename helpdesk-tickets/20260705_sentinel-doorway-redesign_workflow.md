# Helpdesk Ticket: Sentinel / Doorway Protocol Re-Engineering — README Web Fails Agent Economics; Substrate Index Needed

**To**: Senior Architect of Workflows
**From**: Grok (Grok Build inaugural session — architectural discussion with user 2026-07-05; user resetting model/context; requires full re-design, not patch)
**Date**: 2026-07-05
**Subject**: The Doorway "breadcrumb web" (per-directory README.md + MANIFEST auto-sync) does not function as intended for real agents — lazy agents rationally read only `FOLDER_OWNERSHIP.md`; READMEs duplicate ownership, populate unevenly, trigger false hygiene signals, and collide with workflow infrastructure. Request full re-engineer of `/sentinel` + `scripts/doorway/` around a machine-readable substrate index and tiered requirements.
**Urgency**: HIGH (affects every workspace first `/sentinel` run; compounds with lazy-scan bug; blocks trustworthy zero-finding; creates linter CRITICAL in blueprint-workflows)
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING

---

## 1. Executive Summary

The Sovereign Doorway Protocol assumes agents will traverse a **distributed README web** (33+ files) for context, while `docs/FOLDER_OWNERSHIP.md` holds boundary sentences in one file. In practice — especially with token-conscious agents (user cited Gemini) — **only FOLDER_OWNERSHIP is read**. READMEs are mostly Doorway self-heal artifacts: template placeholders, ownership pointers back to FOLDER_OWNERSHIP, and occasionally a one-line BREADCRUMB — at the cost of N file reads, git noise, and hygiene checks that measure **file existence** not **context quality**.

This session exposed multiple coupled defects: inaugural scan false "new directory" signal, lazy-scan stale `has_readme` carry-over (separate ticket, Option C selected), `breadcrumb.py` `--- PROPOSAL` delimiter mismatch (only last entry applied on auto-apply), and `claude-commands/README.md` triggering workflow linter CRITICAL. The user and agent concluded the architecture needs **re-engineering**, not incremental patches. Preferred direction: **virtual web / physical index** — agents consume `doorway.py --output-json` or `.doorway/substrate_index.json`; FOLDER_OWNERSHIP remains canonical for boundaries; README materialization becomes optional.

**Relationship to existing ticket:** `20260705_doorway_lazy-scan-stale-readme_workflow.md` (LOW, Option C tactical fix) should be implemented as **Phase 0 stabilization** or folded into this redesign — do not treat Option C alone as architectural resolution.

---

## 2. Root Cause Analysis: "Hygiene Metrics ≠ Agent Context; Web Cost Dominates Value"

### Named patterns (adjacent)

| Pattern | How it manifests here |
|---------|----------------------|
| **Context Erosion** | Agents read FOLDER_OWNERSHIP once; skip 32 README BREADCRUMBs — rational token economics |
| **Hallucinated Success** (hygiene sense) | `has_readme: true` + placeholder template treated as "breadcrumb web complete" |
| **Stale Snapshot Carry-Over** | Lazy-scan copies old `has_readme` — separate ticket |
| **Grade Fraud** (if mis-fix) | Adding Sovereign frontmatter to navigation README.md to silence linter |

### The How

1. **Doorway** (`scripts/doorway/`) scans workspace, compares to `.doorway/workspace_snapshot.json`, flags drift (`new`, `modified`, `unowned`, `missing_readme`).
2. **Self-heal** (`integrity.py`) creates `README.md` from template in every dir missing one.
3. **Sentinel Phase 1.5** expects agent to read `context_updates.log`, sample files, write agentic BREADCRUMB summaries, run `--auto-apply`.
4. **MANIFEST sync** (`manifest.py`) rebuilds "Root Directories (Auto-Synced)" link list from discovered READMEs.
5. **Auditor** (`auditor.py`) parses `docs/FOLDER_OWNERSHIP.md` for ownership; README presence is separate hygiene gate.
6. **Agents** read one ownership file; ignore README web unless workflow forces it.

### The Why

- The protocol optimized for **filesystem completeness** (every dir has README) over **agent ingestion economics** (one deterministic context payload).
- BREADCRUMB content lives inside HTML comment regions in scattered files — high friction for lazy agents.
- `compute_dir_hash()` is `.py`-only — README/breadcrumb changes invisible to incremental scan (feeds lazy-scan bug).
- INTERFACE / REQUESTS / WORKLOG channels designed in `breadcrumb.py` but **unused** in blueprint-workflows (0 populated INTERFACE tags except possibly scripts/README.md).
- No exclusion rules for special directories (`claude-commands/` is workflow canonical source, not navigation substrate).

---

## 3. Forensic Evidence

### 3a. Design intent (README web + BREADCRUMB)

- **Sentinel Phase 1.5 intent**: [claude-commands/sentinel.md#L168-L171](file:///home/jwils/blueprint-workflows/claude-commands/sentinel.md#L168-L171)
  *Evidence: "When an agent later ingests 5–30 READMEs... BREADCRUMB section... compact key:value format."*
- **README tag channels**: [scripts/doorway/breadcrumb.py#L8-L12](file:///home/jwils/blueprint-workflows/scripts/doorway/breadcrumb.py#L8-L12)
  *Evidence: BREADCRUMB, INTERFACE, REQUESTS, WORKLOG — only BREADCRUMB populated in practice.*
- **README template (minimal)**: [scripts/doorway/templates/README.md.template#L1-L12](file:///home/jwils/blueprint-workflows/scripts/doorway/templates/README.md.template#L1-L12)
  *Evidence: Ownership points back to FOLDER_OWNERSHIP; BREADCRUMB placeholder default.*

### 3b. FOLDER_OWNERSHIP as actual agent anchor

- **Canonical ownership (post-/document)**: [docs/FOLDER_OWNERSHIP.md#L5-L14](file:///home/jwils/blueprint-workflows/docs/FOLDER_OWNERSHIP.md#L5-L14)
  *Evidence: 10 one-line owner sentences; single-file boundary model.*
- **role.md session boundaries**: [claude-commands/role.md#L174-L175](file:///home/jwils/blueprint-workflows/claude-commands/role.md#L174-L175)
  *Evidence: Fresh agents read SUITE_HEALTH + open helpdesk tickets; FOLDER_OWNERSHIP implied via doorway/MANIFEST chain.*

### 3c. README web problems observed this session

- **Duplicative README in claude-commands**: [claude-commands/README.md#L1-L12](file:///home/jwils/blueprint-workflows/claude-commands/README.md#L1-L12)
  *Evidence: Doorway self-heal; not a slash command; causes linter CRITICAL.*
- **Linter treats all claude-commands/*.md as workflows**: [scripts/suite/lint_workflows.py#L94-L94](file:///home/jwils/blueprint-workflows/scripts/suite/lint_workflows.py#L94-L94)
  *Evidence: `glob("*.md")` with no exclude list.*
- **Lazy-scan carry-over**: [scripts/doorway/scanner.py#L107-L118](file:///home/jwils/blueprint-workflows/scripts/doorway/scanner.py#L107-L118)
  *Evidence: Stale child metadata copied when parent hash unchanged.*
- **Py-only hash**: [scripts/doorway/scanner.py#L35-L52](file:///home/jwils/blueprint-workflows/scripts/doorway/scanner.py#L35-L52)
  *Evidence: README creation does not invalidate branch cache.*
- **breadcrumb apply delimiter bug**: [scripts/doorway/breadcrumb.py#L127-L137](file:///home/jwils/blueprint-workflows/scripts/doorway/breadcrumb.py#L127-L137)
  *Evidence: Splits on `--- PROPOSAL` but `propose()` writes blank-line-separated entries — auto-apply applied only last entry until manual `update_readme()` loop in sentinel session.*
- **First-scan false "new"**: [scripts/doorway/auditor.py#L72-L76](file:///home/jwils/blueprint-workflows/scripts/doorway/auditor.py#L72-L76)
  *Evidence: `path not in previous_map` → all dirs new on inaugural scan.*

### 3d. Session outcomes (context for redesign scope)

| Event | Outcome |
|-------|---------|
| Inaugural `/sentinel` | 32 "new" dirs, 32 README repairs, 3 workflow recommendations |
| `/investigate` | HIGH confidence: bootstrap artifact, not rogue dirs |
| `/document` | FOLDER_OWNERSHIP + MANIFEST + Architecture propagated |
| Incremental rescan | 23 phantom `missing_readme` (lazy-scan) |
| `--full-scan` | `zero_finding: true`, 33/33 ingested |
| User discussion | README web poor agent ROI; prefer substrate index + tiered model |

### 3e. MANIFEST sync works but indexes the wrong abstraction

- **Auto-sync from README presence**: [scripts/doorway/manifest.py#L58-L69](file:///home/jwils/blueprint-workflows/scripts/doorway/manifest.py#L58-L69)
  *Evidence: MANIFEST links to README files, not substrate index entries.*

---

## 4. Remediation: Sentinel / Doorway Re-Engineering Program

**This is a multi-phase program.** Use `/implementation-plan` before large code changes. Closure requires Remediation Record + tests + updated workflows — not `/harden-workflow` alone (SUBSTANTIVE-LOGIC).

### Phase 0 — Stabilization (can ship before full redesign)

1. **Implement Option C** from `20260705_doorway_lazy-scan-stale-readme_workflow.md`: `doorway.py` auto-escalates to `--full-scan` when `metrics.repairs > 0` and phantom `missing_readme` persists.
2. **Fix `breadcrumb.py`**: align `propose()` log format with `apply_approved()` delimiter (`--- PROPOSAL`) OR change parser to split on blank-line folder blocks.
3. **Linter exclude**: `LINT_EXCLUDE_FILES = {"README.md"}` in `scripts/suite/models.py` — see triage handover ticket.
4. **Doorway skip list**: do not self-heal README in `claude-commands/` (and other configurable exclude dirs).

### Phase 1 — Architecture decision (user-approved direction)

**Preferred model: Option D — Virtual web, physical index** (from session discussion; user aligned with invert/canonical index thinking).

| Layer | Artifact | Consumer | Canonical? |
|-------|----------|----------|------------|
| Boundaries | `docs/FOLDER_OWNERSHIP.md` | Human + agent | **Yes** (human-edited) |
| Machine context | `.doorway/substrate_index.json` (new) | Agent + doorway CLI | **Yes** (generated) |
| Drift DNA | `.doorway/workspace_snapshot.json` | doorway / sentinel | Yes (generated) |
| Human index | `MANIFEST.md` Auto-Synced section | Human | Generated from index |
| Optional prose | `{dir}/README.md` | Human onboarding | **No** — materialized on demand |

**`substrate_index.json` schema (draft):**

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO8601",
  "workspace": "/absolute/path",
  "directories": {
    "scripts/doorway": {
      "owner_ref": "FOLDER_OWNERSHIP:scripts",
      "breadcrumb": "MODULE:scripts/doorway TYPE:scripts ...",
      "files_count": 11,
      "subdirs": ["data", "templates"],
      "has_interface": false,
      "last_seen": "ISO8601"
    }
  }
}
```

**Agent protocol (new default):**
```bash
python3 scripts/doorway/doorway.py --workspace PATH --output-json
# OR read .doorway/substrate_index.json directly
```
Single call replaces N README reads.

### Phase 2 — Zero-finding redefinition

**Current:** `zero_finding` requires no new/modified/deleted/unowned/missing_readme.

**Proposed tiered model:**

| Tier | Requirement | Gates zero-finding? |
|------|-------------|---------------------|
| Tier 1 | Top-level dirs in FOLDER_OWNERSHIP with non-placeholder sentences | **Yes** |
| Tier 1 | `substrate_index.json` fresh (matches snapshot) | **Yes** |
| Tier 2 | Per-subdir README.md exists | **No** (optional; warn only) |
| Tier 2 | BREADCRUMB populated | **No** (warn if index stale) |

Update `auditor.py`, `recommender.py`, `sentinel.md` routing table accordingly.

### Phase 3 — `/sentinel` workflow rewrite

1. **Phase 1e (interim — may merge with Option C):** post-repair full-scan reconciliation.
2. **Replace Phase 1.5 README walk** with:
   - Generate/update `substrate_index.json` from scanner map + ownership + optional agent enrichment pass on *index entries* not *N files*.
   - Optional `--materialize-readmes` flag for human/export; default off.
3. **Inaugural scan detection:** if `previous_map` empty, suppress SEQ-SUBSTRATE-HEALTH "new directories" routing OR tag as `[BOOTSTRAP]` in report (informational only).
4. **Update STRICT RULES** and integration map for triage/investigate/document routing changes.
5. **SUITE_HEALTH advisory lifecycle:** document pattern for ACTIVE ADVISORY bullets tied to open tickets (this session's precedent).

### Phase 4 — Engine changes (`scripts/doorway/`)

| Module | Change |
|--------|--------|
| `scanner.py` | Include README.md in hash OR stat README on carry-over; fix stale metadata |
| `auditor.py` | Tiered missing_readme; parse enriched FOLDER_OWNERSHIP if Option B hybrid |
| `integrity.py` | Configurable `README_EXCLUDE_DIRS`; optional materialize |
| `manifest.py` | Sync from substrate_index not README glob |
| `breadcrumb.py` | Deprecate or repurpose as index entry writer |
| `doorway.py` | Emit substrate_index; Option C auto-escalation; CLI flags |
| `tests/` | Inaugural scan, lazy-scan, index freshness, tiered zero-finding |

### Phase 5 — Documentation & agent onboarding

1. Update `CLAUDE.md`, `role.md` session boundaries: agents read FOLDER_OWNERSHIP + doorway JSON, not README web.
2. Update `PROCESS_LEARNINGS.md` or DevJournal with "FOLDER_OWNERSHIP wins agent economics" lesson.
3. **On closure:** supersede/remove SUITE_HEALTH lazy-scan ACTIVE ADVISORY (per lazy-scan ticket §4.5).
4. **On closure:** update or supersede any agent note added for workaround — user requirement from session.

### Phase 6 — Alternative options (documented for architect choice)

| Option | Summary | Trade-off |
|--------|---------|-----------|
| **A** | substrate_index.json canonical; README optional export | **User lean** — clean agent protocol |
| **B** | Enrich FOLDER_OWNERSHIP lines with breadcrumb fields | One-file for lazy agents; grows ownership file |
| **C** | Two-tier README requirement (top-level only) | Minimal change; subdir noise reduced |
| **D** | Virtual web (index + JSON API) | Best separation; more engineering |

**User preference stated:** Option C for lazy-scan tactical fix; **Option A/D for architectural redesign** (substrate index + engine-owned context).

### Verification criteria (closure gate)

- [ ] `pytest` doorway suite green (new tests for index, tiered zero-finding, inaugural bootstrap)
- [ ] Inaugural scan on fresh workspace: no false P0 `/investigate` routing for established dirs
- [ ] Incremental scan after self-heal: no phantom `missing_readme` without manual `--full-scan`
- [ ] `lint_workflows.py`: 0 CRITICAL (README exclude or no README in claude-commands)
- [ ] Agent can contextualize workspace from FOLDER_OWNERSHIP + `--output-json` in one session-start pass
- [ ] `sentinel.md` updated; content_hash recomputed
- [ ] SUITE_HEALTH ACTIVE ADVISORY superseded
- [ ] Remediation Record filed; Phylogeny Disposition resolved
- [ ] Consider closing or merging `20260705_doorway_lazy-scan-stale-readme_workflow.md`

---

## 5. Recommendation to Senior Architect

Establish a **Doorway Design Invariant** in suite governance:

> **Agent context is delivered by the engine (JSON index + ownership file), not by filesystem cardinality (N × README.md).** Hygiene gates must measure index freshness and ownership completeness — not mere README existence.

This prevents recurrence across all workspaces using `/sentinel`. The README web can remain as an optional human-facing materialization layer — analogous to how HTML is generated from a database, not the source of truth.

Long-term: add `scripts/doorway/` to mandatory session-start tooling alongside `lint_workflows.py` — `doorway.py --context-only` emits the agent handover payload without full drift report noise.

Consider `/triage` trigger: "inaugural doorway scan on workspace" → route to investigate bootstrap, not document hygiene.

---

**Status**: **OPEN**
**Verification**: PENDING — `/implementation-plan` produced; Phases 0–5 executed; verification checklist in Section 4 complete; Remediation Record attached; sibling lazy-scan ticket disposition documented.

---

## 7. Provenance Note (2026-07-07, Sovereign Scaling Cluster) — partial progress, NOT a closure

While investigating a user question about README breadcrumb cleanup, this ticket's Phase 0 §1 item ("Doorway skip list") was found to have been only partially addressed (a two-directory hardcoded exclude list, not the "materialize on demand, default off" model this ticket's Phase 1 Option A/D actually calls for). That gap is now closed:

- `IntegrityManager.autoheal_enabled` (default `False`) added; `create_readme()` no longer fires by default anywhere. `DoorwayContextualizer.readme_autoheal` passthrough threaded explicitly. 6 tests (4 updated to opt back in for their own regression scenarios + 2 new proving the default) — see `scripts/doorway/integrity.py`, `scripts/doorway/doorway.py`, `scripts/tests/test_doorway.py`.
- Existing breadcrumb README files removed from the workspace (working tree + normal `git rm`, not a history rewrite).

**Also found, worth recording here since it changes this ticket's own premise slightly:** `doorway.py`'s module docstring already carries a "Doorway Design Invariant" note (added under Pillar 1, PR 01-06) stating context should come from `substrate_index.json`, not README cardinality — and `substrate_index.json` emission already exists (PR 01-01). So this ticket's Phase 1 preferred direction (Option A/D) was *partially* built under a separate initiative (Pillar 1) before this ticket was ever addressed directly — the JSON index exists; what was missing was turning off the old README behavior to match, which is now done.

**What remains genuinely open, unchanged:** Phase 2 (tiered zero-finding redefinition), Phase 3 (`/sentinel` Phase 1.5 rewrite — still describes a README walk that no longer reflects actual behavior), Phase 4 (`scanner.py`/`auditor.py`/`manifest.py`/`breadcrumb.py` changes), Phase 5 (documentation/onboarding updates), and the verification checklist in Section 4. This is real, substantial, well-specified work — folded into `tasks.md` (repo root) Phase 8 as a strong candidate for this session's new Gemini single-engineer delegation pilot, precisely because it's already this well-specified. Not closed. Do not treat this note as resolving anything beyond the two bullets above.

*Noted by,*
**Claude**
*(Session Agent — Senior Architect of Workflows role, 2026-07-07)*

---

## 8. Execution-Readiness Assessment (2026-07-07, later same day, post-Verification-Spine campaign)

**Direct answer to the question this ticket's §4 note (line 251) left open**: with the Verification-Spine campaign now complete (9 real Honest-Design Discipline + engine-build cycles, `tasks.md` Phases 4-5) and the Gemini delegation pattern proven twice (Phase 1 full pilot, tasks 2.5a/2.7 mechanical-apply), this ticket's remaining work was re-checked directly against `/execute-build` Phase 2's own observability bar ("a phase where some tasks lack acceptance criteria is underspecified... HALT and ask the user to clarify") — not assumed ready because it "looks well-specified."

**Verdict: NOT YET READY for direct Gemini handoff.** Unlike Phase 1 (Quick Wins) or the STRICT RULES compression tasks, this ticket's remaining phases contain real, unresolved design judgment, not just mechanical execution of an already-fully-decided change:

- **Phase 2 (Zero-finding redefinition)** is the closest to ready — concrete tiers, named files (`auditor.py`, `recommender.py`, `sentinel.md`).
- **Phase 3 item 5** ("document pattern for ACTIVE ADVISORY bullets") names no concrete file or content — underspecified by `/execute-build`'s own gate.
- **Phase 4**'s `auditor.py` row is conditional ("if Option B hybrid") on an option the ticket's own §Phase 6 lists as a documented-but-undecided alternative to the stated preference (A/D) — a live conditional branch is exactly the ambiguity `/execute-build` Phase 2 would legitimately HALT on.
- **Phase 3 item 1** ("Phase 1e — interim — may merge with Option C") is explicitly tentative in its own wording.

**This is not a rejection of the work — it is the same finding this campaign made repeatedly this session**: real, valuable, but requiring a Claude design-tightening pass (resolving the Option B conditional, writing a concrete Phase 3 item 5, converting "may merge" into a decided sequencing) before it is honestly ready to hand to Gemini. That pass has not been done as part of this note — doing so is real, separate work, not a quick addendum, and is being flagged rather than rushed.

**Recommendation**: if this is prioritized as the next delegation target, the next step is a Claude pass converting this ticket's §4 into a proper `implementation-plan.md`/`tasks.md` phase pair (per `templates/plan/`), resolving every conditional/tentative item into a single decided path, before any Gemini invocation — mirroring exactly how `tasks.md` Phases 4-5 were built this session before their own mechanical-apply tasks were staged.

---

## 6. Handover Context (for incoming agent — read if no conversation history)

**Workspace:** `~/blueprint-workflows` — Sovereign Workflow Suite (32 slash commands in `claude-commands/`, symlinked to `~/.claude/commands/`).

**This session (Grok Build inaugural, 2026-07-05):**
- User new to Grok Build; invoked `/sentinel`, `/investigate`, `/document`, `/quality`, `/triage`.
- `/personality` + `/role` active; no-praise directive; user will reset model after ticket filing.

**Files modified this session (governance):**
- `docs/FOLDER_OWNERSHIP.md`, `MANIFEST.md`, `governance/Architecture.md`, `README.md` (root), `DevJournal.md`, `manifest/SUITE_HEALTH.md` (ACTIVE ADVISORY), `.workflow_state/receipts/DOCS_RECEIPTS.md`

**Git state at handover:** ~30 status entries (2 modified, 28 untracked READMEs + governance). Not committed.

**Read first:**
1. `helpdesk-tickets/20260705_triage-session-handover_workflow.md` (work queue)
2. This ticket
3. `manifest/SUITE_HEALTH.md`
4. `helpdesk-tickets/20260705_doorway_lazy-scan-stale-readme_workflow.md`

**Do not:**
- Add Sovereign frontmatter to `claude-commands/README.md` (grade fraud)
- Route to `/document` on phantom `missing_readme` without `--full-scan`
- Treat first-scan "32 new directories" as architectural crisis without checking git history

---
*Signed,*
**Grok**
*(Session agent — Grok Build inaugural blueprint-workflows session)*

---

**[PROVENANCE NOTE — INJECTED 2026-07-07, Claude Code, /nodelete — not a closure]**

This ticket's Phase 0 prerequisite is done: `IntegrityManager.autoheal_enabled` now defaults `False`
and `DoorwayContextualizer.readme_autoheal` passes through explicit `False` at the real call site
(`scripts/doorway/integrity.py`, `scripts/doorway/doorway.py` — 6/6 tests passing, 2 new tests proving
the default-off behavior directly). Breadcrumb README files across the tree were removed from the
working tree the same session (`implementation-plan.md` Phase 3 / `tasks.md` 3.1-3.4).

This ticket's Phase 1-6 substrate-index architecture (the actual redesign this ticket asks for) is
**not built** — folded into `implementation-plan.md` Phase 8 as a delegation-pilot candidate, not yet
selected or scheduled there.

This session's own governance artifacts (`MANIFEST.md`, `governance/Architecture.md`, root
`README.md`) — listed above under "Files modified this session" — are still present, still
uncommitted, exactly as this ticket's handover left them. They were deliberately left out of this
session's own commit (they're this ticket's unresolved scope, not this session's work) rather than
swept in or deleted. Whoever picks up this ticket's Phase 1-6 work should treat those three files as
the starting substrate, not stray files to clean up.