"""
grade_hint.py — One-directional, advisory grade suggestion
=============================================================
Computes a grade_hint from structural presence/absence facts, per THE
SOVEREIGN STANDARD's own literal decision table in harden-workflow.md. This
is NOT a certified grade — see scripts/harden_workflow/__init__.py for why.

The source table has real ambiguity where its four grade definitions
overlap (e.g. "Structured" and "Hardened" both list "missing structured
output" as a qualifying condition under different circumstances). Rather
than silently resolve that ambiguity one way and present it as settled,
this module documents its own resolution rule inline and always returns the
full missing-criteria list so the model — which reads the resolution logic
below in the advisory string — makes the final call, exactly as Phase 1's
own STRICT RULE 2 requires ("never award a grade missing any single
criterion").
"""

from dataclasses import dataclass, field
from typing import List, Optional

_ADVISORY = (
    "grade_hint is a one-directional, advisory signal from structural presence/absence "
    "only — mirrors the /quality v4 smell-linter precedent: a hint of 'Sovereign' means "
    "no missing structural element was found, NEVER that the workflow's content is good. "
    "STRICT RULE 4b's own text (\"a STRICT RULES section that doesn't address the halt "
    "condition is incomplete\") shows presence alone does not prove completeness. Certify "
    "the actual grade only after Phase 4's content-quality judgment passes, never from "
    "this hint alone."
)


@dataclass
class GradeHintResult:
    grade_hint: str
    missing_criteria: List[str] = field(default_factory=list)
    structured_output_unknown: bool = False
    advisory: str = _ADVISORY

    def as_dict(self) -> dict:
        return {
            "grade_hint": self.grade_hint,
            "missing_criteria": self.missing_criteria,
            "structured_output_unknown": self.structured_output_unknown,
            "advisory": self.advisory,
        }


def compute_grade_hint(
    command_file_correct: bool,
    symlink_present: bool,
    frontmatter_present: bool,
    glossary_present: bool,
    how_to_begin_present: bool,
    strict_rules_present: bool,
    changelog_present: bool,
    structured_output_present: Optional[bool] = None,
) -> GradeHintResult:
    """
    `structured_output_present=None` means unknown (this engine cannot
    reliably detect a structured-output template's shape — see
    scripts/harden_workflow/__init__.py). Unknown caps the hint at
    "Hardened" at best — it can never reach "Sovereign" without a confirmed
    structured output, since the source table requires it explicitly for
    that grade.
    """
    missing: List[str] = []
    if not command_file_correct:
        missing.append("command_file_location")
    if not symlink_present:
        missing.append("symlink")
    if not frontmatter_present:
        missing.append("frontmatter")
    if not glossary_present:
        missing.append("glossary")
    if not how_to_begin_present:
        missing.append("how_to_begin")
    if not strict_rules_present:
        missing.append("strict_rules")
    if not changelog_present:
        missing.append("changelog")
    if structured_output_present is False:
        missing.append("structured_output")

    structured_output_unknown = structured_output_present is None

    # Resolution rule for the source table's overlap (see module docstring):
    # location/frontmatter/how_to_begin missing at all -> Legacy (most severe).
    # Otherwise, strict_rules missing -> Structured (more severe than a lone
    # output/changelog/glossary gap). Otherwise, any single one of
    # {structured_output, changelog, glossary} missing, or unknown structured
    # output -> Hardened (cannot confirm Sovereign). Otherwise -> Sovereign.
    if not command_file_correct or not symlink_present or not frontmatter_present or not how_to_begin_present:
        grade_hint = "Legacy"
    elif not strict_rules_present:
        grade_hint = "Structured"
    elif "changelog" in missing or "structured_output" in missing or "glossary" in missing or structured_output_unknown:
        grade_hint = "Hardened"
    else:
        grade_hint = "Sovereign"

    return GradeHintResult(
        grade_hint=grade_hint,
        missing_criteria=missing,
        structured_output_unknown=structured_output_unknown,
    )
