"""
duplicate_detector.py — STRICT RULE 7 duplicate-ticket check
================================================================
"Never create a ticket for a failure that is already documented in an open
ticket. Check helpdesk-tickets/ for existing open tickets against the same
faulting workflow before creating a new one." Reports open tickets already
naming a given workflow as a fact — never an automatic rejection, since two
open tickets for the same workflow could legitimately document distinct
failures.
"""

from dataclasses import dataclass
from typing import List

from helpdesk_tickets.ticket_parser import list_ticket_files, parse_filename


@dataclass
class DuplicateCheckResult:
    workflow_name: str
    open_tickets_for_workflow: List[str]

    def as_dict(self) -> dict:
        return {
            "workflow_name": self.workflow_name,
            "open_tickets_for_workflow": self.open_tickets_for_workflow,
        }


def find_open_tickets_for_workflow(tickets_dir: str, workflow_name: str) -> DuplicateCheckResult:
    """
    Lists non-CLOSED_-prefixed ticket filenames whose parsed workflow-name
    segment matches `workflow_name` exactly (case-sensitive, matching the
    naming convention's own literal workflow-name usage).
    """
    matches = []
    for filename in list_ticket_files(tickets_dir):
        info = parse_filename(filename)
        if info is None or info.closed:
            continue
        if info.workflow_name == workflow_name:
            matches.append(filename)
    return DuplicateCheckResult(workflow_name=workflow_name, open_tickets_for_workflow=matches)
