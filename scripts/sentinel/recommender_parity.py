"""
recommender_parity.py — Recommender-vs-documentation parity check
=====================================================================
Extracts the actual id/workflow/severity triples scripts/doorway/
recommender.py's source emits, and Phase 2b's documented Routing Map table
from sentinel.md, then reports the set difference. Pure text comparison —
never judges whether a routing decision is correct, only whether the
documentation is complete and current.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

from engine_utils import safe_read

# Matches one recs.append({...}) block's id/workflow/severity triple, in the
# order recommender.py's source actually writes them (id, workflow, reason,
# severity). Non-greedy + DOTALL so each match stays within one block.
_TRIPLE_RE = re.compile(
    r'"id":\s*"([^"]+)".*?"workflow":\s*"([^"]+)".*?"severity":\s*"([^"]+)"',
    re.DOTALL,
)

# Matches a Phase 2b markdown table row: first two pipe-delimited cells are
# the Doorway Protocol ID and the Workflow Trigger, each optionally wrapped
# in backticks.
_TABLE_ROW_RE = re.compile(r'^\|\s*`?([^|`]+?)`?\s*\|\s*`?([^|`]+?)`?\s*\|', re.MULTILINE)
_SKIP_ROW_MARKERS = ("---", "Doorway Protocol ID")


@dataclass
class RecommenderTriple:
    id: str
    workflow: str
    severity: str

    def as_dict(self) -> dict:
        return {"id": self.id, "workflow": self.workflow, "severity": self.severity}


def extract_recommender_triples(recommender_py_path: str) -> List[RecommenderTriple]:
    """
    Parse recommender.py's source for every recs.append({...}) block's
    id/workflow/severity triple. Returns [] if the file is missing/
    unreadable — the caller must not treat that as "no recommendations
    exist," only as "the source couldn't be read."
    """
    text = safe_read(Path(recommender_py_path))
    if not text:
        return []
    return [
        RecommenderTriple(id=m.group(1), workflow=m.group(2), severity=m.group(3))
        for m in _TRIPLE_RE.finditer(text)
    ]


@dataclass
class RoutingTableRow:
    id: str
    workflow: str

    def as_dict(self) -> dict:
        return {"id": self.id, "workflow": self.workflow}


def extract_routing_table(sentinel_md_path: str) -> List[RoutingTableRow]:
    """
    Parse sentinel.md's Phase 2b Routing Map table rows. Scoped to the
    '### Step 2b' section only would be more precise, but the table's ID
    column values (SEQ-* or the parenthesized scan_failure marker) are
    distinctive enough that scanning the whole file is safe in practice —
    confirmed against the real file during this engine's own build.
    """
    text = safe_read(Path(sentinel_md_path))
    if not text:
        return []
    rows: List[RoutingTableRow] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        if any(marker in line for marker in _SKIP_ROW_MARKERS):
            continue
        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        id_cell, workflow_cell = m.group(1).strip(), m.group(2).strip()
        if not id_cell.startswith("SEQ-") and not id_cell.startswith("("):
            continue
        rows.append(RoutingTableRow(id=id_cell, workflow=workflow_cell))
    return rows


@dataclass
class ParityResult:
    recommender_ids: List[str] = field(default_factory=list)
    table_ids: List[str] = field(default_factory=list)
    missing_from_table: List[str] = field(default_factory=list)
    undercounted_ids: List[str] = field(default_factory=list)
    documented_severities: Set[str] = field(default_factory=set)
    engine_severities: Set[str] = field(default_factory=set)
    undocumented_severities: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "recommender_ids": self.recommender_ids,
            "table_ids": self.table_ids,
            "missing_from_table": self.missing_from_table,
            "undercounted_ids": self.undercounted_ids,
            "documented_severities": sorted(self.documented_severities),
            "engine_severities": sorted(self.engine_severities),
            "undocumented_severities": self.undocumented_severities,
        }


def compute_parity(
    triples: List[RecommenderTriple],
    table_rows: List[RoutingTableRow],
    documented_severities: Set[str],
) -> ParityResult:
    """
    `documented_severities` is supplied by the caller (the set of severity
    tiers sentinel.md's own GLOSSARY/Phase 2a actually name — currently
    {"HIGH", "MEDIUM", "LOW"}) rather than hardcoded here, so this stays
    correct if the workflow's documented vocabulary is ever deliberately
    expanded.

    `undercounted_ids` catches the specific defect this engine was built to
    find: an ID-presence check alone is insufficient when recommender.py
    emits the SAME id from more than one distinct source block (e.g.
    SEQ-SUBSTRATE-HEALTH fires for both new-directory detection AND
    Tier-1 index/ownership issues) but the table has fewer rows for that id
    than the engine has blocks — meaning at least one triggering condition
    has no documented row at all, even though the id itself "looks" present.
    """
    recommender_ids = [t.id for t in triples]
    table_ids = [r.id for r in table_rows]
    table_id_set = set(table_ids)

    missing_from_table = sorted({tid for tid in recommender_ids if tid not in table_id_set})

    engine_counts = Counter(recommender_ids)
    table_counts = Counter(table_ids)
    undercounted_ids = sorted(
        tid for tid, count in engine_counts.items() if count > table_counts.get(tid, 0)
    )

    engine_severities = {t.severity for t in triples}
    undocumented_severities = sorted(engine_severities - documented_severities)

    return ParityResult(
        recommender_ids=recommender_ids,
        table_ids=table_ids,
        missing_from_table=missing_from_table,
        undercounted_ids=undercounted_ids,
        documented_severities=documented_severities,
        engine_severities=engine_severities,
        undocumented_severities=undocumented_severities,
    )
