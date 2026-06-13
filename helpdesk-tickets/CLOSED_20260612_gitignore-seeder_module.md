# Helpdesk Ticket: Structural Gap — No Autonomous, Security-Aware `.gitignore` Management for Workspaces Touched by the Suite (Build a `/sentinel`-Attached Gitignore Seeder)

**To**: Senior Architect of Workflows
**From**: Claude (Opus 4.8) / blueprint-workflows session 2026-06-12 — three-body reconciliation + tooling
**Date**: 2026-06-12
**Subject**: Workflows now generate local-only directories (`.history/`, `quarantine/`, `.workflow_state/`) and workspaces carry secrets, but nothing autonomously maintains a correct, security-aware `.gitignore`. Build a config-driven, non-destructive seeder module attached to the `/sentinel` run.
**Urgency**: MEDIUM (scoped backlog build — but the security dimension, preventing secret/credential commits, makes it the highest-priority item in the backlog)

---

## 1. Executive Summary
The Sovereign Suite now writes local-only artifacts into every workspace it touches — `.history/` ledgers (ingestion-banned audit memory), `quarantine/` staging, `.workflow_state/` receipts — none of which should be tracked by git. Simultaneously, the user manages `.gitignore` by hand across many workspaces and "really struggles with it," creating a standing risk that suite-generated noise *and actual secrets* (`.env`, keys, credentials) get committed. There is no suite mechanism to autonomously create and maintain a robust, security-aware `.gitignore`. This ticket scopes a deterministic module — a sibling of `doorway.py`, invoked by the `/sentinel` run — that writes a **clearly-marked, idempotent managed block** into the target workspace's `.gitignore`, preloaded from an editable config, and warns when secrets are *already tracked*.

## 2. Root Cause Analysis: "Structural Gap — Generated Artifacts and Secrets Without Ignore Coverage"
- **The How**: `/nodelete` (Pillar 3) and `/depreciate` now create `.history/` and `quarantine/` in arbitrary workspaces; there is no automatic `.gitignore` coverage, so these get committed unless the human remembers to ignore them by hand. Verified live this session: the `.history/depreciate.md.ledger.md` created by the `/depreciate` self-prune is **untracked and would be committed** (the workspace `.gitignore` ignores only `manifest/*`).
- **The Why**: `/sentinel` (via `doorway.py`) already runs against a flagged `--workspace` at session init and is the natural, frequent hook point — but it has no gitignore-hygiene responsibility. The suite never had a place to encode "here is the correct, security-aware ignore set for any workspace I operate in."

## 3. Forensic Evidence
- **Minimal, manual ignore coverage**: [.gitignore L10](file:///home/jwils/blueprint-workflows/.gitignore#L10)
  *Evidence: the entire workspace `.gitignore` ignores only `manifest/*` — no coverage for `.history/`, `quarantine/`, `.workflow_state/`, or any security pattern.*
- **Live, uncovered suite artifact**: [.history/depreciate.md.ledger.md](file:///home/jwils/blueprint-workflows/.history/depreciate.md.ledger.md)
  *Evidence: created 2026-06-12 by the `/depreciate` self-prune; git reports it untracked (`?? .history/`) — it would be committed without manual intervention. This is the gap, demonstrated.*
- **The hook point already runs at session init**: [scripts/doorway/doorway.py](file:///home/jwils/blueprint-workflows/scripts/doorway/doorway.py)
  *Evidence: `doorway.py` is the `/sentinel`-invoked engine that already takes `--workspace` and operates on the target — the seeder attaches here.*
- **Source of the generated dirs to cover**: [nodelete.md L145](file:///home/jwils/blueprint-workflows/claude-commands/nodelete.md#L145)
  *Evidence: `.history/` is mandated "at the workspace root … in every workspace" — i.e., it will appear in every workspace the suite operates on; `/depreciate` adds `quarantine/`.*

## 4. Remediation: Build `scripts/gitignore/` — a config-driven, non-destructive seeder
1. **Location & shape**: a deterministic module in `blueprint-workflows` (e.g., `scripts/gitignore/gitignore_seeder.py`), a sibling of `doorway.py` / `focus.py` / `quality_audit.py`. The governance layer carries the logic; the target workspace receives the file.
2. **Invocation**: called by the `/sentinel` flow (within or alongside `doorway.py`) against the flagged `--workspace`. Writes `.gitignore` **to the target workspace root**.
3. **Non-destructive managed block (`/nodelete` applied to `.gitignore`)**: maintain a clearly-marked, idempotent block —
   ```
   # >>> Sovereign Suite — managed block (auto-generated; edit above/below, not inside) >>>
   .history/
   quarantine/
   ...
   # <<< Sovereign Suite — managed block <<<
   ```
   Create `.gitignore` if absent; if present, append the block and **never touch the user's existing entries**. On re-run, replace only the managed block (idempotent — no duplication).
4. **Editable seed config (not hardcoded)**: a config file in `blueprint-workflows` (e.g., `scripts/gitignore/seed.toml`) with categories the user can tune without touching code:
   - **Suite-generated / ingestion-banned**: `.history/`, `quarantine/`, `.workflow_state/`, `deprecated/`
   - **Security**: `.env`, `.env.*`, `secrets/`, `*.key`, `*.pem`, `id_rsa*`, `*.p12`, `*.pfx`, `credentials*.json`, `.aws/`, service-account JSONs
   - **Common noise**: `__pycache__/`, `*.pyc`, `.venv/`, `node_modules/`, `dist/`, `build/`, `.DS_Store`, `*.log`, `.idea/`, `.vscode/`
5. **Autonomy**: **auto-apply the managed block by default** on every sentinel run (safe because additive + idempotent). No flag for the human to remember.
6. **Detect-and-warn for already-tracked secrets**: intersect the security patterns with `git ls-files`. If any sensitive file is **already tracked**, emit a WARNING and **recommend invoking `/gitclean`** — gitignore prevents only *future* leaks; an already-committed secret needs history rewrite, which is `/gitclean`'s job. The seeder must NOT imply "you're protected now," and must NOT auto-scrub history itself.
7. **Path containment (safety)**: resolve `--workspace` and write only inside it; refuse dangerous targets (`/`, `$HOME` root, non-existent paths).
8. **Output**: a short report — what was added/updated in the managed block, and any already-tracked-secret warnings with the `/gitclean` recommendation.
9. **Acceptance criteria**: idempotency test (two runs → identical file, no duplicate block); existing-`.gitignore` preservation test; path-containment refusal test; detect-and-warn fires on a planted tracked secret.

## 5. Recommendation to Senior Architect
Give `/sentinel` a **gitignore-hygiene responsibility** via a dedicated, config-driven seeder module — so every workspace the suite operates on automatically receives correct, security-aware ignore coverage, written non-destructively (managed block, never overwrite) and tuned from one editable config in the governance layer. Pair it with a **detect-and-warn → `/gitclean`** handoff for secrets already in history, so the tool closes the *future*-leak gap without giving false confidence about *past* commits. This converts a recurring manual, error-prone, security-sensitive chore into an autonomous, auditable, suite-standard behavior.

---
**Status**: **OPEN**
**Verification**: PENDING — scoped backlog build. Closes when `scripts/gitignore/gitignore_seeder.py` + seed config exist, are invoked by the `/sentinel` flow, pass the four acceptance tests, and a live run seeds a target workspace's managed block non-destructively with the detect-and-warn handoff functioning.

---
*Signed,*
**Claude (Opus 4.8)**
*(acting Senior Architect of Workflows, this session)*
