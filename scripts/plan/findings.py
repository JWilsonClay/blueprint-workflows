"""
findings.py — Adversarial Audit Findings Parser
==================================================
Parses a persisted `/implementation-plan --audit` report into a mechanically
enumerated list of Critical and Medium/Lesser findings, so Phase 8
(`--remediate`) can bind each drafted `Fix N` to exactly one finding.

This module is the authority for *what findings exist* in an audit. The agent
does not enumerate findings by reading the report, exactly as it does not
enumerate a changeset by reading the plan when `git diff --stat` is available.
Judgment (what fix a finding deserves) stays with the agent; enumeration does
not.

Origin: helpdesk-tickets/20260727_implementation-plan_workflow.md — the
findings-to-remediation-phase structural gap. See `claude-commands/
implementation-plan.md` Phase 8 and STRICT RULE 29.

Design notes
------------
**Heading tolerance is the hard part, not the item parsing.** The persisted
audit corpus spans every scoring model this workflow has ever had (minimum-4,
flat 7-15, Coverage Ledger) and the heading has been written at least twenty
different ways across them: with and without `#` prefixes, bold-wrapped, upper
and mixed case, with arbitrary parentheticals, with and without a trailing
colon. The matcher is therefore deliberately loose on decoration and strict on
one thing only — the plural noun. A line reading
`**CRITICAL WEAKNESS #1 — tasks.md header contamination...**` is a *finding*,
not a section heading, and is excluded on that basis.

**The load-bearing distinction is "no findings" vs "no findings section".**
An audit that genuinely found zero Critical Weaknesses is a valid, meaningful
result (the Coverage Ledger model explicitly allows it). An audit whose
findings section could not be located is a *parse failure*. Collapsing the
second into the first would tell a user "nothing to remediate" about a report
full of Critical findings — a Hallucinated Success in engine form. They are
reported as distinct statuses and must stay that way.

**IDs.** Reports written under the Finding ID convention (2026-07-27 onward)
carry declared `CRIT-NN` / `MED-NN` prefixes. Everything persisted before it
does not, so IDs are synthesized from list position and flagged
`id_source: "positional"` — the whole reason the convention could be added
without retroactively editing a single immutable audit on disk.
"""

import re
from pathlib import Path

__all__ = [
    "parse_audit",
    "resolve_latest_audit",
    "AUDITS_DIR",
]

#: Canonical global audit registry (see implementation-plan.md Phase 5,
#: Submittal & Persistence Protocol). Suite-rooted per role.md's Script path
#: resolution constant.
AUDITS_DIR = Path.home() / "blueprint-workflows" / "implementation-plan" / "audits"

# --- Section heading matchers -------------------------------------------------
# Loose on decoration (#, **, case, trailing colon, parentheticals);
# strict on the plural noun, which is what separates a heading from a finding.
_CRITICAL_HEADING = re.compile(
    r"^\s*#{0,6}\s*\*{0,2}\s*critical\s+weaknesses\b",
    re.IGNORECASE,
)
_MEDIUM_HEADING = re.compile(
    r"^\s*#{0,6}\s*\*{0,2}\s*(medium|lesser|medium/lesser)\b[^\n]*?weaknesses\b",
    re.IGNORECASE,
)

# Any heading that ends a findings section. Recognized report sections plus a
# generic markdown-heading fallback, so an unanticipated section still
# terminates cleanly rather than swallowing the rest of the file.
_SECTION_TERMINATORS = re.compile(
    r"^\s*#{0,6}\s*\*{0,2}\s*("
    r"honest\s+assessment"
    r"|recommendations"
    r"|strengths"
    r"|coverage\s+ledger"
    r"|archival\s+markers"
    r"|category\s+scores"
    r"|comparative\s+score"
    r"|integration\s+assessment"
    r"|audit\s+findings"
    r"|final\s+assessment"
    r")\b",
    re.IGNORECASE,
)
_ANY_MD_HEADING = re.compile(r"^\s*#{1,6}\s+\S")

# --- Item matchers ------------------------------------------------------------
_LIST_ITEM = re.compile(r"^\s*(?:(\d{1,3})[.)]|[-*+])\s+(.*)$")
# Findings are also written as sub-headings under the section heading
# (`### W1 — claim (−12)`, `### 1. Title (Category)`). A heading deeper than
# the section's own level is an item boundary, not a section terminator —
# treating it as the latter silently swallows every finding in the section.
_SUB_HEADING_ITEM = re.compile(r"^\s*(#{1,6})\s+(.*)$")
_HEADING_DEPTH = re.compile(r"^\s*(#{1,6})\s")
# A fourth convention: an enumeration-labelled paragraph line with no list
# marker and no heading — `**C1 — claim**`, `WEAKNESS 1 — claim`,
# `**CRITICAL WEAKNESS #1 — claim**`. The label plus a separator must both be
# present at line start, which is tight enough not to fire on ordinary prose
# (a four-digit year fails the {1,3} bound, and a bare sentence has no
# separator in that position).
_LABELLED_ITEM = re.compile(
    r"^\s*\**\s*(?:(?:critical|medium|lesser)\s+)?(?:weakness(?:es)?\s*)?"
    r"(?:[CWM]|#)?\s*#?\d{1,3}\s*\**\s*[—–:.)-]\s*\S",
    re.IGNORECASE,
)
_DECLARED_ID = re.compile(r"^\**\s*(CRIT|MED)-(\d{1,3})\b\s*(?:[—:-]\s*)?", re.IGNORECASE)
# Deduction is written at least three ways across the corpus:
#   "Score deduction: 18 points"   "**Deduction:** 8 points"   "(−12)" / "(-12)"
# The unicode minus in the parenthetical form is not a hyphen — both are matched.
_DEDUCTION = re.compile(
    r"(?:score\s+)?deduction[:*\s]*(?:of\s+)?(\d{1,3})"
    r"|[(\[][−–—-]\s*(\d{1,3})\s*(?:pts?|points?)?[)\]]",
    re.IGNORECASE,
)
_BACKTICKED = re.compile(r"`([^`\n]+)`")
# A backticked span is a *citation* when it looks like a file reference: no
# whitespace, and either a path separator or a `name.ext` / `name.ext:line`
# tail. Everything else backticked in a finding is a code/value span (`None`,
# `FAIL`, `wb.save()`), useful context but not something a Fix can be pointed
# at. Both are kept — `raw` preserves the finding verbatim regardless, so the
# split narrows attention without discarding anything.
_CITATION_LIKE = re.compile(r"^(?=\S+$)(?:.*/.*|.*\.\w{1,8}(?::\d+(?:-\d+)?)?)$")
_BOLD_LEAD = re.compile(r"^\s*\*\*(.+?)\*\*", re.DOTALL)
_INLINE_ZERO = re.compile(r"\bnone\s+found\b|\bzero\b|\bnone\b\s*[.:]", re.IGNORECASE)
# Leading enumeration labels the sub-heading conventions use: `W1 —`, `1.`,
# `#3:`, `Weakness 2:`. Stripped before claim extraction so the claim is the
# assertion, not its index.
_ENUM_LABEL = re.compile(
    r"^\**\s*(?:weakness\s*)?#?W?\d{1,3}\s*[.):—–-]+\s*",
    re.IGNORECASE,
)
# Trailing score parenthetical (`(−12)`), captured separately as `deduction`.
_TRAILING_DEDUCTION = re.compile(r"\s*[(\[][−–—-]\s*\d{1,3}\s*(?:pts?|points?)?[)\]]\s*$")

_SEVERITY_PREFIX = {"critical": "CRIT", "medium": "MED"}


def _strip_decoration(text: str) -> str:
    """Collapse whitespace and trim trailing markdown emphasis/punctuation."""
    return re.sub(r"\s+", " ", text).strip().strip("*").strip()


def _extract_claim(body: str) -> str:
    """
    The finding's headline assertion.

    Prefers a leading bold span (the dominant convention across the corpus);
    otherwise falls back to the text up to the first em-dash separator, then to
    the first sentence, then to a hard character cap. Always returns something
    non-empty for a non-empty body — a finding with an unparseable claim is
    still a finding, and dropping it would breach the enumeration contract.

    A leading enumeration label (`W1 —`, `1.`, `#3:`) is stripped first.
    Without that, the em-dash split returns the label itself as the claim,
    which is how the sub-heading conventions degrade to a useless `"W1"`.
    """
    body = _ENUM_LABEL.sub("", body.strip(), count=1)
    body = _TRAILING_DEDUCTION.sub("", body).strip()

    bold = _BOLD_LEAD.match(body)
    if bold:
        claim = _strip_decoration(bold.group(1))
        if claim:
            return claim

    flat = _strip_decoration(body)
    for sep in (" — ", " – ", " -- "):
        if sep in flat:
            head = flat.split(sep, 1)[0].strip()
            if head:
                return head
    sentence = flat.split(". ", 1)[0].strip()
    if sentence:
        return sentence[:300]
    return flat[:300]


def _split_spans(body):
    """
    Split a finding's backticked spans into file citations and other code spans.

    Order is preserved and duplicates are dropped — audits routinely cite the
    same file several times inside one finding, and a Fix only needs the
    distinct set.
    """
    citations, code_spans = [], []
    for span in _BACKTICKED.findall(body):
        cleaned = _strip_decoration(span)
        if not cleaned:
            continue
        bucket = citations if _CITATION_LIKE.match(cleaned) else code_spans
        if cleaned not in bucket:
            bucket.append(cleaned)
    return citations, code_spans


def _heading_depth(line):
    """Markdown heading level of a line, or None when it is not a heading."""
    match = _HEADING_DEPTH.match(line)
    return len(match.group(1)) if match else None


def _collect_section(lines, start_idx):
    """
    Return the raw lines belonging to a findings section, exclusive of its heading.

    Terminates on a recognized sibling section, another findings heading, or any
    markdown heading at the same level or shallower than this section's own.
    Deeper headings are *kept* — they are the per-finding sub-headings that one
    of the corpus's three item conventions uses.
    """
    section_depth = _heading_depth(lines[start_idx]) or 0
    body = []
    for line in lines[start_idx + 1:]:
        if _SECTION_TERMINATORS.match(line) or _CRITICAL_HEADING.match(line) or _MEDIUM_HEADING.match(line):
            break
        depth = _heading_depth(line)
        if depth is not None and section_depth and depth <= section_depth:
            break
        if depth is not None and not section_depth:
            break
        body.append(line)
    return body


def _parse_items(body_lines, severity, source_ids_declared):
    """
    Parse a findings section's lines into finding dicts.

    Items may span multiple lines; a new item begins only at a list marker, so
    continuation prose (the `Impact:` clauses, which routinely run long) is
    folded into the item that owns it.
    """
    prefix = _SEVERITY_PREFIX[severity]
    # The corpus uses four mutually exclusive item conventions within a section.
    # Exactly one is selected, by precedence, and the others then read as that
    # finding's own supporting detail rather than as siblings — e.g. the
    # `- **Citation:** ...` / `- **Deduction:** 8 points` lines beneath a
    # sub-heading item are detail, not four more findings.
    if any(_SUB_HEADING_ITEM.match(line) for line in body_lines):
        convention = "sub_heading"
    elif any(_LIST_ITEM.match(line) for line in body_lines):
        convention = "list"
    elif any(_LABELLED_ITEM.match(line) for line in body_lines):
        convention = "labelled"
    else:
        convention = None

    # Sub-heading and labelled items both put the claim on the boundary line;
    # list items carry it inline in the item body.
    claim_from_head = convention in ("sub_heading", "labelled")

    raw_items = []
    current = None

    for line in body_lines:
        if convention == "sub_heading":
            match = _SUB_HEADING_ITEM.match(line)
            is_boundary = match is not None
            payload = match.group(2) if match else None
        elif convention == "list":
            match = _LIST_ITEM.match(line)
            is_boundary = match is not None
            payload = match.group(2) if match else None
        elif convention == "labelled":
            is_boundary = _LABELLED_ITEM.match(line) is not None
            payload = line.strip() if is_boundary else None
        else:
            is_boundary = False
            payload = None

        if is_boundary:
            if current is not None:
                raw_items.append(current)
            current = {"text": payload, "head": payload}
        elif current is not None and line.strip():
            current["text"] += " " + line.strip()
    if current is not None:
        raw_items.append(current)

    findings = []
    for position, item in enumerate(raw_items, start=1):
        text = item["text"]

        declared = _DECLARED_ID.match(text)
        if declared and declared.group(1).upper() == prefix:
            finding_id = f"{prefix}-{int(declared.group(2)):02d}"
            id_source = "declared"
            body = text[declared.end():]
        else:
            finding_id = f"{prefix}-{position:02d}"
            id_source = "positional"
            body = text

        # Where the convention puts the claim on the boundary line, that line
        # *is* the claim; the lines folded in beneath it are supporting detail.
        # Using the accumulated body there yields a claim hundreds of
        # characters long.
        claim_source = item["head"] if claim_from_head else body

        deduction_match = _DEDUCTION.search(body)
        deduction = None
        if deduction_match:
            deduction = int(deduction_match.group(1) or deduction_match.group(2))
        citations, code_spans = _split_spans(body)
        findings.append({
            "id": finding_id,
            "id_source": id_source,
            "severity": severity,
            "position": position,
            "claim": _extract_claim(claim_source),
            "citations": citations,
            "code_spans": code_spans,
            "deduction": deduction,
            "raw": _strip_decoration(body),
        })

    if findings and all(f["id_source"] == "declared" for f in findings):
        source_ids_declared.append(True)
    elif findings:
        source_ids_declared.append(False)

    return findings


def _find_section(lines, matcher):
    """Locate a findings section heading. Returns (index, heading_text) or (None, None)."""
    for idx, line in enumerate(lines):
        if matcher.match(line):
            # `**CRITICAL WEAKNESS #1 — ...**` is a finding, not a heading; the
            # plural requirement in the matcher already excludes the singular
            # form, but an explicit `#N` immediately after the noun is a second,
            # cheap guard against a heading-shaped finding line.
            if re.search(r"weaknesses\s*#\s*\d", line, re.IGNORECASE):
                continue
            return idx, line.strip()
    return None, None


def parse_audit(audit_path):
    """
    Parse a persisted adversarial audit report into an enumerated Findings Ledger.

    Returns a report dict:
        {
          "audit_path":  str,
          "audit_name":  str,              # the citable key prefix
          "status":      "ok" | "no_findings_section" | "unreadable",
          "id_source":   "declared" | "positional" | "mixed" | "none",
          "sections":    {"critical": bool, "medium": bool},   # heading located?
          "findings":    [ {...}, ... ],
          "summary":     {"critical": int, "medium": int, "total": int,
                          "total_deduction": int|None},
          "errors":      [str, ...],
        }

    `status` distinguishes the two outcomes that must never be conflated:
    `"ok"` with an empty findings list means the audit genuinely reported no
    findings; `"no_findings_section"` means no findings section could be
    located and the result carries no information about the audit's content.
    Phase 8 HALTs on the latter.
    """
    path = Path(audit_path)
    report = {
        "audit_path": str(path),
        "audit_name": path.name,
        "status": "ok",
        "id_source": "none",
        "sections": {"critical": False, "medium": False},
        "findings": [],
        "summary": {"critical": 0, "medium": 0, "total": 0, "total_deduction": None},
        "errors": [],
    }

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeError) as exc:
        report["status"] = "unreadable"
        report["errors"].append(f"Cannot read audit report: {exc}")
        return report

    lines = text.splitlines()
    declared_flags = []

    for severity, matcher in (("critical", _CRITICAL_HEADING), ("medium", _MEDIUM_HEADING)):
        idx, heading = _find_section(lines, matcher)
        if idx is None:
            continue
        report["sections"][severity] = True

        body_lines = _collect_section(lines, idx)
        found = _parse_items(body_lines, severity, declared_flags)

        # A heading that declares its own emptiness ("Critical Weaknesses: none
        # found...") is a genuine zero, and the corpus contains real examples.
        if not found and not _INLINE_ZERO.search(heading or ""):
            joined = " ".join(body_lines).strip()
            if joined and not _INLINE_ZERO.search(joined):
                report["errors"].append(
                    f"'{severity}' section located but no list items parsed; "
                    "content present but not in a recognized list form."
                )
        report["findings"].extend(found)

    if not report["sections"]["critical"] and not report["sections"]["medium"]:
        report["status"] = "no_findings_section"
        report["errors"].append(
            "No Critical or Medium/Lesser Weaknesses section could be located. "
            "This is a parse failure, NOT a zero-findings result — do not treat "
            "it as 'nothing to remediate'."
        )
        return report

    if declared_flags:
        if all(declared_flags):
            report["id_source"] = "declared"
        elif any(declared_flags):
            report["id_source"] = "mixed"
        else:
            report["id_source"] = "positional"

    deductions = [f["deduction"] for f in report["findings"] if f["deduction"] is not None]
    report["summary"] = {
        "critical": sum(1 for f in report["findings"] if f["severity"] == "critical"),
        "medium": sum(1 for f in report["findings"] if f["severity"] == "medium"),
        "total": len(report["findings"]),
        "total_deduction": sum(deductions) if deductions else None,
    }
    return report


def resolve_latest_audit(workspace, audits_dir=None):
    """
    Resolve the most recent persisted audit for a workspace.

    Audit filenames follow `YYYYMMDD-HHMM-<workspace>.md` (Phase 5's Submittal &
    Persistence Protocol), so lexical ordering on the filename is chronological
    ordering. Workstream audits (`-workstreams.md`) are excluded — they are
    Phase 7 artifacts with a different report shape and are not `--remediate`
    inputs.

    Returns a Path, or None when nothing matches. Callers HALT on None rather
    than widening the search — drafting one project's remediation from another
    project's audit is the failure shape CLOSED_20260707_suite-script-path-
    resolution_workflow.md already cost this suite once.
    """
    directory = Path(audits_dir) if audits_dir else AUDITS_DIR
    if not directory.is_dir():
        return None

    name = Path(workspace).resolve().name
    candidates = [
        p for p in directory.glob(f"*-{name}.md")
        if not p.name.endswith("-workstreams.md")
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: p.name)[-1]
