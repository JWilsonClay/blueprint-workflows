---
description: A recursive verification loop to synchronize Intent, Plan, and Substrate before proceeding with execution.
---

## GLOSSARY

| Term | Definition |
|------|------------|
| **Ghost Logic** | A named suite failure pattern: system behavior — DB writes, state changes, feature execution — that was discussed or promised but is absent from the actual substrate. The primary target of this workflow. If found, it is a MISMATCH in Phase 5. |
| **Substrate** | The physical codebase — actual files on disk, as they exist right now. Not the plan. Not the conversation. The ground truth of what is implemented. |
| **Physical Anchors** | The specific, verifiable pointers to substrate locations for a plan item: file paths, function names, class names, protocol IDs. Enumerated in Phase 1 before any file is opened. |
| **Discussion corpus** | All sources where intent was expressed: the current conversation, referenced documents (concept.md, Architecture.md, governance files), prior plans, task files, walkthrough artifacts. Identified at Initialization and mined in Phase 2 and the Negative Space Scan. |
| **Item Inventory** | The numbered list of every plan item to be audited, produced at Initialization. Serves as loop control and final completeness check. |
| **Focus Loop** | The iterative 5-phase audit executed independently for each item in the Item Inventory. |
| **Triad Alignment** | The three-layer verification model: Intent (what the user said), Plan (what the plan documents), Substrate (what the code actually does). All three must be in 1:1 parity for an item to pass Phase 5. |
| **Anchor Manifest** | The explicit enumeration of files, grep patterns, and config files to inspect for a given plan item, produced at the start of Phase 1 before any inspection begins. Even an empty manifest must be stated explicitly. |
| **SEARCH EVIDENCE block** | The mandatory log of every search action in Phase 3 — command, path, and result (including null results). A Phase 3 without a SEARCH EVIDENCE block is invalid. |
| **Reconciliation Gap** | The specific description of how Intent, Plan, and Substrate diverge for a given item. Produced when Phase 5 returns MISMATCH. |
| **PARITY** | Phase 5 outcome: Intent, Plan, and Substrate are in 1:1 alignment and all confidence levels are HIGH. Proceed to the next item. |
| **MISMATCH** | Phase 5 outcome: one or more layers diverge. HALT. Surface the Reconciliation Gap. Wait for user instruction. |
| **UNVERIFIABLE** | Phase 5 outcome: one or more layers carry LOW confidence, or the substrate cannot be physically inspected (feature not yet implemented). HALT. Report which layer, what is needed, and whether to defer or flag as risk. UNVERIFIABLE is honest reporting, not failure. |
| **Sovereign Gate** | Phase 5 itself — the decision point that either confirms PARITY and advances the loop, or halts on MISMATCH or UNVERIFIABLE. Nothing advances past Phase 5 without explicit resolution. |
| **Negative Space Scan** | The post-loop scan that mines the discussion corpus for concepts, decisions, and constraints that have no corresponding plan item — recovering forgotten details the Focus Loop cannot find because they were never in the plan to begin with. |
| **Candidate Forgotten Detail** | Any concept, decision, or constraint surfaced by the Negative Space Scan that has no corresponding Item Inventory entry. |
| **False-negative problem** | The risk that the Focus Loop completes with all-PARITY results not because everything is aligned, but because the evidence gathering was insufficient. Countermeasure: every phase requires explicit evidence — null results included. |
| **Null-result** | A search that returns no matches. Must be logged explicitly (command + "0 matches") — never silently discarded or treated as confirmation. |
| **Confidence level** | The reliability of a Triad layer's evidence. HIGH: direct evidence (quoted text, viewed file, confirmed path). MED: inferred or partially verified. LOW: reconstructed from memory or general understanding. |
| **Hallucinated Success** | A Focus Loop that produces PARITY results without having actually executed the Phase 3 substrate verification — SEARCH EVIDENCE stated but not performed. The false-negative problem realized. |
| **Mock Trap** | A Triad Table showing PARITY where substrate verification was run against a test stub or fixture rather than the real implementation. The verification passed; the actual substrate was never checked. |
| **Context Erosion** | Verification rigor decaying over a long Focus Loop — Phase 3 SEARCH EVIDENCE blocks becoming thinner, Anchor Manifests becoming less exhaustive as the session extends. Countermeasure: re-read STRICT RULES before each new item in sessions with more than 5 items. |
| **Active Witness Marker** | **[INJECTED 2026-05-11 — Divergence #1]** Self-reporting provenance comment or metadata block embedded in substrate code that automatically testifies about its own alignment state. |
| **Suite Memory Ledger** | **[INJECTED 2026-05-11 — Divergence #2]** Persistent append-only record of every Candidate Forgotten Detail across all /focus-plan sessions. |
| **Triad Confidence Oracle** | **[INJECTED 2026-05-11 — Divergence #3]** Forward-looking risk forecast generated from Triad patterns and historical memory. |

---

# /focus-plan — Intent/Plan/Substrate Synchronization Loop

This workflow is designed to eliminate context drift and Ghost Logic by forcing a deep-dive synchronization between historical intent, the current implementation plan, and the physical codebase (the substrate).

**Primary purpose**: Rediscover forgotten details — large and small — that were discussed or implied but never captured in the plan.

**On the false-negative problem**: When this workflow finds nothing, that finding is only as reliable as the evidence gathered. Every phase requires you to show your work — what you searched, where, and what the result was (even null results). "I looked and found nothing" must always be accompanied by proof of where you looked.

---

## 0. Initialization
Before starting the loop, locate the plan source. In priority order:
- `implementation_plan.md` in the current workspace -> read all items
- If no file exists: extract plan items from the current conversation (list them explicitly before starting the loop)
- If no plan exists at all: ask the user to describe the plan, then generate a structured item list before proceeding.

Produce an **Item Inventory** at the start — a numbered list of every plan item you will audit. This list is your loop control and your final completeness check.

Before the loop begins, also identify the "discussion corpus" — all sources where intent was expressed:
- The current conversation (scroll/search from the top)
- Referenced documents (concept.md, Architecture.md, governance files, meeting notes)
- Any prior implementation plans, task files, or walkthrough artifacts
This corpus is what Phases 2 and the Negative Space Scan will mine.

---

## The Focus Loop (Iterative for each Plan Item)

For each item in the Item Inventory, execute the following phases with absolute technical rigor:

### Phase 1: Technical Anchor Extraction
Identify the "Physical Anchors" of this item. Do not rely on memory.
- **Anchors**: List specific File Paths, Function Names, Class Names, and Protocol IDs associated with this item.
- **Keywords**: Extract specific technical jargon or constraints used in previous discussions (e.g., "sinusoidal jitter", "Protocol 26 JSON schema").

**Evidence Manifest (Phase 1)**
List every file you intend to inspect for this item before inspecting them. This forces explicit enumeration rather than selective recall:
```
ANCHOR MANIFEST (Item N):
  Files to inspect: [list]
  Grep patterns to run: [list]
  Registry/config files to check: [list]
```
If the anchor manifest is empty (no files identifiable for this item), state explicitly: "No substrate anchors identified — this item may be entirely new/unimplemented."

---

### Phase 2: Evidence-Based Intent Recovery
Search the discussion corpus (identified in Initialization) for the specific origin of this item's requirements.
- **Forced Retrieval**: Use `grep` or log analysis to find the USER's exact definition of this feature. Show the grep command and its output.
- **Intent Quote**: Quote the USER's requirement directly to reset context.
- **Plan Mapping**: Locate the exact line range in the `implementation_plan.md` that addresses this intent.

**Null-Result Handling**
If no direct quote is found: state "Intent not directly quoted — reconstructed from conversation context: [reconstruction]" and flag confidence as LOW. Do not silently proceed as if intent is confirmed.

---

### Phase 3: Substrate Reality Check (Verification)
Examine the current codebase to verify if reality matches the narrative.
- **Logic Audit**: Use `view_file` on the Anchors identified in Phase 1.
- **Ghost Logic Search**: Specifically look for features that were discussed/promised in the logs but are *absent* from the current files.
- **Import/Path Integrity**: Verify that any paths mentioned in the plan actually exist in the substrate.

**Mandatory Search Evidence**
After every search action in Phase 3, log the result explicitly — even null results:
```
SEARCH EVIDENCE (Item N):
  grep -r "<keyword>" <path> -> [N matches / 0 matches / error]
  view_file <path>:L<start>-L<end> -> [found / not found / file missing]
  path check <path> -> [exists / does not exist]
```
A Phase 3 with no SEARCH EVIDENCE block is invalid. "I searched and found nothing" without the search log is not acceptable.

**[INJECTION — 2026-05-11] Failure Pattern Check — Phase 3:**
Before closing Phase 3, explicitly check for these failure patterns:

| Pattern | Signature | Response |
|---|---|---|
| **Ghost Logic** | Feature was discussed or promised in the corpus; no corresponding code exists in the substrate anchors. | Log as MISMATCH evidence. Surface in Phase 5. File a helpdesk ticket if the feature was believed to be implemented. |
| **Mock Trap** | SEARCH EVIDENCE was run against test files, stubs, or fixtures rather than production substrate. Verification passes; real implementation was never checked. | Re-run all searches excluding `test/`, `spec/`, `mock/`, `__pycache__/` paths. |
| **Sound Effect Execution** | A function or handler exists in the substrate but is never called on the actual execution path for this feature. Code is present; it is never reached. | Verify call sites — not just definition existence. |
| **Hallucinated Success** | SEARCH EVIDENCE block is present but searches were not actually executed — block was written from memory or assumption. | Re-execute every search command listed. Show live output, not reconstructed output. |

**[INJECTED 2026-05-11 — Divergence #1: Substrate as Active Witness]**  
**Phase 3b: Active Witness Marker Embedding (optional but recommended for new code)**  
When updating `implementation_plan.md` or creating new substrate files during a build, embed lightweight self-witnessing markers:
```python
# FOCUS-ANCHOR: item-N, intent-hash:abc123, last-verified:2026-05-11
```
These markers allow future Phase 3 scans to receive direct testimony from the substrate itself, reducing external search overhead and eliminating Sound Effect Execution blind spots.

---

### Phase 4: The Triad Alignment Table
Generate a mandatory "Triad Table" to visualize the state of the item:

| Layer | State / Logic / Requirement | Source (File:Line / Log ID) | Confidence |
| :--- | :--- | :--- | :--- |
| **Intent** | [Direct requirement from the USER] | [Conversation Log Snippet] | HIGH / MED / LOW |
| **Plan** | [How it is currently documented] | [implementation_plan.md:L#] | HIGH / MED / LOW |
| **Substrate** | [How it is actually implemented] | [File_Path:L#] | HIGH / MED / LOW |

**Confidence Definitions**
- **HIGH**: Direct evidence found (quoted text, viewed file, confirmed path)
- **MED**: Inferred from context or partially verified
- **LOW**: No direct evidence; reconstructed from memory or general understanding

A table row with LOW confidence on any layer must be flagged in Phase 5 as UNVERIFIABLE regardless of apparent alignment.

---

### Phase 5: Halt or Proceed (The Sovereign Gate)
Analyze the Triad Table for any "Reconciliation Gaps":

1. **MISMATCH**: If Intent, Plan, and Substrate are not in 1:1 parity, **HALT**. Print the "Reconciliation Gap" to the screen and wait for USER instruction.

2. **PARITY**: If all three layers are synchronized AND all confidence levels are HIGH, document "Alignment Confirmed" and proceed to the next item.

3. **UNVERIFIABLE** (new first-class outcome): If any layer has LOW confidence, or if the substrate cannot be physically verified (file not yet created, feature not yet implemented), **HALT**. Report:
   - Which layer could not be verified
   - What would be needed to verify it
   - Whether to defer verification (plan ahead of implementation) or to flag as a risk

**Important**: A result of UNVERIFIABLE is not a failure — it is honest reporting. It means "we cannot confirm this yet." The user can then decide to accept the risk or resolve the uncertainty before proceeding.

**[INJECTION — 2026-05-11] Context Erosion countermeasure:**
In sessions with more than 5 items in the Item Inventory, re-read the STRICT RULES block before beginning each new item's Phase 1. Verification rigor must not decay as the loop extends. A PARITY result on item 12 must be as evidence-dense as a PARITY result on item 1.

---

## Negative Space Scan (run after the Focus Loop completes)

This is the most important addition. The Focus Loop audits plan items that exist. This scan looks for things that *should* exist in the plan but don't.

**Method**: Mine the discussion corpus for concepts, requirements, decisions, and constraints that have no corresponding plan item.

### Negative Space Scan Procedure:
1. Extract all **named concepts** from the discussion corpus (nouns, system names, protocol names, feature names, data types, external services).
2. Extract all **decisions made** (any sentence containing "we will", "we decided", "we agreed", "let's use", "the approach is").
3. Extract all **constraints expressed** (any sentence containing "must", "cannot", "never", "always", "requires", "depends on").
4. For each item in these three lists: check if it appears in the Item Inventory from Initialization.
5. Any item NOT in the plan is a **Candidate Forgotten Detail**. List it explicitly.

### Forgotten Detail Categories (proactively check each, even if not discussed):
The following categories are commonly forgotten in implementation plans. For each category, explicitly state whether it was addressed in the plan or not:

```
FORGOTTEN DETAIL CHECKLIST:
[ ] Error handling & failure modes -- what happens when each step fails?
[ ] Edge cases -- null inputs, empty collections, concurrent access, timeouts
[ ] Rollback / recovery -- what is the undo strategy if implementation goes wrong?
[ ] Dependencies not in requirements -- new packages, external APIs, credentials needed
[ ] Data migration -- does existing data need to be transformed?
[ ] Testing strategy -- unit, integration, E2E test plan for the new work
[ ] Performance implications -- will this introduce latency, memory pressure, or I/O bottlenecks?
[ ] Security / auth considerations -- new attack surfaces, credential handling
[ ] Configuration / environment -- new env vars, config keys, deployment changes
[ ] Cross-cutting concerns -- logging, monitoring, alerting for the new feature
[ ] Backward compatibility -- does this break existing callers, APIs, or data formats?
[ ] Documentation -- what needs to be updated (README, API docs, architecture docs)?
[ ] Cross-item contradictions -- do any plan items conflict with each other?
```

For each unchecked item: ask "Was this considered? If not, should it be added to the plan?"

**[INJECTED 2026-05-11 — Divergence #2: Memory-Augmented Negative Space]**  
**Persistent Suite Memory Ledger**  
After listing Candidate Forgotten Details, append every new detail (and its recommendation) to the suite-wide ledger at `manifest/FOCUS-MEMORY-LEDGER.md` (append-only per /nodelete).  
Future Negative Space Scans automatically cross-reference this ledger to detect recurring omission patterns and surface *meta-patterns* (e.g., “security is forgotten in 70% of new items”).

---

## Final Review
After the Focus Loop and Negative Space Scan, produce a structured summary:

### Alignment Summary
| Item | Triad Result | Confidence | Notes |
|------|-------------|------------|-------|
| [Item 1] | PARITY / MISMATCH / UNVERIFIABLE | HIGH/MED/LOW | |
| ... | | | |

### Forgotten Details Recovered
List every Candidate Forgotten Detail surfaced by the Negative Space Scan, with a recommendation:
- ADD TO PLAN: [detail] — reason it belongs in the plan
- ACKNOWLEDGED: [detail] — already implicitly covered
- DEFER: [detail] — out of scope for this phase

### Plan Update

**[INJECTION — 2026-05-11] /nodelete discipline — Plan Updates:**
When updating `implementation_plan.md` to reflect MISMATCHes or Forgotten Details:
- Never overwrite an existing plan entry. Inject corrections using a clearly marked reconciliation note:
  `**[FOCUS-PLAN RECONCILIATION — YYYY-MM-DD]** Prior entry: [original text]. Ground truth: [corrected text]. Reason: [Triad evidence].`
- Append new Forgotten Detail items; do not reorganize existing plan structure to accommodate them unless the user explicitly requests restructuring.
- Log every change in the plan's Change Log — append only, never overwrite prior log entries.
- A corrected plan entry and its original form both remain in the file. The correction is the authoritative version; the original is the historical record.

### Verification Confidence Score
At the end, provide a single overall confidence score for the entire plan:
- **GREEN** (HIGH confidence across all items): plan is ready to execute
- **YELLOW** (some MED confidence or UNVERIFIABLE items): proceed with caution, document risks
- **RED** (any MISMATCH or multiple UNVERIFIABLEs): resolve before execution

**[INJECTED 2026-05-11 — Divergence #3: Triad Confidence Oracle]**  
**Triad Confidence Oracle**  
After the Alignment Summary, generate a machine-readable forecast block:
```
TRIAD CONFIDENCE ORACLE
Predicted Ghost Logic risk: X% (based on historical patterns + memory ledger)
High-risk items: [list]
Recommended pre-emptive actions: [list]
```
This oracle is emitted for downstream consumption by /execute-build and /continuous-verify.

---

## STRICT RULES (never violate)

1. Never rely on memory in any phase. Show your work — what you searched, where, and what the result was. Null results must be logged explicitly.
2. Every Phase 1 must produce an Anchor Manifest. Even an empty manifest must be stated explicitly with a reason.
3. Every Phase 3 must contain a SEARCH EVIDENCE block. A Phase 3 without one is invalid regardless of outcome.
4. Null results are never silently discarded. "0 matches" is a result. Log it.
5. Any Triad layer with LOW confidence produces UNVERIFIABLE in Phase 5 — regardless of apparent alignment with the other layers.
6. HALT on MISMATCH. Do not advance the loop without explicit user instruction resolving the Reconciliation Gap.
7. HALT on UNVERIFIABLE. Report which layer, what is needed, and whether to defer or flag as risk. Then wait.
8. Run the Negative Space Scan after every Focus Loop completion. It is not optional. It is the most important part.
9. **[INJECTED — 2026-05-11]** In sessions with more than 5 items, re-read STRICT RULES before beginning each new item's Phase 1. Context Erosion is a real risk in long loops.
10. **[INJECTED — 2026-05-11]** Never overwrite existing `implementation_plan.md` entries. Inject reconciliation notes; append new items. Preserve prior content per /nodelete discipline.
11. **[INJECTED — 2026-05-11]** If Ghost Logic, Mock Trap, Sound Effect Execution, or Hallucinated Success is detected at any phase, name it explicitly, log it in the Phase 5 Reconciliation Gap, and file a helpdesk ticket before proceeding.
12. **[INJECTED — 2026-05-11]** SEARCH EVIDENCE must reflect live command execution, not reconstructed output. If a search was not actually run, do not fabricate its output — state "search not yet executed" and run it before advancing.

13. **[INJECTED 2026-05-11 — Divergences #1–#3]** Always apply Active Witness markers when possible, maintain the Suite Memory Ledger, and generate the Triad Confidence Oracle in every Final Review. These evolutionary extensions are now core responsibilities of /focus-plan.

---

## HOW TO BEGIN

When activated:
1. Read the Initialization section fully.
2. Locate the plan source in priority order (implementation_plan.md → conversation extraction → user description).
3. Produce the Item Inventory — numbered list of every plan item to be audited.
4. Identify the discussion corpus — all sources where intent was expressed.
5. Begin Focus Loop on Item 1, Phase 1.

Do not confirm activation to the user. Do not summarize what was read. Produce the Item Inventory and begin.

**You are now live. Begin Initialization.**

---

## INTEGRATION WITH OTHER WORKFLOWS

/focus-plan operates as the pre-execution synchronization gate in the Sovereign Suite:

```
/triage         → identifies focus-plan as needed (plan newer than last run,
                  orphaned [/] tasks, intent = "start building")
/focus-plan     → THIS WORKFLOW — synchronizes Intent/Plan/Substrate
/execute-build  → downstream: only runs after focus-plan returns GREEN or
                  user accepts YELLOW risk
/continuous-verify → called at phase boundaries during execute-build;
                     benefits from the verified Triad baseline this workflow
                     establishes
/helpdesk-tickets  → receives Ghost Logic, Mock Trap findings surfaced here
```

**Critical pipeline rule**: /focus-plan is a blocking pre-condition for /execute-build when `implementation_plan.md` has been modified since the last verified focus-plan run. /triage enforces this at P0 when intent is "start building."

**New immunity & evolution seeding**: /focus-plan now calls the Ecosystem Immunity Layer (`/harden-workflow --immunity`) after every loop and surfaces Divergence recommendations to /harden-workflow.

---

### Change Log
1. **2026-05-11**: `[CREATED / HARDENED — /harden-workflow, Standard Version 2]` Payload existed as a substantively strong monolithic file with robust Triad model, Negative Space Scan, Sovereign Gate, and null-result enforcement — but missing all five required Sovereign structural shells. Hardening run added: GLOSSARY (19 terms), HOW TO BEGIN block, STRICT RULES block (12 rules, consolidating distributed rules from phase prose), INTEGRATION block documenting pipeline position, Change Log. Failure pattern hooks injected into Phase 3 (Ghost Logic, Mock Trap, Sound Effect Execution, Hallucinated Success table). Context Erosion countermeasure injected into Phase 5. /nodelete discipline injected into Plan Update section. STRICT RULES 9–12 injected as new entries. No original content removed. Grade achieved: **Diamond**.
2. **2026-05-11**: `[INJECTED — Divergences #1, #2, #3, /nodelete + /quality + /focus-plan]` Substrate as Active Witness (Phase 3b), Memory-Augmented Negative Space (persistent ledger in Negative Space Scan), and Triad Confidence Oracle (Final Review) injected. Pointer/Payload conversion completed. STRICT RULE 13 added. All prior content preserved. Grade elevated to **Sovereign** with evolutionary extensions. Standard Version: 2.

---

**You are now live. Begin Initialization.**