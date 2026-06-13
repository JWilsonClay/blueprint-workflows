"""
gitignore — Sovereign Suite Gitignore Seeder
============================================
A deterministic, config-driven, non-destructive `.gitignore` manager (sibling of
the doorway / focus / quality / registry engines). Attached to the `/sentinel`
flow, it writes a clearly-marked, idempotent **managed block** into the target
workspace's `.gitignore` — covering suite-generated artifacts (`.history/`,
`quarantine/`, `.workflow_state/`), security patterns (`.env`, keys, credentials),
and common noise — preloaded from an editable `seed.toml`.

Two contracts it never violates (/nodelete applied to `.gitignore`):
  * It only ever touches content BETWEEN its own markers. The user's existing
    entries above/below the managed block are never modified.
  * It scrubs nothing from git history. If it finds a secret that is ALREADY
    tracked, it WARNS and recommends `/gitclean` — gitignore prevents only
    *future* leaks; an already-committed secret needs history rewrite.

Origin: helpdesk ticket 20260612_gitignore-seeder_module.md.
"""

__version__ = "1.0.0"
