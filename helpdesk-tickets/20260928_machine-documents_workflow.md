# Helpdesk Ticket: Fork-by-Copy Drift — one "machine documents" ruling, three divergent workspace implementations, no canonical spec or conformance check

**To**: Senior Architect of Workflows
**From**: Claude Sonnet 5.5 — game_one session (cross-workspace investigation, read-only in game_two and ai at John's authorization)
**Date**: 2026-09-29
**Subject**: John's 2026-09-24 "machine documents" practice (pages a script rewrites whole, exempt from /nodelete) was adopted in game_one, game_two and ai by copying or re-deriving from prose; the three copies now differ in mechanics, failure metrics and vocabulary, and nothing detects the drift.
**Urgency**: CRITICAL (Architectural) — STRICT RULE 9: affects more than one workflow-bearing workspace (three) and the pattern has occurred more than once (game_two copied game_one; ai re-derived independently four days later).
**Root Cause Type**: SUBSTANTIVE-LOGIC
**Phylogeny Disposition**: PENDING

*Failure date note (STRICT RULE 10): 2026-09-28 is the day the third independent copy (ai) landed, the first moment all three divergent forms coexisted; the divergence was measured 2026-09-29. Route: John directs this to a Fable 5 design-only pass across all workspaces, then build by a separate execution session. `/harden-workflow --ticket` does not apply (no scaffold gap; this needs new spec, metrics and code).*

---

## 1. Executive Summary
Between 2026-09-24 and 2026-09-28 John ruled a new standing practice — *machine documents*: a page a script rewrites whole on every run, never hand-edited, exempt from `/nodelete` because its record is its sources plus git — and it was implemented three times: game_one (Cards 19 and 21), game_two (Card 09, a read-only adaptation of Card 19) and ai (a policy page plus a single-point generator). The three now differ on the label a page carries, whether a registry and a freshness check exist, how churn is stopped, what is in scope, what the hand-kept "judgment" data file is called, and what the practice itself is called. Measured 2026-09-29: three of five game_one registered pages are STALE; ai has no freshness check, no test and no label, and its policy page violates the policy's own failure #1. No document or tool exists that could notice any of this.

## 2. Root Cause Analysis: "Fork-by-Copy Drift (no canonical cross-workspace spec)"
Class: **Structural Gap / Other** — plus one **Sound Effect** instance inside ai (a generator that "passes" as introspecting while embedding static text).

- **The How**: each workspace took John's verbatim words and built its own authority. game_one wrote Card 19 (registry + `regenerate` + five-line header + byte-identical determinism + dispatcher-only writes) and later Card 21 (the *word* "machine document" and unregistered JSON ledgers). game_two copied Card 19 by reading game_one ("Adapted … read-only, at John's direction") and changed the command path, dispatcher hooks and added the asset-order-sheet ladder. ai did not copy; it wrote `DYNAMIC_MACHINE_DOCS_POLICY.md` from John's "dynamically machine generated" words and a single generator, with no registry, header, test or freshness gate.
- **The Why**: the suite has no workflow, spec or vocabulary row for machine documents, so each workspace's card/policy *is* its own only authority, and adoption in workspace N+1 means copying workspace N's prose (game_two) or starting over (ai). No workflow requires a canonical source when one ruling is adopted in several workspaces, and nothing compares the copies.

**Measured divergences (each cited in §3):**

| Dimension | game_one | game_two | ai |
|---|---|---|---|
| Name of the thing | "generated surfaces" (Card 19) / "machine document" (Card 21) | "generated pages / surfaces" (Card 09) | "machine docs" / "dynamically machine-generated" |
| Label on the page | five-line header, first 40 lines | same five lines | none on README, MODEL_MANIFEST, PORT_REGISTRY, policy; only the queue says so in prose |
| Registry ("a page not listed is not generated") | yes, 5 pages — but two generated JSON ledgers are outside it | yes, 8 pages | none |
| Freshness check | `--check`: fresh / STALE / UNSTABLE, tested | same, tested | none; no test file exists; pre-commit runs only the LOC check |
| Who refreshes | dispatcher at audit close; deliberately NOT a hook | same | whoever runs the script |
| Churn control | no clock at all — same sources, same bytes | same | write-if-changed + one timestamp kept in AGENTS.md §7 (a clock inside a generated section) |
| Scope stated | "as many as logical"; README/CLAUDE.md not generated (John's call) | same, explicit never-generated list | "EVERY document"; plan says no file in `docs/` may be hand-authored — but `docs/design/designer_intent.md` is |
| Hand-kept judgment → John queue | intent-journal ask rows | `raised_to_john.json` | `decisions.json` — three schemas, one page name |

**Failure metrics — three vocabularies for overlapping ideas, and four with no owner:**
- Same idea, different names: ai's *Negative Drift Mutation Failure* ≡ game_one/game_two's tested "stale by mutation"; ai's *Zero-Edit Synchronization* ≈ their "same sources → same bytes". Nobody has mapped them.
- Defined only as prose, never a mechanical test: ai's *Canned Script Trick* (static Markdown inside a generator) and *Dual Maintenance*.
- Defined nowhere: (a) **maximum staleness window** for a page a human reads (game_one's pages are refreshed only at audit close by design, so "3 of 5 stale" is currently indistinguishable from healthy); (b) **registry completeness** (a generated-marked file outside the registry — two exist); (c) **cross-workspace conformance**; (d) **no clock inside any generated page**, which ai's AGENTS.md §7 breaks and game_one's card forbids.
- ai's own policy fails its own metric: `policy_docs.py` builds policy §§1–4 from typed-in strings (failure #1), types ports 8080/8188 into the generator, and hard-codes 8098 / 8099 as defaults — the policy's own named example of a forbidden hardcode.

**Evidence limits (stated, not hidden):** game_two was read at card, registry, page-header and intent level only — its generator code and tests were not read; no code was run in game_two or ai; only game_one's `regenerate --check --all` was run (writes nothing). game_two's and ai's freshness are therefore UNMEASURED.

## 3. Forensic Evidence
- **Origin ruling, game_one**: [game_design_intent.md row GDI-343](file:///home/jwils/.prebuild.temp/game_dev/game_one/docs/design/designer_drafts_and_intentions/game_design_intent.md#L8150-L8150)
  *Evidence: John 2026-09-24 — "documents that are machine built, completely refreshed every time, exempt from nodelete"; "the meta is also exempt from no delete. make it machine built."*
- **Origin ruling, game_two**: [designer_intent.md verbatim](file:///home/jwils/.prebuild.temp/game_dev/game_two/docs/design/designer_intent.md#L6840-L6840)
  *Evidence: John tells game_two to "do the same" and to "convert as many documents to machine generated as logical" — same ruling, second workspace, adopted by reading game_one.*
- **Origin ruling, ai**: [designer_intent.md](file:///home/jwils/.prebuild.temp/game_dev/ai/docs/design/designer_intent.md#L33-L37) and [dynamic-introspection entry](file:///home/jwils/.prebuild.temp/game_dev/ai/docs/design/designer_intent.md#L70-L71)
  *Evidence: "the policy is EVERY document is machine generated" and "dynamically machine generated" — scope and mechanism worded differently from game_one/game_two.*
- **game_one law — header, registry-only rule, dispatcher-only writes**: [Card 19 header lines](file:///home/jwils/.prebuild.temp/game_dev/game_one/strategic_operations/workflows/19-generated-surfaces.md#L60-L70), [registry rule](file:///home/jwils/.prebuild.temp/game_dev/game_one/strategic_operations/workflows/19-generated-surfaces.md#L13-L14), [freshness/no-hook invariants](file:///home/jwils/.prebuild.temp/game_dev/game_one/strategic_operations/workflows/19-generated-surfaces.md#L42-L57)
  *Evidence: the five-line header, "a page not listed here is not generated", no clock, `--check` at audit close, never a hook.*
- **game_one two-tier gap**: [Card 21 definition](file:///home/jwils/.prebuild.temp/game_dev/game_one/strategic_operations/workflows/21-machine-documents.md#L55-L59), [the registry, five entries](file:///home/jwils/.prebuild.temp/game_dev/game_one/strategic_operations/generated_surfaces.yaml#L6-L48), [cite_fingerprints.json `_meta`](file:///home/jwils/.prebuild.temp/game_dev/game_one/docs/agent/cite_fingerprints.json#L2-L7)
  *Evidence: Card 21 defines "machine document" broader than Card 19's "generated surface"; `cite_fingerprints.json` (and `contract_index.json`) are generated yet absent from the registry that says unlisted pages are not generated.*
- **game_one measured staleness (2026-09-29)**: command `/usr/bin/python3.10 -B -m strategic_operations.tools.regenerate --check --all` returned `STALE decision-queue`, `STALE decision-queue-legacy`, `STALE meta-contract-architecture`; `fresh meta-contract`, `fresh contract-index`. Pages: [john_decision_queue.md header](file:///home/jwils/.prebuild.temp/game_dev/game_one/docs/agent/john_decision_queue.md#L1-L9)
  *Evidence: 3 of 5 registered pages stale; the queue is the page John reads; by design nothing refreshes it between audit closes and no metric says how stale is too stale.*
- **game_one word origin**: [plan "Words" item 7](file:///home/jwils/.prebuild.temp/game_dev/game_one/strategic_operations/implementation-plan-MAINT-TRUTH-MACHINERY-1.md#L220-L221)
  *Evidence: "machine document" is John's phrase (0 tree hits at that time) — the umbrella term exists but only one workspace's Card 21 uses it.*
- **game_two copy-by-read and scope list**: [Card 09 line 3](file:///home/jwils/.prebuild.temp/game_dev/game_two/strategic_operations/workflows/09-generated-surfaces.md#L3-L3), [never-covered list](file:///home/jwils/.prebuild.temp/game_dev/game_two/strategic_operations/workflows/09-generated-surfaces.md#L42-L46), [registry, 8 entries](file:///home/jwils/.prebuild.temp/game_dev/game_two/strategic_operations/generated_surfaces.yaml#L5-L78)
  *Evidence: a fork of Card 19 by reading, with its own command path and an explicit never-generated class list game_one's card does not carry.*
- **ai policy's own failure metrics**: [Code is Canon / no hardcoded PORT](file:///home/jwils/.prebuild.temp/game_dev/ai/docs/policy/DYNAMIC_MACHINE_DOCS_POLICY.md#L10-L14), [failures #1–#4](file:///home/jwils/.prebuild.temp/game_dev/ai/docs/policy/DYNAMIC_MACHINE_DOCS_POLICY.md#L16-L20)
  *Evidence: the policy names "placing static Markdown strings inside a Python generator file" as FAIL and `PORT = 8098` as the forbidden example.*
- **ai's generator violates it**: [policy_docs.py builds §§1–4 as string literals](file:///home/jwils/.prebuild.temp/game_dev/ai/scripts/policy_docs.py#L98-L126), [reserved ports typed into the generator](file:///home/jwils/.prebuild.temp/game_dev/ai/scripts/generate_workspace_docs.py#L63-L69), [8098 and 8099 defaults](file:///home/jwils/.prebuild.temp/game_dev/ai/scripts/introspect_codebase.py#L35-L63)
  *Evidence: only policy §5 comes from code; ports 8080/8188 typed in; 8098/8099 appear as fallback constants.*
- **ai clock inside a generated section**: [audit timestamp logic](file:///home/jwils/.prebuild.temp/game_dev/ai/scripts/generate_workspace_docs.py#L158-L172), [the stamped section](file:///home/jwils/.prebuild.temp/game_dev/ai/AGENTS.md#L83-L86)
  *Evidence: `Audited: 2026-09-29 22:32:32 UTC` lives in AGENTS.md §7 — a clock in a generated section, which game_one's invariants forbid.*
- **ai has no freshness gate**: [pre-commit hook — LOC check only](file:///home/jwils/.prebuild.temp/game_dev/ai/.git/hooks/pre-commit#L1-L19)
  *Evidence: the only hook that could gate a stale page checks executable-line count and nothing else; searched `generate_workspace_docs` and `--check` across all three hooks: empty; no `test_*.py` outside the comfyui/models/output folders.*
- **ai law wider than practice**: [AGENTS.md law](file:///home/jwils/.prebuild.temp/game_dev/ai/AGENTS.md#L79-L81), [plan sentence](file:///home/jwils/.prebuild.temp/game_dev/ai/implementation-plan.md#L301-L301)
  *Evidence: "Neither README.md nor any file in docs/ may be hand-authored" while `docs/design/designer_intent.md` is hand-kept.*

## 4. Remediation: One canonical machine-document spec, mechanical failure metrics, one vocabulary, then per-workspace conformance
Recommended, future tense — nothing has been fixed:
1. **Fable 5, design only, all workspaces.** Deliver: (a) one canonical spec (definition, five-line header, registry schema, command surface, determinism rule, no-clock rule, retention/`/nodelete` carve-out, what is never generated, the judgment-in-data-file rule); (b) a **failure-metric table where every row has a mechanical check** (candidates below); (c) a **vocabulary row** pinning one umbrella term (John's phrase "machine document") and mapping each existing name to it; (d) a per-workspace migration list. Fable 5 does not build.
2. **Execution session builds** from the design: a read-only conformance checker (same shape as the Ticket Lifecycle Evidence Engine — presence/format/consistency only, never judging content) plus the per-workspace fixes.
3. **John locks** any law; an agent drafts, never flips a status.
4. Per-workspace known fixes to fold in: **ai** — add the five-line label, a `--check`, and move the policy's typed rules into a small hand-kept data file the generator reads (the judgment-in-data pattern the other two already use), or rule that the policy page is hand-kept; **game_one** — either register `cite_fingerprints.json` / `contract_index.json` or state that Card 21 ledgers are a second, unregistered tier, and decide a staleness window for the John-facing queue; **game_two** — audit generator code and tests (not read here).

**Candidate mechanical metrics (union of what the three already define, plus the four gaps):** M1 header conformance · M2 freshness (`--check` exit 0) · M3 determinism (render twice, equal) · M4 negative-drift mutation (change a source, the page must change) · M5 canned-string ratio (static text vs introspected text in a generator) · M6 registry completeness (every generated-marked file registered, no unregistered marker) · M7 no clock/commit-hash inside a generated page · M8 sole-writer (only the designated writer commits a generated page) · M9 maximum staleness window for human-read pages · M10 generator LOC boundary · M11 cross-workspace spec-version match.

**Adjacent findings — CAPTURED, not asserted as scope, not built:** (a) commit-subject label forms differ across the same three workspaces — game_one `GO/DESIGN/MAINT/MISC` ([COMMIT_LABELS.md](file:///home/jwils/.prebuild.temp/game_dev/game_one/docs/agent/COMMIT_LABELS.md#L24-L27)), ai `PRODUCTION: | DESIGN: | MAINT: | ELSE:` ([commit-msg hook](file:///home/jwils/.prebuild.temp/game_dev/ai/.git/hooks/commit-msg#L3-L8)), game_two `PRODUCTION.` / `MAINT.` with a trailing period (git subjects `0a856cf`, `b6dfc64`; [CITATION NEEDED: the game_two file that defines the period form]); same drift class, better ticketed on its own if Fable 5 wants it; (b) the same-named `john_decision_queue.md` has three source schemas (in scope above, listed in the table).

## 5. Recommendation to Senior Architect
When one John ruling is adopted in more than one workspace, workspaces after the first must **consume a canonical spec held in one place, not copy the first workspace's prose**, and a read-only conformance checker must compare each workspace's binding against it — the way `/helpdesk-tickets` already has an evidence engine that checks presence and format mechanically. Concretely for the suite: add a cross-workspace "shared practice" mechanism (canonical spec + per-workspace binding + conformance check + one vocabulary row) and treat "second adoption of a ruling without a canonical source" as an intake trigger. This prevents the class for every future shared practice (commit labels, register rule, delegation cards), not only machine documents. Expected Phylogeny impact at closure: a structural pattern (five-line header, registry, `--check`, judgment-in-data) will move between more than two files, so `NO TRANSFER` is unlikely to be the correct disposition.

---
**Status**: **OPEN**
**Verification**: PENDING

---
*Signed,*
**Claude (Sonnet 5.5)**
*(Sovereign Helpdesk Analyst — game_one session)*

---

## Addendum — 2026-09-29 — Design pass completed (Claude Fable 5.1, Senior Architect of Workflows)

*(Appended; nothing above edited. Ticket status unchanged.)*

The design-only pass §4 item 1 routes to Fable has been delivered: `docs/DESIGN_Machine_Documents.md` — canonical specification (S1–S12), failure-metric table with a mechanical check per row (M1–M13, superset of this ticket's M1–M11), one vocabulary row, per-workspace migration lists for game_one, game_two, ai **and this suite**, checker design, ordered PR plan (PR-0…PR-7), and eleven rulings for John (§10). Nothing was built; no file outside this repo was written.

**Anchoring ruling, John, 2026-09-29 (this session):** *"Machine Documents are exempted completely from the /nodelete protocols. Nodelete applies to LLM's and Users only. This is something else entirely."* The design treats a machine document as outside `/nodelete` by kind (no retention contract, no opt-in under `reduce_after_capture.md`), not as a fourth contract.

**Re-measured 2026-09-29 evening (read-only):** game_one `regenerate --check --all` → **4 of 5 STALE** (this ticket measured 3 of 5 earlier the same day; `contract-index` went stale in between; the John-facing queue trails its journal by 4 commits). game_two `--check --all` → **1 of 8 STALE** (`doc-health`); tree unchanged before/after — its freshness is no longer UNMEASURED. ai generator run twice on a scratch copy → fresh relative to its working tree and byte-identical across the two runs, but by coincidence of runtime state: the generator reads `nvidia-smi`, `ss -tulpn` and `datetime.utcnow()` (design §2.3c). `diff` of the two `regenerate.py` engines → five semantic divergences five days after the copy (design §2.1): the fork is at the code level, not only in prose.

**Route forward:** John rules §10 (R1–R11) → `/implementation-plan` from the design → PR-1/PR-2 in this suite under `/execute-build` → PR-3/4/5 delegated to sessions in each workspace at that workspace's own close → PR-7 closes this ticket (SUBSTANTIVE-LOGIC path, Remediation Record, Phylogeny Disposition expected **TRANSFER**).

**Status**: **OPEN** — awaiting rulings and the execution session.
**Verification**: PENDING

## Addendum 2 — 2026-09-30 — Design amended after John's discussion pass (Claude Fable 5.1)

*(Appended; nothing above edited. Ticket status unchanged.)*

John, of the design: *"this is largely approved"*; of the discussion pass that followed: *"I have zero dissent with your output in full. fold them in."* Folded into `docs/DESIGN_Machine_Documents.md` (its Change Log entry 2): §14 kinds and the contract lifecycle (the draft→locked flag lives in each contract's own status line as a Live-State slot; header, changelog and vNEXT become generated sections; a lock guard names silent body edits); rules S13 and injections into S3/S4/S5/S8/S9/S10; metrics M14–M19 (source-is-generated, anchor drift, size, lock breach, ceremony completeness, vNEXT); rulings R12 (contract body Live-State + Append-Only changelog, superseding the in-place strike rule) and R13 (kinds), both with John's zero dissent recorded and the workspace capture left to PR-0; PR-8/PR-9 as a follow-on that does not gate this ticket's closure. Measured 2026-09-30: strike residue in game_one 198 of 223 contracts (3,769 lines, 556 KB), game_two 96 of 97 (872 lines).

**Status**: **OPEN** — awaiting PR-0 capture of R1–R13 and the execution session.
**Verification**: PENDING

## Addendum 3 — 2026-09-30 — All thirteen design rulings ratified (Claude Fable 5.1)

*(Appended; nothing above edited. Ticket status unchanged.)*

John, verbatim: *"just so it's explicit, all of section 10's recommended rulings are ratified."* R1–R13 of `docs/DESIGN_Machine_Documents.md` stand at their recommended values; the design's status is RATIFIED DESIGN, still design only. Remaining before build: PR-0's verbatim capture in each workspace's designer-intent surface, then `/implementation-plan` and the execution session (PR-1…PR-7 close this ticket; PR-8/PR-9 follow).

**Status**: **OPEN** — rulings ratified; awaiting PR-0 capture and the execution session.
**Verification**: PENDING
