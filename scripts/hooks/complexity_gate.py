#!/usr/bin/env python3
"""Staged per-function cognitive and argument-count gate. ``--staged`` is required."""

import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from hooks import scoring
from hooks.staged import prepare


_NOTE_NESTED = (
    "nested function has no McCabe graph of its own; "
    "displayed 1 is not a measurement and is not a gate"
)
_NOTE_OTHER = "informational only; not a gate"


def _touched(item, posts):
    if item.added:
        return set(posts)
    pre_facts = []
    if item.pre_image is not None:
        try:
            pre_tree = scoring.parse_module(scoring.decode_source(item.pre_image))
        except scoring.GateSyntaxError:
            return set(posts)
        pre_facts = scoring.iter_functions(pre_tree)
    pre_by = defaultdict(list)
    for fact in pre_facts:
        pre_by[fact.qualname].append(fact)
    post_by = defaultdict(list)
    for fact in posts:
        post_by[fact.qualname].append(fact)
    touched = set()
    for hunk in item.hunks:
        # new_count == 0 is a pure deletion: do not touch new_start or the line before it.
        if hunk.new_count != 0:
            for line in hunk.new_lines:
                for fact in posts:
                    if fact.start <= line <= fact.end:
                        touched.add(fact)
        for line in hunk.old_lines:
            for qual, pres in pre_by.items():
                same = post_by.get(qual, [])
                for index, pre in enumerate(pres):
                    if index < len(same) and pre.start <= line <= pre.end:
                        touched.add(same[index])
    return touched


def _complexity_line(path, fact, cfg, exempt):
    cognitive = scoring.cognitive(fact.node, fact.base_nesting)
    args = scoring.argument_count(fact.node)
    over_cog = cognitive > cfg.cognitive
    over_args = args > cfg.max_args
    if not over_cog and not over_args:
        return None, False
    cog_reason = exempt.cog(fact.node.lineno)
    args_reason = exempt.args(fact.node.lineno)
    failed = []
    saved = []
    if over_cog and not cog_reason:
        failed.append("cognitive")
    if over_args and not args_reason:
        failed.append("args")
    if over_cog and cog_reason:
        saved.append("COG")
    if over_args and args_reason:
        saved.append("ARGS")
    note = _NOTE_NESTED if fact.nested else _NOTE_OTHER
    mccabe = scoring.mccabe_display(fact.node, fact.nested)
    result = "reject" if failed else "exempt"
    line = (
        f"complexity {path}::{fact.qualname} "
        f"cognitive={cognitive} ceiling={cfg.cognitive} "
        f"args={args} max_args={cfg.max_args} "
        f'mccabe={mccabe} mccabe_note="{note}" '
        f"result={result} failed={','.join(failed) if failed else '-'} "
        f"exempt={','.join(saved) if saved else '-'}"
    )
    return line, bool(failed)


def main(argv=None):
    prepared = prepare(argv)
    if prepared.exit_code is not None:
        return prepared.exit_code
    failed = False
    for item in prepared.files:
        try:
            tree = scoring.parse_module(scoring.decode_source(item.blob))
            exempt = scoring.exemptions(item.blob)
            posts = scoring.iter_functions(tree)
            touched = _touched(item, posts)
        except scoring.GateSyntaxError as exc:
            print(scoring.syntax_line(item.path, exc))
            failed = True
            continue
        for fact in posts:
            if fact not in touched:
                continue
            line, bad = _complexity_line(item.path, fact, prepared.cfg, exempt)
            if line:
                print(line)
            if bad:
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
