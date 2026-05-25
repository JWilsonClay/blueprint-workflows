## 2026-05-09 — /harden — scripts/doorway/ (retroactive receipt)
- Phase/Stage: Security Hardening (commit 597388b)
- Grade/Status: DIAMOND
- Files: scripts/doorway/doorway.py, scripts/doorway/scanner.py, scripts/doorway/auditor.py, scripts/doorway/breadcrumb.py, scripts/doorway/integrity.py, scripts/doorway/manifest.py, scripts/doorway/reporter.py, scripts/doorway/recommender.py, scripts/doorway/audit_repairs.py, scripts/doorway/_utils.py
- Findings: atomic writes (CWE-362/732), safe_mkdir 0o700 (CWE-732), safe_read bounded (CWE-400), assert_within traversal guard (CWE-22)
- Commit: 597388b
---
## 2026-05-25 — /harden — scripts/core/diff_models.py
- Phase/Stage: Security Hardening (SoC extraction)
- Grade/Status: DIAMOND
- Files: scripts/core/diff_models.py
- Findings: 0 — pure data classes, no I/O, no security surface
- Commit: d1cccc1
---
## 2026-05-25 — /harden — scripts/core/diff_checkers.py
- Phase/Stage: Security Hardening (SoC extraction)
- Grade/Status: DIAMOND
- Files: scripts/core/diff_checkers.py
- Findings: 0 — reads via Diamond-hardened core.filesystem, no subprocess, no shell
- Commit: d1cccc1
---
## 2026-05-25 — /harden — scripts/core/diff_report.py
- Phase/Stage: Security Hardening (SoC extraction)
- Grade/Status: DIAMOND
- Files: scripts/core/diff_report.py
- Findings: 0 — pure stdout display functions, no I/O beyond print
- Commit: d1cccc1
---
## 2026-05-25 — /harden — scripts/workstream/verify.py
- Phase/Stage: Security Hardening
- Grade/Status: GOLD
- Files: scripts/workstream/verify.py
- Findings: 1 MEDIUM — shell=True with f-string interpolation in grep commands. Mitigated: _sanitize_for_shell() strips metacharacters from interpolated values. Not fully Diamond because shell=True remains (by design — complex pipelines with grep/wc/find). No remote input vectors.
- Commit: pending
---
