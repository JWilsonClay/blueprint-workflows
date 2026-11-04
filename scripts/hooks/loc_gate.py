#!/usr/bin/env python3
"""Staged executable-line gate. ``--staged`` is required."""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from hooks import scoring
from hooks.staged import prepare


def _loc_line(path, count, cfg, exempt):
    if count >= cfg.reject:
        band = "reject"
    elif count >= cfg.maintain:
        band = "maintain"
    elif count > cfg.aim:
        band = "aim"
    else:
        return None, False
    reason = exempt.loc_reason
    extra = ""
    if band == "reject" and reason:
        shown = "exempt"
        exempt_field = reason
        bad = False
    elif band == "reject" and exempt.loc_empty:
        shown = "reject"
        exempt_field = "-"
        extra = " empty-reason=LOC-EXEMPT"
        bad = True
    elif band == "reject":
        shown = "reject"
        exempt_field = "-"
        bad = True
    else:
        shown = band
        exempt_field = reason if reason else "-"
        bad = False
    line = (
        f"loc {path} executable={count} aim={cfg.aim} "
        f"maintain={cfg.maintain} reject={cfg.reject} "
        f"band={shown} exempt={exempt_field}{extra}"
    )
    return line, bad


def main(argv=None):
    prepared = prepare(argv)
    if prepared.exit_code is not None:
        return prepared.exit_code
    failed = False
    for item in prepared.files:
        try:
            count = scoring.executable_line_count(item.blob)
            exempt = scoring.exemptions(item.blob)
        except scoring.GateSyntaxError as exc:
            print(scoring.syntax_line(item.path, exc))
            failed = True
            continue
        line, bad = _loc_line(item.path, count, prepared.cfg, exempt)
        if line:
            print(line)
        if bad:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
