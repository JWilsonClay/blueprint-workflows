"""
reporter.py — Gitignore seeder report rendering (human + JSON)
"""

import json


class SeederReporter:
    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        action = report["block_action"]
        print("=" * 64)
        print("  SOVEREIGN GITIGNORE SEEDER")
        print(f"  Workspace:  {report['workspace']}")
        print(f"  .gitignore: {report['gitignore_path']}")
        print(f"  Managed block:  {action}   ({report['managed_patterns']} patterns)")
        if not report["git_repo"]:
            print("  Git repo:   NO — secret scan skipped (not a git repository)")
        print("=" * 64)

        if action == "unchanged":
            print("  Managed block already current — nothing to write (idempotent).")
        elif report["wrote"]:
            print(f"  Wrote managed block ({action}); user entries left untouched.")
        else:
            print(f"  [report-only] Would {action} the managed block; no file written.")

        secrets = report["tracked_secrets"]
        if secrets:
            print("-" * 64)
            print(f"  ⚠  WARNING — {len(secrets)} secret/credential file(s) ALREADY TRACKED:")
            for hit in secrets:
                print(f"      {hit['path']}   (matched: {hit['pattern']})")
            print("  A .gitignore does NOT remove these from history. They are already")
            print("  committed. To scrub them from ALL git history, run:  /gitclean --mode a")
        else:
            if report["git_repo"]:
                print("  Secret scan: clean — no already-tracked secrets detected.")

        print("-" * 64)
        print(f"  (advisory) {report['summary']['advisory']}")
        print("=" * 64)
