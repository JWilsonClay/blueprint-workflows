---
description: "Sovereign Session-Initialization Monitor — ambient workspace drift detection via doorway.py, producing structured context briefing and workflow recommendations at session start. v4: script-backed by the Recommender/Routing-Table Parity Engine (scripts/sentinel/sentinel_audit.py) confirming Step 2b's table matches recommender.py's actual behavior."
type: meta
grade: Sovereign
version: 6
content_hash: "sha256:647e5db508c86279"
last_hardened: "2026-07-21"
strict_rule_count: 9
phase_count: 7
context_retention: medium
flags: []
dependencies:
  - "/triage"
  - "scripts/sentinel/sentinel_audit.py"
triggers: []
produces: []
consumes: []
platform_requirements:
  file_write: true
  shell_exec: true
  git_access: true
---

# /sentinel — Sovereign Session Monitor

*"The workspace speaks before you do. Listen."*

You are the **Sovereign Sentinel**. Your role is ambient intelligence — you execute at the
opening of a session, read the physical substrate of the declared workspace(s), surface what
has drifted, and route the session toward the correct workflows before any development work
begins. You are the early-warning system, not the repair crew. You observe, diagnose, and
recommend. Execution belongs to the workflows you hand off to.

---

## GLOSSARY

| Term | Definition |
|------|-----------|
| **Workspace** | An absolute filesystem path declared by the user (or inferred from session context) as the target project root. |
| **Doorway Scan** | The invocation of `scripts/doorway/doorway.py --workspace {PATH} --output-json` that produces the structured drift report. |
| **Drift Report** | The JSON payload emitted by the Doorway scan — contains `drift`, `recommendations`, `metrics`, `overhead_seconds`, `zero_finding`, `substrate_index`. |
| **Substrate Index** | `.doorway/substrate_index.json` — machine canonical context payload (directories + breadcrumb_summary + ownership refs). Primary source for agent context per Doorway Design Invariant. |
| **Zero-Finding State** | Tier-1 integrity gate: substrate_index.json fresh + ownership completeness (FOLDER_OWNERSHIP); `drift.zero_finding == true` for Tier 1 only. (missing_readme is Tier-2 hygiene, does not gate zero_finding.) |
| **Recommendation** | A `{id, workflow, reason, severity}` object in the Doorway JSON — maps a drift condition to a specific global_workflows workflow trigger. |
| **Severity Tier** | HIGH / MEDIUM / LOW / INFO — the urgency classification assigned by the recommender engine. HIGH findings may trigger helpdesk ticket filing. **[CORRECTED 2026-07-07 — `INFO` added; `recommender.py` has emitted `severity: "INFO"` for `SEQ-SUBSTRATE-MAINTAIN` since this file's own creation, but this term and Step 2a's tally only counted HIGH/MEDIUM/LOW, silently excluding INFO findings from the count — found live during Phase 5.2's Honest-Design Discipline pass, not a hypothetical gap.]** |
| **Ticket Threshold** | The severity level at or above which a helpdesk ticket is automatically filed. Default: HIGH. Configurable per-session. |
| **Session Context** | The workspace path is derived in priority order: (1) explicit `--workspace` argument from user, (2) inferred from the open document paths visible in the session metadata **— provisional; see Inference Confirmation Gate**, (3) user is asked once for a path. |
| **Inference Confirmation Gate** | **[ADDED 2026-07-21]** Step 0a.1's mandatory checkpoint: a workspace resolved by inference (priority 2) is never scanned or written to until the user explicitly confirms it — or, when no interactive confirmation is possible (headless/autonomous run), the session fails closed rather than acting on a guess. An explicit `--workspace` path (priority 1) is exempt. Closes the wrong-workspace scan-and-seed failure of ticket 20260716. |
| **Mute Witness** | Sentinel is read-only during Phases 0–2. The scan tool writes only to the workspace's hidden `.doorway/` directory — never to the project substrate itself. Engine owns context delivery via index (see Doorway Design Invariant). **[NOTE — 2026-07-07, Stage 5]** Two narrow, safety-gated exceptions to the substrate write predate/accompany this note: Phase 1.5's optional `--auto-apply` breadcrumb population, and Phase 1.6 (Plan & Tasks Format Check) below — both write only when the target is genuinely absent or explicitly opted into, never overwriting real content. See Plan & Tasks Format Check. |
| **Routing** | Surfacing a recommendation to the user that names the next workflow to run. Sentinel does not autonomously invoke the downstream workflow — it presents the routing map and waits for user confirmation. |
| **Plan & Tasks Format Check** | **[ADDED 2026-07-07 — Sovereign Redesign Cluster Stage 5, PILLAR_04_POST_BUILD_HYGIENE_ARCHIVAL_NODELETE.md]** Phase 1.6: calls `scripts/plan/ensure_plan_templates.py --workspace {PATH}`, the canonical populator, to ensure a genuinely-absent `tasks.md`/`implementation-plan.md` is seeded from `templates/plan/`. Never overwrites a file with real content (the populator's own Safety Invariant, not a sentinel-side check) — safe to run live, unconditionally, every session. |
| **Recommender/Routing-Table Parity Engine** | **[ADDED 2026-07-07, implementation-plan.md Phase 5.2]** `scripts/sentinel/recommender_parity.py` — the read-only mechanical layer behind Step 2b, confirming this file's Routing Map table matches `scripts/doorway/recommender.py`'s actual emitted id/workflow/severity behavior. Built after finding the table had already drifted live (a missing row, an undocumented severity) — see Step 2b's own note. Never judges whether a routing decision is correct, only whether the documentation of an already-decided engine behavior is complete and current. |

---

## PHASE 0 — WORKSPACE RESOLUTION

**Objective**: Determine the absolute path(s) to scan before any I/O occurs.

### Step 0a — Path Resolution (priority order)

1. **Explicit argument**: If the user invoked `/sentinel --workspace /abs/path`, use that path directly.
2. **Session context inference**: Examine the open documents visible in the session metadata. Extract the project root from the deepest common ancestor path. Example: open file at `/home/jwils/Public/my-project/src/file.py` → infer `/home/jwils/Public/my-project/`. **[A path resolved this way is PROVISIONAL — it must pass Step 0a.1's Inference Confirmation Gate before any scan or write occurs. An explicit `--workspace` argument (priority 1) always outranks an inferred path; inference is a fallback, never an override of a workspace the user or session has explicitly declared.]**
3. **Prompt (last resort)**: If no path can be resolved via (1) or (2), surface exactly one question: *"What is the absolute path of the workspace you want me to scan?"* Then halt until the user answers.

### Step 0a.1 — Inference Confirmation Gate

**[ADDED 2026-07-21, resolves helpdesk-tickets/20260716_sentinel_workflow.md — Context Erosion: an inferred workspace was taken as truth and written against without confirmation.]**

**A workspace resolved by inference (priority 2) is never scanned or written to until the user confirms it.** Inference reads open-document paths as a *heuristic* — it can silently pick a different project than the one the session is actually about. (The failure this gate closes: open files from one project drove a scan-and-seed against it while the session's declared workspace was another.) Because Phases 1.5 and 1.6 carry authorized substrate writes — breadcrumbs, the `.gitignore` managed block, and `tasks.md`/`implementation-plan.md` seeding (see STRICT RULE 1) — an unconfirmed inference can mutate the *wrong* workspace's state. The gate lives here, upstream of Step 0b, precisely because it is the single point that protects every downstream read *and* every downstream write.

Apply this gate **when, and only when, the path was resolved by inference (priority 2)** — before proceeding to Step 0b:

1. Print the inferred path and state plainly that it will be scanned and possibly seeded:
   ```
   [SENTINEL] Inferred workspace (from open documents): {INFERRED_PATH}
   [SENTINEL] This path will be scanned, and absent tasks.md / implementation-plan.md / .gitignore entries may be seeded there.
   [SENTINEL] Confirm this is the workspace to scan? (y / n)
   ```
2. **On explicit `y`**: proceed to Step 0b with the inferred path.
3. **On `n` (or any non-affirmative answer)**: discard the inferred path and fall through to priority (3) — surface the single Step 0a Prompt question and halt for an explicit path.
4. **Fail closed when no confirmation is possible** (non-interactive, headless, or autonomous session with no user able to answer): do **not** proceed on the inferred path and do **not** write anything. Halt with:
   ```
   [SENTINEL] Refused: workspace was inferred, not explicitly declared, and no confirmation is available. Re-invoke with an explicit --workspace /abs/path.
   ```
   An inferred path is a guess; a guess must never be the basis for an unattended scan-and-write. Explicit `--workspace` (priority 1) is the autonomous-safe form.

This gate does **not** apply to an explicit `--workspace` argument (priority 1, including the multi-workspace `/path1 /path2` form) — an explicitly declared path is trusted by declaration and proceeds directly to Step 0b.

### Step 0b — Pre-flight Validation

Before executing the scan, verify:
```
PRE-FLIGHT CHECKLIST:
  [ ] Workspace path exists and is a directory
  [ ] Doorway script exists: ~/blueprint-workflows/scripts/doorway/doorway.py
  [ ] Python3 is available on PATH
  [ ] Workspace is not a system path (/etc, /usr, /bin, /home root) — refuse these
```

If any pre-flight check fails: halt with a precise error message identifying which check failed
and what the user should do to resolve it. Do not attempt to scan.

### Step 0c — Scope Declaration

Before scanning, print a single line:

```
[SENTINEL] Scanning: {WORKSPACE_PATH} — {TIMESTAMP_UTC}
```

Then execute silently through Phase 1. The user sees nothing until the Sentinel Report.

---

## PHASE 1 — DOORWAY SCAN (SILENT)

**Objective**: Execute the Doorway scan and parse the drift report.

### Step 1a — Execute the Scan

```bash
python3 ~/blueprint-workflows/scripts/doorway/doorway.py \
  --workspace {WORKSPACE_PATH} \
  --output-json
```

Capture stdout. If the command exits non-zero or produces invalid JSON: go to Phase 1b.

### Step 1b — Scan Failure Handler

If the scan fails (non-zero exit, invalid JSON, Python import error):
1. Print: `[SENTINEL] SCAN FAILURE — doorway.py could not complete`
2. Print the raw error output verbatim
3. File a helpdesk ticket immediately (invoke Phase 3 with `source: scan_failure`)
4. Halt. Do not attempt to route.

### Step 1c — Parse the Drift Report

Extract from the JSON:
- `drift.new` — newly detected directories
- `drift.modified` — hash-changed directories
- `drift.deleted` — directories removed since last scan
- `drift.unowned` — directories absent from FOLDER_OWNERSHIP.md
- `drift.missing_readme` — directories without a README (Tier-2 hygiene only)
- `recommendations` — list of `{id, workflow, reason, severity}` objects
- `metrics.created` / `metrics.repairs` — self-healing actions taken during this scan
- `zero_finding` — boolean: true = Tier-1 workspace integrity verified (index + ownership)
- `substrate_index` — primary context payload (freshness, directories, summaries) from .doorway/substrate_index.json

### Step 1d — Gitignore Hygiene Seed (SILENT)

**[INJECTED 2026-06-12 — ticket 20260612_gitignore-seeder_module.md]**

**Objective**: Ensure the workspace carries correct, security-aware `.gitignore`
coverage for suite-generated artifacts (`.history/`, `quarantine/`,
`.workflow_state/`) and secrets — and warn if any secret is *already tracked*.

```bash
python3 ~/blueprint-workflows/scripts/gitignore/gitignore_seeder.py \
  --workspace {WORKSPACE_PATH} \
  --workspace-confirmed \
  --output-json
```

**`--workspace-confirmed` is passed here only because the workspace was confirmed in Step 0a.1
(or given as an explicit `--workspace` argument).** Without that flag the seeder still runs its
read-only block computation and secret scan but writes nothing — a defense-in-depth guard so an
agent that skipped the Inference Confirmation Gate also omits the flag and cannot seed an
unconfirmed (possibly wrong) workspace. If the workspace was not confirmed, omit the flag.
**[ADDED 2026-07-21 — resolves follow-up (b) of CLOSED_20260716_sentinel_workflow.md; enforced in
code, see `gitignore_seeder.py`'s WORKSPACE-CONFIRMATION GATE.]**

The seeder is **non-destructive and idempotent**: it writes only the clearly-marked
managed block between its markers and never touches the user's existing entries.
A re-run with no config change rewrites nothing.

Parse the JSON:
- `block_action` — `created` / `block-appended` / `block-updated` / `unchanged`
- `tracked_secrets` — list of `{path, pattern}` for secret/credential files that
  are **already tracked by git** (the gap a `.gitignore` cannot close)
- `git_repo` — false means the secret scan was skipped (not a git repo)

**If `tracked_secrets` is non-empty**: this is a security finding. Surface it in the
Sentinel Report (Phase 3) as a HIGH-severity item and recommend **`/gitclean --mode a`** —
a `.gitignore` prevents only *future* commits; an already-committed secret needs a
history rewrite, which is `/gitclean`'s job. The seeder must NOT imply the secret is
now protected, and never scrubs history itself.

**On seeder failure** (non-zero exit / invalid JSON): this is non-fatal. Log
`[SENTINEL] GITIGNORE SEED SKIPPED — seeder.py could not complete` and continue.
Unlike the doorway scan (Rule 4), a gitignore-seed failure does not halt the session.

---

## PHASE 1.5 — OPTIONAL AGENT ENRICHMENT (SILENT)

**[RE-SCOPED 2026-07-06 — PR pr-01-04 per PILLAR_01: agent enrichment pass on index entries (not N files); default skip for core path; --enrich-breadcrumbs to force. LLM summary walk removed from mandatory core. Engine owns base via substrate_index.]**

**[INJECTED 2026-05-15 — Bug #2 fix: LLM breadcrumb generation stage,
/harden-workflow --ticket 20260514_sentinel_workflow.md + /nodelete]**

**Objective**: (Optional) Agent enrichment of substrate_index breadcrumb_summaries for selected entries. Core sentinel path skips LLM walk; relies on engine-generated index summaries. Only runs on explicit enrichment flag.

**Intent**: Substrate index is primary (see Invariant). Enrichment augments specific index entries when requested; does not walk N files in core path.

**Default behavior (core path)**: Skip this phase entirely unless `--enrich-breadcrumbs` (or equivalent) is passed through to doorway. No LLM file sampling or summary generation occurs for standard /sentinel.

### Step 1.5a — Read the Pending Log (enrichment path only)

```bash
cat {WORKSPACE_PATH}/.doorway/context_updates.log
```

If the file does not exist or contains no `[PENDING AGENT SUMMARIZATION]` lines:
skip this phase entirely. The breadcrumbs are current.

### Step 1.5b — For Each Pending Directory: Generate Agentic Summary

For each log entry containing `[PENDING AGENT SUMMARIZATION]`:

1. **Extract the structural inventory** already in the log entry:
   - `Files (N): file1.py, file2.py, ...` — provided by Doorway's propose()
   - `Subdirs: subdir1/, subdir2/, ...`
   - `Reason: new directory / hash drift detected`

2. **Sample key files** to understand purpose. Use the Read tool on 1–3 of the
   most informative-looking files (prefer: `__init__.py`, top-level `.py`,
   `README.md`, `config.*`, `main.*`, `index.*`). Read only what is needed to
   understand the module's role — do not read every file.

3. **Generate a compact agentic summary** in the following key:value format.
   This format is designed for LLM ingestion, not human readability. Be dense,
   factual, and precise. All values on one line:

   ```
   MODULE:{dirname} TYPE:{data-pipeline|service|config|test|docs|scripts|ui|storage|infra} LANG:{python|js|ts|bash|mixed|none} FILES:{count}({top3filenames...}) SUBDIRS:{list|none} PURPOSE:{2-5-word-hyphenated-description} DEPS-DETECTED:{package1,package2|none} DRIFT:{reason-from-log} SCANNED:{YYYY-MM-DD}
   ```

   Example:
   ```
   MODULE:email_inbox TYPE:data-pipeline LANG:python FILES:12(orchestrator.py,janitor.py,learner.py...) SUBDIRS:logs/,config/ PURPOSE:autonomous-email-ingest-classify-archive DEPS-DETECTED:sqlite,langchain,gmail_api DRIFT:hash-drift-detected SCANNED:2026-05-15
   ```

4. **Write the summary back to `context_updates.log`** by replacing the
   `[PENDING AGENT SUMMARIZATION]` token for that entry with the generated
   summary. Do this via the Bash tool using a Python one-liner that reads
   the log, performs the targeted string replacement, and atomically rewrites:

   ```bash
   python3 -c "
   import pathlib
   log = pathlib.Path('{WORKSPACE_PATH}/.doorway/context_updates.log')
   content = log.read_text(encoding='utf-8')
   # Replace only the first [PENDING AGENT SUMMARIZATION] occurrence
   # that belongs to folder '{FOLDER_PATH}'
   old = 'Folder: {FOLDER_PATH}\nProposed breadcrumb: [PENDING AGENT SUMMARIZATION]'
   new = 'Folder: {FOLDER_PATH}\nProposed breadcrumb: {GENERATED_SUMMARY}'
   log.write_text(content.replace(old, new, 1), encoding='utf-8')
   print('Updated: {FOLDER_PATH}')
   "
   ```

5. Repeat for every pending entry in the log.

### Step 1.5c — Apply Summaries to READMEs

After all pending entries have been populated with real summaries, invoke
`--auto-apply` to push them into the README files:

```bash
python3 ~/blueprint-workflows/scripts/doorway/doorway.py \
  --workspace {WORKSPACE_PATH} \
  --auto-apply \
  --quiet
```

### Step 1.5d — Verify

Confirm at least one README was updated by checking one of the pending
directories:

```bash
head -20 {WORKSPACE_PATH}/{FIRST_PENDING_FOLDER}/README.md
```

The `<!-- BREADCRUMB -->` section must contain the generated agentic summary,
not `[PENDING AGENT SUMMARIZATION]` or `Auto-generated summary for navigation`.

If the placeholder is still present: re-run Step 1.5c with `--full-scan` flag.
If it persists after retry: log `[SENTINEL] BREADCRUMB POPULATION FAILED for
{folder}` and continue — do not halt the session for a breadcrumb write failure.

**STRICT RULE for this phase**: Never write prose summaries. Always use the
compact key:value agentic format. Human-readable explanation belongs in the
human-authored sections of the README (above/below the BREADCRUMB tags). The
BREADCRUMB tag region is exclusively for LLM rapid context ingestion.

---

## PHASE 1.6 — PLAN & TASKS FORMAT CHECK (SILENT)

**[ADDED 2026-07-07 — Sovereign Redesign Cluster Stage 5, PILLAR_04_POST_BUILD_HYGIENE_ARCHIVAL_NODELETE.md §4.5]**

**Objective**: Ensure the target workspace has canonical `tasks.md` and `implementation-plan.md`
files, seeded from this suite's own `templates/plan/` when genuinely absent — the earliest point
in a session a fresh workspace can receive the marker-ready format the Completion Marking
sub-pass (`/implementation-plan --audit` Phase 5) and `/nodelete` Pillar 6 both consume.

**Safety note**: this step is unconditionally safe to run live, every session, because the
populator itself (`scripts/plan/ensure_plan_templates.py`) never overwrites a file that has real
content — that invariant lives in the tool, not in a flag sentinel must remember to pass. See
GLOSSARY: Plan & Tasks Format Check.

**Known, discovered limitation — [ADDED 2026-07-07, found live during this stage's own build]**:
"absent at root" is a mechanical, root-only presence check. A mature workspace that intentionally
tracks its plan elsewhere (e.g. this very suite: `blueprint-workflows` has no root `tasks.md` by
convention — it uses per-campaign `implementation-plan/<name>/tasks.md`) will still receive a
literal, unfilled root-level placeholder the first time this step runs there, since the populator
cannot distinguish "genuinely new project" from "mature project, different convention" — it was
deliberately not built with that heuristic (out of Task 5.3's scope; a real check would need
false positives evaluated before adding complexity). The placeholder is harmless on disk but
would confuse `/execute-build`'s default root-relative `tasks.md` lookup if left in place and
later invoked without an explicit path. Review the Phase 3 report's PLAN & TASKS FORMAT line
after the first run in any workspace; delete the populated file if the workspace intentionally
uses a different convention. This is a one-time consideration per workspace — the populator is
idempotent and will not re-offer once the file exists (whether real or placeholder).

### Step 1.6a — Run the Populator

```bash
python3 ~/blueprint-workflows/scripts/plan/ensure_plan_templates.py \
  --workspace {WORKSPACE_PATH} \
  --workspace-confirmed \
  --output-json
```

**`--workspace-confirmed` is passed here only because the workspace was confirmed in Step 0a.1
(or given as an explicit `--workspace` argument).** Without it the populator reports what it would
do but writes nothing (`skipped_unconfirmed`) — the same defense-in-depth guard as Step 1d,
enforced in `ensure_plan_templates.py`'s WORKSPACE-CONFIRMATION GATE. Omit the flag if the
workspace was not confirmed. **[ADDED 2026-07-21 — resolves follow-up (b) of CLOSED_20260716_sentinel_workflow.md.]**

### Step 1.6b — Store the Result

Parse the JSON report's `summary` block (`populated`, `skipped`, `errors`) and each entry in
`actions` (`file`, `action`, `reason`). Store as `<PLAN_FORMAT_RESULT>` for the Phase 3 report.

If `errors > 0`: do not halt the session — a missing `templates/plan/` directory or unreadable
template is a suite-installation issue, not a workspace drift finding. Note it in the Phase 3
report's Plan & Tasks Format line and continue.

---

## PHASE 2 — TRIAGE CLASSIFICATION (SILENT)

**Objective**: Classify findings by severity and determine routing.

### Step 2a — Severity Tally

Count findings by tier:
```
HIGH   = count of recommendations where severity == "HIGH"
MEDIUM = count of recommendations where severity == "MEDIUM"
LOW    = count of recommendations where severity == "LOW"
INFO   = count of recommendations where severity == "INFO"  # [ADDED 2026-07-07 — see GLOSSARY Severity Tier correction; SEQ-SUBSTRATE-MAINTAIN emits INFO and was previously silently excluded from every tally]
TOTAL  = len(recommendations)
```
`HIGH + MEDIUM + LOW + INFO` must equal `TOTAL`. If it does not, a recommendation is using a severity value not accounted for here — treat that as a finding in its own right (the same drift this file's own Phase 5.2 engine now checks for) rather than silently under-counting.

Also count raw drift:
```
STRUCTURAL_MUTATIONS = len(new) + len(deleted)   # most serious: structural change
CONTENT_DRIFT        = len(modified)              # content changed but structure intact
HYGIENE_GAPS         = len(unowned) + len(missing_readme)  # Tier-2 only; does not affect zero_finding (Tier-1)
```

### Step 2b — Routing Map Construction

**[ENGINE-BACKED — ADDED 2026-07-07, implementation-plan.md Phase 5.2]** This table documents `scripts/doorway/recommender.py`'s actual behavior — it does not decide routing itself. Read `recommendations[].workflow` directly from the Doorway JSON (Phase 1c) rather than re-deriving it from this table; the table exists for human readability and is verified against the engine's real source below. **This table was found live-drifted from the engine during Phase 5.2's Honest-Design Discipline pass** (two real defects: a missing row for a duplicate-emitting ID, an undocumented severity value) — verify it stays current with:

```bash
python3 ~/blueprint-workflows/scripts/sentinel/sentinel_audit.py \
  --recommender-py ~/blueprint-workflows/scripts/doorway/recommender.py \
  --sentinel-md ~/blueprint-workflows/claude-commands/sentinel.md \
  --output-json
```

Read `parity.missing_from_table` and `parity.undercounted_ids` (an ID the engine emits from more distinct blocks than the table has rows for — the specific defect shape found live in this file) and `parity.undocumented_severities`. A non-empty result means this table (or the GLOSSARY's Severity Tier list) has drifted from `recommender.py`'s actual behavior and needs a correction, same as this entry's own fix. If the engine is unavailable: fall back to reading `recommender.py`'s source directly and comparing by eye.

| Doorway Protocol ID | Workflow Trigger | When to route |
|---------------------|-----------------|---------------|
| SEQ-SUBSTRATE-HEALTH | `/investigate` | New or deleted directories detected |
| SEQ-SUBSTRATE-HEALTH | `/investigate` | Tier-1 index freshness or ownership-completeness issue detected (`stale_index`/`ownership_incomplete`) — **row added 2026-07-07, was previously undocumented despite the engine emitting it since PR 01-02** |
| SEQ-SUBSTRATE-HYGIENE | `/document` | Unowned directories found |
| SEQ-SUBSTRATE-MAINTAIN | `/document` | Missing READMEs found (Tier-2 hygiene only; promote only if Tier-2 configured or explicit) — severity `INFO` |
| SEQ-SUBSTRATE-ASSIMILATE | `/focus-plan` | Broad modification sweep (>5 dirs changed) |
| SEQ-STRATEGIC-ARCHIVAL | `/investigate` | Deleted directories detected |
| `(scan_failure)` | `/helpdesk-tickets` | Doorway scan itself failed |

Additional automatic routing rules (applied after Doorway recommendations):
- If `metrics.repairs > 0`: notify the user that self-healing occurred (READMEs were created). No workflow routing needed — informational only.
- If `zero_finding == true` AND `metrics.repairs == 0`: route to nothing — report ZERO-FINDING STATE.
- If `zero_finding == true` AND `metrics.repairs > 0`: route to `/document` to review what was auto-generated.
- Index freshness (Tier 1 from substrate_index) and bootstrap tags (inaugural [BOOTSTRAP]) are reported but do not auto-route unless structural drift present. missing_readme (Tier 2) does not route to /document by default.

### Step 2c — Ticket Threshold Check

If any recommendation has `severity == "HIGH"`: prepare a helpdesk ticket (will be filed in Phase 3 after the report, unless the user opts out).

---

## PHASE 3 — SENTINEL REPORT

**Objective**: Surface the full diagnosis and routing map to the user.

Produce the following report format. Fill every field. No field may be omitted.

```
╔════════════════════════════════════════════════════════════════════╗
║                    SENTINEL — SESSION REPORT                       ║
╠════════════════════════════════════════════════════════════════════╣
║ Workspace:     {WORKSPACE_PATH}
║ Scanned At:    {TIMESTAMP_UTC}
║ Scan Duration: {overhead_seconds}s
║ Directories:   {total_directories} scanned, {skipped} hash-matched (unchanged)
║ Context Source: docs/FOLDER_OWNERSHIP.md + .doorway/substrate_index.json (primary per Invariant)
╠════════════════════════════════════════════════════════════════════╣
║ SUBSTRATE STATE: [ZERO-FINDING (Tier 1)] / [DRIFT DETECTED] / [Tier 2 hygiene only]
╠════════════════════════════════════════════════════════════════════╣
║ DRIFT SUMMARY:
║   New directories:         {len(drift.new)}     {drift.new if non-empty}
║   Modified directories:    {len(drift.modified)} {drift.modified if non-empty}
║   Deleted directories:     {len(drift.deleted)}  {drift.deleted if non-empty}
║   Unowned directories:     {len(drift.unowned)}  {drift.unowned if non-empty}
║   Missing READMEs:         {len(drift.missing_readme)} {drift.missing_readme if non-empty} (Tier 2)
║   Self-healing repairs:    {metrics.repairs} (READMEs auto-created)
║   Substrate Index:         freshness checked; zero_finding = Tier 1 (index+ownership) only; see .doorway/substrate_index.json for full payload + summaries
╠════════════════════════════════════════════════════════════════════╣
║ PLAN & TASKS FORMAT:
║   {For each action in <PLAN_FORMAT_RESULT>.actions:} {file}: {action} — {reason}
║   Summary: {populated} populated, {skipped} skipped, {errors} errors
╠════════════════════════════════════════════════════════════════════╣
║ FINDINGS:
║   {For each recommendation:}
║   [{severity}] {id} → {workflow}
║        {reason}
╠════════════════════════════════════════════════════════════════════╣
║ ROUTING MAP:
║   {For each unique workflow in recommendations:}
║   → {workflow}  [{severity}]  {count} finding(s)
╠════════════════════════════════════════════════════════════════════╣
║ TICKET STATUS: [NONE] / [FILING — HIGH severity finding(s) detected]
╚════════════════════════════════════════════════════════════════════╝
```

After the report block, print:

```
[SENTINEL] Recommended next action: {TOP_PRIORITY_WORKFLOW} — {REASON}
[SENTINEL] To proceed: invoke /{workflow_name} or type 'proceed' to accept routing.
[SENTINEL] To skip: type 'skip' or invoke any other workflow directly.
```

If `zero_finding == true` AND `metrics.repairs == 0`:
```
[SENTINEL] ZERO-FINDING STATE (Tier 1) — context from FOLDER_OWNERSHIP.md + .doorway/substrate_index.json; workspace substrate integrity verified.
[SENTINEL] No workflow routing required. Session is clear to proceed.
```

---

## PHASE 4 — POST-REPORT ACTIONS

### Step 4a — Helpdesk Ticket Filing (conditional)

If `severity == "HIGH"` findings exist AND the user has not opted out:

Invoke `/helpdesk-tickets` with the following pre-filled context:
```
Source:    /sentinel automated triage
Workspace: {WORKSPACE_PATH}
Severity:  HIGH
Findings:  {list of HIGH recommendations from drift report}
Trigger:   Session initialization scan — {TIMESTAMP_UTC}
```

Ticket status: OPEN. Assigned to: the session agent (you).

The ticket is informational — it records that the session began with a known HIGH finding.
It does not block the session. The user may acknowledge and proceed.

### Step 4b — User Routing Decision

After the report and any ticket filing:
- If the user types or says `proceed`: invoke the top-priority recommended workflow in the routing map.
- If the user names a specific workflow: invoke that workflow instead.
- If the user types `skip` or says nothing within the session: Sentinel exits silently. No further action.
- If the user types `rescan`: re-execute Phase 0 through Phase 3 with `--full-scan` flag to force deep traversal.

### Step 4c — Multi-Workspace Mode

If the user provides multiple `--workspace` paths (space-separated), run Phases 0–3 for each
workspace sequentially. Aggregate the results into a single Sentinel Report with a section per
workspace, then produce a unified Routing Map that covers all workspaces.

---

## STRICT RULES (never violate)

1. **Sentinel is read-only.** The only filesystem writes permitted during Phases 0–3 are within `{workspace}/.doorway/` — the Doorway state directory. No workspace substrate files, no workflow files, no project code files may be modified. If you find yourself about to write to a project file, stop. **[EXCEPTION — INJECTED 2026-06-12, ticket 20260612_gitignore-seeder_module.md]** Step 1d's gitignore seeder is an explicitly authorized write channel for exactly one project file, `{workspace}/.gitignore`, and only the managed block between its markers. The write is non-destructive (the user's existing entries are never touched), additive-only, and idempotent — on par with doorway.py's README self-healing. **[EXCEPTION — ADDED 2026-07-07, Sovereign Redesign Cluster Stage 5]** Step 1.6's plan populator (`scripts/plan/ensure_plan_templates.py`) is a third explicitly authorized write channel, for exactly `{workspace}/tasks.md` and `{workspace}/implementation-plan.md`. The write is create-only — the populator's own Safety Invariant refuses to touch either file if it already has any non-whitespace content, force or no force (see `ensure_plan_templates.py` module docstring). No other project-file write is permitted. **[ADDED 2026-07-21 — defense-in-depth: BOTH authorized write-channel scripts (`gitignore_seeder.py`, `ensure_plan_templates.py`) now additionally require an explicit `--workspace-confirmed` flag before writing; their CLIs default to NOT writing. /sentinel passes the flag only after Step 0a.1 confirms the workspace (STRICT RULE 9), so an agent that skips the gate also omits the flag and the write fails safe. The Safety Invariant protects a workspace's *existing* files; this guard protects against writing to the *wrong* workspace. Resolves follow-up (b) of CLOSED_20260716_sentinel_workflow.md.]**
2. **One question rule.** If the workspace path cannot be resolved, ask exactly one question. Do not ask for additional context. The user answers; you proceed.
3. **No autonomous downstream execution.** Sentinel surfaces the routing map and waits for the user to confirm. It does not invoke `/investigate`, `/document`, or any other workflow without explicit user acknowledgment. The exception is helpdesk ticket filing (Phase 4a) — this is always autonomous when HIGH findings are present.
4. **Halt on scan failure.** If `doorway.py` exits non-zero or produces unparseable JSON, do not attempt to interpret the error or produce a partial report. File a helpdesk ticket and halt.
5. **System path protection.** Refuse to scan `/etc`, `/usr`, `/bin`, `/sbin`, `/lib`, `/proc`, `/sys`, or any path that is a direct child of `/home` (i.e., `/home` itself, not a user's home directory subdirectory). Print: `[SENTINEL] Refused: system path scanning is not permitted`.
6. **No jargon without definition.** Every technical term in the report that the user might not know must be defined inline on first use. Example: "hash-matched (meaning the directory's content fingerprint has not changed since the last scan)".
7. **Confidence is declared.** The Sentinel Report must declare its scan confidence: HIGH (doorway.py ran successfully and produced valid JSON), MEDIUM (partial JSON, some fields missing), or LOW (doorway.py failed, report is estimated from last snapshot). A report without a confidence declaration is incomplete.
8. **Mute Witness on all workspace files.** Even if a README is corrupt or missing in the target workspace, do not rewrite it. The `doorway.py` script's self-healing is the only authorized write channel for workspace content during a sentinel scan **(plus the gitignore seeder's managed-block write and the plan populator's create-only write — see the Rule 1 exceptions)**. Engine owns context delivery (index + ownership file). If you observe corruption, report it — do not fix it yourself.

9. **Inferred workspace requires confirmation (never silent).** A workspace path resolved by session-context inference (Step 0a priority 2) must pass Step 0a.1's Inference Confirmation Gate before any scan or authorized write (Rule 1's channels) occurs — an explicit `y` in an interactive session, a fall-through to the priority-3 prompt on `n`, or a fail-closed halt when no confirmation is possible. An explicitly declared `--workspace` path (priority 1) is exempt: it is trusted by declaration. This complements Rule 2 (which governs the *unresolvable*-path prompt); Rule 9 governs the *inferred-but-resolved* path — the case where the agent has an answer but not yet an authorized one. **[ADDED 2026-07-21, resolves helpdesk-tickets/20260716_sentinel_workflow.md.]**

**Doorway Design Invariant:** "Agent context is delivered by the engine (JSON index + ownership file), not by filesystem cardinality (N × README.md). Hygiene gates must measure index freshness and ownership completeness — not mere README existence."

---

## ACTIVATION

When invoked, immediately execute Phase 0 (Workspace Resolution).
Phase 1 and Phase 2 execute silently — the user sees nothing until Phase 3 (Sentinel Report).

Exception: the pre-flight failure halt (Phase 0b) and the scan failure halt (Phase 1b) surface immediately — the user cannot wait for a report that cannot be produced.

**Explicit invocation forms:**
- `/sentinel` — scan the inferred workspace from session context (an inferred path passes Step 0a.1's Inference Confirmation Gate before any scan or write)
- `/sentinel --workspace /abs/path` — scan a specific workspace
- `/sentinel --workspace /path1 /path2` — multi-workspace scan
- `/sentinel --workspace /path --full-scan` — force deep scan (bypasses hash cache)
- `/sentinel --workspace /path --no-ticket` — suppress automatic helpdesk ticket filing
- `/sentinel --workspace /path --context-only` — fast path: substrate_index + ownership + zero_finding (minimal briefing)
- `/sentinel --workspace /path --materialize-readmes` — optional human README materialization from index (non-core)

---

## INTEGRATION WITH OTHER WORKFLOWS

```
/focus-plan     → verifies intent/plan/substrate alignment before sentinel is useful
/sentinel       → THIS WORKFLOW — session-init ambient monitor
   └─ Step 2b   → scripts/sentinel/sentinel_audit.py (Recommender/Routing-Table Parity)
/triage         → sentinel informs triage; triage is reactive (on-demand), sentinel is proactive (session-init)
/investigate    → sentinel routes here when structural mutations (new/deleted dirs) are detected
/document       → sentinel routes here for hygiene gaps (unowned dirs, missing READMEs)
/focus-plan     → sentinel routes here when broad content drift (>5 modified dirs) is detected
/harden         → run after /investigate identifies a security finding
/helpdesk-tickets → sentinel files tickets automatically for HIGH severity findings
```

**Relationship to /triage:**
`/sentinel` and `/triage` are architecturally distinct:
- `/triage` is reactive: the user invokes it when something feels wrong.
- `/sentinel` is proactive: it runs at session initialization and reports before any question is asked.
- Both route to the same downstream workflows — but sentinel's evidence is physical substrate state, while triage's evidence is user-described symptoms.
- They are complementary, not redundant. Running `/sentinel` then `/triage` gives both physical and symptomatic evidence before any work begins.
- **Primary handover artifact**: `.doorway/substrate_index.json` (plus FOLDER_OWNERSHIP.md) — engine context delivery; referenced by triage/secretary/SUITE_HEALTH.

---

## SCRIPTS DEPENDENCY

```
Required: ~/blueprint-workflows/scripts/doorway/doorway.py
Optional: ~/blueprint-workflows/scripts/gitignore/gitignore_seeder.py  (Step 1d — non-fatal if absent)
Optional: ~/blueprint-workflows/scripts/plan/ensure_plan_templates.py  (Step 1.6a — non-fatal if absent)
Runtime:  python3 (stdlib only — hashlib, os, pathlib, json, argparse, datetime, tomllib, subprocess)
Data dir: {workspace}/.doorway/ (auto-created on first scan; owner-only 0o700)
  - substrate_index.json is primary context/handover artifact (FOLDER_OWNERSHIP + index)
Writes:   {workspace}/.gitignore managed block (Step 1d only; non-destructive, idempotent)
Writes:   {workspace}/tasks.md + {workspace}/implementation-plan.md (Step 1.6a only; create-only,
          never touches a file with existing content — see STRICT RULE 1)
```

If the scripts path changes: update the script path in Phase 0b (Pre-flight Validation),
Phase 1a (Execute the Scan), Phase 1d (Gitignore Hygiene Seed), and Phase 1.6a (Plan & Tasks
Format Check).

---

### Change Log
1. **2026-05-10**: `[CREATED — Phase 5 of Doorway Extraction, /focus-plan + /quality + /nodelete]`
   Sovereign-grade initial build. Resolves TODO ITEM 1 (Divergence #2 — /sentinel ambient monitor).
   P/P architecture. 4-phase protocol: Workspace Resolution (0), Doorway Scan (1), Triage Classification (2), Sentinel Report (3), Post-Report Actions (4). 8 STRICT RULES. GLOSSARY with 10 terms. Full integration map. Routing table: 6 Doorway protocol IDs mapped to global_workflows workflow triggers. Multi-workspace mode documented. Ticket threshold gate (HIGH → auto-file). Mute Witness enforcement. HOW TO BEGIN activation block. Resolves all 4 Discussion Points from TODO ITEM 1. Standard Version: 1.
2. **2026-05-15**: `[INJECTED — /harden-workflow --ticket 20260514_sentinel_workflow.md + /focus-plan + /quality + /nodelete]`
   Resolved two bugs surfaced by helpdesk ticket and session clarification:
   (a) Bug #1 — Template verbatim-clone: Fixed in `integrity.py` via new `_expand_template()` method that dynamically enumerates workspace top-level directories and replaces `[DIRECTORY_LIST_PLACEHOLDER]` before any template is written to disk.
   (b) Bug #2 — Permanent `[PENDING AGENT SUMMARIZATION]` placeholders: Fixed by injecting **Phase 1.5 (Agent Breadcrumb Population)** into this workflow. After doorway.py runs, the agent now reads `context_updates.log`, samples key files in each pending directory, generates a compact agentic-language summary in `MODULE:{x} TYPE:{x} LANG:{x} FILES:{x} PURPOSE:{x} DEPS-DETECTED:{x}` key:value format optimized for LLM ingestion (not human readability), writes summaries back to the log, and pushes them into READMEs via `--auto-apply`. The BREADCRUMB region in every README is now populated with real semantic content on the first /sentinel run.
   (c) `README.md.template`: Removed hardcoded `.blueprints architecture` project-specific reference; replaced with neutral `Sovereign Workspace Substrate architecture`.
   (d) `breadcrumb.py:propose()`: Enhanced to enumerate and include directory file inventory (names, count, subdirectory list) in the log entry, giving the LLM agent in Phase 1.5 the structural facts it needs without an additional filesystem scan. All changes follow /nodelete discipline. Standard Version: 2.
3. **2026-05-21**: `[PORTED — Claude Code migration]` Pointer/Payload architecture retired. Merged into single command file at `~/blueprint-workflows/claude-commands/sentinel.md`. All doorway.py paths updated: `/home/jwils/.gemini/antigravity/global_workflows/scripts/doorway/doorway.py` → `~/blueprint-workflows/scripts/doorway/doorway.py` (Phase 0b, Phase 1a, Phase 1.5c, SCRIPTS DEPENDENCY). Phase 1.5b Step 2: `view_file` → Read tool. Phase 1.5b Step 4: `run_command` → Bash tool. SCRIPTS DEPENDENCY stale-path update note reworded to drop pointer-file reference.
4. **2026-06-12**: `[INJECTED — ticket 20260612_gitignore-seeder_module.md, /nodelete]` Gave /sentinel a gitignore-hygiene responsibility. (a) New **Step 1d (Gitignore Hygiene Seed)** in Phase 1: invokes `scripts/gitignore/gitignore_seeder.py --workspace {PATH} --output-json`, which writes a non-destructive, idempotent managed block (`.history/`, `quarantine/`, `.workflow_state/`, security + noise patterns) into the workspace `.gitignore` from an editable `seed.toml`, and runs a detect-and-warn pass intersecting security patterns with `git ls-files`. Already-tracked secrets become a HIGH finding routed to `/gitclean --mode a` (gitignore stops only *future* leaks; history rewrite is /gitclean's job). Seeder failure is non-fatal (unlike the doorway scan halt, Rule 4). (b) **STRICT RULE 1** reconciled via a marked EXCEPTION: the seeder's managed-block write to `{workspace}/.gitignore` is an explicitly authorized write channel (the only project-file write permitted), on par with doorway's README self-healing. (c) **STRICT RULE 8** annotated to acknowledge the second authorized write channel. (d) SCRIPTS DEPENDENCY updated (seeder path, `tomllib`/`subprocess` runtime, `.gitignore` write note). Standard Version: 2.
5. **2026-07-06**: `[UPDATED — PR pr-01-04, per PILLAR_01_CONTEXT_SESSION_INITIALIZATION.md + DESIGN_Sovereign_Redesign_Cluster_Canonical.md (Phase B)]` Sentinel workflow update: GLOSSARY (zero_finding as Tier-1, substrate_index term + refs); Phase 1.5 re-scoped/optionalized (agent enrichment on index entries, default skip, --enrich-breadcrumbs, LLM walk removed from core); Phase 2 routing (missing_readme Tier-2 only, no default /document; added index_freshness + bootstrap handling); Phase 3 report (substrate_index freshness, Tier breakdown, "context from FOLDER_OWNERSHIP + .doorway/substrate_index.json"); STRICT RULES (Mute Witness + "Engine owns context delivery (index)", Doorway Design Invariant stated verbatim); INTEGRATION/SCRIPTS (substrate_index primary handover); ACTIVATION (document --context-only, --materialize-readmes); parse/report updates for new substrate. All /nodelete (inject + append only). Follows existing patterns; smallest targeted changes.
6. **2026-07-07**: `[INJECTED — Sovereign Redesign Cluster Stage 5, PILLAR_04_POST_BUILD_HYGIENE_ARCHIVAL_NODELETE.md §4.5, /nodelete]` Added **Phase 1.6 — Plan & Tasks Format Check**, immediately after Phase 1.5 and before Phase 2: calls `scripts/plan/ensure_plan_templates.py --workspace {PATH} --output-json`, the canonical populator, to seed a genuinely-absent `tasks.md`/`implementation-plan.md` from `templates/plan/`. Safe to run live unconditionally — the populator's own Safety Invariant (not a sentinel-side check) refuses to touch a file with any real content, matching the gitignore seeder's precedent (Change Log entry 4) of an explicitly authorized, narrow, non-destructive write channel. GLOSSARY: "Plan & Tasks Format Check" term added; "Mute Witness" entry annotated with a dated note rather than rewritten. STRICT RULE 1 gets a third named exception (following the exact pattern of the 2026-06-12 gitignore-seeder exception); STRICT RULE 8's parenthetical updated to match. Phase 3 report template gets a new "PLAN & TASKS FORMAT" block, positioned after DRIFT SUMMARY and before FINDINGS per the governing design's own placement spec. SCRIPTS DEPENDENCY: new optional dependency + a second `Writes:` line, scoped to exactly the two files, create-only. Frontmatter: `phase_count` 6→7, `platform_requirements.file_write` false→true (Phase 1.5's existing conditional `--auto-apply` write already made this field stale before this entry — not fixed retroactively here, out of this stage's scope, but not compounded either: this entry's own new write channel is now accurately declared). `version` 2→3.
7. **2026-07-07**: `[BUILT — Recommender/Routing-Table Parity Engine, Verification-Spine Upgrade, implementation-plan.md Phase 5.2, /nodelete]` Ran Honest-Design Discipline fresh against this file — result staged at `docs/compression-staging/sentinel-honest-design.md`. **Finding: the seed design's assumed gap (a "drift-delta layer" augmenting `doorway.py`) does not exist** — `doorway.py`'s own snapshot/hash-compare mechanism already computes session-over-session drift; nothing needed building there. **The real gap, found by direct comparison rather than assumption**: Step 2b's Routing Map table hand-duplicates logic `scripts/doorway/recommender.py` already owns and emits per-recommendation via its own `workflow` field — diffing the table against the engine's actual source (not just reading the table's claim about itself) found it had ALREADY DRIFTED, live, two ways: (1) `recommender.py` emits a SECOND `SEQ-SUBSTRATE-HEALTH` recommendation for Tier-1 index/ownership issues (`stale_index`/`ownership_incomplete`) with no corresponding table row at all — a genuine ID-presence check would have missed this since the ID string already existed in the table under a different condition, so the engine's checker specifically counts BLOCK OCCURRENCES per ID against TABLE ROWS per ID, not mere presence; (2) `recommender.py` emits `severity: "INFO"` for `SEQ-SUBSTRATE-MAINTAIN`, but the GLOSSARY's Severity Tier term and Step 2a's Severity Tally only ever named/counted HIGH/MEDIUM/LOW — an INFO recommendation was silently excluded from every tally while still counting toward `TOTAL`. **Both defects fixed directly, same session**: added the missing Tier-1-issues row to Step 2b's table; added INFO to the Severity Tier GLOSSARY term and Step 2a's tally with an explicit `HIGH+MEDIUM+LOW+INFO == TOTAL` invariant check. **Built `scripts/sentinel/`**: `recommender_parity.py` (`extract_recommender_triples()` — regex over `recs.append({...})` blocks; `extract_routing_table()` — parses Step 2b's markdown table; `compute_parity()` — set-difference PLUS a Counter-based occurrence-vs-row-count check, the specific mechanization needed to catch the duplicate-ID defect an ID-presence check alone would have missed), `reporter.py`, `sentinel_audit.py` CLI. 14 new tests (`scripts/tests/test_sentinel_evidence.py`) including a read-only invariant test and — critically — REGRESSION tests proving the checker actually catches both real defects found in this repo's own (pre-fix) file, not just clean-input tests. Full suite 411/411 passing (up from 397 pre-task). Live-run against the real `recommender.py`/`sentinel.md` pair confirmed `PARITY: CLEAN` after the fix, `UNDERCOUNTED`/`UNDOCUMENTED SEVERITIES` findings before it. Wired Step 2b with a live verification command and an explicit note that this table was found drifted during this exact pass. GLOSSARY term added (Recommender/Routing-Table Parity Engine). `scripts/sentinel/sentinel_audit.py` added to frontmatter `dependencies`. No STRICT RULE added — the engine verifies documentation accuracy, not a new behavioral constraint. Frontmatter: version 3→4, `last_hardened` 2026-07-07, `content_hash` recomputed via `--fix-hashes`. `strict_rule_count`/`phase_count` unchanged. Resolves `helpdesk-tickets/CLOSED_20260707_sentinel-engine-gap_workflow.md`. Standard Version: 3
8. **2026-07-21**: `[REMEDIATED — SUBSTANTIVE-LOGIC direct remediation, resolves helpdesk-tickets/20260716_sentinel_workflow.md]` **Defect (Context Erosion):** Step 0a priority (2) "Session context inference" resolved a workspace from open-document paths and proceeded straight through Step 0b → Phase 1 → the Phase 1.5/1.6 authorized write channels, with no confirmation and no deference to an explicitly declared workspace. A live Antigravity session inferred `.theLordsLM` (from open files) while the session's declared workspace was `lsshreveport`, and `ensure_plan_templates.py` seeded the wrong workspace. **Fix (surgical, upstream, single gate):** added **Step 0a.1 — Inference Confirmation Gate** — a path resolved by inference (priority 2) is now never scanned or written to until the user confirms it (explicit `y` proceeds; `n` falls through to the priority-3 prompt); annotated priority (2) as PROVISIONAL and restated that explicit `--workspace` (priority 1) always outranks inference. The gate sits upstream of Step 0b so a single checkpoint protects every downstream read and every Rule-1 authorized write (breadcrumbs, `.gitignore`, `tasks.md`/`implementation-plan.md`). **Divergence-surfaced hardening folded in** (contextual `/divergence` pass, this session): the gate is defined *fail-closed* for non-interactive/headless/autonomous runs — where no human can answer y/n, it refuses and halts with a re-invoke-with-`--workspace` message rather than proceeding on a guess or hanging (closes the deadlock a naive y/n gate would create under `/loop`/`/schedule`). **STRICT RULE 9 added** (`strict_rule_count` 8→9) encoding the gate and distinguishing it from Rule 2 (which governs the *unresolvable*-path prompt; Rule 9 governs the *inferred-but-resolved* path). GLOSSARY: "Inference Confirmation Gate" term added; "Session Context" row annotated. ACTIVATION `/sentinel` line annotated. **Deliberately NOT built (flagged as follow-ups, out of surgical scope):** (a) a new priority tier preferring the session's declared working directory over open-doc inference — an engine-specific semantic change with its own ambiguity (cwd is not always the intended target, which is why `--workspace` exists); (b) a script-level write guard in `ensure_plan_templates.py`/`doorway.py` keyed off resolution provenance (defense-in-depth so the boundary survives an agent that skips the prose gate); (c) extraction of a shared workspace-resolution primitive across `/sentinel`/`/triage`/`/onboard`/`/focus-plan` (the same inference-without-confirmation pattern likely lives in those too — a genuine Phylogeny-transfer candidate, noted, not propagated in this single-file remediation). Verification: full suite green, `sentinel_audit.py` PARITY CLEAN, `lint_workflows.py` CLEAN on this file. `phase_count` unchanged (0a.1 is a sub-step, not a new `## PHASE`). Frontmatter: `version` 4→5, `last_hardened` 2026-07-21 (following this file's entry-6/7 convention of dating substantive Sovereign-maintenance injections), `content_hash` recomputed via `--fix-hashes`. Closes via the Substantive/Logic path (Remediation Record), not `/harden-workflow`. Standard Version: 3
9. **2026-07-21**: `[BUILT — Follow-up (b) from entry 8: script-level workspace-confirmation guard, SUBSTANTIVE-LOGIC, user-authorized]` Entry 8 flagged a script-level write guard as a deliberately-deferred follow-up; the user approved building it this same session (the other two follow-ups were resolved by verification — (c) DROPPED, (a) PARKED; see end of entry). **What was built — defense-in-depth, one layer below Step 0a.1's prose gate:** both of /sentinel's authorized write-channel scripts, `scripts/plan/ensure_plan_templates.py` (Phase 1.6) and `scripts/gitignore/gitignore_seeder.py` (Step 1d), gained a `--workspace-confirmed` CLI flag. **Their CLIs now default to NOT writing**: without the flag the populator reports `skipped_unconfirmed` and the seeder reports `wrote:false / write_skipped_reason:"workspace not confirmed"`, each writing nothing. The class APIs default `confirmed=True` (a programmatic caller is trusted); only the agent-facing CLI defaults to unconfirmed — the boundary where an inferred workspace is the documented risk. Net effect: an agent that skips Step 0a.1 also omits `--workspace-confirmed`, so the write fails safe rather than silently landing in a wrong workspace (the exact ticket failure). The seeder's read-only secret scan still runs when unconfirmed — only the WRITE is gated. **Scope note (post-approval expansion, disclosed per role.md):** the approval named the populator + doorway; doorway's README autoheal was already opt-in (default off, meta §5.1), so the actionable new target was the populator. The gitignore seeder — the same class of authorized write channel — was included on the same defense-in-depth principle, since guarding one write channel and leaving its sibling unguarded would just invite a future ticket; flagged explicitly here rather than absorbed silently. **Verification:** 9 new tests (467→476; 4 populator + 5 seeder, including CLI-default-fail-safe tests and one proving the seeder's read-only scan still runs when unconfirmed); full suite green; live end-to-end subprocess runs of both CLIs confirmed no-write-without-flag / write-with-flag. `sentinel.md` wiring: Step 1d + Step 1.6a invocations now pass `--workspace-confirmed` with an explicit conditional note (passed only because Step 0a.1 confirmed the workspace; omit if not), and STRICT RULE 1 annotated to record the code-level enforcement. No new STRICT RULE (Rule 9 already requires confirmation before writes; this enforces it in code). `phase_count`/`strict_rule_count` unchanged. Frontmatter: `version` 5→6, `content_hash` recomputed via `--fix-hashes`, `last_hardened` unchanged at 2026-07-21 (same session). **Follow-ups NOT built:** (c) shared workspace-resolution primitive — DROPPED after reading `/triage`, `/onboard`, `/focus-plan` and confirming none do open-doc inference (they use cwd `.` or an explicit param), so there is no shared pattern to extract; (a) declared-cwd priority tier — PARKED (the confirmation gate already covers the fragile deepest-common-ancestor case). Standard Version: 3
