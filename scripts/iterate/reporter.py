"""
reporter.py — Iterate (Mock-Trap) Evidence Reporter
=====================================================
Renders the IterateAuditor report as JSON (for /iterate-test to consume) or a
compact human-readable summary. Mirrors the doorway/focus/quality/harden reporter
contract: --output-json wins, --quiet suppresses human output.
"""

import json


class IterateReporter:
    """Renders an iterate-audit report dict to stdout."""

    def render(self, report: dict, quiet: bool = False, output_json: bool = False) -> None:
        if output_json:
            print(json.dumps(report, indent=2))
            return
        if quiet:
            return

        summary = report.get("summary", {})
        print(f"\n=== {report.get('workspace', 'workspace')} — Mock-Trap Evidence ===")
        print(f"  NOTE: {summary.get('advisory', '')}")
        if report.get("subject"):
            print(f"  Subject under test: {report['subject']}")

        print(
            f"\nTests analyzed: {summary.get('tests_scanned', 0)} | "
            f"mock-trap candidates: {summary.get('mock_trap_candidate_files', 0)} | "
            f"hardcoded-assertion: {summary.get('hardcoded_assertion_files', 0)} | "
            f"no-production-import: {summary.get('no_production_import_files', 0)} | "
            f"parse errors: {summary.get('parse_error_files', 0)}"
        )

        for f in report.get("files", []):
            sig = f.get("file_signal", "?")
            if sig == "LIVE":
                continue  # nothing actionable to show for a live-exercised file
            print(f"\n  {f['path']}  [{sig}]")
            print(f"    {f.get('signal_basis', '')}")
            for s in f.get("symbols", []):
                if s["fidelity"] == "MOCK_TRAP_CANDIDATE":
                    how = s.get("patch_how") or {}
                    subj = " (SUBJECT)" if s.get("is_subject") else ""
                    print(f"    - mocked: {s['name']}{subj} "
                          f"← patch target '{how.get('target', '?')}' "
                          f"(L{how.get('lineno', '?')}, {how.get('kind', '?')})")
            for t in f.get("hardcoded_assertions", [])[:6]:
                print(f"    - hardcoded assertion: canned@L{t['lineno_canned']} "
                      f"echoed in assert@L{t['lineno_assert']} ({t['value_repr']})")

        print(f"\nVerdict hint: {summary.get('verdict_hint', '?')} "
              f"(advisory — mechanical import/patch/call facts only; "
              f"the PRIMARY/INFRASTRUCTURE call and the HOT verdict stay the agent's)")
