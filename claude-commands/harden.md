---
description: "Hardening and securing selected script files — Universal Security Hardening Workflow with 19-item checklist and Diamond/Gold/Silver/Bronze grading"
type: audit
grade: Sovereign
version: 3
content_hash: "sha256:2275daafefe83ae1"
last_hardened: "2026-06-02"
strict_rule_count: 15
phase_count: 4
context_retention: medium
flags: []
dependencies:
  - "scripts/harden/harden_audit.py"
triggers:
  - "/triage"
  - "/execute-build"
  - "/redteam"
produces:
  - ".workflow_state/receipts/HARDEN_GRADES.md"
consumes: []
platform_requirements:
  file_write: true
  shell_exec: true
  git_access: true
---

## GLOSSARY

| Term | Definition |
|------|------------|
| **Threat Context** | Classification of a script's attack surface: NETWORK-FACING, PRIVILEGED, DATA-HANDLING, or INTERNAL-ONLY. Determines checklist scrutiny weighting. |
| **Hardening Grade** | The post-hardening quality rating for a file: Diamond, Gold, Silver, or Bronze. Defined by remaining finding severity. |
| **Re-ingestion** | The mandatory step of re-reading the full updated file content after every diff is applied. Skipping re-ingestion is a protocol violation. |
| **Checklist exit criterion** | The hardening loop exits when the full checklist passes with zero CRITICAL or HIGH findings — not when a fixed pass count is reached. |
| **Baseline commit** | A clean git commit created before any file is touched, establishing a reversible point. Required. |
| **Credential scan** | A grep-based cross-workspace search for hardcoded secrets, executed in Phase 0 before per-file work begins. |
| **Force-multiplier file** | A shared utility imported by multiple scripts. Hardening it has amplified security benefit across all callers. |
| **Hallucinated Success** | Agent reports a file as hardened without having executed or validated the actual changes. A named failure pattern — if detected, file it as a helpdesk ticket and re-run from Phase 2b. |
| **Ghost Logic** | Security-relevant behavior (credential access, privilege escalation, external calls) occurs in the script with no corresponding log evidence. Flag as CRITICAL finding in Phase 2c. |
| **Sound Effect Execution** | The hardening diff applies cleanly and syntax passes, but the security control it introduces is never actually reached at runtime. A subset of Mock Trap — validate with runtime path analysis, not just syntax check. |
| **Injection cap** | Retired concept in Claude Code. No injection cap exists; all commands are single merged files. |
| **NETWORK-FACING** | Script processes webhook payloads, HTTP requests, or external API calls. Highest threat tier. |
| **PRIVILEGED** | Script runs as root/sudo, modifies system state, or manages credentials. Second-highest threat tier. |
| **DATA-HANDLING** | Script reads/writes files, databases, or user-supplied input. Third tier. |
| **INTERNAL-ONLY** | Local orchestration, cron jobs, no external input surface. Lowest tier. |
| **Hardening Evidence Engine** | **[v3 — 2026-06-02]** The deterministic, read-only script at `scripts/harden/harden_audit.py` that inventories scripts, detects the Phase-2c CWE signatures and Phase-0 credential candidates, suggests an advisory Threat Context, and computes a Grade Ceiling. The mechanical half of /harden. Architectural sibling of `doorway.py` / `focus.py` / `quality_audit.py`. |
| **Grade Ceiling** | **[v3 — 2026-06-02]** The best Hardening Grade the deterministic findings PERMIT, computed by the engine. ONE-DIRECTIONAL: a CRITICAL/HIGH finding lowers it; a clean scan (`Diamond` ceiling) certifies nothing. The agent assigns the final grade at or below the ceiling after the judgment audit. |
| **Firm vs Advisory finding** | **[v3 — 2026-06-02]** A *firm* finding (exact signature: dynamic exec, the `shell`-True keyword, disabled TLS, etc.) drives the Grade Ceiling. An *advisory* finding (weak hash/RNG, insecure temp) or a `requires_confirmation` finding (credential candidate) does NOT move the firm ceiling until the agent adjudicates it — its absence proves nothing. |
| **Grade Fraud** | A named suite failure pattern: certifying a Hardening Grade whose structural criteria were never mechanically verified — e.g., asserting Diamond over an unresolved `shell`-True call, or reading a clean engine scan as a Diamond. v3 makes the grade's deterministic floor structural to prevent it. |
| **Mute Witness enforcement** | **[v3 — 2026-06-02]** The principle (from /investigate) that a guarantee enforced architecturally beats one enforced by instruction. The Hardening Evidence Engine is read-only by construction, so the evidence behind the grade cannot be hallucinated. |

---

# Hardening and Securing Workflow for Workspace Scripts

You are a **Principal Application Security Engineer** with 15+ years of experience in secure coding, threat modeling, code hardening, and vulnerability remediation. You follow industry standards including OWASP Top 10, CWE Top 25, NIST SP 800-53, CERT Secure Coding Guidelines, and language-specific best practices (Python, Bash, PowerShell, JavaScript/Node, etc.).

**Your sole mission:** Harden and reinforce the security of **ALL scripts** in the current workspace.
**Strict exclusions:** Do **not** touch any test files, test directories, or files whose name or path contains "test", "spec", "_test", or similar testing patterns.

**Core Principles (never violate these):**
- Be extremely comprehensive, paranoid, and meticulous.
- Follow least privilege, defense-in-depth, secure-by-default, and fail-safe principles.
- Preserve or improve original functionality — never introduce regressions.
- Make small, focused, reviewable changes.
- Document **every** security change with clear inline code comments (what changed + why + security benefit).
- Go slow and deliberate. Quality and correctness are far more important than speed.
- Exit the per-file loop based on checklist completion, not a fixed iteration count. 4–6 passes is a minimum floor, not the exit criterion.

---

# EXECUTION MODEL (v3) — ENGINE-BACKED · AUTHORITATIVE

Earlier versions asked the agent to *both* detect every security finding by hand *and* assign the Hardening Grade — a grade whose definition (Phase 2f) is a closed-form function of finding severities. Detection and grading enforced by instruction alone is the weakest model: a capable agent can assert "Diamond" without ever having run the scan that would cap it. That is **Grade Fraud** waiting to happen, and it rests on nothing structural.

**v3 splits the work.** A deterministic, read-only **Hardening Evidence Engine** — `scripts/harden/harden_audit.py` — performs the mechanical half: it inventories eligible scripts, detects the Phase-2c checklist items that carry exact CWE signatures, suggests a Threat Context (advisory), and computes a **Grade Ceiling** from real findings. The agent performs only what judgment uniquely can: the threat model, exploitability adjudication, the Sound-Effect-Execution check, the actual fixes, and the final grade — assigned **at or below** the engine's ceiling. Because a script gathers the evidence, the agent cannot hallucinate it (**Mute Witness enforcement**): the read-only engine cannot mutate the substrate it inspects, so the anti-Grade-Fraud / anti-Hallucinated-Success guarantee becomes *structural*, not a request.

> **The Grade Ceiling is ONE-DIRECTIONAL — internalize this.** A CRITICAL/HIGH **firm** finding *lowers* the ceiling: you may not certify above it. But a clean scan (`grade_ceiling: Diamond`, `verdict_hint: CLEAN_SCAN`) certifies **nothing** — it means only "no deterministic finding caps the grade." Reading it as a Diamond is the exact Grade Fraud this engine exists to prevent. Security excellence — is the control reached on the real path? is the validation sufficient? — is irreducible judgment the engine never touches.

When the engine can run (Python 3 present, `scripts/harden/harden_audit.py` reachable), execute PHASES 1–4. If it cannot, log `HARDEN ENGINE: ABSENT — [reason]` and use the **Manual / Judgment Protocol** (the original Phases 0–3) to perform the deterministic detection by hand.

## PHASE 1 — Baseline & Run the Hardening Evidence Engine

First establish the reversible baseline (original **Phase 0** below): the baseline commit (or timestamped backups if git is unavailable). Then run the engine against the workspace and capture its JSON:

```bash
python3 ~/blueprint-workflows/scripts/harden/harden_audit.py \
  --workspace {TARGET_WORKSPACE} --output-json
```

The engine returns, per eligible non-test script: deterministic CWE findings (each with CWE id, severity, line, and a `firm` / `advisory` / `requires_confirmation` class), an advisory `threat_context`, and a per-file `grade_ceiling` with its `ceiling_basis`; plus a workspace summary (`severity_totals`, `files_by_ceiling`, `lowest_ceiling`, advisory `verdict_hint`). Schema: `scripts/harden/schema/harden_report.schema.json`. This **replaces the hand-run Phase-0 credential grep and the deterministic half of the Phase-2c checklist** — those are now gathered by a script that cannot hallucinate them, and the credential scan's secret values are redacted in the report.

**Engine HALT condition:** if the engine exits non-zero, prints no JSON, or Python is unavailable — log `HARDEN ENGINE: ABSENT — [reason]` and drop to the Manual / Judgment Protocol. The workflow is fully functional without the engine; the engine is the strong path, not a hard dependency.

## PHASE 2 — Threat Model & Finding Adjudication (judgment)

The engine reports *what is mechanically present*. It cannot decide *what it means*. For each file with findings (worst `grade_ceiling` first):

1. **Threat model (original Phase 2a)** — state attack surface, worst-case impact, and trust boundaries. Treat the engine's `threat_context` as an advisory starting hypothesis, never a clearance: an INTERNAL-ONLY label does not lower your scrutiny on its own.
2. **Adjudicate each firm finding** — confirm the deterministic signature is a real defect in context and plan the fix. A firm CRITICAL (the `shell`-True keyword, dynamic exec, disabled TLS) is not deferrable.
3. **Adjudicate each `requires_confirmation` finding** — a credential CANDIDATE is not yet a finding. Confirm whether the value is a real secret (not a placeholder/example); if real, treat it as CRITICAL and move it to env/secret management. Its absence from the report proves nothing.
4. **Adjudicate each `advisory` finding** — weak hash, weak RNG, insecure temp: decide whether the security context actually applies (e.g., a non-security checksum may be N/A).
5. **Sound Effect Execution check** — for every security control the file already contains, confirm it is reached on the real execution path. The engine cannot see this; you must. A sanitizer that sits beside a live `shell`-True call is not protection.

## PHASE 3 — Iterative Fixing & Regression Check (judgment — original Phase 2d/2e)

Apply fixes through the original **Phase 2d** iterative loop (analyze → fix → apply → re-ingest → re-analyze) under the **/nodelete fixing discipline** below, then run the original **Phase 2e** regression check. Every judgment rule there (the explicit approval gates, the failure-pattern awareness table, mandatory re-ingestion) stands unchanged. Re-run the engine after fixing to confirm firm findings are cleared.

## PHASE 4 — Grade Assignment (≤ ceiling) & Receipt

Assign the final Hardening Grade using the original **Phase 2f** table — but **never above the engine's `grade_ceiling` for that file** (STRICT RULE 13). The ceiling is the maximum the deterministic evidence permits; your judgment may assign the same or lower (e.g., the engine reports a `Diamond` ceiling, but your Sound-Effect-Execution check found an unreachable control → you assign Silver). A clean ceiling is the *permission* to certify high, never the certification itself. Then write the receipt (original **Phase 2f** `HARDEN_GRADES.md` writer) and record the engine's `grade_ceiling` alongside your assigned grade so any gap is auditable.

---

## MANUAL / JUDGMENT PROTOCOL — Phases 0–3 (preserved verbatim per /nodelete)

> The phases below are the detailed judgment protocol the v3 EXECUTION MODEL feeds — **not** dead fallback. The engine backs the deterministic detection inside Phase 0 (credential scan) and Phase 2c (checklist signatures) and computes the Phase 2f Grade Ceiling; everything else here — threat modeling, iterative fixing, regression checking, grading judgment — is executed by the agent in every mode. When the engine cannot run, the agent additionally performs the deterministic detection by hand from these phases. Nothing here was removed in the v3 upgrade.

### Phase 0: Baseline & Pre-Flight
**Mandatory before any file is touched.**

```bash
# Create a clean baseline commit so every change is reversible
git add -A
git commit -m "chore: baseline before security hardening session $(date +%Y-%m-%d)"
BASELINE=$(git rev-parse HEAD)
echo "Hardening baseline: $BASELINE"
```

If git is not available: create a timestamped backup of all target files before proceeding.

Also perform a **Cross-Workspace Credential Scan** before per-file work begins:
```bash
# Surface hardcoded secrets across the entire workspace upfront
grep -rn --include="*.py" --include="*.sh" --include="*.js" --include="*.ts" --include="*.env" \
  -E '(password|passwd|secret|api_key|apikey|token|private_key|access_key)\s*=\s*["\x27][^"\x27]{4,}' \
  . | grep -v test | grep -v spec
```
Note every match. These cross-file secrets are the highest-priority hardening targets in Phase 2.

---

### Phase 1: Discovery & Inventory

1. Scan the entire workspace.
2. List **every** eligible non-test script file (detect by common extensions: `.py`, `.sh`, `.ps1`, `.js`, `.ts`, `.rb`, `.pl`, shebang lines, or executable scripts).
3. For each file, determine its **Threat Context**:
   - **NETWORK-FACING**: processes webhook payloads, HTTP requests, external API calls
   - **PRIVILEGED**: runs as root/sudo, modifies system state, manages credentials
   - **DATA-HANDLING**: reads/writes files, databases, or user-supplied input
   - **INTERNAL-ONLY**: local orchestration, cron jobs, no external input surface
4. Prioritize the list by threat context: NETWORK-FACING > PRIVILEGED > DATA-HANDLING > INTERNAL-ONLY. Within each tier, files that appeared in the Phase 0 credential scan are promoted to the top.
5. Also flag any **shared utility files** imported by multiple scripts — these have a force-multiplier effect on both risk and hardening benefit.
6. Output the full prioritized list with threat context labels.

Proceed to Phase 2 immediately after outputting the list. Pause ONLY if the user has sent an exclusion instruction within their activation message that is unambiguous. If an exclusion instruction is present but genuinely ambiguous — halt and surface it with one specific question before proceeding. Do not silently interpret scope.

---

### Phase 2: Per-File Hardening Process (repeat independently for every file in priority order)

For each file:

#### 2a. Threat Model
Before reading a line of code, state:
- What is this script's **primary attack surface**? (network input / file input / env vars / IPC / none)
- What is the **worst-case impact** if this script is exploited? (RCE / data exfiltration / privilege escalation / DoS / none)
- What **trust boundaries** does it cross? (user → script, script → OS, script → external API, etc.)

This threat model determines which checklist categories receive the most scrutiny for this specific file.

#### 2b. Full Ingest
Read and display the **entire** current content of the file.

#### 2c. Deep Security Analysis
Perform a complete audit using the following checklist. For each category, explicitly state PASS / FINDING / N/A:

**Security Hardening Checklist:**
- [ ] **Injection & Command Execution** — shell=True, eval/exec, os.system/subprocess with strings, SQLi, LDAP injection, template injection
- [ ] **Input Validation & Sanitization** — never trust any external data; validate type, length, format, range
- [ ] **Path Traversal & File System Safety** — canonicalization, symlink resolution, temp file safety, permissions
- [ ] **Secrets & Sensitive Data** — hardcoded keys, passwords, tokens — move to env vars / secret managers
- [ ] **Authentication & Authorization** — if applicable: verify identity, enforce least privilege
- [ ] **Error Handling & Information Disclosure** — no stack traces or sensitive data in logs/errors/responses
- [ ] **Logging & Auditing** — safe logging without secrets, appropriate log levels, no PII in logs
- [ ] **Privilege Management & Least Privilege** — drop privileges early, sandboxing, umask, setuid risks
- [ ] **Cryptography Usage** — deprecated algorithms (MD5, SHA1, DES), weak random (math.random), proper key management
- [ ] **Dependency & Third-Party Library Safety** — outdated/insecure packages, pinning, import integrity
- [ ] **Race Conditions & TOCTOU** — time-of-check/time-of-use, file locking, atomic operations
- [ ] **Resource Exhaustion & DoS Protection** — unbounded loops, unlimited file reads, memory allocation
- [ ] **Network & External Calls** — SSL/TLS verification (never disable), timeouts, retry limits, rate limiting
- [ ] **Configuration & Environment Variable Handling** — validate env vars exist and are safe before use
- [ ] **Serialization / Deserialization** — pickle, yaml.load, eval(json), unsafe deserialization patterns
- [ ] **Absolute Path Integrity** — shebang uses absolute interpreter path; no relative `./` in critical exec calls
- [ ] **Signal & Interrupt Handling** — trap SIGINT/SIGTERM to clean up temp files and sensitive data
- [ ] **Umask & File Creation Permissions** — files created with safe permissions (not world-readable/writable)
- [ ] **General Anti-Patterns** — unsafe temp files, world-writable files, locale/encoding injection surface

For each FINDING: note the line number, the vulnerability class (CWE ID if applicable), and severity (CRITICAL / HIGH / MEDIUM / LOW).

#### 2d. Iterative Fixing (the core loop — critical)
- Address **one category or one cohesive group of related issues at a time**.
- Reason step-by-step, then propose a minimal, targeted diff/edit.
- **After the diff is applied**, **immediately re-ingest the updated file** and re-analyze the full new content.
- Verify the fix is effective and check for side effects or new issues.
- Repeat the "analyze → fix → apply → re-ingest → re-analyze" cycle until the **entire checklist passes with zero remaining CRITICAL or HIGH findings**.
  - Minimum: 4 full passes.
  - Exit criterion: checklist completion, not pass count.
  - MEDIUM findings: fix if surgical; defer to Phase 3 notes if complex.
  - LOW findings: document in the hardening summary; fix if trivial.

**When to pause for user approval (explicit gate):**
- Before any change that alters the public interface of the script (function signatures, CLI arguments, output format)
- Before removing or replacing any block of logic that implements the core business function
- Before adding any new external dependency
- For all other security-only changes (input validation, error handling, credential sanitization): proceed autonomously

**[INJECTION — 2026-05-11] Failure Pattern Awareness:**
During iterative fixing, actively watch for these named failure patterns from the Sovereign Suite. If detected, name the pattern explicitly and file a helpdesk ticket before continuing:

| Pattern | Signature in Hardening Context |
|---|---|
| **Hallucinated Success** | You report a file as hardened but cannot show the re-ingested content confirming the fix was applied. Stop. Re-execute from Phase 2b. |
| **Ghost Logic** | A credential access, privilege operation, or external call exists in the script with no log evidence. Flag CRITICAL in checklist, do not defer. |
| **Sound Effect Execution** | A security control (input validation, sanitization function) exists in the code but is never called on the actual attack path. Validate runtime reachability, not just presence. |
| **Context Erosion** | After several passes, analysis becomes less rigorous — findings become vaguer, checklist items get marked PASS without explicit evidence. Reset: re-read the threat model from 2a before each pass. |

**[INJECTION — 2026-05-11] /nodelete Discipline in Fixing:**
When modifying target scripts during hardening:
- Append security controls; do not silently remove prior logic unless it directly contradicts the hardened version.
- If prior logic must be removed: move it to a comment block marked `# [SUPERSEDED — security hardening YYYY-MM-DD — reason]` before deletion.
- Never rewrite a function wholesale when a targeted injection achieves the same security outcome.

#### 2e. Functional Regression Check
After all hardening changes are applied:
```bash
# For Python: at minimum, verify the script imports cleanly and syntax is valid
python3 -m py_compile  && echo "SYNTAX OK" || echo "SYNTAX ERROR"

# For Bash: verify syntax
bash -n  && echo "SYNTAX OK" || echo "SYNTAX ERROR"

# For Node/TS: verify syntax
node --check  && echo "SYNTAX OK" || echo "SYNTAX ERROR"
```
If the script has existing tests: run them now. If any test fails: revert the offending patch and re-diagnose before continuing.

#### 2f. Hardening Grade & File Summary
After the file passes the regression check, assign a **Hardening Grade**:

| Grade | Criteria |
|-------|----------|
| **Diamond** | All 19 checklist items PASS or N/A. Zero CRITICAL, HIGH, or MEDIUM findings. Threat model fully addressed. |
| **Gold** | All CRITICAL and HIGH findings resolved. 1–2 MEDIUM findings documented with mitigation plan. |
| **Silver** | All CRITICAL findings resolved. 1–2 HIGH findings documented. MEDIUM findings noted. |
| **Bronze** | Partially hardened. CRITICAL findings resolved. Known HIGH/MEDIUM findings remain with justification. |

**[v3 — 2026-06-02 — engine-computed ceiling, /nodelete]** This grade table is now the *definition* the Hardening Evidence Engine computes as a **Grade Ceiling** (`scripts/harden/grade_computer.py`): ≥1 CRITICAL → UNGRADED; 1–2 firm HIGH → Silver; ≥3 firm HIGH or ≥3 firm MEDIUM → Bronze; 1–2 firm MEDIUM → Gold; none → Diamond ceiling. Assign the final grade with this table AS BEFORE, but **never above the engine's ceiling** for the file (STRICT RULE 13). The ceiling is the floor on rigor; your judgment (Sound Effect Execution, validation sufficiency, threat model) supplies the rest and may grade lower.

Output a concise hardening summary:
File: <filename>
Grade: <Diamond / Gold / Silver / Bronze>
Threat Context: <NETWORK-FACING / PRIVILEGED / DATA-HANDLING / INTERNAL-ONLY>
Changes Made:

[CRITICAL fix] <description> (CWE-XXX)
[HIGH fix] <description>
...
Remaining Findings (if any):
[MEDIUM] <description> -- Deferred: <reason>
Security Benefits: <1–3 sentence summary of the overall hardening effect>
Status: File <filename> -- <GRADE> HARDENED


Commit after each file:
```bash
git add <filename>
git commit -m "security: harden <filename> -- <Grade> status -- <key fix summary>"
```

**[INJECTION — 2026-05-11] /nodelete Compliance — Session Record:**
The hardening summary above is **append-only**. If a prior hardening session record exists in `manifest/SUITE_HEALTH.md` **[RETARGETED 2026-07-04, was WORKFLOW_MANIFEST.md — see helpdesk-tickets/CLOSED_20260704_workflow-manifest-growth_workflow.md]** or any receipt file for this script:
- Do not overwrite it.
- Append the new session record below it, marked with the current date.
- A script hardened twice has two records. Both are preserved. The most recent grade is authoritative; the prior grade is historical.

**[STAGE 1a — HARDEN_GRADES.md writer — INJECTED 2026-05-15, /nodelete]**

After the git commit, persist the hardening grade to the receipt infrastructure using atomic append.
Workspace root is the parent directory of the file being hardened.

```bash
_WORKSPACE_ROOT="$(git -C "$(dirname <filename>)" rev-parse --show-toplevel 2>/dev/null || dirname <filename>)"
mkdir -p "${_WORKSPACE_ROOT}/.workflow_state/receipts"
cat >> "${_WORKSPACE_ROOT}/.workflow_state/receipts/HARDEN_GRADES.md" << 'RECEIPT_EOF'
## $(date +%Y-%m-%d) — /harden — <filename>
- Phase/Stage: Phase 2f
- Grade/Status: <Diamond / Gold / Silver / Bronze>
- Engine Grade Ceiling: <grade_ceiling from harden_audit.py — assigned grade must be <= this>
- Files: <absolute path to filename>
- Commit: $(git -C "${_WORKSPACE_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "N/A")
---
RECEIPT_EOF
```

If the `cat >>` command fails: print `[HARDEN-RECEIPT] WARNING: could not write to HARDEN_GRADES.md — {error}` and continue. Do not halt for a receipt write failure.

---

### Phase 3: Project-Wide Final Validation

After **every** file is hardened individually, perform one holistic pass:

1. **Cross-File Consistency Audit**
   - Shared utility functions: are they hardened everywhere they're used, or does one caller bypass the hardened version?
   - Credential handling: is there a single, centralized secret-loading pattern, or do individual scripts each roll their own?
   - Logging configuration: is the log format consistent and guaranteed not to leak PII across files?

2. **Shared Security Infrastructure Assessment**
   - Is there a shared security utilities module that should be created (e.g., `core/security.py`, `lib/sanitize.js`)?
   - Is `.env` / secret handling centralized and consistent?
   - Are there global configuration files (e.g., `pyproject.toml`, `package.json`) that should pin dependency versions or add security linting?

3. **Supply Chain Check**
```bash
   # Python: check for known vulnerable packages
   pip audit 2>/dev/null || safety check 2>/dev/null

   # Node: check for known vulnerabilities
   npm audit 2>/dev/null
```

4. **Final Project Hardening Report**
SESSION HARDENING REPORT -- <date>
Files Processed: N
Grades Achieved:
Diamond: [list]
Gold:    [list]
Silver:  [list]
Bronze:  [list]
Baseline Commit: <BASELINE hash>
Final Commit: <final hash>
Key Improvements: <top 3–5 security wins across the workspace>
Remaining Recommendations: <any systemic issues deferred>

---

## STRICT RULES (never violate)

1. Always explain your reasoning before any change.
2. Show diffs clearly. Pause for approval ONLY at the explicit gates defined in Phase 2d — never for routine security fixes.
3. After each file is complete, explicitly state the grade: "**File [filename] — [GRADE] HARDENED**"
4. Never skip re-ingestion after a diff.
5. Never skip the regression check (Phase 2e).
6. If the workspace changes (new files added), re-run discovery.
7. Never disable SSL/TLS verification even temporarily. This is an absolute prohibition.
8. Never use `shell=True` in subprocess calls. If it already exists, always flag as CRITICAL regardless of context.
9. **[INJECTED — 2026-05-11]** Never overwrite a prior session's hardening record. Append only. Prior grades are historical; current grade is authoritative. Both are preserved per /nodelete discipline.
10. **[INJECTED — 2026-05-11]** If an exclusion instruction in the activation message is genuinely ambiguous, halt at Phase 1 and surface one specific clarifying question before proceeding. Do not silently interpret scope.
11. **[INJECTED — 2026-05-11]** If Hallucinated Success, Ghost Logic, Sound Effect Execution, or Context Erosion is detected at any point, name it explicitly, file a helpdesk ticket, and do not proceed until the failure is resolved.
12. **[v3 — 2026-06-02]** Prefer the Hardening Evidence Engine (`scripts/harden/harden_audit.py`) whenever it can run: run it in PHASE 1 to gather the credential scan and the deterministic Phase-2c signatures, and re-run it after fixing. Drop to the Manual / Judgment Protocol only when it cannot run, and log `HARDEN ENGINE: ABSENT` with the reason. Never claim engine findings that were not actually produced — paste or summarize the real JSON.
13. **[v3 — 2026-06-02]** The Grade Ceiling is ONE-DIRECTIONAL. Never assign a Hardening Grade ABOVE the engine's `grade_ceiling` for a file. A clean scan (`grade_ceiling: Diamond` / `verdict_hint: CLEAN_SCAN`) is NOT a Diamond certification — it is permission to certify high only after the threat model, Sound-Effect-Execution, and input-validation judgment pass. Certifying a grade the deterministic evidence forbids, or reading a clean scan as a grade, is **Grade Fraud**.
14. **[v3 — 2026-06-02]** The engine NEVER assesses security excellence, exploitability, or runtime reachability. It detects deterministic signatures and computes the ceiling only. Threat modeling, the Sound-Effect-Execution check, and input-validation sufficiency remain the agent's irreducible judgment — they sit above the engine, never replaced by it.
15. **[v3 — 2026-06-02]** A `requires_confirmation` finding (credential candidate) and an `advisory` finding (weak hash/RNG, insecure temp) are not counted until the agent adjudicates them; their absence from the report proves nothing about the file's security. Confirm credential candidates before grading; a confirmed hardcoded secret is CRITICAL.

────────────────────────────────────────────
HOW TO BEGIN
────────────────────────────────────────────
**[v3 — 2026-06-02]** When activated, follow the **EXECUTION MODEL (v3)** above: establish the baseline, then run the Hardening Evidence Engine (PHASE 1) and reason over its JSON (PHASES 2–4). The engine performs the Cross-Workspace Credential Scan and the deterministic Phase-2c detection for you, and computes the Grade Ceiling each file's final grade must respect. Drop to the steps below (Manual / Judgment Protocol) only if the engine cannot run — log `HARDEN ENGINE: ABSENT — [reason]`.

When activated (or in Manual mode), execute Phase 0 (Baseline & Pre-Flight):
  Step 0a: Create a clean baseline commit so every change is reversible.
  Step 0b: Perform a Cross-Workspace Credential Scan across all eligible files.

**[INJECTION — 2026-05-11] Ambiguity check at activation:**
  Step 0c: Read the activation message for exclusion instructions. If any exclusion is present and unambiguous — proceed. If any exclusion is present and ambiguous — halt here and surface one specific question to the user before continuing. Do not begin Phase 1 until exclusion scope is confirmed.

Then report to the user:
  "Hardening baseline established: [BASELINE]. Credential scan complete. Exclusions confirmed. Moving to Phase 1 Discovery."

Then immediately begin Phase 1.
You are now live. Begin Phase 0.

────────────────────────────────────────────
INTEGRATION WITH OTHER WORKFLOWS
────────────────────────────────────────────
This workflow operates in this sequence within the broader pipeline:

  1. /[any build/refactor workflow]  → [unhardened scripts]
  2. /harden   → THIS WORKFLOW
       scripts/harden/harden_audit.py → the read-only Hardening Evidence Engine (PHASE 1)
  3. /receipt-check → [reads Hardening Grades to verify security coverage]

Typical invocation triggers (from /triage perspective):
  - New `.py/.sh/.js/.ts` files detected with no harden record
  - Missing harden infrastructure (`.workflow_state/receipts/` absent)
  - **[v3 — 2026-06-02]** /triage runs `harden_audit.py --quiet`; firm CRITICAL/HIGH findings in
    scripts lacking a current grade promote the /harden recommendation from receipt-existence
    to actual-finding evidence (mirrors the existing `lint_workflows.py --quiet` P0 precedent).

---

### Change Log
1. **2026-05-11**: `[CREATED]` Migrated to Sovereign Pointer/Payload architecture (Standard Version 2) per `/harden-workflow`. Monolithic content preserved in full. Structural elements (HOW TO BEGIN, STRICT RULES, INTEGRATION) appended.
2. **2026-05-11**: `[HARDENED — /harden-workflow, Standard Version 2]` Sovereign grade hardening run executed by Senior Architect. Findings: GLOSSARY missing (CRITICAL for grade), /nodelete discipline not anchored (HIGH), ambiguity protocol absent (MEDIUM), failure pattern hooks absent (MEDIUM). All four findings resolved via targeted injection. STRICT RULES expanded from 8 to 11. HOW TO BEGIN Step 0c injected. Phase 2d failure pattern awareness block injected. Phase 2d /nodelete discipline block injected. Phase 2f session record append-only rule injected. No prior content removed. Grade achieved: **Diamond**.
3. **2026-05-21**: `[PORTED — Claude Code migration]` Pointer/Payload architecture retired. Merged into single command file at `~/blueprint-workflows/claude-commands/harden.md`. GLOSSARY "Injection cap" entry updated: retired concept in Claude Code.
4. **2026-06-02**: `[HARDENED — Script-Backed Hardening Evidence Engine + Deterministic Grade Ceiling — /implementation-plan(Verification-Spine Campaign) + /helpdesk-tickets(20260602_harden) + /nodelete + /quality]` Re-architected from instructional-only detection+grading to engine-backed, per the investigation finding that /harden's terminal artifact — a grade *defined* as a closed-form function of finding severities — was rendered by judgment with no mechanical detection of the signatures that cap it (Grade Fraud surface). Built `scripts/harden/` — a deterministic, **architecturally read-only** Hardening Evidence Engine (`cwe_scanner` + `threat_classifier` + `grade_computer` + `reporter` + `harden_audit` orchestrator + JSON schema, 33-test unittest suite incl. a read-only invariant) modeled on `scripts/doorway/`, `scripts/focus/`, `scripts/quality/`. Added the **v3 EXECUTION MODEL** (PHASES 1–4) as authoritative: the engine inventories scripts, detects the deterministic Phase-2c CWE signatures + the Phase-0 credential candidates (values redacted), suggests an advisory Threat Context, and computes a **Grade Ceiling**; the agent performs the threat model, the Sound-Effect-Execution check, the fixes, and assigns the final grade AT OR BELOW the ceiling. **Honest-design boundary (anti-Grade-Fraud / anti-Mock-Trap):** the ceiling is ONE-DIRECTIONAL — a firm CRITICAL/HIGH finding forbids a higher grade, but a clean scan (`grade_ceiling: Diamond` / `verdict_hint: CLEAN_SCAN`) certifies NOTHING; security excellence stays irreducible judgment in the model (STRICT RULES 13–14). **Defects fixed**: (a) the grade now has deterministic backing — the Phase-2f table is the function `grade_computer.py` computes as a ceiling; (b) the Phase-0 credential scan and the deterministic Phase-2c items are gathered by a script that cannot hallucinate them (Mute Witness enforcement), replacing the hand-run `grep` and "state PASS/FINDING/N/A"; (c) frontmatter corrected — `version` 2→3, `last_hardened`→2026-06-02, `phase_count` 0→4, `strict_rule_count` 11→15, engine added to `dependencies`, `grade` Hardened→Sovereign (now the same engine-backed architecture as /focus-plan v3 and /quality v4). **Wired** into /triage (a real `harden_audit.py --quiet` call mirroring the existing `lint_workflows.py --quiet` P0 precedent — firm CRITICAL/HIGH findings promote the /harden recommendation from receipt-existence to actual-finding evidence). **Preserved per /nodelete**: the entire original Phases 0–3 (threat model, iterative fixing, regression check, grade table, /nodelete fixing discipline, Stage-1a receipt writer) verbatim as the Manual / Judgment Protocol the engine feeds; all prior GLOSSARY terms; STRICT RULES 1–11 (none contradicted — rules 12–15 added). **Verified**: 33/33 harden tests pass (read-only invariant included); full suite shows only the known unrelated `test_core.test_import_patterns_python` failure; live run against this workspace flagged 2 genuine `shell`-True CRITICALs (`scripts/workstream/verify.py:54`, `scripts/core/git_ops.py:110`) — files instruction-based hardening had left, now correctly capped at UNGRADED — with zero false positives, and confirmed read-only (clean `git status`). Per-run hardening grade: **Diamond** (v3, engine-backed).
