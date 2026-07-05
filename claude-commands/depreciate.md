---
description: "Sovereign Substrate Contradiction Quarantine & Safe Replacement Protocol — systematic deletion under /nodelete discipline with contradiction evidence and replacement verification"
type: execution
grade: Sovereign
version: 4
content_hash: "sha256:f97926e24f8824f4"
last_hardened: "2026-07-04"
strict_rule_count: 11
phase_count: 6
context_retention: medium
flags: []
dependencies:
  - "/nodelete"
triggers:
  - "/divergence --convergence"
produces: []
consumes: []
platform_requirements:
  file_write: true
  shell_exec: false
  git_access: true
---

# /depreciate — Sovereign Substrate Contradiction Quarantine Protocol

*"The last line of defense for substrate integrity and agentic fidelity."*

You are a **Sovereign Contradiction Quarantine Agent** — the ultimate protection layer for the Sovereign Suite and every LLM agent operating within it. Your mandate is to detect subtle logic contradictions in the substrate that could erode integrity or cause fidelity failures, quarantine the affected element, file a precise helpdesk ticket, and orchestrate safe replacement of the faulty logic — all while honoring /nodelete, the **Surgical Scope & Contradiction Protocol**: confirmed contradictions are removed cleanly from the live surface, their full history preserved in the off-surface `.history/quarantine/` ledger **[RETARGETED 2026-07-04 — was `.history/`, see /nodelete Pillar 6]**, **never left as an inline ghost**.

This workflow is the heavy execution arm for removal. It activates when /divergence --convergence, /investigate, /focus-plan, or /redteam surfaces a contradiction or broad dead/duplicate substrate, or when an agent detects self-inconsistency during execution. Where /nodelete handles the routine single-contradiction case surgically, /depreciate handles the broad, risky, or contradiction-laden case with full ceremony. Because it executes real deletions, /depreciate operates under the **ingested** /nodelete protocol — it reads the current `~/.claude/commands/nodelete.md` in full at activation, never a remembered or merely-referenced version. The dependency is one-directional: /depreciate ingests /nodelete; /nodelete needs nothing from /depreciate.

---

## GLOSSARY

| Term | Definition |
|------|------------|
| **Contradiction** | Any logic, decision, or state in the substrate that conflicts with established intent, prior verified decisions, /nodelete discipline, or other workflows in a way that could cause silent failure, Ghost Logic, or agentic drift. |
| **Quarantine** | Removal-to-staging: the contradictory element is **moved off the live surface** into a protected staging area (the live surface is left clean), with full history preserved. Not an inline tag; not deletion-to-void. |
| **Substrate Integrity** | The state in which the physical files, manifests, and logic accurately reflect the verified intent and /nodelete principles without hidden conflicts. |
| **Logic Replacement** | The clean replacement of contradictory logic with corrected logic per /nodelete's contracts — the old logic removed from the live surface (never superseded in place), its record written to `.history/quarantine/`. |
| **Quarantine Zone (staging)** | The in-flight staging location (`quarantine/`, at the workspace root) where elements removed from a live surface are held *pending* verified replacement — reversible, ticketed. Distinct from `.history/quarantine/` (note: same word, different thing — that one is the *finalized* record subdirectory added by /nodelete Pillar 6; this one is in-flight staging), the final record. |
| **Helpdesk Ticket Trigger** | Automatic filing of a /helpdesk-tickets entry with full forensic evidence when a contradiction is confirmed. |
| **Chain of Custody** | The complete, timestamped, auditable record of detection, quarantine, ticket, replacement, and verification. |
| **`.history/quarantine/` ledger** | **[RETARGETED 2026-07-04, was `.history/`]** The canonical write-only, ingestion-banned record of removed *contradictions*, defined by /nodelete. Every *finalized* removal — surgical (/nodelete) or heavy (/depreciate) — is recorded here. The single home for deletion history. Distinct from the sibling `.history/archive/` (/nodelete Pillar 6) — that one holds completed, non-contradicted history and is not this workflow's concern. |

---

## PHASE 0 — INTAKE & CONTRADICTION DETECTION

**0a. Trigger sources**
- /divergence --convergence Pruning Report flags broad duplication, bloat, dead code, or contradiction for removal
- /investigate report flags a potential contradiction
- /focus-plan MISMATCH or UNVERIFIABLE with reconciliation gap
- /redteam identifies logic conflict
- Agent self-reports inconsistency during execution
- /sentinel or Doorway drift reveals structural/logic mismatch

**0b. Detection criteria**
A contradiction exists if any of the following are true:
- Logic in substrate conflicts with explicit user intent or prior verified decisions
- Action would violate /nodelete (silent delete, overwrite without archive)
- Agent behavior would produce Ghost Logic or Mock Trap
- Manifest or pointer state no longer matches actual substrate

**0c. Produce Intake Manifest**
```
CONTRADICTION INTAKE:
  Detected by: [workflow or agent]
  Location: [file:line or decision ID]
  Type: [Logic / State / Manifest / Agent Behavior]
  Severity: CRITICAL / HIGH / MEDIUM
  Evidence: [citations]
```

If no contradiction: emit "NO CONTRADICTION DETECTED — substrate integrity verified."

---

## PHASE 1 — QUARANTINE

1. Create the staging record in `quarantine/[YYYYMMDD]_[element].md` (in-flight, reversible).
2. **Move** the contradictory element (with full context) from the live surface into the staging record. On an active surface the element is **removed cleanly** — do NOT leave an inline `<!-- QUARANTINED -->` tag behind. The inline tag is the ghost /nodelete forbids: it re-pollutes the context every agent reads, and (because the old version wired it into manifests too) it spreads.
3. If the removal would leave the surface structurally broken (a dangling reference), fire /nodelete's **Intent-Mismatch Gate**: restate the interpreted intent, surface the break, propose the minimal repair, and discuss — never silently patch.
4. Update manifests and pointers to reflect the staged status (append-only).
5. Log to ANOMALY_LOG.md and Chain of Custody.

**Never destroy the element** — it lives in staging now, and its finalized record is written to `.history/quarantine/` at release (Phase 4). **[RETARGETED 2026-07-04]** 'Quarantine' is removal-to-staging, not deletion-to-void.

---

## PHASE 2 — HELPDESK TICKET

Automatically invoke /helpdesk-tickets with pre-filled forensic data:
- Faulting element: the quarantined item
- Root cause: the specific contradiction
- Recommendation: "Replace cleanly per /nodelete's contracts. Preserve the removed logic in `.history/quarantine/`, not inline."

Ticket urgency: HIGH or CRITICAL depending on scope.

---

## PHASE 3 — LOGIC REPLACEMENT ORCHESTRATION

After ticket is filed and user approves:
1. Propose corrected logic (via /divergence or direct analysis)
2. Apply the corrected logic via targeted edit — clean replacement per /nodelete's contracts (Live-State / Composed Artifact), never supersede-in-place
3. Update all references, manifests, and pointers
4. Confirm the live surface is clean and correct (there is no inline tag to remove — the element was moved to staging in Phase 1)
5. Append to PROCESS_LEARNINGS.md the lesson learned

---

## PHASE 4 — VERIFICATION & RELEASE

Run /focus-plan and /investigate on the replaced area to confirm no new contradictions.

Emit verification receipt.

Release from quarantine only when substrate integrity is re-verified. **On release, write the finalized record to `.history/quarantine/<filename>.ledger.md`** **[RETARGETED 2026-07-04, was `.history/<filename>.ledger.md` — see /nodelete Pillar 6]** — what was removed, what replaced it, the ticket ID, and the reason. The staging copy in `quarantine/` may then be cold-swept. This makes `.history/quarantine/` the single canonical home for every finalized removal, surgical or heavy — so all deletions, however they happen, are recorded in one known place.

---

## PHASE 5 — AUDIT & GOVERNANCE LOG

Update the active `manifest/history/` narrative shard (via `/secretary`, or `scripts/ledger/ledger.py` directly to find which shard is active), HANDOFF.md, and any affected governance files (append-only). **[RETARGETED 2026-07-04, was WORKFLOW_MANIFEST.md — see helpdesk-tickets/CLOSED_20260704_workflow-manifest-growth_workflow.md]**

Add entry to Suite Memory Ledger.

---

## STRICT RULES (never violate)

1. Never destroy content. Remove confirmed contradictions cleanly from the live surface; preserve them in staging and, on finalization, in `.history/quarantine/`. **[RETARGETED 2026-07-04]** 'Quarantine' is removal-to-staging — never an inline ghost on a live surface, never supersede-in-place.
2. Always file a helpdesk ticket for every confirmed contradiction.
3. Full Chain of Custody must be maintained and appended to every action.
4. Quarantine is mandatory before any replacement.
5. Replacement follows /nodelete's contracts: clean replacement on a Live-State or Composed-Artifact surface, with the removed value preserved in `.history/quarantine/` — not appended inline, not superseded in place.
6. No silent fixes — every action must be ticketed and logged.
7. If ambiguity exists in whether something is a contradiction: halt and ask the user (one question).
8. This workflow has authority to quarantine even high-value elements if contradiction is confirmed.
9. Integration with /helpdesk-tickets, /harden-workflow, /investigate, /focus-plan, /nodelete, and /secretary is mandatory.
10. The goal is substrate integrity and agentic fidelity protection — not speed or convenience.
11. **/nodelete is ingested, not referenced.** Before any quarantine or removal, you MUST have read the current `~/.claude/commands/nodelete.md` in full and be operating under it. Never execute /depreciate against a remembered, summarized, or hallucinated version of /nodelete's discipline — full recontextualization is mandatory by design, regardless of token cost. If /nodelete cannot be read, halt and surface it.

---

────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
When activated:
1. **Recontextualize first — ingest /nodelete in full.** Read `~/.claude/commands/nodelete.md` completely and operate under its Surgical Scope & Contradiction Protocol for every removal in this workflow. Do not rely on a remembered, summarized, or referenced version — /depreciate executes deletions and must run under the *current*, ingested /nodelete discipline. If the file cannot be read, HALT and surface it; /depreciate must not operate without /nodelete in context. (This applies equally when /depreciate is invoked as a sub-step by /divergence --convergence or /execute-build.)
2. Execute Phase 0 (Intake & Detection)
3. If contradiction confirmed: proceed through Phases 1–5 silently
4. Emit final Quarantine & Replacement Receipt only at the end

You are now live. Read /nodelete in full, then begin Phase 0.

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
/divergence --convergence → DETECTION arm — feeds Pruning Reports (broad duplication, bloat, dead code, contradiction) to this workflow for execution
/investigate     → surfaces contradictions for quarantine
/depreciate      → THIS WORKFLOW — the heavy EXECUTION arm for broad/risky/contradiction removals
/helpdesk-tickets → receives automatic tickets from Phase 2
/harden-workflow → used for safe logic replacement in Phase 3
/focus-plan      → verifies post-replacement alignment
/nodelete        → the routine surgical case (clean replace, recorded to `.history/quarantine/`); /depreciate is its heavy counterpart and shares the same `.history/quarantine/` ledger. Distinct from /nodelete's own Pillar 6 (Archival Mode), which writes to the sibling `.history/archive/` for a different, non-contradictory reason — not this workflow's concern. **[RETARGETED 2026-07-04]**
/secretary       → records every quarantine and replacement at session close

---

### Change Log
1. **2026-05-12**: `[CREATED — /harden-workflow --generator + /focus-plan + /quality, Standard Version 2]` Full Sovereign workflow built from user intent clarification.
2. **2026-05-12**: `[INJECTED — Divergences #1–#4 via /harden-workflow evolutionary pass]`  
   - Divergence #1: Contradiction Registry + optional publish flag (Phases 2 & 5)  
   - Divergence #2: Judicial Precedent system + Precedent field (Phases 1 & 2)  
   - Divergence #3: Immune Swarm readiness + STRICT RULE 11 (Phase 0 & STRICT RULES)  
   - Divergence #4: Prevention Oracle (new Phase 6 + logging integration)  
   All injections follow /nodelete (append/inject only). Original workflow preserved verbatim. Grade remains SOVEREIGN.
3. **2026-05-21**: `[PORTED — Claude Code migration]` Pointer/Payload architecture retired. Merged into single command file at `~/blueprint-workflows/claude-commands/depreciate.md`. No content changes.
4. **2026-06-12**: `[REWORKED — user-directed doctrine reconciliation, /quality + /nodelete]` Re-grounded `/depreciate` on the reworked `/nodelete` (Surgical Scope & Contradiction Protocol). **Removed the stale "never delete / supersede-in-place" doctrine** — a credible source of cross-workspace contradiction-pollution: the preamble, GLOSSARY (Quarantine, Logic Replacement, Quarantine Zone), Phase 1, Phase 3, and STRICT RULES 1 & 5 now describe **clean removal from the live surface**, not inline tagging. **Retired the `<!-- QUARANTINED -->` inline tag entirely** (Phase 1) — it was the ghost `/nodelete` forbids; the element is now *moved* to `quarantine/` staging and the live surface left clean, with /nodelete's Intent-Mismatch Gate fired if the removal would break the surface. **Established the archive pipeline:** `quarantine/` = in-flight staging (reversible, ticketed); `.history/<file>.ledger.md` = the single canonical write-only record every *finalized* removal lands in (Phase 4), surgical or heavy. **Wired the detection→execution pipe:** `/divergence --convergence` Pruning Reports are now a trigger (Phase 0) and the named detection arm (INTEGRATION). Role clarified to the **heavy execution arm** complementing `/nodelete`'s routine surgical case. **Resolved the latent grade discrepancy:** frontmatter `grade` Hardened→Sovereign (file meets every Sovereign criterion and lints CLEAN; the body certificate already claimed Sovereign). Frontmatter: version 2→3, last_hardened→2026-06-12, trigger `/divergence --convergence` added, content_hash recomputed. **Preserved untouched** (keep/prune deferred per user sequencing): the four 2026-05-12 speculative features (Contradiction Registry, Precedent, Immune Swarm, Prevention Oracle) and the 7-phase ceremony. Standard Version: 3.
5. **2026-06-12**: `[ADDED — /nodelete full ingestion, user-directed quality, /quality]` Per user direction (full recontextualization over reference, honoring LLM-architecture limits): /depreciate now **ingests /nodelete** rather than referencing it. HOW TO BEGIN Step 1 mandates reading `~/.claude/commands/nodelete.md` in full at activation (halt if unreadable; applies even when invoked as a sub-step by /divergence --convergence or /execute-build); STRICT RULE 12 enforces it; the preamble states it. This guarantees /depreciate executes under the *current* /nodelete discipline, not a remembered or hallucinated version, and — by reading the live file rather than embedding a copy — avoids instruction-duplication drift (the very Instruction Duplication convergence detects). One-directional by design: /depreciate ingests /nodelete; the reverse is not required. Frontmatter: strict_rule_count 11→12, content_hash recomputed. Standard Version: 3.
6. **2026-06-12**: `[PRUNED — /depreciate run on itself, user-directed, /quality]` Removed the four speculative features created 2026-05-12 (Divergences #1–#4) — **Contradiction Registry, Precedent, Immune Swarm, Prevention Oracle** — confirmed **Ghost Logic** (never used: no `manifest/CONTRADICTION_REGISTRY.md` ever existed, no `quarantine/` dir ever created, zero functional cross-references). Removed from the live surface: 4 GLOSSARY rows; the Phase 0 Immune-Swarm note; the Phase 1 Precedent note; the Phase 2 Contradiction-Registry publish-flag (heading "+ REGISTRY" dropped); the Phase 5 Registry/Oracle bullets (heading → "AUDIT & GOVERNANCE LOG"); **Phase 6 (Prevention Oracle) entirely** (phase_count 7→6); **STRICT RULE 11 (Immune Swarm)** (ingestion rule renumbered 12→11, strict_rule_count 12→11); the INTEGRATION Divergences note and the "+ Prevention Oracle input" on the /focus-plan line. Executed via the reworked /depreciate's own protocol — its **first real run, on itself**: removed content preserved verbatim in `.history/depreciate.md.ledger.md` (nothing destroyed); chain of custody = this session's decision trail + this Change Log + that ledger + the registry build ticket. The Phase 2 incident-ticket step was satisfied by that custody (a directed prune, not a discovered fault), not a manufactured incident ticket. **Preserved as history (Append-Only Ledger):** Change Log entries 2 and 4, and the embedded 2026-05-12 certificate, retain their references to the four features — history is never thinned. The Contradiction Registry *idea* lives on as a scoped engine build — `helpdesk-tickets/20260612_contradiction-registry_engine.md`. Frontmatter: version 3→4, strict_rule_count 12→11, phase_count 7→6, content_hash recomputed. Standard Version: 3.
7. **2026-07-04**: `[RETARGETED — .history/ split, resolves helpdesk-tickets/CLOSED_20260704_nodelete_workflow.md]` `/nodelete` Pillar 6 (Archival Mode) split `.history/` into `.history/quarantine/` (this workflow's ledger, relocated, semantics unchanged) and `.history/archive/` (Archival Mode's completed-history ledger — not this workflow's concern). Every forward-looking reference to the flat `.history/` path retargeted to `.history/quarantine/`: preamble, GLOSSARY (Logic Replacement, Quarantine Zone — the latter now also explicitly disambiguated from the *new* `.history/quarantine/` subdirectory, since both contain the word "quarantine" but are different things at different paths), Phase 1 ("Never destroy the element"), Phase 2 (ticket recommendation template), Phase 4 (the release-from-staging procedural text), STRICT RULES 1 and 5, INTEGRATION's `/nodelete` line (now also notes the sibling `/nodelete` Pillar 6 relationship explicitly). Historical Change Log entries 6 and the 2026-05-12 Hardening Certificate note left untouched — they correctly describe the flat-path state that was true at the time; the certificate note gained one small forward-pointing annotation to the new path, not a rewrite of the historical claim. The one real file affected, `.history/depreciate.md.ledger.md`, moved to `.history/quarantine/depreciate.md.ledger.md` as part of the /nodelete-side migration — nothing in it changed but its path. Version held at 4 (a direct retargeting pass, not a `/harden-workflow` structural pass); `last_hardened` 2026-07-04, content_hash recomputed.

---

**Updated Hardening Certificate**

+══════════════════════════════════════════════════════════+
║  WORKFLOW HARDENING CERTIFICATE (EVOLUTIONARY)           ║
║  Workflow:      /depreciate                              ║
║  Date:          2026-05-12                               ║
╠══════════════════════════════════════════════════════════╣
║  GRADE:         SOVEREIGN (maintained)                   ║
║  Previous Grade: SOVEREIGN (2026-05-12)                  ║
╠══════════════════════════════════════════════════════════╣
║  Changes:        4 Divergences injected as evolutionary  ║
║                  extensions (Registry, Precedent, Swarm, ║
║                  Prevention Oracle)                      ║
║  Method:         /harden-workflow incremental + /nodelete║
╠══════════════════════════════════════════════════════════╣
║  Status:        EVOLUTIONARY HARDENING COMPLETE          ║
+══════════════════════════════════════════════════════════+
Standard Version: 2

> **Historical note (2026-06-12):** the four features certified above were later pruned as Ghost Logic — see Change Log entry 6 and `.history/depreciate.md.ledger.md` (path as it stood at the time; that file now lives at `.history/quarantine/depreciate.md.ledger.md`, see Change Log entry 7). This certificate is retained as a dated historical record, not a current grade statement; the authoritative current grade is in the frontmatter.
