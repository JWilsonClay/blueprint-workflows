# Helpdesk Ticket: Vendor State-Root Relocation Stranded 6.2 GB of Primary Agent History — Intact, Irreplaceable, and Invisible to the Live Install

**To**: Senior Architect of Workflows
**From**: Claude Fable 5 — `blueprint-workflows` Senior Architect session (sibling filed under the Antigravity Restoration Cluster meta ticket)
**Date**: 2026-08-13
**Subject**: The 2026-08-13 Antigravity release reads a fresh state root (`~/.gemini/antigravity-ide/`) and performed no visible migration of the prior root's agent history. 5.6 GB of `brain/` state (103 entries, Feb–Aug 2026) and 605 MB of `conversations/` (written up to ~40 minutes before the transition) remain intact at `~/.gemini/antigravity/` but are unreachable from the running IDE. Unlike the workflow pointers (derived artifacts, regenerable from `claude-commands/` at will), this history is primary data with no other copy anywhere.
**Urgency**: HIGH (user-valued data invisible to the live install; not CRITICAL — the data is stable and at rest on disk, not at risk, so long as the old root is preserved)
**Root Cause Type**: SUBSTANTIVE-LOGIC
*(Classification note: external-substrate incident — no suite workflow's structure is at fault, so `/harden-workflow` does not apply; closes via the direct-remediation path with a Remediation Record.)*
**Phylogeny Disposition**: PENDING
**Meta**: Sibling of `20260813_secretary_workflow.md` (Antigravity Restoration Cluster) — closes independently, on its own evidence, per /helpdesk-tickets Step 4d.

---

## 1. Executive Summary

The user updated Antigravity on 2026-08-13 and found their conversation history gone from the IDE — which, in the user's words, "sort of upset me," and reasonably so. It is not gone: the new release created a fresh state root under a new installation identity and left the old root — months of agent brain state and conversation history — intact but unread. The user's workflow pointers, stranded by the same rename, are tracked by the meta ticket and are trivially regenerable; this ticket exists because the history is not. It is the only asset in the incident that cannot be rebuilt from canonical sources.

## 2. Root Cause Analysis: "Other — vendor state-root relocation without data migration"

Not a named Sovereign Suite failure class: no workflow misbehaved, and no suite structure could have prevented a vendor's updater from abandoning its own data directory. Filed nonetheless because the suite's mandate now includes repairing this surface (explicit user direction, 2026-08-13), and because the *detection* gap that let the stranding pass silently is ours — that half is the meta ticket's Section 2 (Ghost Logic, delivery-surface variant) and is not restated here.

- **The How**: The new install binds to `~/.gemini/antigravity-ide/` (installation ID `de8d6dce-…`, created 16:32) and immediately began accumulating fresh, divergent state (1 brain entry, 35 MB of conversations by the same evening). The prior root (`~/.gemini/antigravity/`, installation ID `76990fbf-…`) took its last writes 16:14–16:23 and has not been read since. No migration artifact, import log, or copied data appears anywhere under the new root.
- **The Why** (hypothesis, explicitly unconfirmed): the updater either does not migrate state by design, or attempted migration and failed — `~/.gemini/antigravity-ide/crashes/` holds three crash logs stamped 16:40–16:45, the new IDE's first ~15 minutes. All three are zero-byte, so the cause is not recoverable from them; they are noted here so a future agent neither misses them nor over-reads them.

## 3. Forensic Evidence

- **Two distinct installation identities**: [old root installation_id](file:///home/jwils/.gemini/antigravity/installation_id#L1-L1) vs. [new root installation_id](file:///home/jwils/.gemini/antigravity-ide/installation_id#L1-L1)
  *Evidence: `76990fbf-223b-4270-b76c-4bdb15c421d6` vs. `de8d6dce-1b3b-462a-9741-7e91a58041a4` — the new root is a different installation identity, not a re-homed continuation of the old one. Any naive state copy therefore crosses an identity boundary that the vendor's own data may be keyed against. (This same measurement is what invalidated `DevJournal.md:33`'s "same installation ID" learning — see the meta ticket, Section 2.)*
- **The running program, confirmed — and confirmed absent from the orphaned root**: [antigravity-ide.desktop, Exec line](file:///home/jwils/.local/share/applications/antigravity-ide.desktop#L5-L5)
  *Evidence: `Exec=/home/jwils/.local/share/antigravity-ide/bin/antigravity-ide` — the live IDE binary. The old `antigravity` deb (v1.23.2) is dpkg status `rc` (removed, remnants only). The orphaned root is data only; no program repair is possible or needed there, and its 17 MB `bin/` is runtime-downloaded helper tooling, present in all three state roots.*
- **The stranding, as the meta ticket measured it**: [20260813_secretary_workflow.md — Executive Summary](file:///home/jwils/blueprint-workflows/helpdesk-tickets/20260813_secretary_workflow.md#L16-L16)
  *Evidence: the meta ticket's finding for the same transition — "The pointers were stranded, not lost." This ticket extends that finding to the state mass behind the pointers, which the meta ticket's measured-surface table did not inventory.*

**Measured inventory of the orphaned root, 2026-08-13** (commands run this session, not inferred):

| Asset (`~/.gemini/antigravity/`) | Size | Last written | Replaceability |
|---|---|---|---|
| `brain/` (103 entries) | **5.6 GB** | 2026-08-10 | **None — primary data, no other copy exists** |
| `conversations/` | **605 MB** | **2026-08-13 15:54** | **None — primary data, no other copy exists** |
| `implicit/` | 83 MB | 2026-07-27 | None known; operational value unclear |
| `browser_recordings/` | 51 MB | 2026-07-16 | None; archival value only |
| `global_workflows/` (34 files) | 148 KB | 2026-05-25 | **Full — regenerable from `claude-commands/`** (meta ticket scope, not this ticket's) |
| `artifacts/`, `code_tracker/`, `annotations/`, `playground/`, misc | ~3.5 MB | various | Partial |
| `manifest/`, `process_learnings/`, `knowledge/` | ~30 KB | May–Jun 2026 | Suite-side snapshots; canonical versions live in the repo |
| `mcp_config.json` | symlink | — | Not stranded — targets `~/.gemini/config/mcp_config.json`, outside the orphaned root |

## 4. Remediation: Preserve First, Investigate Second, Migrate Only on Evidence

Ordered so that every step is reversible and the irreplaceable asset is never the experiment.

1. **Preserve (standing order, effective at filing)**: `~/.gemini/antigravity/` is the backup — the role `antigravity-backup/` used to fill and no longer does. Nothing writes into it and nothing deletes from it for the life of the Antigravity Restoration Cluster. RECOMMENDED, user decision on destination: one true offline copy of `brain/` + `conversations/` (~6.2 GB, `tar` or `cp -a`), so that the backup is no longer also the only copy.
2. **Investigate the vendor path before building one**: (a) check the new IDE's own surface for an import/migration affordance (settings, first-run flow, release notes); (b) watch whether a subsequent point release performs the migration the 2026-08-13 release did not — three first-15-minutes crash logs leave open that it was attempted; (c) search vendor documentation and issue trackers for the `antigravity` → `antigravity-ide` state-root rename. A vendor-provided migration beats anything hand-rolled across an undocumented identity boundary.
3. **Only if step 2 yields nothing**: a controlled, user-approved experiment — IDE closed; the NEW root backed up in full first; old `brain/` + `conversations/` copied in additively (no-overwrite semantics); IDE launched and observed; full rollback from the backup on ANY anomaly. Never run against the only copy of anything, in either direction.
4. **Accept the honest closure if it comes to that**: "not safely migratable by us" is a legitimate Remediation Record. In that outcome, the old root is documented as a permanent read-only archive, the offline-copy decision from step 1 is recorded, and the cluster's delivered repair is the surface restoration alone.

## 5. Recommendation to Senior Architect

The surface registry the meta ticket's step 5 will create should record, for every registered surface and state root, a **data-class field: DERIVED (regenerable from a canonical source) vs. PRIMARY (no other copy exists)** — and the delivery-surface check being added to `/secretary` Phase 1 should report a stranded PRIMARY root as its own named condition, not as a footnote to a pointer count. This incident's cost asymmetry was exactly inverted from what the suite could see: the 148 KB of pointers were fully replaceable, and the 6.2 GB behind them was not. A health pass that knows which class it is looking at reports "primary data stranded" the day a vendor renames a root — instead of the user discovering it by missing their own conversations.

---
**Status**: **OPEN**
**Verification**: PENDING — closure requires either (a) the history reachable from the live install via a vendor or verified-safe migration, with the old root still intact afterward, or (b) a Remediation Record documenting the preserve-don't-migrate outcome, the offline-copy decision, and the old root's archive status.

---
*Signed,*
**Claude Fable 5**
*(Senior Architect of Workflows — `blueprint-workflows` session, 2026-08-13)*
