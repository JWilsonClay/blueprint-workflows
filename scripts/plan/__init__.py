"""
plan — Canonical Plan & Tasks Template Populator
===================================================
Idempotently ensures a target workspace has canonical `tasks.md` and
`implementation-plan.md` files, sourced from `templates/plan/` at this
suite's own root (never from the target workspace).

Design invariant: this package NEVER overwrites a file that already has
real content. It only creates what is genuinely absent (or, under
`--force`, refreshes a file that is empty/whitespace-only). See
`ensure_plan_templates.py`'s module docstring for the full safety rationale
— this deliberately narrows PILLAR_04_POST_BUILD_HYGIENE_ARCHIVAL_NODELETE.md
§4.4's literal "copy from template if missing required marker structure"
description, which read literally would silently clobber any pre-existing
tasks.md/implementation-plan.md that simply predates the marker convention.

Architectural sibling: scripts/doorway/ (the only other script package in
this suite that writes to a target workspace).
"""

__version__ = "1.0"
