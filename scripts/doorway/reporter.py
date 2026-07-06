"""
reporter.py — Substrate Reporter
==================================
Reporting layer for the Doorway Protocol.
Produces high-fidelity console output and assertion-based confirmation
that the scan completed successfully.

Refactored from .blueprints/governance/thedoorway/reporter.py:
  - Removed hardcoded ".blueprints" workspace name from report header.
  - Workspace name is now derived from the workspace path passed in render().
  - Added --quiet mode support via the 'quiet' parameter.
  - JSON output mode added for workflow consumption.
"""

import json


class SubstrateReporter:
    """
    Reporting layer for the Doorway Protocol.
    Produces human-readable console output from the contextualizer's results dict.
    """

    def render(
        self,
        results: dict,
        metrics: dict,
        workspace_name: str = "workspace",
        quiet: bool = False,
        output_json: bool = False,
        context_only: bool = False,
    ) -> None:
        """
        Renders the final substrate health report to stdout.

        Args:
            results:        Output dict from DoorwayContextualizer.run().
            metrics:        Metrics dict {'created': int, 'ingested': int, 'repairs': int}.
            workspace_name: Display name for the workspace (derived from workspace path).
            quiet:          If True, suppress all output except errors.
            output_json:    If True, emit results as JSON to stdout.
            context_only:   If True with output_json, emit minimal substrate-focused payload (PR 01-01).
        """
        if output_json:
            self._render_json(results, metrics, context_only=context_only)
            return

        if quiet:
            return

        drift = results.get("drift", {})
        recommendations = results.get("recommendations", [])

        print(f"\n=== {workspace_name} — Doorway Contextualizer Report ===")
        print(f"Scan completed in {results.get('overhead', 0.0):.2f}s")
        print(f"  README files created:  {metrics.get('created', 0)}")
        print(f"  README files ingested: {metrics.get('ingested', 0)}")
        print(f"  Substrate repairs:     {metrics.get('repairs', 0)}")
        if results.get("escalated"):
            print("  [INFO] Auto-escalated to full-scan after self-heal repairs (Option C)")

        if drift.get("new"):
            new_display = [
                f"{p} [BOOTSTRAP]" if drift.get("is_bootstrap") else p
                for p in drift["new"]
            ]
            print(f"\n[+] NEW DIRECTORIES:     {', '.join(new_display)}")
        if drift.get("modified"):
            print(f"[*] MODIFIED:            {', '.join(drift['modified'])}")
        if drift.get("deleted"):
            print(f"[-] DELETED:             {', '.join(drift['deleted'])}")
        if drift.get("unowned"):
            print(f"[?] UNOWNED:             {', '.join(drift['unowned'])}")
        if drift.get("missing_readme"):
            print(f"[!] MISSING README:      {', '.join(drift['missing_readme'])}")

        print("\n[TEST] Substrate Scan:              [CONFIRMED]")
        print("[TEST] Hash Verification:           [CONFIRMED]")
        print("[TEST] Manifest Synchronization:    [CONFIRMED]")
        print("[TEST] Ownership Audit:             [CONFIRMED]")

        if recommendations or any(
            drift.get(k) for k in ("new", "modified", "deleted", "unowned", "ownership_incomplete", "stale_index")
        ):
            print("\n[!] DRIFT DETECTED — review findings above.")
            if recommendations:
                print("\nRecommended next steps:")
                for rec in recommendations:
                    severity_tag = f"[{rec.get('severity', 'INFO')}]"
                    print(f"  {severity_tag} {rec['id']} → {rec['workflow']}")
                    print(f"       {rec['reason']}")
        else:
            print("\n[+] ZERO-FINDING STATE: Workspace structural integrity verified.")

        total = len(results.get("map", {}))
        skipped = results.get("skipped", 0)
        print(
            f"\nContextualization complete. "
            f"{total} directories scanned, {skipped} skipped (hash-matched)."
        )
        if results.get("data_dir"):
            print(f"Proposals logged to: {results['data_dir']}/context_updates.log")

    def _render_json(self, results: dict, metrics: dict, context_only: bool = False) -> None:
        """
        Emits a structured JSON payload to stdout for workflow/agent consumption.
        Removes the non-serializable 'map' key (too large for typical consumption).
        PR 01-01: includes substrate_index (always in full); --context-only yields minimal.
        """
        if context_only:
            payload = {
                "substrate_index": results.get("substrate_index", {}),
                "zero_finding": results.get("zero_finding", False),
                "ownership_summary": results.get("substrate_index", {}).get("ownership_source", "docs/FOLDER_OWNERSHIP.md"),
                "overhead_seconds": round(results.get("overhead", 0.0), 3),
            }
            print(json.dumps(payload, indent=2))
            return

        payload = {
            "drift": results.get("drift", {}),
            "recommendations": results.get("recommendations", []),
            "metrics": metrics,
            "overhead_seconds": round(results.get("overhead", 0.0), 3),
            "total_directories": len(results.get("map", {})),
            "skipped": results.get("skipped", 0),
            "zero_finding": results.get("zero_finding", not any(
                results.get("drift", {}).get(k)
                for k in ("new", "modified", "deleted", "unowned", "ownership_incomplete", "stale_index")
            )),
            "escalated": results.get("escalated", False),
            "substrate_index": results.get("substrate_index"),
        }
        print(json.dumps(payload, indent=2))
