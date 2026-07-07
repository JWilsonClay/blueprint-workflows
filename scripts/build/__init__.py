"""
build — Build Evidence Engine
===============================
Deterministic engine (sibling of doorway / focus / receipt / registry) backing
`/execute-build`'s mechanical checks. Answers three questions a script can
answer honestly, so `/execute-build` stops asking the model to eyeball facts
it has no reason to get wrong:

  1. Phase Map + receipt cross-reference — delegates entirely to the existing
     `focus.phase_status.build_phase_status_report()` (built for /focus-plan
     and /nodelete Pillar 6). Not duplicated here — imported directly.
  2. Completeness scan (Step 5d) — grep a given file list for TODO/FIXME/
     PLACEHOLDER/HACK/bare-`pass`/`raise NotImplementedError` markers. Reports
     a match list only. Whether a match is "justified" is never this
     package's call — that judgment stays with the agent.
  3. Scope diff (Step 5f) — set-difference between a phase's declared file
     scope and what `git status --porcelain` reports actually changed.
     Reports the two sets only. Whether an out-of-scope touch was "warranted"
     stays with the agent.

Neither (2) nor (3) judges quality, design soundness, or intent — the
Mock-Trap test this suite's engines are held to (see `implementation-plan.md`,
"HONEST-DESIGN DISCIPLINE"). Read-only; writes nothing.

Origin: implementation-plan.md Phase 4.1-4.2 (Sovereign Scaling Cluster),
docs/compression-staging/execute-build-honest-design.md.
"""

__version__ = "1.0.0"
