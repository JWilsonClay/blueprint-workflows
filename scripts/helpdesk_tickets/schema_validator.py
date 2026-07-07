"""
schema_validator.py — Phase 2 TICKET VALIDATION checklist, mechanized
=========================================================================
Checks the mechanical portion of Phase 2's TICKET VALIDATION checklist
plus the STRICT RULE 12 Phylogeny-Disposition-vs-Status contradiction —
never the ticket's content quality (root-cause correctness, urgency
judgment, Phylogeny Disposition correctness). Citation checks are
delegated to scripts/investigate/citation_fidelity.py directly — the
citation format is byte-for-byte identical to /investigate's own
convention, so this module imports it rather than reimplementing it.
"""

from dataclasses import dataclass, field
from typing import List

from helpdesk_tickets.ticket_parser import (
    REQUIRED_SECTIONS,
    VALID_ROOT_CAUSE_TYPES,
    TicketFields,
    parse_filename,
)
from investigate.citation_fidelity import extract_citations, verify_citation

_STATUS_OPEN = "OPEN"
_MIN_CITATIONS = 2


@dataclass
class ValidationResult:
    filename_valid: bool
    sections_missing: List[str] = field(default_factory=list)
    root_cause_type: str = None
    root_cause_type_valid: bool = False
    phylogeny_disposition_present: bool = False
    status_valid_format: bool = False
    phylogeny_status_contradiction: bool = False
    citation_count: int = 0
    citations_valid_count: int = 0
    citation_findings: List[dict] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "filename_valid": self.filename_valid,
            "sections_missing": self.sections_missing,
            "root_cause_type": self.root_cause_type,
            "root_cause_type_valid": self.root_cause_type_valid,
            "phylogeny_disposition_present": self.phylogeny_disposition_present,
            "status_valid_format": self.status_valid_format,
            "phylogeny_status_contradiction": self.phylogeny_status_contradiction,
            "citation_count": self.citation_count,
            "citations_valid_count": self.citations_valid_count,
            "citation_findings": self.citation_findings,
            "issues": self.issues,
        }


def validate_ticket(fields: TicketFields, filename: str, report_text: str) -> ValidationResult:
    """
    `report_text` is the full ticket text, passed separately from `fields`
    so citation extraction (which scans raw text, not parsed fields) can
    reuse scripts/investigate/citation_fidelity.py directly.
    """
    issues: List[str] = []

    filename_info = parse_filename(filename)
    filename_valid = filename_info is not None
    if not filename_valid:
        issues.append(f"Filename '{filename}' does not match the YYYYMMDD_[workflow]_workflow.md convention.")

    sections_missing = sorted(REQUIRED_SECTIONS - fields.sections_present)
    if sections_missing:
        issues.append(f"Missing required section(s): {sections_missing}")

    root_cause_type = fields.header_fields.get("Root Cause Type")
    root_cause_type_valid = root_cause_type in VALID_ROOT_CAUSE_TYPES
    if not root_cause_type_valid:
        issues.append(f"Root Cause Type '{root_cause_type}' is not one of {sorted(VALID_ROOT_CAUSE_TYPES)}.")

    phylogeny_disposition = fields.header_fields.get("Phylogeny Disposition")
    phylogeny_disposition_present = bool(phylogeny_disposition)
    if not phylogeny_disposition_present:
        issues.append("Phylogeny Disposition field is missing.")

    status = fields.status or ""
    status_valid_format = status == _STATUS_OPEN or status.upper().startswith("REMEDIATED")
    if not status_valid_format:
        issues.append(f"Status '{status}' is neither OPEN nor REMEDIATED (...).")

    # STRICT RULE 12: a ticket cannot close with Phylogeny Disposition still PENDING.
    phylogeny_status_contradiction = (
        status.upper().startswith("REMEDIATED")
        and (phylogeny_disposition or "").strip().upper() == "PENDING"
    )
    if phylogeny_status_contradiction:
        issues.append("Status is REMEDIATED but Phylogeny Disposition is still PENDING (STRICT RULE 12).")

    citations = extract_citations(report_text)
    citation_results = [verify_citation(c) for c in citations]
    citation_findings = [
        r.as_dict() for r in citation_results if r.status not in ("VALID", "VALID_NO_LINE_RANGE")
    ]
    citations_valid_count = sum(1 for r in citation_results if r.status in ("VALID", "VALID_NO_LINE_RANGE"))
    if len(citations) < _MIN_CITATIONS:
        issues.append(f"Only {len(citations)} citation(s) found; Section 3 requires at least {_MIN_CITATIONS}.")
    if citation_findings:
        issues.append(f"{len(citation_findings)} citation(s) do not resolve (missing file or bad line range).")

    return ValidationResult(
        filename_valid=filename_valid,
        sections_missing=sections_missing,
        root_cause_type=root_cause_type,
        root_cause_type_valid=root_cause_type_valid,
        phylogeny_disposition_present=phylogeny_disposition_present,
        status_valid_format=status_valid_format,
        phylogeny_status_contradiction=phylogeny_status_contradiction,
        citation_count=len(citations),
        citations_valid_count=citations_valid_count,
        citation_findings=citation_findings,
        issues=issues,
    )
