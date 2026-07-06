"""
recommender.py — Protocol Recommender
=======================================
Intelligence layer for the Doorway Protocol.
Analyzes drift results from the structural auditor and maps them to
specific workflow/protocol IDs that an agent should invoke next.

This module is stateless — it receives a drift dict and returns a list
of recommendations. It does not read from or write to any filesystem path.

Refactored from .blueprints/governance/thedoorway/recommender.py:
  - No path changes needed (stateless module).
  - Expanded recommendation set to include global_workflows workflow IDs
    alongside the original .blueprints SEQ protocol IDs.
  - Added 'workflow' key to each recommendation entry for direct workflow routing.
"""


class ProtocolRecommender:
    """
    Intelligence layer for the Doorway Protocol.
    Maps detected workspace drift conditions to actionable protocol/workflow IDs.
    """

    def recommend(self, drift: dict) -> list:
        """
        Analyzes drift results and returns a ranked list of recommended
        actions, each identified by both a .blueprints protocol ID and the
        corresponding global_workflows workflow trigger.

        Args:
            drift: Output dict from StructuralAuditor.audit(), containing
                   keys: 'new', 'modified', 'deleted', 'unowned', 'missing_readme'.

        Returns:
            List of recommendation dicts, each with:
                id       — .blueprints protocol ID
                workflow — global_workflows equivalent trigger
                reason   — human-readable explanation
                severity — 'HIGH', 'MEDIUM', or 'LOW'
        """
        recs = []

        if drift.get("new"):
            new_entries = drift["new"]
            # P1 bootstrap tagging: inaugural run produces many "new"; suppress
            # SEQ-SUBSTRATE-HEALTH (expected, not actionable) per PILLAR_01.
            is_bootstrap = any("[BOOTSTRAP]" in str(e) for e in new_entries)
            if not is_bootstrap:
                dirs = ", ".join(new_entries[:3])
                recs.append({
                    "id": "SEQ-SUBSTRATE-HEALTH",
                    "workflow": "/investigate",
                    "reason": (
                        f"New directories detected ({dirs}). "
                        "Verify architectural alignment before proceeding."
                    ),
                    "severity": "MEDIUM",
                })

        if drift.get("unowned"):
            dirs = ", ".join(drift["unowned"][:3])
            recs.append({
                "id": "SEQ-SUBSTRATE-HYGIENE",
                "workflow": "/document",
                "reason": (
                    f"Unowned directories found ({dirs}). "
                    "Update FOLDER_OWNERSHIP.md to prevent logic bloat."
                ),
                "severity": "MEDIUM",
            })

        if drift.get("missing_readme"):
            dirs = ", ".join(drift["missing_readme"][:3])
            recs.append({
                "id": "SEQ-SUBSTRATE-MAINTAIN",
                "workflow": "/document",
                "reason": (
                    f"Directories without README files ({dirs}). "
                    "Breadcrumb web is incomplete — regenerate documentation."
                ),
                "severity": "LOW",
            })

        if drift.get("deleted"):
            dirs = ", ".join(drift["deleted"][:3])
            recs.append({
                "id": "SEQ-STRATEGIC-ARCHIVAL",
                "workflow": "/investigate",
                "reason": (
                    f"Deleted directories detected ({dirs}). "
                    "Confirm intentional removal; update MANIFEST and ownership records."
                ),
                "severity": "HIGH",
            })

        if drift.get("modified") and len(drift["modified"]) > 5:
            recs.append({
                "id": "SEQ-SUBSTRATE-ASSIMILATE",
                "workflow": "/focus-plan",
                "reason": (
                    f"{len(drift['modified'])} directories show content changes. "
                    "Broad modification sweep warrants a full substrate re-assimilation."
                ),
                "severity": "HIGH",
            })

        return recs
